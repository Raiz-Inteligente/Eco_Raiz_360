# -*- coding: utf-8 -*-

"""
PIPELINE INMET - VERSÃO CONSOLIDADA E CORRIGIDA

RAW -> PROCESSED -> CURATED -> BASE CONSOLIDADA FINAL

Correções principais desta versão:

1. Leitura robusta dos metadados do INMET.
   Aceita:
       UF:;DF
       UF: DF
       UF;DF

       ESTACAO:;BRASILIA
       ESTACAO: BRASILIA
       ESTAÇÃO: BRASILIA
       ESTACAO;BRASILIA

2. Normalização de acentos e caracteres corrompidos.

3. Detecção dinâmica do cabeçalho da tabela.

4. Identificadores de estação sempre tratados como string:
       codigo_wmo
       estacao
       uf
       regiao

5. Latitude, longitude e altitude extraídas dos metadados.

6. Fallback pelo nome do arquivo quando o código WMO ou estação
   estiverem ausentes.

7. Deduplicação priorizando registros com identificadores preenchidos.

8. Valores -9999 e valores fisicamente impossíveis -> NaN.

9. Valores ausentes nunca são transformados silenciosamente em zero.

10. Agregação diária com arredondamento adequado.

11. Média circular para direção do vento.

12. KPIs meteorológicos.

13. Validação de tipos.

14. Validação contra notação científica.

15. Consolidação final.

Período:
    2019 a 2024

Regiões:
    Centro-Oeste
    Sul
"""

from __future__ import annotations

import logging
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd


# ==================================================================
# CONFIGURAÇÃO DE CAMINHOS
# ==================================================================

CAMINHO_PROJETO = Path(".")

CAMINHO_RAW = (
    CAMINHO_PROJETO
    / "data"
    / "raw"
    / "INMET"
)

CAMINHO_PROCESSED = (
    CAMINHO_PROJETO
    / "data"
    / "databases_processed"
    / "INMET"
)

CAMINHO_CURATED = (
    CAMINHO_PROJETO
    / "data"
    / "databases_curated"
    / "INMET"
)

CAMINHO_CONSOLIDADO = (
    CAMINHO_CURATED
    / "databases_juntos"
    / "INMET_completo.csv"
)

CAMINHO_RELATORIOS = (
    CAMINHO_PROJETO
    / "outputs"
    / "relatorios"
)


ANOS = range(2019, 2025)

HORAS_ESPERADAS = 24

VALOR_NAO_CAPTADO = "dados_nao_captados"


# ==================================================================
# REGIÕES
# ==================================================================

UF_CENTRO_OESTE = {
    "DF",
    "GO",
    "MT",
    "MS",
}

UF_SUL = {
    "PR",
    "SC",
    "RS",
}


UF_REGIAO = {}

for _uf in UF_CENTRO_OESTE:
    UF_REGIAO[_uf] = "centro_oeste"

for _uf in UF_SUL:
    UF_REGIAO[_uf] = "sul"


# ==================================================================
# LIMITES FÍSICOS
# ==================================================================

LIMITES_FISICOS = {

    "precipitacao_mm": (0, 500),

    "pressao_mb": (800, 1100),

    "radiacao_kj_m2": (0, 5000),

    "temperatura_c": (-50, 60),

    "ponto_orvalho_c": (-50, 60),

    "temperatura_max_c": (-50, 60),

    "temperatura_min_c": (-50, 60),

    "ponto_orvalho_max_c": (-50, 60),

    "ponto_orvalho_min_c": (-50, 60),

    "umidade_pct": (0, 100),

    "umidade_max_pct": (0, 100),

    "umidade_min_pct": (0, 100),

    "direcao_vento_graus": (0, 360),

    "rajada_max_ms": (0, 100),

    "velocidade_vento_ms": (0, 100),
}


# ==================================================================
# REGRAS DOS KPIs
# ==================================================================

CHUVA_MM_DIA = 0.1

CHUVA_FORTE_MM_DIA = 50

TEMPERATURA_ALTA_C = 35

TEMPERATURA_BAIXA_C = 10

VENTANIA_MS = 17.2

VENTO_FORTE_MS = 10


# ==================================================================
# CASAS DECIMAIS DOS DADOS AGREGADOS
# ==================================================================

CASAS_DECIMAIS_AGREGADO = {

    "precipitacao_total_mm": 1,

    "pressao_media_mb": 2,

    "pressao_max_mb": 1,

    "pressao_min_mb": 1,

    "radiacao_total_kj_m2": 1,

    "radiacao_total_mj_m2": 4,

    "temperatura_media_c": 2,

    "temperatura_maxima_c": 1,

    "temperatura_minima_c": 1,

    "amplitude_termica_c": 1,

    "ponto_orvalho_medio_c": 2,

    "umidade_media_pct": 2,

    "umidade_max_pct": 1,

    "umidade_min_pct": 1,

    "rajada_maxima_ms": 1,

    "velocidade_vento_media_ms": 2,

    "direcao_vento_media_graus": 1,

    "completude_pct": 1,
}


# ==================================================================
# LOGGING
# ==================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("pipeline_inmet")


# ==================================================================
# NORMALIZAÇÃO DE TEXTO
# ==================================================================

def normalizar_texto(valor) -> str:
    """
    Normaliza textos do INMET.

    Trata:
    - acentos;
    - espaços;
    - maiúsculas/minúsculas;
    - caracteres corrompidos;
    - '?';
    - caracteres �;
    """

    if pd.isna(valor):
        return ""

    texto = str(valor).strip().upper()

    texto = unicodedata.normalize(
        "NFKD",
        texto,
    )

    texto = "".join(
        c
        for c in texto
        if not unicodedata.combining(c)
    )

    substituicoes = {
        "?": "",
        "�": "",
        "Ã": "",
        "Â": "",
    }

    for antigo, novo in substituicoes.items():
        texto = texto.replace(
            antigo,
            novo,
        )

    texto = re.sub(
        r"\s+",
        " ",
        texto,
    )

    return texto.strip()


# ==================================================================
# PADRONIZAÇÃO DOS NOMES DAS COLUNAS
# ==================================================================

def padronizar_nome_coluna(nome) -> str:
    """
    Converte nomes de colunas para snake_case.
    """

    texto = normalizar_texto(nome)

    texto = (
        texto
        .replace("°", "")
        .replace("²", "2")
    )

    texto = re.sub(
        r"[^A-Z0-9]+",
        "_",
        texto,
    )

    texto = re.sub(
        r"_+",
        "_",
        texto,
    )

    texto = texto.strip("_")

    return texto.lower()


# ==================================================================
# CONVERSÃO NUMÉRICA
# ==================================================================

def converter_numero(
    serie: pd.Series,
) -> pd.Series:

    serie = (
        serie
        .astype("string")
        .str.strip()
    )

    serie = serie.str.replace(
        ",",
        ".",
        regex=False,
    )

    serie = serie.replace(
        [
            "-9999",
            "-9999.0",
            "-9999.00",
            "",
            "nan",
            "NaN",
            "NULL",
            "null",
            "None",
        ],
        pd.NA,
    )

    return pd.to_numeric(
        serie,
        errors="coerce",
    ).astype("float64")


# ==================================================================
# CORREÇÃO DA PRECIPITAÇÃO
# ==================================================================

def corrigir_precipitacao(
    serie: pd.Series,
) -> pd.Series:

    serie = converter_numero(serie)

    mascara_invalida = (
        (serie < 0)
        | (serie > 500)
        | (serie.abs() >= 1_000_000)
    )

    serie.loc[mascara_invalida] = np.nan

    return serie


# ==================================================================
# ABERTURA DO ARQUIVO
# ==================================================================

def _abrir_texto(
    caminho: Path,
):
    """
    Tenta abrir usando encodings comuns do INMET.
    """

    for encoding in (
        "latin1",
        "cp1252",
        "utf-8",
    ):

        try:

            arquivo = caminho.open(
                "r",
                encoding=encoding,
                errors="strict",
            )

            return arquivo, encoding

        except (
            UnicodeDecodeError,
            LookupError,
        ):
            continue

    return (
        caminho.open(
            "r",
            encoding="latin1",
            errors="replace",
        ),
        "latin1",
    )


# ==================================================================
# EXTRAÇÃO ROBUSTA DOS METADADOS
# ==================================================================

