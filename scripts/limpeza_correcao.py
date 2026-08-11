# -*- coding: utf-8 -*-

"""
PIPELINE INMET
RAW -> PROCESSED -> CURATED

Arquitetura:

data/
├── raw/
│   └── INMET/
│       ├── 2019/
│       ├── 2020/
│       ├── 2021/
│       ├── 2022/
│       ├── 2023/
│       └── 2024/
│
├── databases_processed/
│   └── INMET/
│       ├── 2019/
│       ├── 2020/
│       └── ...
│
└── databases_curated/
    └── INMET/
        ├── centro_oeste/
        │   └── YYYY-MM-DD.csv
        └── sul/
            └── YYYY-MM-DD.csv

Fluxo:

RAW
 ↓
Limpeza e padronização
 ↓
PROCESSED
 ↓
Agregação diária + KPIs + validação
 ↓
CURATED
 ↓
Dashboard / Power BI / Streamlit
"""

from __future__ import annotations

import logging
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# CONFIGURAÇÃO
# ============================================================

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

CAMINHO_RELATORIOS = (
    CAMINHO_PROJETO
    / "outputs"
    / "relatorios"
)

ANOS = range(2019, 2025)

HORAS_ESPERADAS = 24

VALOR_NAO_CAPTADO = "dados_nao_captados"


# ============================================================
# REGIÕES
# ============================================================

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

for uf in UF_CENTRO_OESTE:
    UF_REGIAO[uf] = "centro_oeste"

for uf in UF_SUL:
    UF_REGIAO[uf] = "sul"


# ============================================================
# LIMITES FÍSICOS
# ============================================================

# Estes limites servem apenas para identificar valores
# fisicamente impossíveis.
#
# Eles NÃO representam limites de clima extremo.

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


# ============================================================
# REGRAS DOS KPIs
# ============================================================

CHUVA_MM_DIA = 0.1
CHUVA_FORTE_MM_DIA = 50

TEMPERATURA_ALTA_C = 35
TEMPERATURA_BAIXA_C = 10

VENTANIA_MS = 17.2
VENTO_FORTE_MS = 10


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("pipeline_inmet")


# ============================================================
# NORMALIZAÇÃO DE TEXTO
# ============================================================

def normalizar_texto(valor) -> str:
    """
    Normaliza textos removendo espaços extras,
    acentos e convertendo para maiúsculas.
    """

    if pd.isna(valor):
        return ""

    texto = str(valor).strip().upper()

    texto = unicodedata.normalize(
        "NFKD",
        texto,
    )

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto,
    )

    return texto


# ============================================================
# PADRONIZAÇÃO DE COLUNAS
# ============================================================

def padronizar_nome_coluna(nome) -> str:
    """
    Converte nomes de colunas para snake_case estrito.
    """

    texto = normalizar_texto(nome)

    texto = texto.replace("°", "")
    texto = texto.replace("²", "2")

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


# ============================================================
# CONVERSÃO NUMÉRICA
# ============================================================

def converter_numero(serie: pd.Series) -> pd.Series:
    """
    Converte valores meteorológicos para float64.

    Valores como -9999 representam falha de captura
    e são convertidos para NaN.

    IMPORTANTE:
    NaN é mantido internamente nas colunas numéricas
    para que médias, somas e agregações continuem
    matematicamente válidas.
    """

    serie = (
        serie
        .astype("string")
        .str.strip()
        .str.replace(",", ".", regex=False)
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
        ],
        pd.NA,
    )

    return pd.to_numeric(
        serie,
        errors="coerce",
    ).astype("float64")


# ============================================================
# EXTRAÇÃO DE METADADOS
# ============================================================

