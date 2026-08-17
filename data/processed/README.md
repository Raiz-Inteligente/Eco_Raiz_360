# Processed Data

Esta pasta contém as bases de dados após as etapas de **limpeza, padronização, validação, transformação e integração** realizadas no projeto **Eco_Raiz_360**.

Os dados processados são derivados das fontes originais armazenadas em `data/raw/` e representam a **camada intermediária do pipeline de dados**, na qual diferentes fontes são preparadas e integradas para posterior análise.

---

# Objetivo

A camada `processed` tem como objetivo transformar os dados brutos em conjuntos de dados **estruturados, consistentes, padronizados e integrados**, preparados para as etapas de segmentação, análise e construção dos indicadores do projeto.

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
* Cruzamento entre diferentes fontes;
* Integração de bases;
* Preparação dos dados para análises e indicadores.

---

# Bases Processadas

## 1. EMBRAPA — Dados Agropecuários

**Pasta:** `embrapa_dados_agropecuarios`

**Descrição:**

Dados agropecuários utilizados para caracterização das atividades produtivas e análise do setor agropecuário.

### Principais tratamentos

* Padronização das variáveis agropecuárias;
* Tratamento de valores ausentes;
* Padronização de unidades;
* Padronização de municípios e códigos geográficos;
* Seleção das variáveis relevantes;
* Preparação para integração com outras fontes.

---

## 2. INMET — Dados Históricos Climáticos

**Pasta:** `inmet_dados_historicos_climaticos`

**Descrição:**

Dados meteorológicos históricos utilizados para caracterização das condições climáticas dos territórios analisados.

### Principais tratamentos

* Padronização de datas e horários;
* Tratamento de registros inconsistentes;
* Padronização das variáveis meteorológicas;
* Tratamento de valores ausentes;
* Organização por estação e período;
* Padronização das unidades de medida;
* Preparação para integração com dados territoriais e agropecuários.

---

## 3. MapBiomas — Cobertura e Uso da Terra

**Pasta:** `mapbiomas_cobertura_uso_terra`

**Descrição:**

Dados utilizados para caracterizar a cobertura e o uso da terra nos municípios analisados.

### Principais tratamentos

* Seleção das classes relevantes;
* Padronização dos códigos territoriais;
* Organização das informações temporais;
* Tratamento de valores ausentes ou inconsistentes;
* Padronização das categorias;
* Preparação para análises territoriais e ambientais.

---

## 4. SEEG — Emissões de Gases de Efeito Estufa

**Pasta:** `seeg_emissoes_gee`

**Descrição:**

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

# Integrações Realizadas

Durante o processamento, algumas fontes foram **integradas entre si**, utilizando principalmente identificadores geográficos e informações territoriais.

Essas integrações permitem consolidar informações provenientes de diferentes fontes e criar uma estrutura mais adequada para as análises do projeto.

---

## 5. IBGE — Malha Municipal + Bioma Predominante por Município

### Fontes utilizadas

* **IBGE — Malha Municipal**
* **IBGE — Bioma Predominante por Município**

### Descrição

As informações da **Malha Municipal do IBGE** foram integradas aos dados de **bioma predominante por município**, utilizando os identificadores geográficos municipais como referência.

Essa integração permite associar cada município às suas respectivas informações territoriais e ambientais.

### Principais tratamentos

* Padronização dos códigos dos municípios;
* Padronização dos nomes dos municípios;
* Validação dos identificadores geográficos;
* Verificação da correspondência entre municípios;
* Tratamento de duplicidades;
* Tratamento de valores ausentes;
* Integração das informações territoriais e ambientais;
* Validação da consistência da base resultante.

### Resultado

A integração gera uma base municipal contendo informações territoriais associadas ao **bioma predominante de cada município**, servindo como referência para o relacionamento com outras bases do projeto.

---

## 6. IBGE PAM + MapBiomas Solo

### Fontes utilizadas

* **IBGE — Produção Agrícola Municipal (PAM)**
* **MapBiomas — Solo**

### Descrição

Os dados da **PAM**, principalmente relacionados à produção de soja e cana-de-açúcar, foram integrados às informações de **solo do MapBiomas** durante a etapa de processamento.

Essa integração permite relacionar a produção agrícola às características ambientais e territoriais dos municípios analisados.

### Principais tratamentos

* Seleção das culturas relevantes;
* Padronização dos municípios;
* Padronização dos códigos IBGE;
* Padronização das unidades de produção;
* Tratamento de valores ausentes;
* Padronização dos períodos de referência;
* Organização das variáveis de produção;
* Integração das informações agrícolas e de solo;
* Validação das chaves utilizadas no cruzamento.

### Resultado

A base resultante permite análises relacionadas à **produção agrícola e às características do solo**, servindo como uma das bases de apoio para os indicadores do projeto.

---

# Resumo das Bases e Integrações

| Fonte / Integração                   | Tipo            | Finalidade                             |
| ------------------------------------ | --------------- | -------------------------------------- |
| EMBRAPA — Dados Agropecuários        | Base processada | Caracterização agropecuária            |
| IBGE Malha + Bioma                   | **Integração**  | Referência territorial e ambiental     |
| IBGE PAM + MapBiomas Solo            | **Integração**  | Relação entre produção agrícola e solo |
| INMET — Dados Climáticos             | Base processada | Caracterização climática               |
| MapBiomas — Cobertura e Uso da Terra | Base processada | Caracterização territorial             |
| SEEG — Emissões GEE                  | Base processada | Análise de emissões                    |