def extrair_metadados(
    caminho: Path,
) -> tuple[dict, int, str]:

    """
    Lê os metadados do arquivo INMET.

    Aceita formatos como:

        UF:;DF
        UF: DF
        UF;DF

        ESTACAO:;BRASILIA
        ESTACAO: BRASILIA
        ESTACAO;BRASILIA

    Também detecta automaticamente a linha do cabeçalho da tabela.
    """

    metadados = {}

    linha_cabecalho_tabela = None

    arquivo, encoding = _abrir_texto(
        caminho
    )

    with arquivo:

        for indice, linha in enumerate(arquivo):

            if indice > 40:
                break

            linha_limpa = linha.rstrip(
                "\r\n"
            )

            if not linha_limpa.strip():
                continue

            partes = linha_limpa.split(";")

            primeiro_campo = (
                normalizar_texto(partes[0])
                if partes
                else ""
            )

            segundo_campo = (
                normalizar_texto(partes[1])
                if len(partes) >= 2
                else ""
            )

            # ------------------------------------------------------
            # DETECÇÃO DO CABEÇALHO DA TABELA
            # ------------------------------------------------------

            primeiro_sem_dois_pontos = (
                primeiro_campo
                .rstrip(":")
                .strip()
            )

            if (
                primeiro_sem_dois_pontos == "DATA"
                and (
                    "HORA" in segundo_campo
                    or "HORARIO" in segundo_campo
                )
            ):

                linha_cabecalho_tabela = indice

                break

            # ------------------------------------------------------
            # FORMATO:
            #
            # UF:;DF
            # ESTACAO:;BRASILIA
            # ------------------------------------------------------

            if len(partes) >= 2:

                chave = normalizar_texto(
                    partes[0]
                ).rstrip(":").strip()

                valor = (
                    partes[1]
                    .strip()
                    if len(partes) >= 2
                    else ""
                )

                if chave:
                    metadados[chave] = valor

                continue

            # ------------------------------------------------------
            # FORMATO:
            #
            # UF: DF
            # ESTACAO: BRASILIA
            #
            # ou:
            #
            # UF;DF
            # ------------------------------------------------------

            linha_normalizada = normalizar_texto(
                linha_limpa
            )

            if ":" in linha_normalizada:

                chave, valor = (
                    linha_normalizada.split(
                        ":",
                        1,
                    )
                )

                chave = chave.strip()

                valor = valor.strip()

                if chave:
                    metadados[chave] = valor

                continue

            # ------------------------------------------------------
            # FORMATO:
            #
            # UF DF
            #
            # ESTACAO BRASILIA
            # ------------------------------------------------------

            padrao = re.match(
                r"^([A-Z0-9_() ]+?)\s+(.+)$",
                linha_normalizada,
            )

            if padrao:

                chave = (
                    padrao.group(1)
                    .strip()
                    .rstrip(":")
                )

                valor = padrao.group(2).strip()

                chaves_conhecidas = {
                    "UF",
                    "ESTACAO",
                    "CODIGO WMO",
                    "CODIGO",
                    "LATITUDE",
                    "LONGITUDE",
                    "ALTITUDE",
                }

                if chave in chaves_conhecidas:
                    metadados[chave] = valor

    if linha_cabecalho_tabela is None:

        linha_cabecalho_tabela = 8

        logger.warning(
            "Cabeçalho não detectado dinamicamente em %s. "
            "Usando fallback skiprows=8.",
            caminho.name,
        )

    return (
        metadados,
        linha_cabecalho_tabela,
        encoding,
    )


# ==================================================================
# OBTÉM METADADO
# ==================================================================

def obter_metadado(
    metadados: dict,
    *chaves,
) -> str:

    metadados_normalizados = {}

    for chave, valor in metadados.items():

        chave_norm = normalizar_texto(
            chave
        )

        metadados_normalizados[
            chave_norm
        ] = valor

    # --------------------------------------------------------------
    # Correspondência exata
    # --------------------------------------------------------------

    for chave in chaves:

        chave_norm = normalizar_texto(
            chave
        )

        if chave_norm in metadados_normalizados:

            valor = metadados_normalizados[
                chave_norm
            ]

            if valor is not None:
                return str(valor).strip()

    # --------------------------------------------------------------
    # Correspondência aproximada
    # --------------------------------------------------------------

    for chave in chaves:

        chave_norm = normalizar_texto(
            chave
        )

        for existente, valor in (
            metadados_normalizados.items()
        ):

            if (
                chave_norm in existente
                or existente in chave_norm
            ):

                if valor is not None:
                    return str(valor).strip()

    return ""


# ==================================================================
# FALLBACK PARA METADADOS PELO NOME DO ARQUIVO
# ==================================================================

def obter_metadados_pelo_nome_arquivo(
    caminho: Path,
) -> tuple[str, str]:

    """
    Tenta recuperar código WMO e nome da estação
    através do padrão do nome do arquivo.

    Exemplo:

    INMET_CO_DF_A001_BRASILIA_01-01-2019_A_31-12-2019.CSV

    Retorna:

        A001
        BRASILIA
    """

    nome = caminho.stem

    partes = nome.split("_")

    codigo_wmo = ""

    estacao = ""

    # --------------------------------------------------------------
    # Procura um código semelhante a A001
    # --------------------------------------------------------------

    for parte in partes:

        if re.fullmatch(
            r"[A-Z]\d{3,5}",
            parte.upper(),
        ):

            codigo_wmo = parte.upper()

            break

    # --------------------------------------------------------------
    # Tenta identificar estação depois do código WMO
    # --------------------------------------------------------------

    if codigo_wmo:

        try:

            indice = [
                p.upper()
                for p in partes
            ].index(codigo_wmo)

            candidatos = partes[
                indice + 1:
            ]

            ignorar = {
                "A",
                "AUT",
                "AUTO",
            }

            nomes = []

            for parte in candidatos:

                if re.fullmatch(
                    r"\d{2}-\d{2}-\d{4}",
                    parte,
                ):
                    break

                if parte.upper() in ignorar:
                    continue

                nomes.append(parte)

            if nomes:
                estacao = " ".join(
                    nomes
                ).upper()

        except ValueError:
            pass

    return (
        codigo_wmo,
        estacao,
    )


# ==================================================================
# MAPEAMENTO DE COLUNAS
# ==================================================================

