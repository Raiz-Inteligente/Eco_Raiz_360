"""
========================================================================
PIPELINE DE DADOS CLIMÁTICOS POR MUNICÍPIO - BRASIL
Projeto: Inteligência Agroambiental / Agricultura de Precisão
========================================================================

Fluxo:
  IBGE (municípios oficiais) + base de coordenadas por município
        -> validação e limpeza
        -> divisão em lotes
        -> Open-Meteo (multi-coordenadas por requisição)
        -> associação dados climáticos <-> município
        -> gravação incremental em Parquet (evita estourar memória)
        -> pós-processamento / engenharia de atributos / dashboards
"""

import time
import json
import logging
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import requests

# ---------------------------------------------------------------------
# CONFIGURAÇÃO GERAL
# --------------------------------------------------------------------- 
ANO_INICIAL = "2019-01-01"
ANO_FINAL = "2024-12-31"

# Quantos municípios por requisição à Open-Meteo.
# A API aceita várias coordenadas numa única chamada. Com dados diários
# (~4 mil linhas por município para 11 anos), lotes maiores já são
# seguros, mas mantemos um valor moderado para reduzir risco de
# timeout/erro e permitir checkpoint de progresso.
# Tamanho inicial do lote. Não precisa ser exato: se a Open-Meteo recusar
# (HTTP 400, geralmente por excesso de coordenadas/volume de dados por
# requisição), o lote é dividido automaticamente ao meio até funcionar.
BATCH_SIZE = 30

# Regiões a processar. Deixe como None (ou lista vazia) para processar
# TODAS as regiões do Brasil; ou informe uma lista para restringir,
# por exemplo: ["Centro-Oeste", "Sul"].
REGIOES_ALVO = ["Centro-Oeste", "Sul"]

TIMEOUT_SEGUNDOS = 60
MAX_TENTATIVAS = 4
ESPERA_ENTRE_TENTATIVAS = 8  # segundos, cresce a cada nova tentativa (backoff)

URL_OPEN_METEO = "https://archive-api.open-meteo.com/v1/archive"
URL_IBGE_MUNICIPIOS = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
# Base pública com código IBGE + latitude/longitude de sede de todos os
# municípios brasileiros (derivada de dados do IBGE). A API oficial de
# localidades do IBGE (acima) não devolve latitude/longitude, apenas a
# hierarquia administrativa (código, nome, UF, região). Por isso os dois
# são cruzados pelo código IBGE.
URL_COORDENADAS_MUNICIPIOS = (
    "https://raw.githubusercontent.com/kelvins/municipios-brasileiros/main/csv/municipios.csv"
)

SAIDA_DIR = Path("dados_tratados")
SAIDA_PARQUET_DIR = SAIDA_DIR / "clima_municipios_parquet"
SAIDA_LOG_ERROS = SAIDA_DIR / "municipios_com_erro.parquet"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("clima_municipios")


class LoteMuitoGrandeError(Exception):
    """Sinaliza que a Open-Meteo recusou o lote (HTTP 400), tipicamente por
    excesso de coordenadas/volume de dados em uma única requisição."""


# =======================================================================
# ETAPA 1 - BASE DE MUNICÍPIOS (IDENTIFICAÇÃO OFICIAL + COORDENADAS)
# =======================================================================
def obter_municipios_ibge() -> pd.DataFrame:
    """Busca a lista oficial de municípios na API de Localidades do IBGE.

    Retorna: codigo_ibge, municipio, uf, regiao
    """
    logger.info("Consultando API de Localidades do IBGE...")
    resposta = requests.get(URL_IBGE_MUNICIPIOS, timeout=TIMEOUT_SEGUNDOS)
    resposta.raise_for_status()
    dados = resposta.json()

    registros = []
    for item in dados:
        try:
            uf = item["microrregiao"]["mesorregiao"]["UF"]
            registros.append(
                {
                    "codigo_ibge": item["id"],
                    "municipio": item["nome"],
                    "uf": uf["sigla"],
                    "regiao": uf["regiao"]["nome"],
                }
            )
        except (KeyError, TypeError):
            # Alguns municípios (poucos) usam regiao-imediata em vez de
            # microrregiao na resposta do IBGE; tratamos como fallback.
            uf = item.get("regiao-imediata", {}).get("regiao-intermediaria", {}).get("UF", {})
            registros.append(
                {
                    "codigo_ibge": item["id"],
                    "municipio": item["nome"],
                    "uf": uf.get("sigla"),
                    "regiao": uf.get("regiao", {}).get("nome"),
                }
            )

    df = pd.DataFrame(registros)
    logger.info("IBGE retornou %d municípios.", len(df))
    return df