def extrair_metadados(caminho: Path) -> dict:
    """
    Extrai os metadados presentes no cabeçalho
    dos arquivos do INMET.
    """

    metadados = {}

    with caminho.open(
        "r",
        encoding="latin1",
        errors="replace",
    ) as arquivo:

        for _ in range(15):

            linha = arquivo.readline()

            if not linha:
                break

            partes = linha.rstrip(
                "\r\n"
            ).split(
                ";",
                1,
            )

            if len(partes) != 2:
                continue

            chave = normalizar_texto(
                partes[0]
            ).rstrip(":")

            valor = partes[1].strip()

            metadados[chave] = valor

    return metadados


# ============================================================
# OBTÉM METADADO
# ============================================================

def obter_metadado(
    metadados: dict,
    *chaves,
) -> str:
    """
    Busca um metadado pelo nome da chave.

    Tenta primeiro uma correspondência exata (após normalização
    de acentos/maiúsculas). Se não encontrar, tenta uma
    correspondência tolerante a caracteres corrompidos
    (ex.: 'ESTAC?O' no lugar de 'ESTAÇÃO', 'REGI?O' no lugar
    de 'REGIÃO'), o que acontece quando o arquivo de origem
    tem problemas de codificação e o caractere acentuado vira
    um '?' literal.
    """

    # ------------------------------------------------------
    # 1) Correspondência exata (comportamento original)
    # ------------------------------------------------------

    for chave in chaves:

        chave_normalizada = (
            normalizar_texto(chave)
        )

        if chave_normalizada in metadados:

            return metadados[
                chave_normalizada
            ]

    # ------------------------------------------------------
    # 2) Correspondência tolerante a '?' (novo)
    #
    # Compara caractere a caractere: qualquer posição com
    # '?' (na chave alvo OU na chave lida do arquivo) é
    # aceita como coringa, desde que o restante da palavra
    # e o tamanho batam.
    # ------------------------------------------------------

    def bate_com_coringa(chave_alvo: str, chave_arquivo: str) -> bool:

        if len(chave_alvo) != len(chave_arquivo):
            return False

        for caractere_alvo, caractere_arquivo in zip(
            chave_alvo,
            chave_arquivo,
        ):

            if caractere_alvo == "?" or caractere_arquivo == "?":
                continue

            if caractere_alvo != caractere_arquivo:
                return False

        return True

    for chave in chaves:

        chave_normalizada = normalizar_texto(chave)

        for chave_arquivo, valor_arquivo in metadados.items():

            if bate_com_coringa(chave_normalizada, chave_arquivo):

                return valor_arquivo

    return ""


# ============================================================
# LEITURA DA REGIÃO DECLARADA NO CABEÇALHO
# ============================================================

def obter_regiao_declarada(metadados: dict) -> str:
    """
    Lê o campo REGIÃO diretamente do cabeçalho do arquivo INMET
    (ex.: 'REGIÃO: CO'), da mesma forma que ESTAÇÃO, UF,
    LATITUDE etc.

    Também é tolerante a arquivos em que o caractere acentuado
    foi corrompido para '?' (ex.: 'REGI?O'), graças ao
    tratamento adicionado em obter_metadado.

    Esse valor é apenas informativo/auxiliar — a coluna
    'regiao' usada no pipeline continua sendo derivada de
    UF_REGIAO, então esta função não altera o comportamento
    existente do pipeline.
    """

    regiao_bruta = obter_metadado(
        metadados,
        "REGIAO",
        "REGI?O",
        "REGIÃO",
    )

    return normalizar_texto(regiao_bruta)


# ============================================================
# LEITURA DO ARQUIVO INMET
# ============================================================