def mapear_colunas(
    colunas: list[str],
) -> dict[str, str]:

    mapa = {}

    for coluna in colunas:

        # ----------------------------------------------------------
        # PRECIPITAÇÃO
        # ----------------------------------------------------------

        if (
            "precipitacao_total" in coluna
            or "precipitacao_horaria" in coluna
            or "chuva" in coluna
        ):

            mapa[coluna] = (
                "precipitacao_mm"
            )

        # ----------------------------------------------------------
        # PRESSÃO MÁXIMA
        # ----------------------------------------------------------

        elif (
            "pressao_atmosferica_max" in coluna
            or "pressao_max" in coluna
        ):

            mapa[coluna] = (
                "pressao_max_mb"
            )

        # ----------------------------------------------------------
        # PRESSÃO MÍNIMA
        # ----------------------------------------------------------

        elif (
            "pressao_atmosferica_min" in coluna
            or "pressao_min" in coluna
        ):

            mapa[coluna] = (
                "pressao_min_mb"
            )

        # ----------------------------------------------------------
        # PRESSÃO NORMAL
        # ----------------------------------------------------------

        elif (
            "pressao_atmosferica_ao_nivel_da_estacao"
            in coluna
            or "pressao_nivel_estacao" in coluna
            or coluna == "pressao"
        ):

            mapa[coluna] = "pressao_mb"

        # ----------------------------------------------------------
        # RADIAÇÃO
        # ----------------------------------------------------------

        elif (
            "radiacao_global" in coluna
            or "radiacao" in coluna
        ):

            mapa[coluna] = (
                "radiacao_kj_m2"
            )

        # ----------------------------------------------------------
        # TEMPERATURA MÁXIMA
        # ----------------------------------------------------------

        elif (
            "temperatura_maxima" in coluna
            or "temperatura_max" in coluna
        ):

            mapa[coluna] = (
                "temperatura_max_c"
            )

        # ----------------------------------------------------------
        # TEMPERATURA MÍNIMA
        # ----------------------------------------------------------

        elif (
            "temperatura_minima" in coluna
            or "temperatura_min" in coluna
        ):

            mapa[coluna] = (
                "temperatura_min_c"
            )

        # ----------------------------------------------------------
        # TEMPERATURA DO AR
        # ----------------------------------------------------------

        elif (
            "temperatura_do_ar_bulbo_seco"
            in coluna
            or "temperatura_ar" in coluna
            or coluna == "temperatura"
        ):

            mapa[coluna] = (
                "temperatura_c"
            )

        # ----------------------------------------------------------
        # PONTO DE ORVALHO MÁXIMO
        # ----------------------------------------------------------

        elif (
            "temperatura_orvalho_max" in coluna
            or "ponto_orvalho_max" in coluna
        ):

            mapa[coluna] = (
                "ponto_orvalho_max_c"
            )

        # ----------------------------------------------------------
        # PONTO DE ORVALHO MÍNIMO
        # ----------------------------------------------------------

        elif (
            "temperatura_orvalho_min" in coluna
            or "ponto_orvalho_min" in coluna
        ):

            mapa[coluna] = (
                "ponto_orvalho_min_c"
            )

        # ----------------------------------------------------------
        # PONTO DE ORVALHO
        # ----------------------------------------------------------

        elif (
            "temperatura_do_ponto_de_orvalho"
            in coluna
            or "ponto_orvalho" in coluna
        ):

            mapa[coluna] = (
                "ponto_orvalho_c"
            )

        # ----------------------------------------------------------
        # UMIDADE MÁXIMA
        # ----------------------------------------------------------

        elif (
            "umidade_rel_max" in coluna
            or "umidade_max" in coluna
        ):

            mapa[coluna] = (
                "umidade_max_pct"
            )

        # ----------------------------------------------------------
        # UMIDADE MÍNIMA
        # ----------------------------------------------------------

        elif (
            "umidade_rel_min" in coluna
            or "umidade_min" in coluna
        ):

            mapa[coluna] = (
                "umidade_min_pct"
            )

        # ----------------------------------------------------------
        # UMIDADE
        # ----------------------------------------------------------

        elif (
            "umidade_relativa_do_ar_horaria"
            in coluna
            or "umidade_relativa" in coluna
            or coluna == "umidade"
        ):

            mapa[coluna] = (
                "umidade_pct"
            )

        # ----------------------------------------------------------
        # DIREÇÃO DO VENTO
        # ----------------------------------------------------------

        elif (
            "vento_direcao_horaria" in coluna
            or "direcao_vento" in coluna
            or "vento_direcao" in coluna
        ):

            mapa[coluna] = (
                "direcao_vento_graus"
            )

        # ----------------------------------------------------------
        # RAJADA
        # ----------------------------------------------------------

        elif (
            "vento_rajada_maxima" in coluna
            or "rajada_maxima" in coluna
            or coluna == "rajada"
        ):

            mapa[coluna] = (
                "rajada_max_ms"
            )

        # ----------------------------------------------------------
        # VELOCIDADE DO VENTO
        # ----------------------------------------------------------

        elif (
            "vento_velocidade_horaria"
            in coluna
            or "velocidade_vento" in coluna
            or "vento_velocidade" in coluna
        ):

            mapa[coluna] = (
                "velocidade_vento_ms"
            )

    return mapa


# ==================================================================
# DETECTAR DATA E HORA
# ==================================================================

def detectar_coluna_data_hora(
    df: pd.DataFrame,
) -> tuple[str | None, str | None]:

    coluna_data = None

    coluna_hora = None

    candidatos_data = [
        "data",
        "data_yyyy_mm_dd",
        "data_hora",
    ]

    candidatos_hora = [
        "hora_utc",
        "hora",
        "horario",
        "horario_utc",
        "hora_gmt",
    ]

    # --------------------------------------------------------------
    # DATA
    # --------------------------------------------------------------

    for coluna in df.columns:

        if coluna in candidatos_data:

            coluna_data = coluna

            break

        if coluna.startswith("data"):

            coluna_data = coluna

            break

    # --------------------------------------------------------------
    # HORA
    # --------------------------------------------------------------

    for coluna in df.columns:

        if coluna in candidatos_hora:

            coluna_hora = coluna

            break

        if "hora" in coluna:

            coluna_hora = coluna

            break

    # --------------------------------------------------------------
    # DATA PELO CONTEÚDO
    # --------------------------------------------------------------

    if coluna_data is None:

        for coluna in df.columns:

            amostra = (
                df[coluna]
                .dropna()
                .astype(str)
                .head(20)
            )

            if amostra.empty:
                continue

            padrao_data = (
                amostra
                .str.match(
                    r"^\d{4}[-/]\d{2}[-/]\d{2}$"
                )
                .mean()
            )

            if padrao_data >= 0.5:

                coluna_data = coluna

                break

    # --------------------------------------------------------------
    # HORA PELO CONTEÚDO
    # --------------------------------------------------------------

    if coluna_hora is None:

        for coluna in df.columns:

            amostra = (
                df[coluna]
                .dropna()
                .astype(str)
                .str.strip()
                .head(20)
            )

            if amostra.empty:
                continue

            padrao_hora = (
                amostra
                .str.match(
                    r"^\d{4}\s*UTC$",
                    case=False,
                )
                .mean()
            )

            if padrao_hora >= 0.5:

                coluna_hora = coluna

                break

    return (
        coluna_data,
        coluna_hora,
    )


# ==================================================================
# DETECTAR SEPARADOR
# ==================================================================

def detectar_separador(
    caminho: Path,
    encoding: str,
) -> str:

    with caminho.open(
        "r",
        encoding=encoding,
        errors="replace",
    ) as arquivo:

        for _ in range(20):

            linha = arquivo.readline()

            if not linha:
                break

            if ";" in linha:
                return ";"

            if "," in linha:
                return ","

            if "\t" in linha:
                return "\t"

    return ";"


# ==================================================================
# COLUNAS NUMÉRICAS HORÁRIAS
# ==================================================================

COLUNAS_NUMERICAS_HORARIAS = [

    "pressao_mb",

    "pressao_max_mb",

    "pressao_min_mb",

    "radiacao_kj_m2",

    "temperatura_c",

    "temperatura_max_c",

    "temperatura_min_c",

    "ponto_orvalho_c",

    "ponto_orvalho_max_c",

    "ponto_orvalho_min_c",

    "umidade_pct",

    "umidade_max_pct",

    "umidade_min_pct",

    "direcao_vento_graus",

    "rajada_max_ms",

    "velocidade_vento_ms",
]


# ==================================================================
# LEITURA DO INMET
# ==================================================================