def obter_coordenadas_municipios() -> pd.DataFrame:
    """Busca latitude/longitude de sede de cada município (por código IBGE).

    Retorna: codigo_ibge, latitude, longitude
    """
    logger.info("Baixando base de coordenadas por município...")
    df = pd.read_csv(URL_COORDENADAS_MUNICIPIOS)
    df = df.rename(columns={"codigo_ibge": "codigo_ibge"})
    df = df[["codigo_ibge", "latitude", "longitude"]].copy()
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    logger.info("Base de coordenadas com %d municípios.", len(df))
    return df


def montar_base_municipios() -> pd.DataFrame:
    """Une identificação oficial (IBGE) com coordenadas por município,
    filtra pelas regiões-alvo (REGIOES_ALVO) e valida as coordenadas."""
    municipios = obter_municipios_ibge()

    if REGIOES_ALVO:
        municipios = municipios[municipios["regiao"].isin(REGIOES_ALVO)].reset_index(drop=True)
        logger.info(
            "Filtrando para as regiões %s: %d municípios restantes.",
            REGIOES_ALVO, len(municipios),
        )

    coordenadas = obter_coordenadas_municipios()

    base = municipios.merge(coordenadas, on="codigo_ibge", how="left")

    sem_coordenada = base["latitude"].isna() | base["longitude"].isna()
    n_sem_coordenada = int(sem_coordenada.sum())
    if n_sem_coordenada:
        logger.warning(
            "%d municípios sem coordenada válida foram removidos do processamento.",
            n_sem_coordenada,
        )

    # Bounding box aproximado do território brasileiro, para descartar
    # coordenadas absurdas sem "inventar" nenhum valor novo.
    dentro_do_brasil = (
        base["latitude"].between(-34, 6)
        & base["longitude"].between(-74, -32)
    )

    base_valida = base[~sem_coordenada & dentro_do_brasil].reset_index(drop=True)
    base_invalida = base[sem_coordenada | ~dentro_do_brasil].copy()

    if not base_invalida.empty:
        SAIDA_DIR.mkdir(parents=True, exist_ok=True)
        base_invalida.to_parquet(SAIDA_DIR / "municipios_sem_coordenada_valida.parquet", index=False)

    logger.info(
        "Base final: %d municípios válidos de %d totais.", len(base_valida), len(base)
    )
    return base_valida


# =======================================================================
# ETAPA 2 - CONSULTA À OPEN-METEO EM LOTES
# =======================================================================
def dividir_em_lotes(df: pd.DataFrame, tamanho_lote: int = BATCH_SIZE):
    """Gera fatias sequenciais do DataFrame de municípios."""
    for inicio in range(0, len(df), tamanho_lote):
        yield df.iloc[inicio : inicio + tamanho_lote].reset_index(drop=True)


