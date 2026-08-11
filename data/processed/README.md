# Processed Data

Esta pasta contém as bases de dados após as etapas de **limpeza, padronização, validação e transformação** dos dados brutos utilizados no projeto **Eco_Raiz_360**.

Os dados processados são derivados das fontes originais armazenadas em `data/raw/` e representam a camada intermediária do pipeline de dados.

---

## Objetivo

A camada `processed` tem como objetivo transformar os dados brutos em conjuntos de dados **estruturados, consistentes e prontos para integração e análise**.

As etapas de processamento podem incluir:

* Padronização dos nomes das colunas;
* Padronização dos tipos de dados;
* Tratamento de valores ausentes;
* Remoção de registros duplicados;
* Tratamento de inconsistências;
* Padronização de unidades de medida;
* Padronização de identificadores geográficos;
* Tratamento de valores inválidos;
* Seleção das variáveis relevantes;
* Conversão e normalização de formatos;
* Validação da estrutura dos dados;
* Preparação para integração entre diferentes fontes.

---

# Bases Processadas

## 1. EMBRAPA — Dados Agropecuários

**Pasta:** `embrapa_dados_agropecuarios`

**Link dos dados processados:**
🔗 `COLE_O_LINK_DO_GOOGLE_DRIVE_AQUI`

### Descrição

Dados agropecuários utilizados para caracterização das atividades produtivas e análise do setor agropecuário.

### Principais tratamentos

* Padronização das variáveis agropecuárias;
* Tratamento de valores ausentes;
* Padronização de unidades;
* Padronização de municípios e códigos geográficos;
* Seleção das variáveis relevantes para análise.

---

## 2. IBGE — Bioma Predominante por Município

**Pasta:** `ibge_bioma_predominante_municipio`

**Link dos dados processados:**
🔗 `COLE_O_LINK_DO_GOOGLE_DRIVE_AQUI`

### Descrição

Dados utilizados para identificar o bioma predominante associado a cada município.

### Principais tratamentos

* Padronização dos códigos dos municípios;
* Padronização dos nomes dos municípios;
* Tratamento de valores ausentes;
* Validação dos municípios;
* Organização das informações para integração com outras bases.

---

## 3. IBGE — Malha Municipal

**Pasta:** `ibge_malha_municipal`

**Link dos dados processados:**
🔗 `COLE_O_LINK_DO_GOOGLE_DRIVE_AQUI`

### Descrição

Dados geográficos utilizados como referência territorial para os municípios analisados.

### Principais tratamentos

* Padronização dos identificadores municipais;
* Validação da estrutura territorial;
* Padronização dos nomes das unidades geográficas;
* Organização dos atributos espaciais;
* Preparação para integração com dados socioeconômicos, ambientais e agropecuários.

---

## 4. IBGE — PAM — Soja e Cana-de-açúcar

**Pasta:** `ibge_pam_soja_cana_municipios`

**Link dos dados processados:**
🔗 `COLE_O_LINK_DO_GOOGLE_DRIVE_AQUI`

### Descrição

Dados da Produção Agrícola Municipal relacionados principalmente à produção de **soja e cana-de-açúcar**.

### Principais tratamentos

* Seleção das culturas relevantes;
* Padronização de municípios;
* Padronização de unidades de produção;
* Tratamento de valores ausentes;
* Padronização dos períodos de referência;
* Organização das variáveis de produção e área plantada/colhida.

---

## 5. INMET — Dados Históricos Climáticos

**Pasta:** `inmet_dados_historicos_climaticos`

**Link dos dados processados:**
🔗 `COLE_O_LINK_DO_GOOGLE_DRIVE_AQUI`

### Descrição

Dados meteorológicos históricos utilizados para caracterização das condições climáticas das regiões analisadas.

### Principais tratamentos

* Padronização de datas e horários;
* Tratamento de registros inconsistentes;
* Padronização das variáveis meteorológicas;
* Tratamento de valores ausentes;
* Organização das informações por estação e período;
* Padronização das unidades de medida.

---

## 6. MapBiomas — Cobertura e Uso da Terra

**Pasta:** `mapbiomas_cobertura_uso_terra`