def ler_inmet(
    caminho: Path,
    ano: int,
    relatorios: list,
) -> pd.DataFrame | None:

    metadados, linha_cabecalho, encoding = (
        extrair_metadados(caminho)
    )

    separador = detectar_separador(
        caminho,
        encoding,
    )

    logger.info(
        "LEITURA | %s | cabeçalho=%s | encoding=%s | separador=%r",
        caminho.name,
        linha_cabecalho,
        encoding,
        separador,
    )

    # ==============================================================
    # LEITURA DA TABELA
    # ==============================================================

    df = pd.read_csv(
        caminho,
        sep=separador,
        encoding=encoding,
        skiprows=range(linha_cabecalho),
        header=0,
        low_memory=False,
    )

    df = df.dropna(
        axis=1,
        how="all",
    )

    if df.empty:

        logger.warning(
            "Arquivo vazio após leitura: %s",
            caminho,
        )

        return None

    # ==============================================================
    # NORMALIZAÇÃO DAS COLUNAS
    # ==============================================================

    df.columns = [
        padronizar_nome_coluna(c)
        for c in df.columns
    ]

    logger.info(
        "COLUNAS | %s | %s",
        caminho.name,
        list(df.columns),
    )

    # ==============================================================
    # DATA/HORA
    # ==============================================================

    coluna_data, coluna_hora = (
        detectar_coluna_data_hora(df)
    )

    if coluna_data is None:

        relatorios.append({
            "etapa": "leitura",
            "arquivo": str(caminho),
            "ano": ano,
            "status": "erro",
            "erro": "coluna de data não encontrada",
            "colunas_encontradas": ",".join(
                df.columns
            ),
        })

        logger.error(
            "Data não encontrada: %s",
            caminho,
        )

        return None

    if coluna_hora is None:

        relatorios.append({
            "etapa": "leitura",
            "arquivo": str(caminho),
            "ano": ano,
            "status": "erro",
            "erro": "coluna de hora não encontrada",
            "colunas_encontradas": ",".join(
                df.columns
            ),
        })

        logger.error(
            "Hora não encontrada: %s",
            caminho,
        )

        return None

    # ==============================================================
    # MAPEAMENTO METEOROLÓGICO
    # ==============================================================

    df = df.rename(
        columns=mapear_colunas(
            list(df.columns)
        )
    )

    # ==============================================================
    # DATA
    # ==============================================================

    df["data"] = pd.to_datetime(
        df[coluna_data],
        errors="coerce",
    )

    linhas_data_invalida = int(
        df["data"].isna().sum()
    )

    df = df[
        df["data"].dt.year == ano
    ].copy()

    if df.empty:

        logger.warning(
            "Nenhum registro do ano %s em %s",
            ano,
            caminho.name,
        )

        return None

    # ==============================================================
    # HORA
    # ==============================================================

    df["hora_utc"] = (
        df[coluna_hora]
        .astype("string")
        .str.strip()
        .str.upper()
    )

    # ==============================================================
    # METADADOS DA ESTAÇÃO
    # ==============================================================

    uf = normalizar_texto(
        obter_metadado(
            metadados,
            "UF",
        )
    )

    # --------------------------------------------------------------
    # CÓDIGO WMO
    # --------------------------------------------------------------

    codigo_wmo = normalizar_texto(
        obter_metadado(
            metadados,
            "CODIGO (WMO)",
            "CODIGO WMO",
            "CODIGO",
        )
    )

    # --------------------------------------------------------------
    # ESTAÇÃO
    # --------------------------------------------------------------

    estacao = normalizar_texto(
        obter_metadado(
            metadados,
            "ESTACAO",
            "ESTAÇÃO",
        )
    )

    # --------------------------------------------------------------
    # FALLBACK PELO NOME DO ARQUIVO
    # --------------------------------------------------------------

    codigo_arquivo, estacao_arquivo = (
        obter_metadados_pelo_nome_arquivo(
            caminho
        )
    )

    if not codigo_wmo and codigo_arquivo:

        codigo_wmo = codigo_arquivo

        logger.info(
            "WMO recuperado pelo nome do arquivo | %s | WMO=%s",
            caminho.name,
            codigo_wmo,
        )

    if not estacao and estacao_arquivo:

        estacao = estacao_arquivo

        logger.info(
            "ESTAÇÃO recuperada pelo nome do arquivo | %s | ESTACAO=%s",
            caminho.name,
            estacao,
        )

    # ==============================================================
    # UF FORA DO ESCOPO
    # ==============================================================

    if uf not in UF_REGIAO:

        logger.info(
            "Estação fora do escopo: %s | UF=%s",
            caminho.name,
            uf,
        )

        return None

    # ==============================================================
    # ALERTA DE METADADOS VAZIOS
    # ==============================================================

    if not codigo_wmo:

        logger.warning(
            "WMO VAZIO | arquivo=%s | UF=%s | estação=%s",
            caminho.name,
            uf,
            estacao,
        )

    if not estacao:

        logger.warning(
            "ESTAÇÃO VAZIA | arquivo=%s | WMO=%s | UF=%s",
            caminho.name,
            codigo_wmo,
            uf,
        )

    # ==============================================================
    # COORDENADAS
    # ==============================================================

    latitude_txt = obter_metadado(
        metadados,
        "LATITUDE",
    )

    longitude_txt = obter_metadado(
        metadados,
        "LONGITUDE",
    )

    altitude_txt = obter_metadado(
        metadados,
        "ALTITUDE",
    )

    # ==============================================================
    # IDENTIFICADORES
    # ==============================================================

    df["uf"] = pd.array(
        [uf] * len(df),
        dtype="string",
    )

    df["regiao"] = pd.array(
        [UF_REGIAO[uf]] * len(df),
        dtype="string",
    )

    df["codigo_wmo"] = pd.array(
        [codigo_wmo] * len(df),
        dtype="string",
    )

    df["estacao"] = pd.array(
        [estacao] * len(df),
        dtype="string",
    )

    # ==============================================================
    # COORDENADAS
    # ==============================================================

    df["latitude"] = converter_numero(
        pd.Series(
            [latitude_txt] * len(df),
            index=df.index,
        )
    )

    df["longitude"] = converter_numero(
        pd.Series(
            [longitude_txt] * len(df),
            index=df.index,
        )
    )

    df["altitude_m"] = converter_numero(
        pd.Series(
            [altitude_txt] * len(df),
            index=df.index,
        )
    )

    # ==============================================================
    # VARIÁVEIS METEOROLÓGICAS
    # ==============================================================

    for coluna in COLUNAS_NUMERICAS_HORARIAS:

        if coluna in df.columns:

            df[coluna] = converter_numero(
                df[coluna]
            )

    # ==============================================================
    # PRECIPITAÇÃO
    # ==============================================================

    if "precipitacao_mm" in df.columns:

        df["precipitacao_mm"] = (
            corrigir_precipitacao(
                df["precipitacao_mm"]
            )
        )

    # ==============================================================
    # RELATÓRIO DE VARIÁVEIS
    # ==============================================================

    variaveis_encontradas = [
        coluna
        for coluna in COLUNAS_NUMERICAS_HORARIAS
        if coluna in df.columns
    ]

    variaveis_ausentes = [
        coluna
        for coluna in COLUNAS_NUMERICAS_HORARIAS
        if coluna not in df.columns
    ]

    if variaveis_ausentes:

        logger.warning(
            "VARIÁVEIS AUSENTES | %s | %s",
            caminho.name,
            variaveis_ausentes,
        )

    logger.info(
        "VARIÁVEIS | %s | encontradas=%s | ausentes=%s",
        caminho.name,
        len(variaveis_encontradas),
        len(variaveis_ausentes),
    )

    if linhas_data_invalida:

        relatorios.append({
            "etapa": "leitura",
            "arquivo": str(caminho),
            "ano": ano,
            "status": "aviso",
            "aviso": (
                f"{linhas_data_invalida} linha(s) "
                "com data inválida"
            ),
        })

    return df


# ==================================================================
# TRATAMENTO FÍSICO
# ==================================================================

def tratar_valores_fisicos(
    df: pd.DataFrame,
    relatorios: list,
    arquivo: str,
) -> pd.DataFrame:

    df = df.copy()

    for coluna, (
        minimo,
        maximo,
    ) in LIMITES_FISICOS.items():

        if coluna not in df.columns:
            continue

        mascara = (
            df[coluna].notna()
            & (
                (df[coluna] < minimo)
                | (df[coluna] > maximo)
            )
        )

        quantidade = int(
            mascara.sum()
        )

        if quantidade:

            relatorios.append({
                "etapa": "tratamento_fisico",
                "arquivo": arquivo,
                "coluna": coluna,
                "valores_invalidados": quantidade,
                "motivo": (
                    f"fora do intervalo físico "
                    f"[{minimo}, {maximo}]"
                ),
            })

        df.loc[
            mascara,
            coluna,
        ] = np.nan

    return df


# ==================================================================
# INDICADORES DE AUSÊNCIA
# ==================================================================

def criar_indicadores_ausencia(
    df: pd.DataFrame,
) -> pd.DataFrame:

    df = df.copy()

    for coluna in [
        c
        for c in LIMITES_FISICOS
        if c in df.columns
    ]:

        df[
            f"{coluna}_status"
        ] = np.where(
            df[coluna].isna(),
            VALOR_NAO_CAPTADO,
            "captado",
        )

    return df


# ==================================================================
# VALIDAÇÃO DE TIPOS
# ==================================================================

def validar_tipos_horarios(
    df: pd.DataFrame,
    arquivo: str,
) -> list[str]:

    problemas = []

    for coluna in (
        "codigo_wmo",
        "estacao",
        "uf",
        "regiao",
        "hora_utc",
    ):

        if (
            coluna in df.columns
            and not pd.api.types.is_string_dtype(
                df[coluna]
            )
        ):

            problemas.append(
                f"{arquivo}: coluna '{coluna}' "
                f"deveria ser string, "
                f"está {df[coluna].dtype}"
            )

    for coluna in (
        COLUNAS_NUMERICAS_HORARIAS
        + [
            "latitude",
            "longitude",
            "altitude_m",
        ]
    ):

        if (
            coluna in df.columns
            and not pd.api.types.is_float_dtype(
                df[coluna]
            )
        ):

            problemas.append(
                f"{arquivo}: coluna '{coluna}' "
                f"deveria ser float, "
                f"está {df[coluna].dtype}"
            )

    if (
        "data" in df.columns
        and not pd.api.types.is_datetime64_any_dtype(
            df["data"]
        )
    ):

        problemas.append(
            f"{arquivo}: coluna 'data' "
            "não é datetime"
        )

    return problemas


# ==================================================================
# EXPORTAR PROCESSED
# ==================================================================

def exportar_processed(df: pd.DataFrame, ano: int, numero_arquivo: int) -> Path:

    pasta_saida = CAMINHO_PROCESSED / str(ano)
    pasta_saida.mkdir(parents=True, exist_ok=True)

    codigo_wmo = (
        str(df["codigo_wmo"].iloc[0])
        .replace("/", "_")
        .replace(" ", "_")
        or "SEM_CODIGO"
    )

    nome_arquivo = f"{ano}_{codigo_wmo}_{numero_arquivo:04d}.csv"
    caminho_saida = pasta_saida / nome_arquivo

    df.to_csv(
        caminho_saida,
        index=False,
        encoding="utf-8-sig",
        sep=";",
        decimal=",",
    )

    return caminho_saida