def consultar_open_meteo_lote(lote: pd.DataFrame) -> list:
    """Consulta a Open-Meteo para várias coordenadas em uma única requisição.

    Retorna a lista de respostas (uma por município, na mesma ordem do lote).
    Implementa retry com backoff para timeout / erro HTTP 429 / erro temporário.
    Erros HTTP 400 (requisição malformada, ex.: excesso de coordenadas para
    o plano gratuito) NÃO são reenviados sem alteração — eles são sinalizados
    imediatamente para que o chamador reduza o tamanho do lote.
    """
    params = {
        "latitude": lote["latitude"].tolist(),
        "longitude": lote["longitude"].tolist(),
        "start_date": ANO_INICIAL,
        "end_date": ANO_FINAL,
        "daily": ["temperature_2m_mean", "precipitation_sum"],
        "timezone": "America/Sao_Paulo",
    }

    ultima_excecao = None
    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            resposta = requests.get(URL_OPEN_METEO, params=params, timeout=TIMEOUT_SEGUNDOS)

            if resposta.status_code == 429:
                # Rate limit: espera mais e tenta de novo.
                espera = ESPERA_ENTRE_TENTATIVAS * tentativa
                logger.warning("Rate limit atingido. Aguardando %ds...", espera)
                time.sleep(espera)
                continue

            if resposta.status_code == 400:
                # Erro de requisição (ex.: lote grande demais para o plano
                # gratuito). Repetir a MESMA requisição não resolve, então
                # sinalizamos já na primeira tentativa (LoteMuitoGrandeError)
                # para o chamador dividir o lote e tentar de novo.
                logger.warning("HTTP 400 no lote de %d municípios. Corpo: %s", len(lote), resposta.text[:500])
                raise LoteMuitoGrandeError(resposta.text[:500])

            resposta.raise_for_status()
            dados = resposta.json()

            # Quando há apenas 1 coordenada, a API devolve um objeto único
            # em vez de uma lista. Padronizamos sempre para lista.
            if isinstance(dados, dict):
                dados = [dados]

            if not dados:
                raise ValueError("Resposta vazia da Open-Meteo.")

            return dados

        except LoteMuitoGrandeError:
            raise
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            ultima_excecao = exc
            logger.warning(
                "Tentativa %d/%d falhou (timeout/conexão): %s",
                tentativa, MAX_TENTATIVAS, exc,
            )
        except requests.exceptions.HTTPError as exc:
            ultima_excecao = exc
            logger.warning(
                "Tentativa %d/%d falhou (HTTP %s): %s",
                tentativa, MAX_TENTATIVAS, resposta.status_code, exc,
            )
        except (ValueError, KeyError) as exc:
            ultima_excecao = exc
            logger.warning(
                "Tentativa %d/%d falhou (resposta inválida): %s",
                tentativa, MAX_TENTATIVAS, exc,
            )

        time.sleep(ESPERA_ENTRE_TENTATIVAS * tentativa)

    raise RuntimeError(f"Falha após {MAX_TENTATIVAS} tentativas: {ultima_excecao}")


def consultar_com_divisao_automatica(lote: pd.DataFrame, profundidade: int = 0):
    """Consulta a Open-Meteo para um lote e, se a API rejeitar por excesso
    de coordenadas (HTTP 400), divide o lote ao meio recursivamente até
    encontrar um tamanho aceito — ou isolar o(s) município(s) problemático(s).

    Retorna uma tupla (respostas, erros):
      - respostas: lista de tuplas (municipio_series, resposta_json) para
        os municípios atendidos com sucesso.
      - erros: lista de tuplas (municipio_series, motivo) para os
        municípios que falharam mesmo isolados — nunca silenciosamente
        descartados.
    """
    try:
        respostas_json = consultar_open_meteo_lote(lote)
        pares = list(zip([linha for _, linha in lote.iterrows()], respostas_json))
        return pares, []
    except LoteMuitoGrandeError as exc:
        if len(lote) == 1:
            return [], [(lote.iloc[0], f"Rejeitado pela Open-Meteo mesmo isolado: {exc}")]

        meio = len(lote) // 2
        metade_1 = lote.iloc[:meio].reset_index(drop=True)
        metade_2 = lote.iloc[meio:].reset_index(drop=True)

        logger.info(
            "Lote de %d municípios rejeitado (HTTP 400). Dividindo em %d + %d "
            "e tentando novamente (profundidade %d)...",
            len(lote), len(metade_1), len(metade_2), profundidade + 1,
        )

        pares_1, erros_1 = consultar_com_divisao_automatica(metade_1, profundidade + 1)
        pares_2, erros_2 = consultar_com_divisao_automatica(metade_2, profundidade + 1)
        return pares_1 + pares_2, erros_1 + erros_2
    except RuntimeError as exc:
        # Falha "normal" (timeout/erro de rede/etc. após todas as
        # tentativas) — não é um problema de tamanho de lote, então não
        # adianta dividir. Marca todo este sub-lote como erro.
        return [], [(municipio, str(exc)) for _, municipio in lote.iterrows()]


