# SQL — Eco360 | Raiz Inteligente

Esta pasta contém a documentação e os scripts SQL utilizados na **estruturação do banco de dados relacional do projeto Eco360 — Raiz Inteligente**.

A camada SQL foi desenvolvida em **MySQL** para armazenar os dados previamente tratados e modelados, organizando as informações em uma dimensão municipal e tabelas fato.

O SQL é responsável principalmente pela **estruturação do banco, definição das tabelas e integridade dos relacionamentos**.

A carga dos dados no MySQL é realizada por meio de um processo **ETL desenvolvido em Python**, enquanto a camada de análise e visualização é realizada posteriormente no **Power BI**.

---

# Objetivo

A camada SQL tem como objetivos:

* estruturar o banco de dados relacional;
* organizar os dados em dimensão e tabelas fato;
* reduzir redundâncias;
* estabelecer chaves primárias e estrangeiras;
* garantir integridade referencial;
* centralizar a identificação geográfica dos municípios;
* disponibilizar os dados estruturados para o Power BI.

O banco utilizado no projeto é:

```text
eco_360
```

---

# Arquitetura da Solução

O fluxo geral do projeto é:

```text
Fontes de Dados
      ↓
Tratamento e Padronização
      ↓
CSV Processados
      ↓
Modelagem Relacional
      ↓
Python + Pandas
      ↓
ETL / Carga
      ↓
MySQL — eco_360
      ↓
Power BI
      ↓
DAX + Análises + Dashboards
```

### Responsabilidade de cada tecnologia

| Tecnologia          | Responsabilidade                         |
| ------------------- | ---------------------------------------- |
| **Python / Pandas** | Tratamento, preparação e carga dos dados |
| **SQL / MySQL**     | Estruturação e armazenamento relacional  |
| **Power BI / DAX**  | Análise, indicadores e visualizações     |
| **Git / GitHub**    | Versionamento e documentação             |

---

# Estrutura da Modelagem

O banco foi organizado utilizando uma abordagem dimensional, composta por uma dimensão geográfica e tabelas fato.

```text
                         ┌─────────────────────┐
                         │   dim_municipio     │
                         │─────────────────────│
                         │ PK codigo_ibge      │
                         │ municipio           │
                         │ uf                  │
                         │ regiao              │
                         │ area_km2            │
                         │ latitude            │
                         │ longitude           │
                         └──────────┬──────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              │ 1:N                 │ 1:N                 │ 1:N
              ▼                     ▼                     ▼
    ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
    │   fato_soja     │   │   fato_clima    │   │ fato_cobertura  │
    │─────────────────│   │─────────────────│   │─────────────────│
    │ codigo_ibge FK  │   │ codigo_ibge FK  │   │ codigo_ibge FK  │
    │ ano             │   │ ano             │   │ ano             │
    │ produção        │   │ clima           │   │ cobertura       │
    └─────────────────┘   └─────────────────┘   └─────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ fato_emissao_soja   │
                         │─────────────────────│
                         │ id_emissao PK       │
                         │ codigo_ibge FK      │
                         │ ano                 │
                         │ metodologia        │
                         │ metrica             │
                         │ unidade             │
                         │ tipo_emissao        │
                         │ bioma               │
                         │ emissao_t           │
                         └─────────────────────┘


                         ┌─────────────────────┐
                         │ fato_emissao_estado │
                         │─────────────────────│
                         │ PK uf               │
                         │ estado              │
                         │ regiao              │
                         │ cultura             │
                         │ indicadores         │
                         └─────────────────────┘
```

A `dim_municipio` funciona como referência geográfica para as tabelas fato de granularidade municipal.

A `fato_emissao_estado` permanece separada porque trabalha em **granularidade estadual**.

---

# Justificativas de Engenharia da Modelagem

## 1. Eliminação de Redundâncias

Atributos geográficos estáticos, como:

* `area_km2`;
* `latitude`;
* `longitude`;

não mudam anualmente.

Armazenar essas informações repetidamente em cada registro anual das tabelas fato aumentaria a redundância e poderia gerar inconsistências.