# ==================================================================
# ETAPA 1 - RAW -> PROCESSED
# ==================================================================

def processar_raw(
    relatorios: list,
) -> None:

    logger.info("=" * 70)

    logger.info(
        "ETAPA 1 - RAW -> PROCESSED"
    )

    logger.info(
        "Entrada: %s",
        CAMINHO_RAW.resolve(),
    )

    logger.info(
        "Saída: %s",
        CAMINHO_PROCESSED.resolve(),
    )

    logger.info("=" * 70)

    for ano in ANOS:

        pasta_ano = (
            CAMINHO_RAW
            / str(ano)
        )

        if not pasta_ano.exists():

            logger.warning(
                "Pasta inexistente: %s",
                pasta_ano,
            )

            continue

        arquivos = sorted(
            list(
                dict.fromkeys(
                    list(
                        pasta_ano.rglob(
                            "*.CSV"
                        )
                    )
                    + list(
                        pasta_ano.rglob(
                            "*.csv"
                        )
                    )
                )
            )
        )

        logger.info(
            "ANO %s | %s arquivos encontrados",
            ano,
            len(arquivos),
        )

        for numero, caminho in enumerate(
            arquivos,
            start=1,
        ):

            try:

                df = ler_inmet(
                    caminho,
                    ano,
                    relatorios,
                )

                if df is None:
                    continue

                linhas_originais = len(df)

                df = tratar_valores_fisicos(
                    df,
                    relatorios,
                    str(caminho),
                )

                df = criar_indicadores_ausencia(
                    df
                )

                # --------------------------------------------------
                # DEDUPLICAÇÃO
                #
                # Antes de remover duplicatas, prioriza:
                # 1. código WMO preenchido
                # 2. estação preenchida
                # 3. demais identificadores
                # --------------------------------------------------

                df["_prioridade_metadados"] = (
                    df["codigo_wmo"]
                    .fillna("")
                    .astype("string")
                    .str.strip()
                    .ne("")
                    .astype(int)
                    * 2
                    +
                    df["estacao"]
                    .fillna("")
                    .astype("string")
                    .str.strip()
                    .ne("")
                    .astype(int)
                )

                df = df.sort_values(
                    [
                        "_prioridade_metadados",
                        "data",
                        "hora_utc",
                    ],
                    ascending=[
                        False,
                        True,
                        True,
                    ],
                )

                duplicadas = int(
                    df.duplicated(
                        subset=[
                            "codigo_wmo",
                            "data",
                            "hora_utc",
                        ]
                    ).sum()
                )

                df = df.drop_duplicates(
                    subset=[
                        "codigo_wmo",
                        "data",
                        "hora_utc",
                    ],
                    keep="first",
                )

                df = df.drop(
                    columns=[
                        "_prioridade_metadados"
                    ]
                )

                df = df.sort_values(
                    [
                        "data",
                        "hora_utc",
                    ]
                ).reset_index(
                    drop=True
                )

                problemas_tipo = (
                    validar_tipos_horarios(
                        df,
                        str(caminho),
                    )
                )

                for problema in problemas_tipo:

                    logger.warning(
                        "VALIDAÇÃO DE TIPO: %s",
                        problema,
                    )

                caminho_saida = (
                    exportar_processed(
                        df,
                        ano,
                        numero,
                    )
                )

                nulos_por_coluna = {
                    coluna: int(
                        df[coluna].isna().sum()
                    )
                    for coluna in (
                        COLUNAS_NUMERICAS_HORARIAS
                        + [
                            "precipitacao_mm"
                        ]
                    )
                    if coluna in df.columns
                }

                relatorios.append({
                    "etapa": "processed",
                    "arquivo": str(caminho),
                    "arquivo_saida": str(
                        caminho_saida
                    ),
                    "ano": ano,
                    "uf": df["uf"].iloc[0],
                    "regiao": df[
                        "regiao"
                    ].iloc[0],
                    "codigo_wmo": df[
                        "codigo_wmo"
                    ].iloc[0],
                    "estacao": df[
                        "estacao"
                    ].iloc[0],
                    "linhas_entrada": (
                        linhas_originais
                    ),
                    "linhas_saida": len(df),
                    "duplicadas_removidas": (
                        duplicadas
                    ),
                    "valores_ausentes_por_coluna": (
                        nulos_por_coluna
                    ),
                    "problemas_tipo": len(
                        problemas_tipo
                    ),
                    "status": "ok",
                })

                logger.info(
                    "PROCESSED | %s -> %s | "
                    "%s linhas | UF=%s | WMO=%s | ESTACAO=%s",
                    caminho.name,
                    caminho_saida.name,
                    len(df),
                    df["uf"].iloc[0],
                    df["codigo_wmo"].iloc[0],
                    df["estacao"].iloc[0],
                )

            except Exception as erro:

                logger.exception(
                    "Erro processando %s",
                    caminho,
                )

                relatorios.append({
                    "etapa": "processed",
                    "arquivo": str(caminho),
                    "ano": ano,
                    "status": "erro",
                    "erro": repr(erro),
                })


# ==================================================================
# MÉDIA CIRCULAR
# ==================================================================

def media_circular(
    serie: pd.Series,
) -> float:

    valores = (
        serie
        .dropna()
        .to_numpy(dtype=float)
    )

    if len(valores) == 0:
        return np.nan

    radianos = np.deg2rad(
        valores
    )

    seno = np.mean(
        np.sin(radianos)
    )

    cosseno = np.mean(
        np.cos(radianos)
    )

    return float(
        np.rad2deg(
            np.arctan2(
                seno,
                cosseno,
            )
        )
        % 360
    )


# ==================================================================
# LEITURA DO PROCESSED
# ==================================================================

def ler_processed(caminho: Path) -> pd.DataFrame:

    df = pd.read_csv(
        caminho,
        encoding="utf-8-sig",
        sep=";",
        decimal=",",
        low_memory=False,
    )

    df["data"] = pd.to_datetime(
        df["data"],
        errors="coerce"
    )

    for coluna in (
        "codigo_wmo",
        "estacao",
        "uf",
        "regiao",
        "hora_utc",
    ):
        if coluna in df.columns:
            df[coluna] = df[coluna].astype("string")

    for coluna in [
        c for c in LIMITES_FISICOS
        if c in df.columns
    ]:
        df[coluna] = pd.to_numeric(
            df[coluna],
            errors="coerce"
        )

    return df


# ==================================================================
# AGREGAÇÃO DIÁRIA
# ==================================================================

def gerar_dados_diarios(
    df: pd.DataFrame,
) -> pd.DataFrame | None:

    if df.empty:
        return None

    df = df.copy()

    grupo = [
        "codigo_wmo",
        "estacao",
        "uf",
        "regiao",
        "latitude",
        "longitude",
        "altitude_m",
        "data",
    ]

    agregacoes = {}

    def registrar(
        nome_saida,
        coluna_entrada,
        funcao,
    ):

        if coluna_entrada in df.columns:

            agregacoes[
                nome_saida
            ] = (
                coluna_entrada,
                funcao,
            )

    registrar(
        "precipitacao_total_mm",
        "precipitacao_mm",
        "sum",
    )

    registrar(
        "pressao_media_mb",
        "pressao_mb",
        "mean",
    )

    registrar(
        "pressao_max_mb",
        "pressao_max_mb",
        "max",
    )

    registrar(
        "pressao_min_mb",
        "pressao_min_mb",
        "min",
    )

    registrar(
        "radiacao_total_kj_m2",
        "radiacao_kj_m2",
        "sum",
    )

    registrar(
        "temperatura_media_c",
        "temperatura_c",
        "mean",
    )

    registrar(
        "temperatura_maxima_c",
        "temperatura_max_c",
        "max",
    )

    registrar(
        "temperatura_minima_c",
        "temperatura_min_c",
        "min",
    )

    registrar(
        "ponto_orvalho_medio_c",
        "ponto_orvalho_c",
        "mean",
    )

    registrar(
        "umidade_media_pct",
        "umidade_pct",
        "mean",
    )

    registrar(
        "umidade_max_pct",
        "umidade_max_pct",
        "max",
    )

    registrar(
        "umidade_min_pct",
        "umidade_min_pct",
        "min",
    )

    registrar(
        "rajada_maxima_ms",
        "rajada_max_ms",
        "max",
    )

    registrar(
        "velocidade_vento_media_ms",
        "velocidade_vento_ms",
        "mean",
    )

    diario = (
        df.groupby(
            grupo,
            dropna=False,
        )
        .agg(**agregacoes)
        .reset_index()
    )

    # ==============================================================
    # HORAS OBSERVADAS
    # ==============================================================

    cobertura = (
        df.groupby(
            [
                "codigo_wmo",
                "data",
            ]
        )
        .size()
        .reset_index(
            name="horas_observadas"
        )
    )

    diario = diario.merge(
        cobertura,
        on=[
            "codigo_wmo",
            "data",
        ],
        how="left",
    )

    diario[
        "completude_pct"
    ] = (
        diario[
            "horas_observadas"
        ]
        / HORAS_ESPERADAS
        * 100
    ).clip(
        upper=100
    )

    # ==============================================================
    # DIREÇÃO DO VENTO
    # ==============================================================

    if (
        "direcao_vento_graus"
        in df.columns
    ):

        direcao = (
            df.groupby(
                [
                    "codigo_wmo",
                    "data",
                ]
            )[
                "direcao_vento_graus"
            ]
            .apply(media_circular)
            .reset_index(
                name="direcao_vento_media_graus"
            )
        )

        diario = diario.merge(
            direcao,
            on=[
                "codigo_wmo",
                "data",
            ],
            how="left",
        )

    # ==============================================================
    # ARREDONDAMENTO
    # ==============================================================

    for coluna, casas in (
        CASAS_DECIMAIS_AGREGADO.items()
    ):

        if coluna in diario.columns:

            diario[coluna] = (
                diario[coluna]
                .round(casas)
            )

    return diario


