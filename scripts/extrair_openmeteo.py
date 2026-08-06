import pandas as pd
import requests

# ---------------------------------------------------------
# 1. Configuração e Extração Inicial
# ---------------------------------------------------------
url = "https://archive-api.open-meteo.com/v1/archive"

ANO_INICIAL = "2015-01-01"
ANO_FINAL = "2025-12-31"

params = {
    "latitude": -12.54,
    "longitude": -55.72,
    "start_date": ANO_INICIAL,
    "end_date": ANO_FINAL,
    "hourly": ["temperature_2m", "precipitation"],
}
resposta = requests.get(url, params=params)

print(resposta.status_code)
dados = resposta.json()
dados["hourly"]["temperature_2m"]

df_clima = pd.DataFrame({
    "data_hora": dados["hourly"]["time"],
    "temperatura": dados["hourly"]["temperature_2m"],
    "precipitacao": dados["hourly"]["precipitation"],
})
df_clima.head()

# ---------------------------------------------------------
# 2. Definição das Regiões e Iteração da Extração
# ---------------------------------------------------------
regioes = pd.DataFrame({
    "regiao": ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"],
    "latitude": [-3.119, -12.977, -15.793, -23.550, -25.428],
    "longitude": [-60.021, -38.501, -47.882, -46.633, -49.273],
})

dados_clima = []
for _, linha in regioes.iterrows():
  params = {
      "latitude": linha["latitude"],
      "longitude": linha["longitude"],
      "start_date": ANO_INICIAL,
      "end_date": ANO_FINAL,
      "hourly": ["temperature_2m", "precipitation"],
  }

  resposta = requests.get(url, params=params)
  dados = resposta.json()

  df = pd.DataFrame({
      "data_hora": dados["hourly"]["time"],
      "temperatura": dados["hourly"]["temperature_2m"],
      "precipitacao": dados["hourly"]["precipitation"],
  })

  df["regiao"] = linha["regiao"]
  dados_clima.append(df)
  print(f'{linha["regiao"]} ✔')

df_clima = pd.concat(dados_clima, ignore_index=True)

df_clima.head()
df_clima.info()
df_clima["regiao"].value_counts()

# ---------------------------------------------------------
# 3. Inspeção Inicial e Tratamento de Dados
# ---------------------------------------------------------
df_clima.shape
df_clima.info()
df_clima.describe()
df_clima.isnull().sum()
df_clima.duplicated().sum()
df_clima.head(10)
df_clima[df_clima["precipitacao"] > 0].head(20)

df_clima["data_hora"] = pd.to_datetime(df_clima["data_hora"])
df_clima.info()

df_clima["ano"] = df_clima["data_hora"].dt.year
df_clima["mes"] = df_clima["data_hora"].dt.month
df_clima["dia"] = df_clima["data_hora"].dt.day
df_clima["hora"] = df_clima["data_hora"].dt.hour

df_clima.head()
df_clima.info()

# ==========================================================
# ETAPA 1 - INSPEÇÃO INICIAL DOS DADOS
# ==========================================================
# print("Dimensões da base:")
# print(df_clima.shape)

# print("\nInformações da base:")
# print(df_clima.info())

# print("\nTipos das colunas:")
# print(df_clima.dtypes)

# print("\nPrimeiros registros:")
# display(df_clima.head())

# print("\nÚltimos registros:")
# display(df_clima.tail())

# ==========================================================
# ETAPA 2 - VALORES NULOS
# ==========================================================
print("\nValores nulos por coluna:")
print(df_clima.isnull().sum())

print("\nPercentual de valores nulos:")
print((df_clima.isnull().sum() / len(df_clima)) * 100)

# ==========================================================
# ETAPA 3 - REGISTROS DUPLICADOS
# ==========================================================
print("\nDuplicados encontrados:")
print(df_clima.duplicated().sum())

df_clima = df_clima.drop_duplicates()

print("\nDuplicados após limpeza:")
print(df_clima.duplicated().sum())

# ==========================================================
# ETAPA 4 - PADRONIZAÇÃO DOS TIPOS
# ==========================================================
df_clima["data_hora"] = pd.to_datetime(df_clima["data_hora"])
df_clima["temperatura"] = df_clima["temperatura"].astype(float)
df_clima["precipitacao"] = df_clima["precipitacao"].astype(float)