def resposta_para_dataframe(municipio_info: pd.Series, resposta_json: dict) -> pd.DataFrame:
    """Converte a resposta diária de UM município em DataFrame, já
    identificado com os dados cadastrais desse município."""
    daily = resposta_json.get("daily")
    if not daily or "time" not in daily:
        raise ValueError("Município sem dados climáticos na resposta.")

    df = pd.DataFrame(
        {
            "data": daily["time"],
            "temperatura": daily.get("temperature_2m_mean"),
            "precipitacao": daily.get("precipitation_sum"),
        }
    )
    df["codigo_ibge"] = municipio_info["codigo_ibge"]
    df["municipio"] = municipio_info["municipio"]
    df["uf"] = municipio_info["uf"]
    df["regiao"] = municipio_info["regiao"]
    df["latitude"] = municipio_info["latitude"]
    df["longitude"] = municipio_info["longitude"]
    return df


# =======================================================================
# ETAPA 3 - ORQUESTRAÇÃO: PERCORRE TODOS OS LOTES E GRAVA EM PARQUET
# =======================================================================
def processar_todos_os_municipios(base_municipios: pd.DataFrame) -> dict:
    """Executa a coleta completa, grava resultados incrementalmente em
    Parquet (particionado por região, para não acumular tudo em memória)
    e devolve um resumo com as métricas pedidas."""

    SAIDA_PARQUET_DIR.mkdir(parents=True, exist_ok=True)
    SAIDA_DIR.mkdir(parents=True, exist_ok=True)

    lotes = list(dividir_em_lotes(base_municipios, BATCH_SIZE))
    total_lotes = len(lotes)

    municipios_com_erro = []
    total_processados = 0
    total_sucesso = 0
    total_registros_climaticos = 0

    for indice_lote, lote in enumerate(lotes, start=1):
        logger.info("Processando lote %d/%d (%d municípios)...", indice_lote, total_lotes, len(lote))

        pares_sucesso, erros_lote = consultar_com_divisao_automatica(lote)

        for municipio, motivo in erros_lote:
            municipios_com_erro.append({**municipio.to_dict(), "motivo_erro": motivo})
        total_processados += len(lote)

        dfs_lote = []
        for municipio, resposta_json in pares_sucesso:
            try:
                df_municipio = resposta_para_dataframe(municipio, resposta_json)
                dfs_lote.append(df_municipio)
                total_sucesso += 1
            except (ValueError, KeyError) as exc:
                municipios_com_erro.append({**municipio.to_dict(), "motivo_erro": str(exc)})

        if dfs_lote:
            df_lote_final = pd.concat(dfs_lote, ignore_index=True)
            total_registros_climaticos += len(df_lote_final)
            _gravar_lote_parquet(df_lote_final, indice_lote)

        # Libera memória do lote antes de seguir.
        del pares_sucesso, dfs_lote

    if municipios_com_erro:
        pd.DataFrame(municipios_com_erro).to_parquet(SAIDA_LOG_ERROS, index=False)

    resumo = {
        "total_municipios": len(base_municipios),
        "total_processados": total_processados,
        "total_sucesso": total_sucesso,
        "total_erro": len(municipios_com_erro),
        "total_registros_climaticos": total_registros_climaticos,
    }
    return resumo