# ==================================================================
# KPIs
# ==================================================================

def criar_kpis(
    df: pd.DataFrame,
) -> pd.DataFrame:

    df = df.copy()

    # ==============================================================
    # CHUVA
    # ==============================================================

    if (
        "precipitacao_total_mm"
        in df.columns
    ):

        df["choveu"] = np.where(
            df[
                "precipitacao_total_mm"
            ].isna(),
            VALOR_NAO_CAPTADO,
            np.where(
                df[
                    "precipitacao_total_mm"
                ]
                >= CHUVA_MM_DIA,
                "sim",
                "nao",
            ),
        )

        df["chuva_forte"] = np.where(
            df[
                "precipitacao_total_mm"
            ].isna(),
            VALOR_NAO_CAPTADO,
            np.where(
                df[
                    "precipitacao_total_mm"
                ]
                >= CHUVA_FORTE_MM_DIA,
                "sim",
                "nao",
            ),
        )

        df["classe_chuva"] = np.select(
            [
                df[
                    "precipitacao_total_mm"
                ].isna(),

                df[
                    "precipitacao_total_mm"
                ] < 0.1,

                df[
                    "precipitacao_total_mm"
                ] < 10,

                df[
                    "precipitacao_total_mm"
                ] < 50,

                df[
                    "precipitacao_total_mm"
                ] >= 50,
            ],
            [
                VALOR_NAO_CAPTADO,
                "sem_chuva",
                "chuva_fraca",
                "chuva_moderada",
                "chuva_forte",
            ],
            default=VALOR_NAO_CAPTADO,
        )

    # ==============================================================
    # TEMPERATURA ALTA
    # ==============================================================

    if (
        "temperatura_maxima_c"
        in df.columns
    ):

        df[
            "temperatura_extrema_alta"
        ] = np.where(
            df[
                "temperatura_maxima_c"
            ].isna(),
            VALOR_NAO_CAPTADO,
            np.where(
                df[
                    "temperatura_maxima_c"
                ]
                >= TEMPERATURA_ALTA_C,
                "sim",
                "nao",
            ),
        )

    # ==============================================================
    # TEMPERATURA BAIXA
    # ==============================================================

    if (
        "temperatura_minima_c"
        in df.columns
    ):

        df[
            "temperatura_extrema_baixa"
        ] = np.where(
            df[
                "temperatura_minima_c"
            ].isna(),
            VALOR_NAO_CAPTADO,
            np.where(
                df[
                    "temperatura_minima_c"
                ]
                <= TEMPERATURA_BAIXA_C,
                "sim",
                "nao",
            ),
        )

    # ==============================================================
    # AMPLITUDE TÉRMICA
    # ==============================================================

    if (
        "temperatura_maxima_c"
        in df.columns
        and
        "temperatura_minima_c"
        in df.columns
    ):

        df[
            "amplitude_termica_c"
        ] = (
            df["temperatura_maxima_c"]
            - df["temperatura_minima_c"]
        ).round(1)

    # ==============================================================
    # VENTO
    # ==============================================================

    if (
        "rajada_maxima_ms"
        in df.columns
    ):

        df[
            "ventania_extrema"
        ] = np.where(
            df[
                "rajada_maxima_ms"
            ].isna(),
            VALOR_NAO_CAPTADO,
            np.where(
                df[
                    "rajada_maxima_ms"
                ]
                >= VENTANIA_MS,
                "sim",
                "nao",
            ),
        )

        df[
            "vento_forte"
        ] = np.where(
            df[
                "rajada_maxima_ms"
            ].isna(),
            VALOR_NAO_CAPTADO,
            np.where(
                df[
                    "rajada_maxima_ms"
                ]
                >= VENTO_FORTE_MS,
                "sim",
                "nao",
            ),
        )

        df[
            "classe_vento"
        ] = np.select(
            [
                df[
                    "rajada_maxima_ms"
                ].isna(),

                df[
                    "rajada_maxima_ms"
                ] < 5,

                df[
                    "rajada_maxima_ms"
                ] < 10,

                df[
                    "rajada_maxima_ms"
                ] < VENTANIA_MS,

                df[
                    "rajada_maxima_ms"
                ] >= VENTANIA_MS,
            ],
            [
                VALOR_NAO_CAPTADO,
                "calmo_fraco",
                "moderado",
                "forte",
                "ventania_extrema",
            ],
            default=VALOR_NAO_CAPTADO,
        )

    # ==============================================================
    # UMIDADE
    # ==============================================================

    if (
        "umidade_media_pct"
        in df.columns
    ):

        df[
            "umidade_muito_alta"
        ] = np.where(
            df[
                "umidade_media_pct"
            ].isna(),
            VALOR_NAO_CAPTADO,
            np.where(
                df[
                    "umidade_media_pct"
                ] >= 90,
                "sim",
                "nao",
            ),
        )

        df[
            "umidade_baixa"
        ] = np.where(
            df[
                "umidade_media_pct"
            ].isna(),
            VALOR_NAO_CAPTADO,
            np.where(
                df[
                    "umidade_media_pct"
                ] <= 30,
                "sim",
                "nao",
            ),
        )

    # ==============================================================
    # RADIAÇÃO MJ
    # ==============================================================

    if (
        "radiacao_total_kj_m2"
        in df.columns
    ):

        df[
            "radiacao_total_mj_m2"
        ] = (
            df[
                "radiacao_total_kj_m2"
            ]
            / 1000
        ).round(
            CASAS_DECIMAIS_AGREGADO.get(
                "radiacao_total_mj_m2",
                4,
            )
        )

    return df


# ==================================================================
# STATUS DIÁRIO
# ==================================================================

def criar_status_diario(
    df: pd.DataFrame,
) -> pd.DataFrame:

    df = df.copy()

    df[
        "status_dados"
    ] = np.where(
        df["horas_observadas"] == 0,
        VALOR_NAO_CAPTADO,
        np.where(
            df["completude_pct"] < 100,
            "dados_parcialmente_captados",
            "dados_completamente_captados",
        ),
    )

    return df


# ==================================================================
# PREPARAR CURATED
# ==================================================================

def preparar_curated(
    df: pd.DataFrame,
) -> pd.DataFrame:

    if df.empty:
        return df

    df = df.copy()

    df["data"] = pd.to_datetime(
        df["data"],
        errors="coerce",
    )

    df = df[
        df["data"].notna()
    ]

    df = df[
        df["uf"].isin(
            UF_REGIAO
        )
    ]

    # --------------------------------------------------------------
    # Priorizar registros com estação preenchida
    # --------------------------------------------------------------

    df["_prioridade_estacao"] = (
        df["estacao"]
        .fillna("")
        .astype("string")
        .str.strip()
        .ne("")
        .astype(int)
    )

    df = df.sort_values(
        [
            "_prioridade_estacao",
            "codigo_wmo",
            "data",
        ],
        ascending=[
            False,
            True,
            True,
        ],
    )

    df = df.drop_duplicates(
        subset=[
            "codigo_wmo",
            "data",
        ],
        keep="first",
    )

    df = df.drop(
        columns=[
            "_prioridade_estacao"
        ]
    )

    df = criar_kpis(df)

    df = criar_status_diario(df)

    df = df.sort_values(
        [
            "data",
            "uf",
            "estacao",
        ]
    )

    return df.reset_index(
        drop=True
    )