**Link dos dados processados:**
🔗 `COLE_O_LINK_DO_GOOGLE_DRIVE_AQUI`

### Descrição

Dados utilizados para caracterizar a cobertura e o uso da terra nos territórios analisados.

### Principais tratamentos

* Seleção das classes de cobertura e uso relevantes;
* Padronização dos códigos territoriais;
* Organização das informações temporais;
* Tratamento de valores ausentes ou inconsistentes;
* Preparação dos dados para análises territoriais e ambientais.

---

## 7. MapBiomas — Solo

**Pasta:** `mapbiomas_solo`

**Link dos dados processados:**
🔗 `COLE_O_LINK_DO_GOOGLE_DRIVE_AQUI`

### Descrição

Dados relacionados às características e classificação dos solos utilizados na análise ambiental e territorial.

### Principais tratamentos

* Padronização das classes de solo;
* Organização das informações territoriais;
* Padronização dos identificadores geográficos;
* Tratamento de inconsistências;
* Seleção das variáveis relevantes para integração.

---

## 8. SEEG — Emissões de Gases de Efeito Estufa

**Pasta:** `seeg_emissoes_gee`

**Link dos dados processados:**
🔗 `https://drive.google.com/drive/folders/1aG6PNyGRIFVlrDvo-jAF64y_7rwqx6q0?usp=sharing`

### Descrição

Dados de emissões e remoções de gases de efeito estufa utilizados para análise da dimensão climática e ambiental do projeto.

### Principais tratamentos

* Seleção dos setores e categorias relevantes;
* Padronização dos municípios;
* Padronização das unidades de emissão;
* Tratamento de valores ausentes;
* Organização por ano;
* Padronização dos gases e categorias de emissão;
* Preparação para integração com dados agropecuários, climáticos e territoriais.

---

# Estrutura do Pipeline

```text
┌──────────────────────────────┐
│            RAW               │
│     Dados originais          │
│     Google Drive              │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│         PROCESSING            │
│                              │
│ • Limpeza                    │
│ • Padronização               │
│ • Validação                  │
│ • Transformação              │
│ • Seleção de variáveis       │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│          PROCESSED            │
│                              │
│ Dados estruturados e         │
│ consistentes                 │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│         SEGMENTED             │
│                              │
│ Dados preparados para        │
│ análises específicas         │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│   ANÁLISE / MODELAGEM / BI    │
└──────────────────────────────┘
```

# Rastreabilidade

Cada conjunto de dados processado deve manter relação com sua respectiva fonte original em `data/raw/`.

A transformação dos dados deve ser realizada por meio dos scripts e notebooks disponíveis no projeto, permitindo a **reprodutibilidade do pipeline**.

| Camada    | Localização       | Finalidade                                 |
| --------- | ----------------- | ------------------------------------------ |
| Raw       | `data/raw/`       | Dados originais                            |
| Processed | `data/processed/` | Dados limpos e padronizados                |
| Segmented | `data/segmented/` | Dados preparados para análises específicas |

## Versionamento

Os arquivos de grande volume não são versionados diretamente no GitHub.

Os dados são armazenados externamente e referenciados neste documento por meio dos respectivos links do Google Drive.

---

## Links dos dados processados

| Dataset                              | Google Drive                      |
| ------------------------------------ | --------------------------------- |
| EMBRAPA — Dados Agropecuários        | [Acessar dados](COLE_O_LINK_AQUI) |
| IBGE — Bioma Predominante            | [Acessar dados](COLE_O_LINK_AQUI) |
| IBGE — Malha Municipal               | [Acessar dados](COLE_O_LINK_AQUI) |
| IBGE — PAM Soja e Cana               | [Acessar dados](COLE_O_LINK_AQUI) |
| INMET — Dados Climáticos             | [Acessar dados](COLE_O_LINK_AQUI) |
| MapBiomas — Cobertura e Uso da Terra | [Acessar dados](COLE_O_LINK_AQUI) |
| MapBiomas — Solo                     | [Acessar dados](COLE_O_LINK_AQUI) |
| SEEG — Emissões GEE                  | [Acessar dados](COLE_O_LINK_AQUI) |