Por isso, esses atributos foram centralizados na `dim_municipio`.

---

## 2. Chave Geográfica

Foi utilizado o:

```text
codigo_ibge
```

como chave principal da dimensão municipal.

O nome do município não é considerado uma chave confiável, pois podem existir municípios com o mesmo nome em diferentes estados.

O `codigo_ibge` fornece uma identificação oficial utilizada para estabelecer os relacionamentos entre as tabelas municipais.

---

## 3. Integridade Referencial

As tabelas fato de granularidade municipal utilizam `codigo_ibge` como chave estrangeira para `dim_municipio`.

O relacionamento segue o padrão:

```text
dim_municipio 1 ───────── N tabela_fato
```

Essa estrutura permite centralizar os atributos geográficos e facilita a integração dos dados no Power BI.

---

# Dicionário de Tabelas

| Tabela                | Tipo     | Granularidade                          | Descrição                                                                    | Chave Primária      |
| --------------------- | -------- | -------------------------------------- | ---------------------------------------------------------------------------- | ------------------- |
| `dim_municipio`       | Dimensão | Município                              | Cadastro consolidado dos municípios com atributos territoriais e coordenadas | `codigo_ibge`       |
| `fato_soja`           | Fato     | Município + Ano                        | Dados agrícolas da soja                                                      | `codigo_ibge + ano` |
| `fato_clima`          | Fato     | Município + Ano                        | Métricas climáticas e indicadores de qualidade                               | `codigo_ibge + ano` |
| `fato_cobertura`      | Fato     | Município + Ano                        | Uso e cobertura da terra                                                     | `codigo_ibge + ano` |
| `fato_emissao_soja`   | Fato     | Município + Ano + dimensões de emissão | Emissões relacionadas à soja                                                 | `id_emissao`        |
| `fato_emissao_estado` | Fato     | UF                                     | Indicadores estaduais de emissões                                            | `uf`                |

---

#  `dim_municipio`

A `dim_municipio` concentra as informações geográficas utilizadas como referência no modelo.

### Principais campos

| Campo         | Descrição                   |
| ------------- | --------------------------- |
| `codigo_ibge` | Código oficial do município |
| `municipio`   | Nome do município           |
| `uf`          | Unidade Federativa          |
| `regiao`      | Região brasileira           |
| `area_km2`    | Área territorial em km²     |
| `latitude`    | Latitude do centróide       |
| `longitude`   | Longitude do centróide      |

### Chave

```text
PK: codigo_ibge
```

A dimensão consolidou os municípios presentes nas diferentes fontes utilizadas no projeto.

As coordenadas geográficas foram incorporadas à dimensão para permitir a utilização dos municípios em análises territoriais e mapas no Power BI.

---

# `fato_soja`

A tabela `fato_soja` contém os dados agrícolas anuais relacionados à produção de soja.

### Granularidade

```text
Município + Ano
```

### Principais indicadores

* área plantada;
* área colhida;
* área não colhida;
* aproveitamento da área;
* quantidade produzida;
* rendimento médio;
* valor da produção;
* carbono do solo;
* disponibilidade do dado de produção.

### Chaves

```text
PK: codigo_ibge + ano
FK: codigo_ibge → dim_municipio.codigo_ibge
```

---

# `fato_clima`

A tabela `fato_clima` contém os indicadores climáticos utilizados no projeto.

### Granularidade

```text
Município + Ano
```

### Principais informações

* precipitação anual;
* temperatura média anual;
* umidade média anual;
* origem dos dados;
* número de estações observadas;
* número de estações utilizadas na interpolação IDW;
* score de qualidade climática;
* qualidade climática geral;
* tipo de representação climática.

### Chaves

```text
PK: codigo_ibge + ano
FK: codigo_ibge → dim_municipio.codigo_ibge
```

### Observação

Os valores nulos relacionados à quantidade de estações não devem ser automaticamente interpretados como ausência de estações.

A documentação do pipeline identificou que os registros podem utilizar diferentes métodos de representação climática, incluindo observação direta e interpolação IDW.

