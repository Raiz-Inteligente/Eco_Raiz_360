# Segmented Data & Exploratory Analysis

Esta pasta contém os resultados da **Análise Exploratória de Dados (EDA)** e das etapas de **segmentação** realizadas a partir dos datasets processados do projeto **Eco_Raiz_360**.

A camada `segmented` representa a etapa analítica do pipeline, na qual os dados processados são explorados individualmente, avaliados quanto à qualidade e utilizados para identificação de padrões, características e possíveis critérios de segmentação.

A Análise Exploratória será realizada para **todos os datasets utilizados no projeto**, antes das etapas de integração e construção dos indicadores.

---

## Objetivo

A camada `segmented` tem como principais objetivos:

* Explorar individualmente os datasets processados;
* Avaliar a qualidade e consistência dos dados;
* Identificar padrões, tendências e comportamentos;
* Analisar distribuições e variabilidade;
* Identificar valores ausentes, duplicidades e possíveis outliers;
* Avaliar relações entre variáveis;
* Realizar análises temporais e territoriais quando aplicável;
* Identificar variáveis relevantes para o projeto;
* Definir critérios de segmentação a partir dos resultados encontrados;
* Preparar os dados para integração e análises posteriores.

---

# Datasets Analisados

A Análise Exploratória será realizada para os **8 datasets** utilizados no projeto:

| # | Dataset                                   | Diretório                           |
| - | ----------------------------------------- | ----------------------------------- |
| 1 | EMBRAPA — Dados Agropecuários             | `embrapa_dados_agropecuarios`       |
| 2 | IBGE — Bioma Predominante por Município   | `ibge_bioma_predominante_municipio` |
| 3 | IBGE — Malha Municipal                    | `ibge_malha_municipal`              |
| 4 | IBGE — PAM Soja e Cana                    | `ibge_pam_soja_cana_municipios`     |
| 5 | INMET — Dados Históricos Climáticos       | `inmet_dados_historicos_climaticos` |
| 6 | MapBiomas — Cobertura e Uso da Terra      | `mapbiomas_cobertura_uso_terra`     |
| 7 | MapBiomas — Solo                          | `mapbiomas_solo`                    |
| 8 | SEEG — Emissões de Gases de Efeito Estufa | `seeg_emissoes_gee`                 |

---

# Análise Exploratória de Dados — EDA

Cada dataset será analisado individualmente para compreender sua estrutura, qualidade, características e potencial de utilização nas análises do projeto.

## Estrutura dos dados

Serão avaliados:

* Quantidade de registros;
* Quantidade de variáveis;
* Nomes das colunas;
* Tipos de dados;
* Identificadores;
* Granularidade dos registros;
* Períodos disponíveis;
* Cobertura territorial.

## Qualidade dos dados

Serão verificadas:

* Valores ausentes;
* Registros duplicados;
* Valores inconsistentes;
* Valores inválidos;
* Formatos inadequados;
* Possíveis erros de preenchimento;
* Consistência dos identificadores.

## Análise estatística

Quando aplicável:

* Média;
* Mediana;
* Mínimo e máximo;
* Quartis;
* Desvio padrão;
* Distribuição das variáveis;
* Frequência das categorias.

## Distribuição e comportamento

Serão utilizadas visualizações para identificar:

* Distribuições;
* Outliers;
* Concentrações;
* Variações;
* Tendências;
* Diferenças entre grupos.

## Análise temporal

Para datasets que possuem dimensão temporal, serão avaliados:

* Evolução ao longo dos anos;
* Tendências;
* Variações;
* Comportamentos sazonais, quando aplicável;
* Mudanças ao longo do período analisado.

## Análise territorial

Quando aplicável, serão analisados:

* Municípios;
* Estados;
* Regiões;
* Biomas;
* Distribuição territorial;
* Concentração de atividades e indicadores.

## Relações entre variáveis

Quando aplicável, serão investigadas:

