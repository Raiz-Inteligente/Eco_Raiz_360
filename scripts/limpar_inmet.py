"""
PIPELINE PROFISSIONAL - DADOS METEOROLÓGICOS INMET

Entrada:
    data/raw/INMET/
        2019/
        2020/
        2021/
        2022/
        2023/
        2024/

Saída:
    dados_tratados/
        centro_oeste/
            YYYY-MM-DD.csv

        sul/
            YYYY-MM-DD.csv

Características:

- Processa 2019-2024
- Centro-Oeste:
    DF, GO, MT, MS

- Sul:
    PR, SC, RS

- Mantém dados meteorológicos relevantes
- Remove duplicidades
- Trata valores ausentes
- Converte tipos
- Trata valores meteorológicos inválidos
- Detecta outliers estatísticos
- Agrega dados horários para dados diários
- Cria KPIs meteorológicos
- Mantém latitude, longitude e altitude da estação
- Exporta uma base por região e por dia
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

RAW_ROOT = Path("data/raw/INMET")

OUTPUT_ROOT = Path("dados_tratados")

REPORT_ROOT = OUTPUT_ROOT / "_relatorios"

ANOS = range(2019, 2025)


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
# CONFIGURAÇÃO DE QUALIDADE
# ============================================================

HORAS_ESPERADAS = 24

VALORES_INVALIDOS = [
    -9999,
    -9999.0,
    -9999.00,
]


# Limites físicos muito amplos.
# Eles NÃO representam "clima extremo".
# Servem somente para retirar valores claramente impossíveis.

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
# KPIs
# ============================================================

# Critérios usados para classificação do dashboard.

CHUVA_MM_DIA = 0.1

CHUVA_FORTE_MM_DIA = 50

TEMPERATURA_ALTA_C = 35

TEMPERATURA_BAIXA_C = 10

VENTANIA_MS = 17.2

VENTO_FORTE_MS = 10


# ============================================================
# LOG
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("INMET")


# ============================================================
# NORMALIZAÇÃO DE TEXTO
# ============================================================

def normalizar_texto(valor) -> str:

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

    texto = re.sub(
        r"\s+",
        " ",
        texto,
    )

    return texto


# ============================================================
# NORMALIZAÇÃO DE COLUNAS
# ============================================================

def normalizar_coluna(nome) -> str:

    texto = normalizar_texto(nome)

    texto = texto.replace("°", "")
    texto = texto.replace("²", "2")

    texto = re.sub(
        r"[^A-Z0-9]+",
        "_",
        texto,
    )

    texto = texto.strip("_")

    return texto.lower()


# ============================================================
# CONVERSÃO NUMÉRICA
# ============================================================

def converter_numero(serie):

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
        ],
        pd.NA,
    )

    numeros = pd.to_numeric(
        serie,
        errors="coerce",
    )

    # IMPORTANTE: pd.to_numeric() sobre uma coluna "string" devolve o tipo
    # nullable "Float64" (com <NA>), não o float64 comum do NumPy. Isso faz
    # com que comparações (ex.: df["col"] < 5) virem uma Series "boolean"
    # nullable, que o np.select() NÃO aceita como "boolean ndarray" —
    # gerando o TypeError observado em criar_kpis(). Convertendo aqui para
    # float64 puro (NA vira NaN), as comparações voltam a ser bool comuns
    # do NumPy em toda a pipeline.
    return numeros.astype("float64")


# ============================================================
# METADADOS INMET
# ============================================================

def extrair_metadados(caminho):

    metadata = {}

    with caminho.open(
        "r",
        encoding="latin1",
        errors="replace",
    ) as arquivo:

        for _ in range(15):

            linha = arquivo.readline()

            if not linha:
                break

            partes = linha.rstrip("\r\n").split(
                ";",
                1,
            )

            if len(partes) != 2:
                continue

            chave = normalizar_texto(
                partes[0]
            ).rstrip(":")

            valor = partes[1].strip()

            metadata[chave] = valor

    return metadata


# ============================================================
# EXTRAÇÃO DE METADADOS
# ============================================================

def obter_metadado(metadata, *chaves):

    for chave in chaves:

        chave_normalizada = normalizar_texto(chave)

        if chave_normalizada in metadata:

            return metadata[chave_normalizada]

    return ""


# ============================================================
# LEITURA DO CSV
# ============================================================

def ler_inmet(caminho, ano):

    metadata = extrair_metadados(caminho)

    df = pd.read_csv(
        caminho,
        sep=";",
        encoding="latin1",
        skiprows=8,
        low_memory=False,
    )

    # --------------------------------------------------------
    # Remove colunas completamente vazias
    # --------------------------------------------------------

    df = df.dropna(
        axis=1,
        how="all",
    )

    # --------------------------------------------------------
    # Normaliza nomes
    # --------------------------------------------------------

    df.columns = [
        normalizar_coluna(c)
        for c in df.columns
    ]

    # --------------------------------------------------------
    # Identifica data
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
            "Coluna de data não encontrada"
        )

    # --------------------------------------------------------
    # Identifica hora
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
            "Coluna de hora não encontrada"
        )

    # --------------------------------------------------------
    # Renomeia variáveis meteorológicas
    # --------------------------------------------------------

    mapa = {}

    for coluna in df.columns:

        if "precipitacao_total" in coluna:

            mapa[coluna] = "precipitacao_mm"

        elif (
            "pressao_atmosferica_ao_nivel_da_estacao"
            in coluna
        ):

            mapa[coluna] = "pressao_mb"

        elif "pressao_atmosferica_max" in coluna:

            mapa[coluna] = "pressao_max_mb"

        elif "pressao_atmosferica_min" in coluna:

            mapa[coluna] = "pressao_min_mb"

        elif "radiacao_global" in coluna:

            mapa[coluna] = "radiacao_kj_m2"

        elif "temperatura_do_ar_bulbo_seco" in coluna:

            mapa[coluna] = "temperatura_c"

        elif "temperatura_do_ponto_de_orvalho" in coluna:

            mapa[coluna] = "ponto_orvalho_c"

        elif "temperatura_maxima" in coluna:

            mapa[coluna] = "temperatura_max_c"

        elif "temperatura_minima" in coluna:

            mapa[coluna] = "temperatura_min_c"

        elif "temperatura_orvalho_max" in coluna:

            mapa[coluna] = "ponto_orvalho_max_c"

        elif "temperatura_orvalho_min" in coluna:

            mapa[coluna] = "ponto_orvalho_min_c"

        elif "umidade_rel_max" in coluna:

            mapa[coluna] = "umidade_max_pct"

        elif "umidade_rel_min" in coluna:

            mapa[coluna] = "umidade_min_pct"

        elif "umidade_relativa_do_ar_horaria" in coluna:

            mapa[coluna] = "umidade_pct"

        elif "vento_direcao_horaria" in coluna:

            mapa[coluna] = "direcao_vento_graus"

        elif "vento_rajada_maxima" in coluna:

            mapa[coluna] = "rajada_max_ms"

        elif "vento_velocidade_horaria" in coluna:

            mapa[coluna] = "velocidade_vento_ms"

    df = df.rename(
        columns=mapa
    )

    # --------------------------------------------------------
    # DATA
    # --------------------------------------------------------

    df["data"] = pd.to_datetime(
        df[coluna_data],
        errors="coerce",
    )

    # --------------------------------------------------------
    # Mantém somente o ano da pasta
    # --------------------------------------------------------

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

    uf = obter_metadado(
        metadata,
        "UF",
    )

    uf = normalizar_texto(uf)

    codigo_wmo = obter_metadado(
        metadata,
        "CODIGO (WMO)",
        "CODIGO WMO",
    )

    estacao = obter_metadado(
        metadata,
        "ESTACAO",
    )

    latitude = obter_metadado(
        metadata,
        "LATITUDE",
    )

    longitude = obter_metadado(
        metadata,
        "LONGITUDE",
    )

    altitude = obter_metadado(
        metadata,
        "ALTITUDE",
    )

    # --------------------------------------------------------
    # REGIÃO BASEADA NA UF
    # --------------------------------------------------------

    if uf not in UF_REGIAO:

        return None

    df["uf"] = uf

    df["regiao"] = UF_REGIAO[uf]

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
    # CONVERSÃO DAS VARIÁVEIS
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
# TRATAMENTO FÍSICO
# ============================================================

def tratar_valores_fisicos(df):

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

        df.loc[
            mascara,
            coluna
        ] = np.nan

    return df


# ============================================================
# OUTLIERS - IQR
# ============================================================

def remover_outliers_iqr(df):

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

    # IMPORTANTE:
    # O IQR é calculado por estação.
    # Isso evita comparar uma estação fria
    # com uma estação quente.

    for coluna in colunas:

        if coluna not in df.columns:
            continue

        grupo = df.groupby(
            "codigo_wmo"
        )[coluna]

        q1 = grupo.transform(
            lambda x: x.quantile(0.25)
        )

        q3 = grupo.transform(
            lambda x: x.quantile(0.75)
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

        # Não remove a linha.
        # Somente torna a medição inválida nula.

        df.loc[
            mascara,
            coluna
        ] = np.nan

    return df


# ============================================================
# MÉDIA CIRCULAR DO VENTO
# ============================================================

def media_circular(serie):

    valores = serie.dropna().to_numpy(
        dtype=float
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

    angulo = np.rad2deg(
        np.arctan2(
            seno,
            cosseno,
        )
    ) % 360

    return float(angulo)


# ============================================================
# AGREGAÇÃO DIÁRIA
# ============================================================

def gerar_dados_diarios(df):

    if df is None or df.empty:

        return None

    df = df.copy()

    # --------------------------------------------------------
    # DUPLICADOS
    # --------------------------------------------------------

    df = df.drop_duplicates(
        subset=[
            "codigo_wmo",
            "data",
            "hora_utc",
        ],
        keep="first",
    )

    # --------------------------------------------------------
    # AGRUPAMENTO
    # --------------------------------------------------------

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

    if "ponto_orvalho_max_c" in df.columns:

        agregacoes[
            "ponto_orvalho_max_c"
        ] = (
            "ponto_orvalho_max_c",
            "max",
        )

    if "ponto_orvalho_min_c" in df.columns:

        agregacoes[
            "ponto_orvalho_min_c"
        ] = (
            "ponto_orvalho_min_c",
            "min",
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
        .agg(**agregacoes)
        .reset_index()
    )

    # --------------------------------------------------------
    # QUANTIDADE DE HORAS
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

    diario[
        "completude_pct"
    ] = (
        diario["horas_observadas"]
        / HORAS_ESPERADAS
        * 100
    ).clip(
        upper=100
    )

    # --------------------------------------------------------
    # DIREÇÃO DO VENTO
    # --------------------------------------------------------

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
# KPIs METEOROLÓGICOS
# ============================================================

def criar_kpis(df):

    df = df.copy()

    # --------------------------------------------------------
    # CHUVA
    # --------------------------------------------------------

    if "precipitacao_total_mm" in df.columns:

        df[
            "choveu"
        ] = (
            df["precipitacao_total_mm"]
            >= CHUVA_MM_DIA
        )

        df[
            "chuva_forte"
        ] = (
            df["precipitacao_total_mm"]
            >= CHUVA_FORTE_MM_DIA
        )

        df[
            "classe_chuva"
        ] = np.select(
            [
                df["precipitacao_total_mm"] < 0.1,

                df["precipitacao_total_mm"] < 10,

                df["precipitacao_total_mm"] < 50,

                df["precipitacao_total_mm"] >= 50,
            ],
            [
                "sem chuva",
                "chuva fraca",
                "chuva moderada",
                "chuva forte",
            ],
            default="sem dado",
        )

    # --------------------------------------------------------
    # TEMPERATURA
    # --------------------------------------------------------

    if "temperatura_maxima_c" in df.columns:

        df[
            "temperatura_extrema_alta"
        ] = (
            df["temperatura_maxima_c"]
            >= TEMPERATURA_ALTA_C
        )

    if "temperatura_minima_c" in df.columns:

        df[
            "temperatura_extrema_baixa"
        ] = (
            df["temperatura_minima_c"]
            <= TEMPERATURA_BAIXA_C
        )

    if (
        "temperatura_maxima_c" in df.columns
        and
        "temperatura_minima_c" in df.columns
    ):

        df[
            "amplitude_termica_c"
        ] = (
            df["temperatura_maxima_c"]
            -
            df["temperatura_minima_c"]
        )

    # --------------------------------------------------------
    # VENTO
    # --------------------------------------------------------

    if "rajada_maxima_ms" in df.columns:

        df[
            "ventania_extrema"
        ] = (
            df["rajada_maxima_ms"]
            >= VENTANIA_MS
        )

        df[
            "vento_forte"
        ] = (
            df["rajada_maxima_ms"]
            >= VENTO_FORTE_MS
        )

    # --------------------------------------------------------
    # CLASSIFICAÇÃO DO VENTO
    # --------------------------------------------------------

    if "rajada_maxima_ms" in df.columns:

        df[
            "classe_vento"
        ] = np.select(
            [
                df["rajada_maxima_ms"] < 5,

                df["rajada_maxima_ms"] < 10,

                df["rajada_maxima_ms"] < VENTANIA_MS,

                df["rajada_maxima_ms"] >= VENTANIA_MS,
            ],
            [
                "calmo/fraco",
                "moderado",
                "forte",
                "ventania extrema",
            ],
            default="sem dado",
        )

    # --------------------------------------------------------
    # UMIDADE
    # --------------------------------------------------------

    if "umidade_media_pct" in df.columns:

        df[
            "umidade_muito_alta"
        ] = (
            df["umidade_media_pct"]
            >= 90
        )

        df[
            "umidade_baixa"
        ] = (
            df["umidade_media_pct"]
            <= 30
        )

    # --------------------------------------------------------
    # RADIAÇÃO
    # --------------------------------------------------------

    if "radiacao_total_kj_m2" in df.columns:

        df[
            "radiacao_total_mj_m2"
        ] = (
            df["radiacao_total_kj_m2"]
            / 1000
        )

    return df


# ============================================================
# ORGANIZAÇÃO FINAL
# ============================================================

def preparar_saida(df):

    if df is None or df.empty:

        return None

    df = df.copy()

    # Data em formato padrão
    df["data"] = pd.to_datetime(
        df["data"],
        errors="coerce",
    )

    df = df[
        df["data"].notna()
    ]

    # Apenas regiões permitidas
    df = df[
        df["uf"].isin(
            UF_REGIAO
        )
    ]

    # Segurança contra duplicação
    df = df.drop_duplicates(
        subset=[
            "codigo_wmo",
            "data",
        ],
        keep="first",
    )

    # Cria KPIs
    df = criar_kpis(df)

    # Ordenação
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
# EXPORTAÇÃO
# ============================================================

def exportar_dados(df):

    if df is None or df.empty:

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
            OUTPUT_ROOT
            / regiao
        )

        pasta.mkdir(
            parents=True,
            exist_ok=True,
        )

        for data, dados_dia in dados_regiao.groupby(
            "data"
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

            # ------------------------------------------------
            # EXPORTAÇÃO
            # ------------------------------------------------

            dados_dia.to_csv(
                caminho,
                index=False,
                encoding="utf-8-sig",
                sep=",",
                decimal=".",
            )

            total += 1

            logger.info(
                "EXPORTADO: %s | %s registros",
                caminho,
                len(dados_dia),
            )

    return total


# ============================================================
# RELATÓRIO
# ============================================================

def salvar_relatorio(relatorios):

    REPORT_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = pd.DataFrame(
        relatorios
    )

    caminho = (
        REPORT_ROOT
        / "relatorio_processamento.csv"
    )

    df.to_csv(
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
# PROCESSAMENTO DE UM ANO
# ============================================================

def processar_ano(ano, relatorios):

    pasta_ano = (
        RAW_ROOT
        / str(ano)
    )

    if not pasta_ano.exists():

        logger.warning(
            "Pasta inexistente: %s",
            pasta_ano,
        )

        return

    arquivos = sorted(
        pasta_ano.rglob("*.CSV")
    )

    # Também aceita .csv
    arquivos += sorted(
        pasta_ano.rglob("*.csv")
    )

    # Remove duplicados
    arquivos = list(
        dict.fromkeys(
            arquivos
        )
    )

    logger.info(
        "ANO %s | %s arquivos encontrados",
        ano,
        len(arquivos),
    )

    bases = []

    for numero, caminho in enumerate(
        arquivos,
        start=1,
    ):

        logger.info(
            "[%s/%s] %s",
            numero,
            len(arquivos),
            caminho.name,
        )

        try:

            df = ler_inmet(
                caminho,
                ano,
            )

            if df is None:

                relatorios.append(
                    {
                        "arquivo": str(caminho),
                        "ano": ano,
                        "status": "IGNORADO",
                        "motivo": "UF fora do escopo",
                    }
                )

                continue

            linhas_brutas = len(df)

            # Tratamento físico
            df = tratar_valores_fisicos(
                df
            )

            # Outliers estatísticos
            df = remover_outliers_iqr(
                df
            )

            # Diário
            diario = gerar_dados_diarios(
                df
            )

            if diario is None:

                continue

            bases.append(
                diario
            )

            relatorios.append(
                {
                    "arquivo": str(caminho),
                    "ano": ano,
                    "uf": df["uf"].iloc[0],
                    "regiao": df["regiao"].iloc[0],
                    "linhas_horarias": linhas_brutas,
                    "linhas_diarias": len(diario),
                    "status": "OK",
                }
            )

        except Exception as erro:

            logger.error(
                "ERRO: %s | %s",
                caminho.name,
                erro,
            )

            relatorios.append(
                {
                    "arquivo": str(caminho),
                    "ano": ano,
                    "status": "ERRO",
                    "erro": repr(erro),
                }
            )

    # --------------------------------------------------------
    # CONSOLIDA O ANO
    # --------------------------------------------------------

    if not bases:

        logger.warning(
            "Nenhuma base válida encontrada em %s",
            ano,
        )

        return

    df_ano = pd.concat(
        bases,
        ignore_index=True,
    )

    # --------------------------------------------------------
    # SEGURANÇA
    # --------------------------------------------------------

    df_ano = preparar_saida(
        df_ano
    )

    if df_ano is None or df_ano.empty:

        logger.warning(
            "Nenhum dado disponível após tratamento em %s",
            ano,
        )

        return

    # --------------------------------------------------------
    # EXPORTAÇÃO
    # --------------------------------------------------------

    arquivos_exportados = (
        exportar_dados(
            df_ano
        )
    )

    logger.info(
        "ANO %s FINALIZADO | %s registros | %s arquivos exportados",
        ano,
        len(df_ano),
        arquivos_exportados,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    logger.info(
        "=" * 70
    )

    logger.info(
        "INICIANDO PIPELINE INMET"
    )

    logger.info(
        "Entrada: %s",
        RAW_ROOT.resolve(),
    )

    logger.info(
        "Saída: %s",
        OUTPUT_ROOT.resolve(),
    )

    logger.info(
        "Regiões: Centro-Oeste + Sul"
    )

    logger.info(
        "Período: 2019-2024"
    )

    logger.info(
        "=" * 70
    )

    OUTPUT_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    relatorios = []

    for ano in ANOS:

        processar_ano(
            ano,
            relatorios,
        )

    salvar_relatorio(
        relatorios
    )

    logger.info(
        "=" * 70
    )

    logger.info(
        "PIPELINE FINALIZADO"
    )

    logger.info(
        "Verifique: %s",
        OUTPUT_ROOT.resolve(),
    )

    logger.info(
        "=" * 70
    )


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    main()