# ==================================================================
# EXPORTAR CURATED
# ==================================================================

def exportar_curated(df: pd.DataFrame) -> int:

    if df.empty:
        return 0

    total = 0

    for regiao in ("centro_oeste", "sul"):

        dados_regiao = df[
            df["regiao"] == regiao
        ].copy()

        if dados_regiao.empty:
            continue

        pasta = CAMINHO_CURATED / regiao
        pasta.mkdir(
            parents=True,
            exist_ok=True
        )

        for data, dados_dia in dados_regiao.groupby("data"):

            nome = (
                pd.Timestamp(data)
                .strftime("%Y-%m-%d")
                + ".csv"
            )

            caminho = pasta / nome

            dados_dia.to_csv(
                caminho,
                index=False,
                encoding="utf-8-sig",
                sep=";",
                decimal=",",
            )

            total += 1

    return total


# ==================================================================
# CHECAR NOTAÇÃO CIENTÍFICA
# ==================================================================

def checar_risco_notacao_cientifica(
    df: pd.DataFrame,
    contexto: str,
) -> list[str]:

    problemas = []

    for coluna in df.select_dtypes(
        include=[
            "float64",
            "float32",
        ]
    ).columns:

        valores = df[
            coluna
        ].dropna()

        if valores.empty:
            continue

        def digitos_sem_ponto(v):

            texto = (
                f"{v:.10f}"
                .rstrip("0")
                .rstrip(".")
            )

            return len(
                texto
                .replace(".", "")
                .replace("-", "")
            )

        maximo_digitos = (
            valores
            .apply(
                digitos_sem_ponto
            )
            .max()
        )

        if maximo_digitos > 12:

            problemas.append(
                f"{contexto}: coluna "
                f"'{coluna}' tem valor(es) "
                f"com {maximo_digitos} "
                "dígitos após remover o "
                "ponto decimal -> risco "
                "de notação científica."
            )

    return problemas


# ==================================================================
# VALIDAÇÃO CRUZADA
# ==================================================================

def validar_comparacao_bruto_tratado(
    caminho_processed: Path,
    df_curated_dia: pd.DataFrame,
    codigo_wmo: str,
) -> list[str]:

    problemas = []

    df_hora = ler_processed(
        caminho_processed
    )

    linha_curated = (
        df_curated_dia[
            df_curated_dia[
                "codigo_wmo"
            ] == codigo_wmo
        ]
    )

    if linha_curated.empty:

        return [
            "validação cruzada: estação "
            f"{codigo_wmo} não encontrada "
            "no CURATED do dia"
        ]

    if (
        "precipitacao_mm"
        in df_hora.columns
        and
        "precipitacao_total_mm"
        in linha_curated.columns
    ):

        soma_manual = round(
            float(
                df_hora[
                    "precipitacao_mm"
                ].sum()
            ),
            1,
        )

        valor_curated = float(
            linha_curated[
                "precipitacao_total_mm"
            ].iloc[0]
        )

        if abs(
            soma_manual
            - valor_curated
        ) > 0.15:

            problemas.append(
                "validação cruzada "
                "precipitação: "
                f"manual={soma_manual} "
                f"vs curated={valor_curated} "
                f"(estação {codigo_wmo})"
            )

    if (
        "temperatura_c"
        in df_hora.columns
        and
        "temperatura_media_c"
        in linha_curated.columns
    ):

        media_manual = round(
            float(
                df_hora[
                    "temperatura_c"
                ].mean()
            ),
            2,
        )

        valor_curated = float(
            linha_curated[
                "temperatura_media_c"
            ].iloc[0]
        )

        if abs(
            media_manual
            - valor_curated
        ) > 0.05:

            problemas.append(
                "validação cruzada "
                "temperatura: "
                f"manual={media_manual} "
                f"vs curated={valor_curated} "
                f"(estação {codigo_wmo})"
            )

    return problemas


# ==================================================================
# ETAPA 2 - PROCESSED -> CURATED
# ==================================================================

def processar_processed(
    relatorios: list,
) -> None:

    logger.info("=" * 70)

    logger.info(
        "ETAPA 2 - PROCESSED -> CURATED"
    )

    logger.info(
        "Entrada: %s",
        CAMINHO_PROCESSED.resolve(),
    )

    logger.info(
        "Saída: %s",
        CAMINHO_CURATED.resolve(),
    )

    logger.info("=" * 70)

    for ano in ANOS:

        pasta_ano = (
            CAMINHO_PROCESSED
            / str(ano)
        )

        if not pasta_ano.exists():

            logger.warning(
                "Processed inexistente: %s",
                pasta_ano,
            )

            continue

        arquivos = list(
            pasta_ano.glob("*.csv")
        )

        if not arquivos:
            continue

        bases = []

        mapa_arquivo_por_estacao = {}

        for caminho in arquivos:

            try:

                df = ler_processed(
                    caminho
                )

                if not df.empty:

                    codigo = str(
                        df[
                            "codigo_wmo"
                        ].iloc[0]
                    )

                    mapa_arquivo_por_estacao[
                        codigo
                    ] = caminho

                diario = (
                    gerar_dados_diarios(
                        df
                    )
                )

                if diario is None:
                    continue

                bases.append(
                    diario
                )

            except Exception as erro:

                logger.exception(
                    "Erro lendo processed: %s",
                    caminho,
                )

                relatorios.append({
                    "etapa": "curated",
                    "arquivo": str(
                        caminho
                    ),
                    "ano": ano,
                    "status": "erro",
                    "erro": repr(erro),
                })

        if not bases:
            continue

        df_ano = pd.concat(
            bases,
            ignore_index=True,
        )

        df_ano = preparar_curated(
            df_ano
        )

        # ==========================================================
        # VALIDAÇÃO DE NOTAÇÃO
        # ==========================================================

        problemas_notacao = (
            checar_risco_notacao_cientifica(
                df_ano,
                f"curated/{ano}",
            )
        )

        for problema in (
            problemas_notacao
        ):

            logger.warning(
                "VALIDAÇÃO: %s",
                problema,
            )

        # ==========================================================
        # VALIDAÇÃO CRUZADA
        # ==========================================================

        problemas_cruzados = []

        if not df_ano.empty:

            amostra = (
                df_ano
                .dropna(
                    subset=["data"]
                )
                .sample(
                    n=min(
                        5,
                        len(df_ano),
                    ),
                    random_state=42,
                )
            )

            for _, linha in (
                amostra.iterrows()
            ):

                codigo = linha[
                    "codigo_wmo"
                ]

                if codigo in (
                    mapa_arquivo_por_estacao
                ):

                    dia = df_ano[
                        df_ano["data"]
                        == linha["data"]
                    ]

                    problemas_cruzados.extend(
                        validar_comparacao_bruto_tratado(
                            mapa_arquivo_por_estacao[
                                codigo
                            ],
                            dia,
                            codigo,
                        )
                    )

        for problema in (
            problemas_cruzados
        ):

            logger.warning(
                "VALIDAÇÃO CRUZADA: %s",
                problema,
            )

        arquivos_exportados = (
            exportar_curated(
                df_ano
            )
        )

        relatorios.append({
            "etapa": "curated",
            "ano": ano,
            "linhas_diarias": len(
                df_ano
            ),
            "arquivos_exportados": (
                arquivos_exportados
            ),
            "problemas_notacao_cientifica": (
                len(problemas_notacao)
            ),
            "problemas_validacao_cruzada": (
                len(problemas_cruzados)
            ),
            "status": "ok",
        })

        logger.info(
            "CURATED %s FINALIZADO | "
            "%s registros | "
            "%s arquivos | "
            "%s alertas notação | "
            "%s alertas cruzados",
            ano,
            len(df_ano),
            arquivos_exportados,
            len(problemas_notacao),
            len(problemas_cruzados),
        )


# ==================================================================
# ETAPA 3 - CONSOLIDAÇÃO
# ==================================================================