# ==========================================================
# ETAPA 5 - CRIAÇÃO DAS COLUNAS DE DATA
# ==========================================================
df_clima["ano"] = df_clima["data_hora"].dt.year
df_clima["mes"] = df_clima["data_hora"].dt.month
df_clima["dia"] = df_clima["data_hora"].dt.day
df_clima["hora"] = df_clima["data_hora"].dt.hour
df_clima["nome_mes"] = df_clima["data_hora"].dt.month_name()
df_clima["dia_semana"] = df_clima["data_hora"].dt.day_name()

# ==========================================================
# ETAPA 6 - VALORES IMPOSSÍVEIS
# ==========================================================
print(df_clima.describe())

print("\nTemperatura mínima:")
print(df_clima["temperatura"].min())

print("\nTemperatura máxima:")
print(df_clima["temperatura"].max())

print("\nPrecipitação mínima:")
print(df_clima["precipitacao"].min())

print("\nPrecipitação máxima:")
print(df_clima["precipitacao"].max())

# ==========================================================
# ETAPA 7 - TRATAMENTO DE VALORES INVÁLIDOS
# ==========================================================
df_clima = df_clima[df_clima["temperatura"] > -20]
df_clima = df_clima[df_clima["temperatura"] < 60]
df_clima = df_clima[df_clima["precipitacao"] >= 0]

# ==========================================================
# ETAPA 8 - ORDENAÇÃO DOS DADOS
# ==========================================================
df_clima = df_clima.sort_values(by=["regiao", "data_hora"])
df_clima = df_clima.reset_index(drop=True)

# ==========================================================
# ETAPA 9 - CONFERÊNCIA FINAL
# ==========================================================
print("\nResumo final da base:")
print(df_clima.info())

print("\nDimensão final:")
print(df_clima.shape)



# ==========================================================
# ETAPA 10 - ENGENHARIA DE ATRIBUTOS
# ==========================================================
chuva_diaria = (
    df_clima.groupby(["regiao", "ano", "mes", "dia"])["precipitacao"]
    .sum()
    .reset_index(name="chuva_dia")
)

temperatura_diaria = (
    df_clima.groupby(["regiao", "ano", "mes", "dia"])["temperatura"]
    .mean()
    .reset_index(name="temperatura_media_dia")
)

chuva_mensal = (
    df_clima.groupby(["regiao", "ano", "mes"])["precipitacao"]
    .sum()
    .reset_index(name="chuva_mes")
)

temperatura_mensal = (
    df_clima.groupby(["regiao", "ano", "mes"])["temperatura"]
    .mean()
    .reset_index(name="temperatura_media_mes")
)


# Classificação da Temperatura
def classificar_temperatura(valor):
  if valor < 18:
    return "Frio"
  elif valor < 25:
    return "Ameno"
  elif valor < 30:
    return "Quente"
  else:
    return "Muito Quente"


df_clima["classe_temperatura"] = df_clima["temperatura"].apply(
    classificar_temperatura
)


# Classificação da Precipitação
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


df_clima["classe_chuva"] = df_clima["precipitacao"].apply(classificar_chuva)


# Estação do Ano
def estacao(mes):
  if mes in [12, 1, 2]:
    return "Verão"
  elif mes in [3, 4, 5]:
    return "Outono"
  elif mes in [6, 7, 8]:
    return "Inverno"
  else:
    return "Primavera"


df_clima["estacao"] = df_clima["mes"].apply(estacao)

df_clima["sem_chuva"] = df_clima["precipitacao"] == 0
df_clima["onda_calor"] = df_clima["temperatura"] >= 35
df_clima["chuva_extrema"] = df_clima["precipitacao"] >= 30

# Dias Consecutivos sem Chuva
df_clima["sem_chuva"] = df_clima["precipitacao"] == 0
df_clima = df_clima.sort_values(["regiao", "data_hora"]).reset_index(drop=True)
df_clima["horas_sem_chuva"] = 0

for regiao in df_clima["regiao"].unique():
  mascara = df_clima["regiao"] == regiao
  contador = 0
  valores = []

  for chuva in df_clima.loc[mascara, "sem_chuva"]:
    if chuva:
      contador += 1
    else:
      contador = 0
    valores.append(contador)

  df_clima.loc[mascara, "horas_sem_chuva"] = valores

df_clima["dias_sem_chuva"] = df_clima["horas_sem_chuva"] / 24

# Eventos Extremos
df_clima["evento_chuva_extrema"] = df_clima["precipitacao"] >= 30
df_clima["evento_calor_extremo"] = df_clima["temperatura"] >= 35
df_clima["evento_extremo"] = (
    df_clima["evento_chuva_extrema"] | df_clima["evento_calor_extremo"]
)