---

# `fato_cobertura`

A tabela `fato_cobertura` contém informações de uso e cobertura da terra.

### Granularidade

```text
Município + Ano
```

### Principais indicadores

* área de agricultura;
* área de soja;
* área de cobertura natural;
* área de pastagem;
* percentual de agricultura;
* percentual de soja;
* percentual de cobertura natural;
* percentual de pastagem;
* biomas presentes;
* quantidade de biomas.

### Chaves

```text
PK: codigo_ibge + ano
FK: codigo_ibge → dim_municipio.codigo_ibge
```

---

# `fato_emissao_soja`

A tabela `fato_emissao_soja` contém os dados municipais de emissões relacionados à soja.

A base original apresentava os anos como colunas. Durante o tratamento dos dados, essa estrutura foi transformada de **formato largo para formato longo**.

### Estrutura original

```text
municipio | uf | 2019 | 2020 | 2021 | 2022 | 2023 | 2024
```

### Estrutura tratada

```text
codigo_ibge | municipio | uf | ano | emissao_t
```

Essa transformação permite trabalhar o ano como uma dimensão do registro, facilitando a integração e utilização dos dados no modelo relacional.

### Granularidade

```text
Município
+ Ano
+ Metodologia
+ Métrica
+ Unidade
+ Tipo de emissão
```

### Principais campos

| Campo          | Descrição                            |
| -------------- | ------------------------------------ |
| `id_emissao`   | Identificador do registro de emissão |
| `codigo_ibge`  | Código do município                  |
| `ano`          | Ano da emissão                       |
| `metodologia`  | Metodologia utilizada                |
| `metrica`      | Métrica utilizada                    |
| `unidade`      | Unidade da emissão                   |
| `tipo_emissao` | Tipo de emissão                      |
| `bioma`        | Bioma relacionado                    |
| `emissao_t`    | Valor da emissão                     |

### Chaves

```text
PK: id_emissao
FK: codigo_ibge → dim_municipio.codigo_ibge
```

---

# `fato_emissao_estado`

A tabela `fato_emissao_estado` apresenta indicadores de emissões em nível estadual.

### Granularidade

```text
UF
```

### Principais informações

* estado;
* região;
* cultura;
* taxa de emissão;
* intervalo de confiança inferior;
* intervalo de confiança superior;
* emissão absoluta;
* intervalo de confiança da emissão;
* área de conversão.

### Chave

```text
PK: uf
```

### Observação

Essa tabela não possui `FOREIGN KEY` para `dim_municipio`, pois sua granularidade é **estadual**, enquanto as demais tabelas fato relacionadas à dimensão trabalham em nível municipal.

---

# Relacionamentos

Os relacionamentos municipais são estabelecidos por meio do `codigo_ibge`.

```text
dim_municipio[codigo_ibge]
        │
        ├── fato_soja[codigo_ibge]
        │
        ├── fato_clima[codigo_ibge]
        │
        ├── fato_cobertura[codigo_ibge]
        │
        └── fato_emissao_soja[codigo_ibge]
```

A tabela `fato_emissao_estado` utiliza `uf`, pois possui granularidade estadual.

---

# Processo de Carga

A carga dos dados no MySQL é realizada por meio de um processo **ETL desenvolvido em Python**, utilizando Pandas.

O SQL não é utilizado como camada principal de carga dos CSVs.

O fluxo de carga é:

```text
CSV Processados
      ↓
Python + Pandas
      ↓
etl_eco360.py
      ↓
MySQL
      ↓
Banco eco_360
```

O processo ETL realiza:

1. leitura dos arquivos CSV tratados;
2. identificação de separadores e encoding;
3. conexão com o MySQL;
4. criação do banco `eco_360`, quando necessário;
5. carregamento da `dim_municipio`;
6. carregamento das tabelas fato;
7. aplicação das chaves necessárias;
8. disponibilização dos dados estruturados para o Power BI.

### Ordem de carregamento

A `dim_municipio` é carregada primeiro porque as tabelas fato municipais possuem relacionamento com ela por meio de `codigo_ibge`.