def _gravar_lote_parquet(df_lote: pd.DataFrame, indice_lote: int) -> None:
    """Grava um lote em Parquet, particionado por região, sem manter
    o histórico completo em memória (append incremental em disco)."""
    for regiao, df_regiao in df_lote.groupby("regiao"):
        pasta_regiao = SAIDA_PARQUET_DIR / f"regiao={regiao}"
        pasta_regiao.mkdir(parents=True, exist_ok=True)
        arquivo = pasta_regiao / f"lote_{indice_lote:05d}.parquet"
        df_regiao.to_parquet(arquivo, index=False)


# =======================================================================
# ETAPA 4 - PÓS-PROCESSAMENTO / ENGENHARIA DE ATRIBUTOS
# (mesma lógica do código original, agora aplicada por MUNICÍPIO em vez
#  de por região; a região continua disponível como dimensão de análise)
# =======================================================================
def classificar_temperatura(valor):
    if valor < 18:
        return "Frio"
    elif valor < 25:
        return "Ameno"
    elif valor < 30:
        return "Quente"
    else:
        return "Muito Quente"


def classificar_chuva(valor):
    if valor == 0:
        return "Sem chuva"
    elif valor < 2.5:
        return "Fraca"
    elif valor < 10:
        return "Moderada"
    elif valor < 30:
        return "Forte"
    else:
        return "Muito Forte"


def estacao(mes):
    if mes in [12, 1, 2]:
        return "Verão"
    elif mes in [3, 4, 5]:
        return "Outono"
    elif mes in [6, 7, 8]:
        return "Inverno"
    else:
        return "Primavera"