def consolidar_curated(
    relatorios: list,
) -> None:

    logger.info("=" * 70)

    logger.info(
        "ETAPA 3 - CONSOLIDAÇÃO DOS CSVs CURATED"
    )

    logger.info("=" * 70)

    pasta_centro_oeste = (
        CAMINHO_CURATED
        / "centro_oeste"
    )

    pasta_sul = (
        CAMINHO_CURATED
        / "sul"
    )

    CAMINHO_CONSOLIDADO.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    arquivos_csv = []

    for pasta in (
        pasta_centro_oeste,
        pasta_sul,
    ):

        if pasta.exists():

            arquivos_csv.extend(
                pasta.rglob("*.csv")
            )

        else:

            logger.warning(
                "Pasta não encontrada: %s",
                pasta,
            )

    arquivos_csv = [
        a
        for a in arquivos_csv
        if CAMINHO_CONSOLIDADO.parent
        not in a.parents
    ]

    if not arquivos_csv:

        logger.warning(
            "Nenhum arquivo CURATED "
            "encontrado para consolidar."
        )

        relatorios.append({
            "etapa": "consolidacao",
            "status": "sem_arquivos",
        })

        return

    logger.info(
        "Arquivos a consolidar: %s",
        len(arquivos_csv),
    )

    dtype_identificadores = {

        "codigo_wmo": "string",

        "estacao": "string",

        "uf": "string",

        "regiao": "string",

        "hora_utc": "string",
    }

    todas_colunas = []

    for arquivo in arquivos_csv:

        colunas = pd.read_csv(
            arquivo,
            encoding="utf-8-sig",
            sep=";",
            decimal=",",
            nrows=0,
        ).columns

        for coluna in colunas:

            if coluna not in todas_colunas:

                todas_colunas.append(
                    coluna
                )

    if CAMINHO_CONSOLIDADO.exists():

        CAMINHO_CONSOLIDADO.unlink()

    primeira_escrita = True

    total_registros = 0

    arquivos_processados = 0

    todos_os_dados = []

    for numero, arquivo in enumerate(
        arquivos_csv,
        start=1,
    ):

        try:

            df = pd.read_csv(
                arquivo,
                encoding="utf-8-sig",
                sep=";",
                decimal=",",
                low_memory=False,
                dtype={
                    k: v
                    for k, v in dtype_identificadores.items()
                },
            )   

        except Exception as erro:

            logger.exception(
                "Erro lendo %s durante consolidação",
                arquivo,
            )

            relatorios.append({
                "etapa": "consolidacao",
                "arquivo": str(
                    arquivo
                ),
                "status": "erro",
                "erro": repr(erro),
            })

            continue

        quantidade_registros = len(df)

        for coluna in todas_colunas:

            if coluna not in df.columns:

                df[coluna] = pd.NA

        df = df[
            todas_colunas
        ]

        df[
            "arquivo_origem"
        ] = arquivo.name

        df.to_csv(
            CAMINHO_CONSOLIDADO,
            mode=(
                "w"
                if primeira_escrita
                else "a"
            ),
            header=primeira_escrita,
            index=False,
            encoding="utf-8-sig",
            sep=";",
            decimal=",",
        )

        primeira_escrita = False

        total_registros += (
            quantidade_registros
        )

        arquivos_processados += 1

        if len(todos_os_dados) < 50:

            todos_os_dados.append(
                df
            )

        if numero % 200 == 0:

            logger.info(
                "Consolidação: %s/%s arquivos",
                numero,
                len(arquivos_csv),
            )

    logger.info("=" * 70)

    logger.info(
        "CONSOLIDAÇÃO CONCLUÍDA"
    )

    logger.info(
        "Arquivos processados: %s / %s",
        arquivos_processados,
        len(arquivos_csv),
    )

    logger.info(
        "Total de registros: %s",
        total_registros,
    )

    logger.info(
        "Arquivo final: %s",
        CAMINHO_CONSOLIDADO,
    )

    logger.info("=" * 70)

    # ==============================================================
    # VALIDAÇÃO FINAL
    # ==============================================================

    problemas_finais = []

    if todos_os_dados:

        amostra_final = pd.concat(
            todos_os_dados,
            ignore_index=True,
        )

        problemas_finais = (
            checar_risco_notacao_cientifica(
                amostra_final,
                "consolidado_final",
            )
        )

        for coluna in (
            "codigo_wmo",
            "estacao",
            "uf",
        ):

            if (
                coluna in amostra_final.columns
                and not pd.api.types.is_string_dtype(
                    amostra_final[coluna]
                )
            ):

                problemas_finais.append(
                    f"consolidado_final: "
                    f"identificador '{coluna}' "
                    f"não é string "
                    f"(dtype={amostra_final[coluna].dtype})"
                )

        # ----------------------------------------------------------
        # Verifica identificadores vazios
        # ----------------------------------------------------------

        for coluna in (
            "codigo_wmo",
            "estacao",
            "uf",
        ):

            if coluna not in (
                amostra_final.columns
            ):
                continue

            vazios = (
                amostra_final[
                    coluna
                ]
                .fillna("")
                .astype("string")
                .str.strip()
                .eq("")
                .sum()
            )

            if vazios > 0:

                problemas_finais.append(
                    f"consolidado_final: "
                    f"coluna '{coluna}' possui "
                    f"{int(vazios)} registro(s) "
                    "vazio(s) na amostra."
                )

        if problemas_finais:

            logger.warning(
                "VALIDAÇÃO FINAL encontrou "
                "%s problema(s):",
                len(problemas_finais),
            )

            for problema in (
                problemas_finais
            ):

                logger.warning(
                    "  - %s",
                    problema,
                )

        else:

            logger.info(
                "VALIDAÇÃO FINAL: OK - "
                "nenhum valor com risco de "
                "notação científica e "
                "identificadores válidos."
            )

    relatorios.append({
        "etapa": "consolidacao",
        "arquivos_encontrados": (
            len(arquivos_csv)
        ),
        "arquivos_processados": (
            arquivos_processados
        ),
        "total_registros": (
            total_registros
        ),
        "arquivo_final": str(
            CAMINHO_CONSOLIDADO
        ),
        "problemas_validacao_final": (
            len(problemas_finais)
        ),
        "status": "ok",
    })


# ==================================================================
# RELATÓRIO FINAL
# ==================================================================

def salvar_relatorio(
    relatorios: list,
) -> None:

    CAMINHO_RELATORIOS.mkdir(
        parents=True,
        exist_ok=True,
    )

    df_relatorio = pd.DataFrame(
        relatorios
    )

    caminho = (
        CAMINHO_RELATORIOS
        / "relatorio_processamento.csv"
    )

    df_relatorio.to_csv(
        caminho,
        index=False,
        encoding="utf-8-sig",
        sep=";",
    )

    logger.info(
        "Relatório salvo em: %s",
        caminho,
    )

    erros = [
        r
        for r in relatorios
        if r.get("status")
        == "erro"
    ]

    avisos = [
        r
        for r in relatorios
        if r.get("status")
        == "aviso"
    ]

    logger.info(
        "Resumo: %s erro(s), %s aviso(s) "
        "ao longo do pipeline.",
        len(erros),
        len(avisos),
    )


# ==================================================================
# MAIN
# ==================================================================

def main():

    logger.info("=" * 70)

    logger.info(
        "PIPELINE INMET CONSOLIDADO INICIADO"
    )

    logger.info(
        "Período: 2019-2024 | "
        "Regiões: Centro-Oeste + Sul"
    )

    logger.info(
        "Regra de ausência: %s (nunca 0)",
        VALOR_NAO_CAPTADO,
    )

    logger.info("=" * 70)

    CAMINHO_PROCESSED.mkdir(
        parents=True,
        exist_ok=True,
    )

    CAMINHO_CURATED.mkdir(
        parents=True,
        exist_ok=True,
    )

    relatorios = []

    # ==============================================================
    # ETAPA 1
    # ==============================================================

    processar_raw(
        relatorios
    )

    # ==============================================================
    # ETAPA 2
    # ==============================================================

    processar_processed(
        relatorios
    )

    # ==============================================================
    # ETAPA 3
    # ==============================================================

    consolidar_curated(
        relatorios
    )

    # ==============================================================
    # RELATÓRIO
    # ==============================================================

    salvar_relatorio(
        relatorios
    )

    logger.info("=" * 70)

    logger.info(
        "PIPELINE INMET FINALIZADO"
    )

    logger.info(
        "Processed: %s",
        CAMINHO_PROCESSED.resolve(),
    )

    logger.info(
        "Curated: %s",
        CAMINHO_CURATED.resolve(),
    )

    logger.info(
        "Consolidado: %s",
        CAMINHO_CONSOLIDADO.resolve(),
    )

    logger.info("=" * 70)


# ==================================================================
# EXECUÇÃO
# ==================================================================

if __name__ == "__main__":
    main()