---

# Estrutura do Pipeline

```text
┌────────────────────────────────────┐
│                RAW                 │
│                                    │
│       Dados originais das fontes   │
│                                    │
│ • EMBRAPA                           │
│ • IBGE                              │
│ • INMET                             │
│ • MapBiomas                         │
│ • SEEG                              │
└──────────────────┬─────────────────┘
                   │
                   ▼
┌────────────────────────────────────┐
│             PROCESSING              │
│                                    │
│ • Limpeza                           │
│ • Padronização                      │
│ • Validação                         │
│ • Transformação                     │
│ • Seleção de variáveis              │
│ • Cruzamento de bases               │
│ • Integração                        │
└──────────────────┬─────────────────┘
                   │
          ┌────────┴─────────┐
          ▼                  ▼
┌──────────────────┐ ┌──────────────────────┐
│ BASES PROCESSADAS│ │ BASES INTEGRADAS     │
│                  │ │                      │
│ EMBRAPA          │ │ IBGE Malha + Bioma   │
│ INMET            │ │ PAM + MapBiomas Solo │
│ MapBiomas        │ │                      │
│ SEEG             │ │                      │
└────────┬─────────┘ └──────────┬───────────┘
         │                      │
         └──────────┬───────────┘
                    ▼
┌────────────────────────────────────┐
│             PROCESSED               │
│                                    │
│ Dados estruturados,                │
│ padronizados e integrados          │
└──────────────────┬─────────────────┘
                   │
                   ▼
┌────────────────────────────────────┐
│             SEGMENTED               │
│                                    │
│ Dados preparados para análises     │
│ específicas                        │
└──────────────────┬─────────────────┘
                   │
                   ▼
┌────────────────────────────────────┐
│           ANÁLISE / BI              │
│                                    │
│ Indicadores • DAX • Power BI       │
└────────────────────────────────────┘
```

---

# Rastreabilidade

Cada conjunto de dados processado mantém relação com sua respectiva **fonte original em `data/raw/`**.

Quando diferentes fontes são integradas, a documentação identifica quais bases participaram da construção do conjunto de dados resultante.

As transformações são realizadas por meio dos **scripts e notebooks versionados no projeto**, permitindo maior rastreabilidade e reprodutibilidade do pipeline.

| Camada    | Localização       | Finalidade                                             |
| --------- | ----------------- | ------------------------------------------------------ |
| Raw       | `data/raw/`       | Dados originais                                        |
| Processed | `data/processed/` | Dados limpos, padronizados, transformados e integrados |
| Segmented | `data/segmented/` | Dados preparados para análises específicas             |

---

# Versionamento

Os arquivos de grande volume não são versionados diretamente no GitHub.

Os dados processados são armazenados externamente e referenciados por meio dos respectivos links do Google Drive.

Os **scripts e notebooks responsáveis pelo processamento** permanecem versionados no GitHub para garantir a rastreabilidade das transformações realizadas.

---

# Links dos Dados Processados

| Dataset / Integração                 | Google Drive                                                                                             |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------- |
| EMBRAPA — Dados Agropecuários        | [Acessar dados](https://drive.google.com/drive/folders/1f6Rl11YcJGDn6h2oMTQBsXi6FJuUZ0VU?usp=drive_link) |
| IBGE — Malha Municipal + Bioma       | [Acessar dados](https://drive.google.com/drive/folders/1W_uK1lecurGJgaSM9FEKwh-9ug8cpFce?usp=drive_link) |
| IBGE PAM + MapBiomas Solo            | [Acessar dados](https://drive.google.com/drive/folders/1JjIRkZNkpsCLVmOv1zaH-b3F4jDaqcA9?usp=drive_link) |
| INMET — Dados Climáticos             | [Acessar dados](https://drive.google.com/drive/folders/19SZrmA9dEzl6Zi3RH_1rFz1nSCTyACjG?usp=drive_link) |
| MapBiomas — Cobertura e Uso da Terra | [Acessar dados](https://drive.google.com/drive/folders/1kJ8XSA_Lbwf8j1040ppRyZAt6mc5cEr3?usp=drive_link) |
| SEEG — Emissões de GEE               | [Acessar dados](https://drive.google.com/drive/folders/1aG6PNyGRIFVlrDvo-jAF64y_7rwqx6q0?usp=sharing)    |

---

## Observação

A camada `processed` não representa apenas uma coleção de arquivos individualmente tratados. Ela também contém **resultados de integrações entre diferentes fontes de dados**.

No projeto **Eco_Raiz_360**, destacam-se duas integrações realizadas durante o processamento:

1. **IBGE Malha Municipal + IBGE Bioma Predominante por Município**
2. **IBGE PAM + MapBiomas Solo**

Essas integrações permitem construir uma base mais consistente para relacionar **território, bioma, produção agrícola e características ambientais**, servindo de suporte às etapas posteriores de análise, indicadores e visualização no Power BI.