def enriquecer_particao(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica limpeza + engenharia de atributos em uma partição (uma
    região) do dataset. Pensado para ser chamado partição a partição,
    para manter o uso de memória sob controle mesmo com ~5.500 municípios
    em base diária."""

    df = df.drop_duplicates()
    df["data"] = pd.to_datetime(df["data"])
    df["temperatura"] = pd.to_numeric(df["temperatura"], errors="coerce")
    df["precipitacao"] = pd.to_numeric(df["precipitacao"], errors="coerce")

    df = df[(df["temperatura"] > -20) & (df["temperatura"] < 60)]
    df = df[df["precipitacao"] >= 0]

    df["ano"] = df["data"].dt.year
    df["mes"] = df["data"].dt.month
    df["dia"] = df["data"].dt.day
    df["dia_semana"] = df["data"].dt.day_name()
    df["estacao"] = df["mes"].apply(estacao)

    df["classe_temperatura"] = df["temperatura"].apply(classificar_temperatura)
    df["classe_chuva"] = df["precipitacao"].apply(classificar_chuva)

    df["sem_chuva"] = df["precipitacao"] == 0
    df["onda_calor"] = df["temperatura"] >= 35
    df["evento_chuva_extrema"] = df["precipitacao"] >= 30
    df["evento_calor_extremo"] = df["temperatura"] >= 35
    df["evento_extremo"] = df["evento_chuva_extrema"] | df["evento_calor_extremo"]

    # Dias consecutivos sem chuva, calculado por MUNICÍPIO (codigo_ibge),
    # não mais por região — cada município tem sua própria série. Como
    # cada linha agora representa 1 dia (base diária), o contador de
    # sequência já é diretamente "dias_sem_chuva", sem precisar dividir
    # por 24 como na versão horária.
    df = df.sort_values(["codigo_ibge", "data"]).reset_index(drop=True)
    df["dias_sem_chuva"] = (
        df.groupby("codigo_ibge")["sem_chuva"]
        .apply(lambda serie: serie.groupby((~serie).cumsum()).cumcount() + 1)
        .where(df["sem_chuva"], 0)
        .reset_index(drop=True)
    )

    media_municipio = df.groupby("codigo_ibge")["temperatura"].transform("mean")
    df["anomalia_temperatura"] = df["temperatura"] - media_municipio

    df["risco_climatico"] = (
        df["dias_sem_chuva"] * 0.40
        + df["anomalia_temperatura"].abs() * 0.30
        + df["evento_extremo"].astype(int) * 30
    )

    condicoes_aptidao = [
        df["temperatura"] < 18,
        df["temperatura"] > 34,
    ]
    penalidade_temp = np.select(condicoes_aptidao, [20, 20], default=0)
    penalidade_chuva = np.select(
        [df["precipitacao"] == 0, df["precipitacao"] > 25], [15, 10], default=0
    )
    df["aptidao_agricola"] = (100 - penalidade_temp - penalidade_chuva).clip(lower=0)

    score = 100 - df["dias_sem_chuva"] * 0.8 - df["anomalia_temperatura"].abs() * 2
    score = score - df["evento_extremo"].astype(int) * 20
    df["score_esg"] = score.clip(lower=0, upper=100)

    return df


def gerar_resumos(diretorio_parquet: Path) -> dict:
    """Lê o dataset particionado em disco e gera os agregados finais
    (ranking por região, resumo executivo, etc.), sem carregar tudo de
    uma vez: processa região por região."""

    resumo_por_regiao = []
    ranking_linhas = []
    chuva_mensal_partes = []
    temperatura_mensal_partes = []

    for pasta_regiao in sorted(diretorio_parquet.glob("regiao=*")):
        arquivos = sorted(pasta_regiao.glob("*.parquet"))
        if not arquivos:
            continue

        df_regiao = pd.concat((pd.read_parquet(a) for a in arquivos), ignore_index=True)
        df_regiao = enriquecer_particao(df_regiao)

        # Salva de volta já enriquecido (sobrescreve os lotes brutos por
        # um único arquivo tratado por região).
        arquivo_final = pasta_regiao / "_tratado.parquet"
        df_regiao.to_parquet(arquivo_final, index=False)
        for a in arquivos:
            a.unlink()

        nome_regiao = pasta_regiao.name.split("=", 1)[1]

        resumo_por_regiao.append(
            {
                "regiao": nome_regiao,
                "temperatura_media": df_regiao["temperatura"].mean(),
                "temperatura_maxima": df_regiao["temperatura"].max(),
                "temperatura_minima": df_regiao["temperatura"].min(),
                "chuva_total": df_regiao["precipitacao"].sum(),
                "chuva_media": df_regiao["precipitacao"].mean(),
                "eventos_extremos": int(df_regiao["evento_extremo"].sum()),
                "risco_climatico_medio": df_regiao["risco_climatico"].mean(),
                "aptidao_agricola_media": df_regiao["aptidao_agricola"].mean(),
                "score_esg_medio": df_regiao["score_esg"].mean(),
                "qtd_municipios": df_regiao["codigo_ibge"].nunique(),
            }
        )

        chuva_mensal_partes.append(
            df_regiao.groupby(["codigo_ibge", "municipio", "uf", "regiao", "ano", "mes"])["precipitacao"]
            .sum()
            .reset_index(name="chuva_mes")
        )
        temperatura_mensal_partes.append(
            df_regiao.groupby(["codigo_ibge", "municipio", "uf", "regiao", "ano", "mes"])["temperatura"]
            .mean()
            .reset_index(name="temperatura_media_mes")
        )

        del df_regiao

    resumo_clima = pd.DataFrame(resumo_por_regiao).round(2).sort_values(
        "score_esg_medio", ascending=False
    )
    chuva_mensal = pd.concat(chuva_mensal_partes, ignore_index=True) if chuva_mensal_partes else pd.DataFrame()
    temperatura_mensal = (
        pd.concat(temperatura_mensal_partes, ignore_index=True) if temperatura_mensal_partes else pd.DataFrame()
    )

    return {
        "resumo_clima": resumo_clima,
        "chuva_mensal_por_municipio": chuva_mensal,
        "temperatura_mensal_por_municipio": temperatura_mensal,
    }


# =======================================================================
# ETAPA 5 - EXPORTAÇÃO FINAL (mantém a mesma UX do código original)
# =======================================================================
def exportar_base_completa_csv(diretorio_parquet: Path, arquivo_saida: Path) -> None:
    """Converte a base tratada em Parquet para CSV SOMENTE quando o usuário
    solicitar a exportação.

    A conversão é feita em batches para evitar carregar toda a base na memória.
    """
    try:
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError(
            "A exportação CSV da base completa requer 'pyarrow'. "
            "Instale com: pip install pyarrow"
        ) from exc

    arquivos = sorted(diretorio_parquet.glob("regiao=*/_tratado.parquet"))
    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum arquivo _tratado.parquet encontrado em {diretorio_parquet}."
        )

    arquivo_saida.parent.mkdir(parents=True, exist_ok=True)

    if arquivo_saida.exists():
        arquivo_saida.unlink()

    primeira_escrita = True
    total_linhas = 0

    logger.info(
        "Exportando base completa de Parquet para CSV: %s",
        arquivo_saida,
    )

    for arquivo_parquet in arquivos:
        logger.info("Exportando %s...", arquivo_parquet)

        parquet_file = pq.ParquetFile(arquivo_parquet)

        for batch in parquet_file.iter_batches(batch_size=100_000):
            df_batch = batch.to_pandas()

            df_batch.to_csv(
                arquivo_saida,
                mode="w" if primeira_escrita else "a",
                header=primeira_escrita,
                index=False,
                encoding="utf-8-sig",
            )

            total_linhas += len(df_batch)
            primeira_escrita = False

            del df_batch

    logger.info(
        "Exportação CSV concluída: %d registros em %s",
        total_linhas,
        arquivo_saida,
    )


def exportar(resultados: dict) -> None:
    print(
        """
        ┌────────────────────────────────────────────────────────────┐
        │                    OPÇÕES DE EXPORTAÇÃO                    │
        ├────────────────────────────────────────────────────────────┤
        │ [ 1 ] Base completa — manter em Parquet                   │
        │ [ 2 ] Base completa — exportar para CSV                   │
        │ [ 3 ] Resumos e agregados — exportar para CSV              │
        └────────────────────────────────────────────────────────────┘
        """
    )

    while True:
        try:
            opcao = int(input("Escolha uma opção (1, 2 ou 3): ").strip())
        except ValueError:
            print("Entrada inválida. Digite apenas números.")
            continue

        if opcao == 1:
            print(
                f"Base completa mantida em Parquet, particionada por região, em:\n"
                f"{SAIDA_PARQUET_DIR}"
            )
            break

        elif opcao == 2:
            arquivo_csv = SAIDA_DIR / "clima_municipios_completo.csv"

            exportar_base_completa_csv(
                SAIDA_PARQUET_DIR,
                arquivo_csv,
            )

            print(f"Base completa exportada para CSV em:\n{arquivo_csv}")
            break

        elif opcao == 3:
            resultados["resumo_clima"].to_csv(
                SAIDA_DIR / "clima_resumo_por_regiao.csv",
                index=False,
                encoding="utf-8-sig",
            )

            resultados["chuva_mensal_por_municipio"].to_csv(
                SAIDA_DIR / "chuva_mensal_por_municipio.csv",
                index=False,
                encoding="utf-8-sig",
            )

            resultados["temperatura_mensal_por_municipio"].to_csv(
                SAIDA_DIR / "temperatura_mensal_por_municipio.csv",
                index=False,
                encoding="utf-8-sig",
            )

            print(f"Resumos exportados para CSV em:\n{SAIDA_DIR}")
            break

        else:
            print("Opção inválida. Digite 1, 2 ou 3.")

    print("Exportação concluída com sucesso!")


# =======================================================================
# MAIN
# =======================================================================
def main():
    inicio = datetime.now()

    base_municipios = montar_base_municipios()
    resumo_execucao = processar_todos_os_municipios(base_municipios)

    print("\nResumo da coleta:")
    for chave, valor in resumo_execucao.items():
        print(f"  {chave}: {valor}")

    resultados = gerar_resumos(SAIDA_PARQUET_DIR)
    print("\nRanking por região (Score ESG):")
    print(resultados["resumo_clima"])

    exportar(resultados)

    duracao = datetime.now() - inicio
    logger.info("Pipeline concluído em %s.", duracao)


if __name__ == "__main__":
    main()