```text
dim_municipio
      ↓
fato_soja
fato_clima
fato_cobertura
fato_emissao_soja
fato_emissao_estado
```

O script responsável pelo processo de carga está localizado em:

```text
src/etl/etl_eco360.py
```

---

# Consumo dos Dados no Power BI

Após a carga no MySQL, os dados são disponibilizados para o **Power BI**, que concentra a camada analítica e de visualização do projeto.

No Power BI são desenvolvidos:

* medidas DAX;
* indicadores;
* rankings;
* análises territoriais;
* análise de produção;
* análise climática;
* análise de emissões;
* Índice de Oportunidade;
* visualizações e dashboards.

Portanto, a divisão das responsabilidades no projeto é:

```text
Python
↓
Tratamento e carga

MySQL / SQL
↓
Estrutura e armazenamento relacional

Power BI / DAX
↓
Análise e visualização
```

---

# Estrutura dos Arquivos SQL

A camada SQL do repositório está organizada da seguinte forma:

```text
sql/
│
├── README.md
│
└── 01_ddl/
    └── eco360_mysql.sql
```

## `01_ddl/eco360_mysql.sql`

Contém o **DDL (Data Definition Language)** responsável pela criação da estrutura do banco.

O arquivo inclui:

* criação do banco `eco_360`;
* criação da `dim_municipio`;
* criação das tabelas fato;
* definição das chaves primárias;
* definição das chaves estrangeiras;
* definição dos tipos de dados;
* estrutura das tabelas relacionais.

---

# DDL — Estrutura do Banco

O banco é iniciado com:

```sql
CREATE DATABASE IF NOT EXISTS eco_360;
USE eco_360;
```

A estrutura é criada na seguinte ordem:

```text
1. dim_municipio
2. fato_soja
3. fato_clima
4. fato_cobertura
5. fato_emissao_soja
6. fato_emissao_estado
```

A `dim_municipio` é criada primeiro para que as tabelas fato municipais possam utilizar `codigo_ibge` como chave estrangeira.

---

# Qualidade e Rastreabilidade

Durante o processo de preparação e modelagem foram identificados pontos importantes de qualidade dos dados.

Entre eles:

* valores nulos metodológicos na base climática;
* registros com produção ausente;
* diferenças de granularidade entre fontes;
* transformação da base de emissões de formato largo para longo;
* registros sem coordenadas geográficas;
* comportamento praticamente constante da razão entre emissão e produção.

Esses pontos não são tratados automaticamente como erros, pois dependem da metodologia e das características das fontes originais.

A documentação detalhada dessas decisões está disponível em:

```text
docs/qualidade_dados.md
```

---

# Documentação Relacionada

Para compreender o projeto como um todo:

### Pipeline

[`docs/arquitetura_pipeline.md`](../docs/documentacao_pipeline_eco360.pdf)

### ETL

```text
src/etl/etl_eco360.py
```

---

# 🧰 Tecnologias

* **Python**
* **Pandas**
* **SQL**
* **MySQL**
* **Power BI**
* **DAX**
* **Git**
* **GitHub**

---

# 📌 Resumo

A camada SQL do Eco360 foi desenvolvida para estruturar os dados tratados em um modelo relacional organizado em uma dimensão municipal e tabelas fato.

O `codigo_ibge` foi adotado como chave geográfica para integrar as diferentes fontes municipais, enquanto a `fato_emissao_estado` permanece independente devido à sua granularidade estadual.

O processo completo segue:

```text
Fontes de Dados
      ↓
Tratamento e Padronização
      ↓
CSV Processados
      ↓
Modelagem Relacional
      ↓
Python + Pandas
      ↓
ETL
      ↓
MySQL — eco_360
      ↓
Power BI
      ↓
DAX + Análise + Visualização
```

> **SQL estrutura. Python carrega. Power BI analisa.**

---

**Projeto Eco360 — Raiz Inteligente**

*Integração de dados agrícolas, climáticos, ambientais e de emissões para análise territorial e tomada de decisão.*