def ler_inmet(
    caminho: Path,
    ano: int,
) -> pd.DataFrame | None:

    metadados = extrair_metadados(
        caminho
    )

    df = pd.read_csv(
        caminho,
        sep=";",
        encoding="latin1",
        skiprows=8,
        low_memory=False,
    )

    # Remove colunas completamente vazias.
    df = df.dropna(
        axis=1,
        how="all",
    )

    # Padroniza nomes.
    df.columns = [
        padronizar_nome_coluna(
            coluna
        )
        for coluna in df.columns
    ]

    # --------------------------------------------------------
    # DATA
    # --------------------------------------------------------

    coluna_data = None

    for coluna in df.columns:

        if (
            coluna == "data"
            or "data_yyyy_mm_dd" in coluna
            or coluna.startswith("data")
        ):

            coluna_data = coluna
            break

    if coluna_data is None:

        raise ValueError(
            "Coluna de data não encontrada."
        )

    # --------------------------------------------------------
    # HORA
    # --------------------------------------------------------

    coluna_hora = None

    for coluna in df.columns:

        if "hora_utc" in coluna:

            coluna_hora = coluna
            break

    if coluna_hora is None:

        for coluna in df.columns:

            if "hora" in coluna:

                coluna_hora = coluna
                break

    if coluna_hora is None:

        raise ValueError(
            "Coluna de hora não encontrada."
        )

    # --------------------------------------------------------
    # MAPEAMENTO METEOROLÓGICO
    # --------------------------------------------------------

    mapa_colunas = {}

    for coluna in df.columns:

        if "precipitacao_total" in coluna:

            mapa_colunas[
                coluna
            ] = "precipitacao_mm"

        elif (
            "pressao_atmosferica_ao_nivel_da_estacao"
            in coluna
        ):

            mapa_colunas[
                coluna
            ] = "pressao_mb"

        elif (
            "pressao_atmosferica_max"
            in coluna
        ):

            mapa_colunas[
                coluna
            ] = "pressao_max_mb"

        elif (
            "pressao_atmosferica_min"
            in coluna
        ):

            mapa_colunas[
                coluna
            ] = "pressao_min_mb"

        elif "radiacao_global" in coluna:

            mapa_colunas[
                coluna
            ] = "radiacao_kj_m2"

        elif (
            "temperatura_do_ar_bulbo_seco"
            in coluna
        ):

            mapa_colunas[
                coluna
            ] = "temperatura_c"

        elif (
            "temperatura_do_ponto_de_orvalho"
            in coluna
        ):

            mapa_colunas[
                coluna
            ] = "ponto_orvalho_c"

        elif "temperatura_maxima" in coluna:

            mapa_colunas[
                coluna
            ] = "temperatura_max_c"

        elif "temperatura_minima" in coluna:

            mapa_colunas[
                coluna
            ] = "temperatura_min_c"

        elif "temperatura_orvalho_max" in coluna:

            mapa_colunas[
                coluna
            ] = "ponto_orvalho_max_c"

        elif "temperatura_orvalho_min" in coluna:

            mapa_colunas[
                coluna
            ] = "ponto_orvalho_min_c"

        elif "umidade_rel_max" in coluna:

            mapa_colunas[
                coluna
            ] = "umidade_max_pct"

        elif "umidade_rel_min" in coluna:

            mapa_colunas[
                coluna
            ] = "umidade_min_pct"

        elif (
            "umidade_relativa_do_ar_horaria"
            in coluna
        ):

            mapa_colunas[
                coluna
            ] = "umidade_pct"

        elif "vento_direcao_horaria" in coluna:

            mapa_colunas[
                coluna
            ] = "direcao_vento_graus"

        elif "vento_rajada_maxima" in coluna:

            mapa_colunas[
                coluna
            ] = "rajada_max_ms"

        elif "vento_velocidade_horaria" in coluna:

            mapa_colunas[
                coluna
            ] = "velocidade_vento_ms"

    df = df.rename(
        columns=mapa_colunas
    )

    # --------------------------------------------------------
    # DATA
    # --------------------------------------------------------

    df["data"] = pd.to_datetime(
        df[coluna_data],
        errors="coerce",
    )

    # Mantém somente o ano esperado.
    df = df[
        df["data"].dt.year == ano
    ].copy()

    if df.empty:
        return None

    # --------------------------------------------------------
    # HORA
    # --------------------------------------------------------

    df["hora_utc"] = (
        df[coluna_hora]
        .astype("string")
        .str.strip()
    )

    # --------------------------------------------------------
    # METADADOS
    # --------------------------------------------------------

    uf = normalizar_texto(
        obter_metadado(
            metadados,
            "UF",
        )
    )

    if uf not in UF_REGIAO:
        return None

    codigo_wmo = obter_metadado(
        metadados,
        "CODIGO (WMO)",
        "CODIGO WMO",
    )

    estacao = obter_metadado(
        metadados,
        "ESTACAO",
        "ESTAC?O",
        "ESTA??O",
        "ESTAÇÃO",
    )

    latitude = obter_metadado(
        metadados,
        "LATITUDE",
    )

    longitude = obter_metadado(
        metadados,
        "LONGITUDE",
    )

    altitude = obter_metadado(
        metadados,
        "ALTITUDE",
    )

    regiao_declarada = obter_regiao_declarada(
        metadados
    )

    df["uf"] = uf

    df["regiao"] = UF_REGIAO[uf]

    df["regiao_declarada_arquivo"] = regiao_declarada

    df["codigo_wmo"] = normalizar_texto(
        codigo_wmo
    )

    df["estacao"] = normalizar_texto(
        estacao
    )

    df["latitude"] = converter_numero(
        pd.Series(
            [latitude] * len(df),
            index=df.index,
        )
    )

    df["longitude"] = converter_numero(
        pd.Series(
            [longitude] * len(df),
            index=df.index,
        )
    )

    df["altitude_m"] = converter_numero(
        pd.Series(
            [altitude] * len(df),
            index=df.index,
        )
    )

    # --------------------------------------------------------
    # VARIÁVEIS NUMÉRICAS
    # --------------------------------------------------------

    colunas_numericas = [
        "precipitacao_mm",
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

    for coluna in colunas_numericas:

        if coluna in df.columns:

            df[coluna] = converter_numero(
                df[coluna]
            )

    return df


# ============================================================
# TRATAMENTO DE VALORES FÍSICOS
# ============================================================

def tratar_valores_fisicos(
    df: pd.DataFrame,
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
            &
            (
                (df[coluna] < minimo)
                |
                (df[coluna] > maximo)
            )
        )

        # Valor fisicamente impossível
        # passa a representar ausência de captura.
        df.loc[
            mascara,
            coluna,
        ] = np.nan

    return df


# ============================================================
# OUTLIERS IQR
# ============================================================

def remover_outliers_iqr(
    df: pd.DataFrame,
) -> pd.DataFrame:

    df = df.copy()

    colunas = [
        "precipitacao_mm",
        "pressao_mb",
        "radiacao_kj_m2",
        "temperatura_c",
        "ponto_orvalho_c",
        "umidade_pct",
        "rajada_max_ms",
        "velocidade_vento_ms",
    ]

    for coluna in colunas:

        if coluna not in df.columns:
            continue

        grupo = df.groupby(
            "codigo_wmo"
        )[coluna]

        q1 = grupo.transform(
            lambda serie:
            serie.quantile(0.25)
        )

        q3 = grupo.transform(
            lambda serie:
            serie.quantile(0.75)
        )

        iqr = q3 - q1

        limite_inferior = (
            q1 - 3 * iqr
        )

        limite_superior = (
            q3 + 3 * iqr
        )

        mascara = (
            df[coluna].notna()
            &
            (
                (df[coluna] < limite_inferior)
                |
                (df[coluna] > limite_superior)
            )
        )

        # O registro não é excluído.
        # Apenas a medição suspeita é convertida
        # em ausência de dado.
        df.loc[
            mascara,
            coluna,
        ] = np.nan

    return df


# ============================================================
# MARCAÇÃO DE DADOS NÃO CAPTADOS
# ============================================================

def criar_indicadores_ausencia(
    df: pd.DataFrame,
) -> pd.DataFrame:

    df = df.copy()

    colunas_meteorologicas = [
        coluna
        for coluna in LIMITES_FISICOS
        if coluna in df.columns
    ]

    for coluna in colunas_meteorologicas:

        nome_indicador = (
            f"{coluna}_status"
        )

        df[nome_indicador] = np.where(
            df[coluna].isna(),
            VALOR_NAO_CAPTADO,
            "captado",
        )

    return df


# ============================================================
# EXPORTAÇÃO PROCESSED
# ============================================================

def exportar_processed(
    df: pd.DataFrame,
    ano: int,
    numero_arquivo: int,
) -> Path:

    pasta_saida = (
        CAMINHO_PROCESSED
        / str(ano)
    )

    pasta_saida.mkdir(
        parents=True,
        exist_ok=True,
    )

    codigo_wmo = (
        df["codigo_wmo"]
        .iloc[0]
        .replace("/", "_")
        .replace(" ", "_")
    )

    nome_arquivo = (
        f"{ano}_{codigo_wmo}_"
        f"{numero_arquivo:04d}.csv"
    )

    caminho_saida = (
        pasta_saida
        / nome_arquivo
    )

    df.to_csv(
        caminho_saida,
        index=False,
        encoding="utf-8-sig",
    )

    return caminho_saida


# ============================================================
# PROCESSAMENTO DO RAW
# ============================================================

def processar_raw(
    relatorios: list,
) -> None:

    logger.info(
        "=" * 70
    )

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

    logger.info(
        "=" * 70
    )

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

        arquivos = list(
            pasta_ano.rglob("*.CSV")
        )

        arquivos += list(
            pasta_ano.rglob("*.csv")
        )

        arquivos = list(
            dict.fromkeys(
                arquivos
            )
        )

        logger.info(
            "ANO %s | %s arquivos",
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
                )

                if df is None:

                    relatorios.append(
                        {
                            "etapa": "processed",
                            "arquivo": str(caminho),
                            "ano": ano,
                            "status": "ignorado",
                            "motivo": "uf_fora_do_escopo",
                        }
                    )

                    continue

                linhas_originais = len(df)

                # Tratamento físico.
                df = tratar_valores_fisicos(
                    df
                )

                # Tratamento estatístico.
                df = remover_outliers_iqr(
                    df
                )

                # Indicadores de ausência.
                df = criar_indicadores_ausencia(
                    df
                )

                # Remove duplicidades horárias.
                df = df.drop_duplicates(
                    subset=[
                        "codigo_wmo",
                        "data",
                        "hora_utc",
                    ],
                    keep="first",
                )

                df = df.sort_values(
                    [
                        "data",
                        "hora_utc",
                    ]
                ).reset_index(
                    drop=True
                )

                caminho_saida = exportar_processed(
                    df,
                    ano,
                    numero,
                )

                relatorios.append(
                    {
                        "etapa": "processed",
                        "arquivo": str(caminho),
                        "arquivo_saida": str(caminho_saida),
                        "ano": ano,
                        "uf": df["uf"].iloc[0],
                        "regiao": df["regiao"].iloc[0],
                        "linhas_entrada": linhas_originais,
                        "linhas_saida": len(df),
                        "status": "ok",
                    }
                )

                logger.info(
                    "PROCESSED | %s -> %s",
                    caminho.name,
                    caminho_saida,
                )

            except Exception as erro:

                logger.exception(
                    "Erro processando %s",
                    caminho,
                )

                relatorios.append(
                    {
                        "etapa": "processed",
                        "arquivo": str(caminho),
                        "ano": ano,
                        "status": "erro",
                        "erro": repr(erro),
                    }
                )


# ============================================================
# MÉDIA CIRCULAR
# ============================================================

def media_circular(
    serie: pd.Series,
) -> float:

    valores = (
        serie
        .dropna()
        .to_numpy(
            dtype=float
        )
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

    angulo = (
        np.rad2deg(
            np.arctan2(
                seno,
                cosseno,
            )
        )
        % 360
    )

    return float(angulo)


# ============================================================
# LEITURA DO PROCESSED
# ============================================================

def ler_processed(
    caminho: Path,
) -> pd.DataFrame:

    df = pd.read_csv(
        caminho,
        encoding="utf-8-sig",
    )

    df["data"] = pd.to_datetime(
        df["data"],
        errors="coerce",
    )

    colunas_numericas = [
        coluna
        for coluna in LIMITES_FISICOS
        if coluna in df.columns
    ]

    for coluna in colunas_numericas:

        df[coluna] = pd.to_numeric(
            df[coluna],
            errors="coerce",
        )

    return df


# ============================================================
# AGREGAÇÃO DIÁRIA
# ============================================================

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

    if "precipitacao_mm" in df.columns:

        agregacoes[
            "precipitacao_total_mm"
        ] = (
            "precipitacao_mm",
            "sum",
        )

    if "pressao_mb" in df.columns:

        agregacoes[
            "pressao_media_mb"
        ] = (
            "pressao_mb",
            "mean",
        )

    if "pressao_max_mb" in df.columns:

        agregacoes[
            "pressao_max_mb"
        ] = (
            "pressao_max_mb",
            "max",
        )

    if "pressao_min_mb" in df.columns:

        agregacoes[
            "pressao_min_mb"
        ] = (
            "pressao_min_mb",
            "min",
        )

    if "radiacao_kj_m2" in df.columns:

        agregacoes[
            "radiacao_total_kj_m2"
        ] = (
            "radiacao_kj_m2",
            "sum",
        )

    if "temperatura_c" in df.columns:

        agregacoes[
            "temperatura_media_c"
        ] = (
            "temperatura_c",
            "mean",
        )

    if "temperatura_max_c" in df.columns:

        agregacoes[
            "temperatura_maxima_c"
        ] = (
            "temperatura_max_c",
            "max",
        )

    if "temperatura_min_c" in df.columns:

        agregacoes[
            "temperatura_minima_c"
        ] = (
            "temperatura_min_c",
            "min",
        )

    if "ponto_orvalho_c" in df.columns:

        agregacoes[
            "ponto_orvalho_medio_c"
        ] = (
            "ponto_orvalho_c",
            "mean",
        )

    if "umidade_pct" in df.columns:

        agregacoes[
            "umidade_media_pct"
        ] = (
            "umidade_pct",
            "mean",
        )

    if "umidade_max_pct" in df.columns:

        agregacoes[
            "umidade_max_pct"
        ] = (
            "umidade_max_pct",
            "max",
        )

    if "umidade_min_pct" in df.columns:

        agregacoes[
            "umidade_min_pct"
        ] = (
            "umidade_min_pct",
            "min",
        )

    if "rajada_max_ms" in df.columns:

        agregacoes[
            "rajada_maxima_ms"
        ] = (
            "rajada_max_ms",
            "max",
        )

    if "velocidade_vento_ms" in df.columns:

        agregacoes[
            "velocidade_vento_media_ms"
        ] = (
            "velocidade_vento_ms",
            "mean",
        )

    diario = (
        df.groupby(
            grupo,
            dropna=False,
        )
        .agg(
            **agregacoes
        )
        .reset_index()
    )

    # --------------------------------------------------------
    # HORAS OBSERVADAS
    # --------------------------------------------------------

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

    diario["completude_pct"] = (
        diario["horas_observadas"]
        / HORAS_ESPERADAS
        * 100
    ).clip(
        upper=100
    )

    # --------------------------------------------------------
    # DIREÇÃO DO VENTO
    # --------------------------------------------------------

    if "direcao_vento_graus" in df.columns:

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

    return diario


# ============================================================
# KPIs
# ============================================================

def criar_kpis(
    df: pd.DataFrame,
) -> pd.DataFrame:

    df = df.copy()

    # --------------------------------------------------------
    # CHUVA
    # --------------------------------------------------------

    if "precipitacao_total_mm" in df.columns:

        df["choveu"] = np.where(
            df["precipitacao_total_mm"].isna(),
            VALOR_NAO_CAPTADO,
            np.where(
                df["precipitacao_total_mm"]
                >= CHUVA_MM_DIA,
                "sim",
                "nao",
            ),
        )

        df["chuva_forte"] = np.where(
            df["precipitacao_total_mm"].isna(),
            VALOR_NAO_CAPTADO,
            np.where(
                df["precipitacao_total_mm"]
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

    # --------------------------------------------------------
    # TEMPERATURA
    # --------------------------------------------------------

    if "temperatura_maxima_c" in df.columns:

        df["temperatura_extrema_alta"] = np.where(
            df[
                "temperatura_maxima_c"
            ].isna(),
            VALOR_NAO_CAPTADO,
            np.where(
                df[
                    "temperatura_maxima_c"
                ] >= TEMPERATURA_ALTA_C,
                "sim",
                "nao",
            ),
        )

    if "temperatura_minima_c" in df.columns:

        df["temperatura_extrema_baixa"] = np.where(
            df[
                "temperatura_minima_c"
            ].isna(),
            VALOR_NAO_CAPTADO,
            np.where(
                df[
                    "temperatura_minima_c"
                ] <= TEMPERATURA_BAIXA_C,
                "sim",
                "nao",
            ),
        )

    if (
        "temperatura_maxima_c" in df.columns
        and
        "temperatura_minima_c" in df.columns
    ):

        df["amplitude_termica_c"] = (
            df["temperatura_maxima_c"]
            - df["temperatura_minima_c"]
        )

    # --------------------------------------------------------
    # VENTO
    # --------------------------------------------------------

    if "rajada_maxima_ms" in df.columns:

        df["ventania_extrema"] = np.where(
            df[
                "rajada_maxima_ms"
            ].isna(),
            VALOR_NAO_CAPTADO,
            np.where(
                df[
                    "rajada_maxima_ms"
                ] >= VENTANIA_MS,
                "sim",
                "nao",
            ),
        )

        df["vento_forte"] = np.where(
            df[
                "rajada_maxima_ms"
            ].isna(),
            VALOR_NAO_CAPTADO,
            np.where(
                df[
                    "rajada_maxima_ms"
                ] >= VENTO_FORTE_MS,
                "sim",
                "nao",
            ),
        )

        df["classe_vento"] = np.select(
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

    # --------------------------------------------------------
    # UMIDADE
    # --------------------------------------------------------

    if "umidade_media_pct" in df.columns:

        df["umidade_muito_alta"] = np.where(
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

        df["umidade_baixa"] = np.where(
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

    # --------------------------------------------------------
    # RADIAÇÃO
    # --------------------------------------------------------

    if "radiacao_total_kj_m2" in df.columns:

        df["radiacao_total_mj_m2"] = (
            df[
                "radiacao_total_kj_m2"
            ] / 1000
        )

    return df


# ============================================================
# STATUS DE CAPTURA DIÁRIA
# ============================================================

def criar_status_diario(
    df: pd.DataFrame,
) -> pd.DataFrame:

    df = df.copy()

    df["status_dados"] = np.where(
        df["horas_observadas"] == 0,
        VALOR_NAO_CAPTADO,
        np.where(
            df["completude_pct"] < 100,
            "dados_parcialmente_captados",
            "dados_completamente_captados",
        ),
    )

    return df


# ============================================================
# PREPARAÇÃO DA CURATED
# ============================================================

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

    # Segurança contra duplicação.
    df = df.drop_duplicates(
        subset=[
            "codigo_wmo",
            "data",
        ],
        keep="first",
    )

    # Criação dos KPIs.
    df = criar_kpis(
        df
    )

    # Status de cobertura.
    df = criar_status_diario(
        df
    )

    # Ordenação final.
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


# ============================================================
# EXPORTAÇÃO CURATED
# ============================================================

def exportar_curated(
    df: pd.DataFrame,
) -> int:

    if df.empty:
        return 0

    total = 0

    for regiao in [
        "centro_oeste",
        "sul",
    ]:

        dados_regiao = df[
            df["regiao"] == regiao
        ].copy()

        if dados_regiao.empty:
            continue

        pasta = (
            CAMINHO_CURATED
            / regiao
        )

        pasta.mkdir(
            parents=True,
            exist_ok=True,
        )

        for data, dados_dia in (
            dados_regiao.groupby(
                "data"
            )
        ):

            data = pd.Timestamp(
                data
            )

            nome = (
                data.strftime(
                    "%Y-%m-%d"
                )
                + ".csv"
            )

            caminho = (
                pasta
                / nome
            )

            dados_dia.to_csv(
                caminho,
                index=False,
                encoding="utf-8-sig",
            )

            total += 1

            logger.info(
                "CURATED | %s | %s registros",
                caminho,
                len(dados_dia),
            )

    return total


# ============================================================
# PROCESSAMENTO PROCESSED -> CURATED
# ============================================================

def processar_processed(
    relatorios: list,
) -> None:

    logger.info(
        "=" * 70
    )

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

    logger.info(
        "=" * 70
    )

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

        for caminho in arquivos:

            try:

                df = ler_processed(
                    caminho
                )

                diario = gerar_dados_diarios(
                    df
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

                relatorios.append(
                    {
                        "etapa": "curated",
                        "arquivo": str(caminho),
                        "ano": ano,
                        "status": "erro",
                        "erro": repr(erro),
                    }
                )

        if not bases:
            continue

        df_ano = pd.concat(
            bases,
            ignore_index=True,
        )

        df_ano = preparar_curated(
            df_ano
        )

        arquivos_exportados = (
            exportar_curated(
                df_ano
            )
        )

        relatorios.append(
            {
                "etapa": "curated",
                "ano": ano,
                "linhas_diarias": len(df_ano),
                "arquivos_exportados": arquivos_exportados,
                "status": "ok",
            }
        )

        logger.info(
            "CURATED %s FINALIZADO | %s registros | %s arquivos",
            ano,
            len(df_ano),
            arquivos_exportados,
        )


# ============================================================
# RELATÓRIO
# ============================================================

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


# ============================================================
# MAIN
# ============================================================

def main():

    logger.info(
        "=" * 70
    )

    logger.info(
        "PIPELINE INMET INICIADO"
    )

    logger.info(
        "Período: 2019-2024"
    )

    logger.info(
        "Regiões: Centro-Oeste + Sul"
    )

    logger.info(
        "Regra de ausência: %s",
        VALOR_NAO_CAPTADO,
    )

    logger.info(
        "=" * 70
    )

    # Cria somente as pastas de saída.
    CAMINHO_PROCESSED.mkdir(
        parents=True,
        exist_ok=True,
    )

    CAMINHO_CURATED.mkdir(
        parents=True,
        exist_ok=True,
    )

    relatorios = []

    # --------------------------------------------------------
    # ETAPA 1
    # RAW -> PROCESSED
    # --------------------------------------------------------

    processar_raw(
        relatorios
    )

    # --------------------------------------------------------
    # ETAPA 2
    # PROCESSED -> CURATED
    # --------------------------------------------------------

    processar_processed(
        relatorios
    )

    # --------------------------------------------------------
    # RELATÓRIO
    # --------------------------------------------------------

    salvar_relatorio(
        relatorios
    )

    logger.info(
        "=" * 70
    )

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
        "=" * 70
    )


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":
    main()