# Anomalia de Temperatura
media_regiao = df_clima.groupby("regiao")["temperatura"].transform("mean")
df_clima["anomalia_temperatura"] = df_clima["temperatura"] - media_regiao

# Índice de Risco Climático
df_clima["risco_climatico"] = (
    df_clima["dias_sem_chuva"] * 0.40
    + df_clima["anomalia_temperatura"].abs() * 0.30
    + df_clima["evento_extremo"].astype(int) * 30
)


# Aptidão Agrícola
def calcular_aptidao(linha):
  temperatura = linha["temperatura"]
  chuva = linha["precipitacao"]
  score = 100

  if temperatura < 18:
    score -= 20
  elif temperatura > 34:
    score -= 20

  if chuva == 0:
    score -= 15
  elif chuva > 25:
    score -= 10

  return max(score, 0)


df_clima["aptidao_agricola"] = df_clima.apply(calcular_aptidao, axis=1)


# Score ESG Climático
def score_esg(linha):
  score = 100
  score -= linha["dias_sem_chuva"] * 0.8
  score -= abs(linha["anomalia_temperatura"]) * 2
  if linha["evento_extremo"]:
    score -= 20
  return max(0, min(score, 100))


df_clima["score_esg"] = df_clima.apply(score_esg, axis=1)

# Ranking Climático
ranking = (
    df_clima.groupby("regiao")
    .agg(
        Score_ESG=("score_esg", "mean"),
        Aptidao=("aptidao_agricola", "mean"),
        Risco=("risco_climatico", "mean"),
        Temperatura=("temperatura", "mean"),
        Chuva=("precipitacao", "sum"),
    )
    .sort_values("Score_ESG", ascending=False)
)
ranking

# Dashboard Executivo - Resumo por Região
resumo_clima = (
    df_clima.groupby("regiao")
    .agg(
        temperatura_media=("temperatura", "mean"),
        temperatura_maxima=("temperatura", "max"),
        temperatura_minima=("temperatura", "min"),
        chuva_total=("precipitacao", "sum"),
        chuva_media=("precipitacao", "mean"),
        chuva_maxima=("precipitacao", "max"),
        horas_sem_chuva=("sem_chuva", "sum"),
        dias_sem_chuva=("dias_sem_chuva", "max"),
        horas_onda_calor=("onda_calor", "sum"),
        eventos_chuva_extrema=("evento_chuva_extrema", "sum"),
        eventos_calor_extremo=("evento_calor_extremo", "sum"),
        eventos_extremos=("evento_extremo", "sum"),
        anomalia_media=("anomalia_temperatura", "mean"),
        risco_climatico=("risco_climatico", "mean"),
        aptidao_agricola=("aptidao_agricola", "mean"),
        score_esg=("score_esg", "mean"),
    )
    .round(2)
)
resumo_clima

# ---------------------------------------------------------
# 4. Exportação
# ---------------------------------------------------------
# df_clima.to_csv(
#     "../dados_tratados/clima_tratado.csv", index=False, encoding="utf-8-sig"
# )


print('''
        ┌──────────────────────────────────────────────┐
        │            OPÇÕES DE DOWNLOAD                │
        ├──────────────────────────────────────────────┤
        │  [ 1 ] Baixar Base Completa                  │
        │  [ 2 ] Baixar Base Resumida                  │
        └──────────────────────────────────────────────┘
''')

while True:
  try:
    analista = int(input("Escolha uma opção (1 ou 2): ").strip())

    if analista == 1:
      # Exporta a base inteira (dados brutos/tratados)
      df_clima.to_csv("dados_tratados/clima_tratado.csv", index=False, encoding="utf-8-sig")
      break

    elif analista == 2:
      # Exporta fracionado agrupa e salva em 1 linha para cada arquivo
      df_clima.groupby(["regiao", "ano", "mes", "dia"])[
          ["precipitacao", "temperatura"]
      ].agg({"precipitacao": "sum", "temperatura": "mean"}).reset_index().to_csv(
          "dados_tratados/clima_resumo_diario.csv", index=False, encoding="utf-8-sig"
      )

      df_clima.groupby(["regiao", "ano", "mes"])[
          ["precipitacao", "temperatura"]
      ].agg({"precipitacao": "sum", "temperatura": "mean"}).reset_index().to_csv(
          "dados_tratados/clima_resumo_mesal.csv", index=False, encoding="utf-8-sig"
      )
      break

    else:
      print("Opção inválida. Digite 1 ou 2.")

  except ValueError:
    print("Entrada inválida. Digite apenas números.")

print("Exportação concluída com sucesso!")