* Correlações;
* Relações entre variáveis;
* Diferenças entre grupos;
* Relações temporais;
* Relações territoriais;
* Possíveis relações entre indicadores ambientais e agropecuários.

---

# Segmentação

A segmentação será realizada com base nos padrões identificados durante a Análise Exploratória.

Os critérios poderão considerar diferentes dimensões, como:

* Município;
* Estado;
* Região;
* Bioma;
* Produção agropecuária;
* Cultura agrícola;
* Período;
* Cobertura e uso da terra;
* Características climáticas;
* Características do solo;
* Níveis de emissão;
* Indicadores ambientais;
* Indicadores agropecuários.

Os critérios definitivos serão estabelecidos após a conclusão da análise exploratória dos datasets.

---

# Organização

A estrutura desta camada será organizada de acordo com o desenvolvimento das análises:

```text
segmented/
│
├── README.md
│
├── exploratory_analysis/
│   ├── embrapa_dados_agropecuarios/
│   ├── ibge_bioma_predominante_municipio/
│   ├── ibge_malha_municipal/
│   ├── ibge_pam_soja_cana_municipios/
│   ├── inmet_dados_historicos_climaticos/
│   ├── mapbiomas_cobertura_uso_terra/
│   ├── mapbiomas_solo/
│   └── seeg_emissoes_gee/
│
└── segmentation/
```

Cada análise poderá conter:

```text
dataset/
├── notebooks/
├── outputs/
└── README.md
```

---

# Fluxo do Projeto

```text
                 RAW
                  │
                  ▼
        ┌───────────────────┐
        │     PROCESSED     │
        │                   │
        │ Limpeza           │
        │ Padronização      │
        │ Validação         │
        │ Transformação     │
        └─────────┬─────────┘
                  │
                  ▼
        ┌───────────────────┐
        │     SEGMENTED     │
        │                   │
        │ EDA dos 8 datasets│
        │        +          │
        │    Segmentação    │
        └─────────┬─────────┘
                  │
                  ▼
        ┌───────────────────┐
        │     INTEGRAÇÃO    │
        │    E ANÁLISES     │
        └─────────┬─────────┘
                  │
                  ▼
        ┌───────────────────┐
        │    INDICADORES    │
        │        +          │
        │     DASHBOARD     │
        └───────────────────┘
```

---

# Rastreabilidade

Os datasets utilizados nesta camada devem ter como origem os dados disponíveis em:

```text
data/processed/
```

O fluxo de transformação deve permitir rastrear:

```text
RAW
 ↓
PROCESSING
 ↓
PROCESSED
 ↓
EDA
 ↓
SEGMENTAÇÃO
 ↓
INTEGRAÇÃO
 ↓
INDICADORES / DASHBOARD
```

Os notebooks, scripts e resultados utilizados nas análises devem ser mantidos organizados para garantir **reprodutibilidade, transparência e rastreabilidade**.

---

# Resultados Esperados

A Análise Exploratória dos oito datasets deverá permitir:

* Compreender as características de cada fonte;
* Avaliar a qualidade dos dados;
* Identificar inconsistências;
* Identificar padrões e tendências;
* Identificar variáveis relevantes;
* Identificar relações entre os datasets;
* Definir critérios de segmentação;
* Apoiar a integração das diferentes fontes;
* Subsidiar a construção de indicadores;
* Apoiar o desenvolvimento dos dashboards do projeto.

---

## Status

**Camada:** Segmented
**Escopo:** Análise Exploratória dos 8 datasets e Segmentação
**Entrada:** `data/processed/`
**Saída:** Resultados exploratórios, dados segmentados e informações para integração e construção de indicadores.

---

## Datasets

1. EMBRAPA — Dados Agropecuários
2. IBGE — Bioma Predominante por Município
3. IBGE — Malha Municipal
4. IBGE — PAM Soja e Cana
5. INMET — Dados Históricos Climáticos
6. MapBiomas — Cobertura e Uso da Terra
7. MapBiomas — Solo
8. SEEG — Emissões de Gases de Efeito Estufa
