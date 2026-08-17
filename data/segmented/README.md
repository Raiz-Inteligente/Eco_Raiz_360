# Segmented Data

Esta pasta contém os dados **segmentados a partir das bases disponíveis em `data/processed/`**, organizados de acordo com os diferentes recortes analíticos necessários para o projeto **Eco_Raiz_360**.

A camada `segmented` representa uma etapa intermediária entre os dados processados e a análise. Seu objetivo é organizar os dados por **dimensões, territórios, períodos, culturas e categorias de interesse**, facilitando a exploração dos dados e a construção dos indicadores utilizados no projeto.

> **Importante:** a segmentação não substitui o processamento dos dados. As bases utilizadas nesta camada têm como origem os dados já tratados, padronizados e integrados em `data/processed/`.

---

# Objetivo

A camada `segmented` tem como objetivo criar **recortes específicos dos dados processados**, permitindo trabalhar separadamente com diferentes dimensões do projeto.

As segmentações podem considerar:

* Município;
* Estado;
* Região;
* Bioma;
* Cultura agrícola;
* Ano;
* Uso e cobertura da terra;
* Características do solo;
* Variáveis climáticas;
* Setores de emissão;
* Categorias de emissão;
* Gases de efeito estufa;
* Indicadores agropecuários;
* Indicadores ambientais.

A segmentação permite organizar os dados de acordo com as necessidades das análises posteriores, mantendo a rastreabilidade das fontes utilizadas.

---

# Relação com o Pipeline

```text
┌──────────────────────────────┐
│             RAW              │
│                              │
│      Dados originais         │
│      das diferentes fontes   │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│          PROCESSED           │
│                              │
│ • Limpeza                    │
│ • Padronização               │
│ • Validação                  │
│ • Transformação              │
│ • Integração                 │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│          SEGMENTED           │
│                              │
│ • Recortes territoriais      │
│ • Recortes por bioma         │
│ • Recortes agropecuários     │
│ • Recortes de solo           │
│ • Recortes de cobertura      │
│ • Recortes climáticos        │
│ • Recortes de emissões       │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│            ANÁLISE           │
│                              │
│ • Análise exploratória       │
│ • Comparações                │
│ • Identificação de padrões   │
│ • Construção de indicadores  │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│          POWER BI            │
│                              │
│ • KPIs                       │
│ • DAX                        │
│ • Dashboards                 │
└──────────────────────────────┘
```

---

# Fontes Utilizadas

Os dados desta camada são provenientes das bases processadas em `data/processed/`.

As principais fontes são:

* EMBRAPA — Dados Agropecuários;
* IBGE — Malha Municipal;
* IBGE — Bioma Predominante por Município;
* IBGE — Produção Agrícola Municipal (PAM);
* INMET — Dados Históricos Climáticos;
* MapBiomas — Cobertura e Uso da Terra;
* MapBiomas — Solo;
* SEEG — Emissões de Gases de Efeito Estufa.

Algumas dessas fontes foram **integradas durante a etapa de processamento** antes de serem utilizadas na segmentação.

---

# Integrações Realizadas no Processamento

Duas integrações principais são consideradas na estrutura dos dados segmentados.

## 1. IBGE — Malha Municipal + Bioma

As informações da **Malha Municipal do IBGE** foram integradas aos dados de **Bioma Predominante por Município**.

```text
IBGE — Malha Municipal
          +
IBGE — Bioma Predominante
          │
          ▼
Integração Territorial
          │
          ▼
   data/processed/
          │
          ▼
     Segmentação
```

### Objetivo

Associar cada município às suas respectivas informações territoriais e ao bioma predominante.

### Utilização

Essa integração permite segmentar os municípios por:

* Município;
* UF;
* Região;
* Bioma.

Também possibilita o relacionamento com outras bases ambientais, agropecuárias, climáticas e de emissões.

---

## 2. IBGE PAM + MapBiomas Solo

Os dados da **Produção Agrícola Municipal (PAM)** foram integrados às informações de **solo do MapBiomas** durante a etapa de processamento.

```text
IBGE — PAM
    +
MapBiomas — Solo
    │
    ▼
Integração Agroambiental
    │
    ▼
 data/processed/
    │
    ▼
  Segmentação
```

### Objetivo

Relacionar informações de produção agrícola com características do solo dos municípios analisados.

### Utilização

Essa integração permite segmentar os dados por:

* Município;
* UF;
* Região;
* Cultura;
* Ano;
* Características do solo;
* Produção;
* Área plantada;
* Área colhida;
* Produtividade.

---

# Tipos de Segmentação

## 1. Segmentação Territorial

A segmentação territorial organiza os dados de acordo com a localização geográfica.

### Níveis

```text
Brasil
   │
   ├── Região
   │     │
   │     └── Estado
   │            │
   │            └── Município
   │
   └── Bioma
```

### Principais dimensões

* Região;
* Unidade Federativa (UF);
* Município;
* Código IBGE;
* Bioma.

Essa segmentação permite realizar análises em diferentes níveis territoriais.

---

# 2. Segmentação por Bioma

A segmentação por bioma utiliza a base resultante da integração entre:

**IBGE — Malha Municipal + IBGE — Bioma Predominante por Município**

### Dimensões

* Município;
* Código IBGE;
* UF;
* Região;
* Bioma.

### Objetivo

Organizar os municípios de acordo com o bioma predominante e permitir posteriormente análises relacionadas a:

* Produção agrícola;
* Cobertura e uso da terra;
* Solo;
* Clima;
* Emissões;
* Indicadores ambientais.

---

# 3. Segmentação Agropecuária

A segmentação agropecuária utiliza principalmente os dados provenientes da integração:

**IBGE PAM + MapBiomas Solo**

### Principais dimensões

* Município;
* UF;
* Região;
* Ano;
* Cultura;
* Área plantada;
* Área colhida;
* Produção;
* Produtividade;
* Características do solo.

### Culturas de interesse

Entre as principais culturas consideradas no projeto estão:

* Soja;
* Cana-de-açúcar.

A segmentação permite organizar os dados por cultura e período, facilitando as análises posteriores.

---

# 4. Segmentação por Solo

A segmentação por solo utiliza as informações do **MapBiomas Solo**, integradas aos dados da PAM durante o processamento.

### Principais dimensões

* Município;
* UF;
* Região;
* Cultura;
* Ano;
* Classe ou característica do solo;
* Área;
* Produção.

### Objetivo

Permitir análises relacionadas à relação entre **produção agrícola e características ambientais do território**.

---

# 5. Segmentação por Uso e Cobertura da Terra

Utiliza os dados processados do **MapBiomas — Cobertura e Uso da Terra**.

### Principais categorias

* Agricultura;
* Pastagem;
* Soja;
* Cobertura natural;
* Outras classes relevantes disponíveis na base.

### Dimensões

* Município;
* UF;
* Bioma;
* Ano;
* Classe de cobertura;
* Área em hectares.

Essa segmentação permite organizar os dados territoriais conforme o tipo de cobertura ou uso da terra.

---

# 6. Segmentação Climática

Utiliza os dados processados provenientes do **INMET**.

### Principais dimensões

* Estação meteorológica;
* Município;
* UF;
* Ano;
* Mês;
* Período.

### Principais variáveis

* Temperatura;
* Precipitação;
* Umidade;
* Outras variáveis meteorológicas disponíveis.

A segmentação temporal permite organizar os dados climáticos por diferentes períodos de referência.

---

# 7. Segmentação de Emissões

Utiliza os dados processados provenientes do **SEEG — Emissões de Gases de Efeito Estufa**.

### Principais dimensões

* Município;
* UF;
* Região;
* Ano;
* Setor;
* Categoria;
* Gás.

### Principais medidas

* Emissões;
* Remoções;
* Emissões líquidas, quando aplicável.

Essa segmentação permite organizar as emissões de acordo com diferentes níveis territoriais, temporais e setoriais.

---

# 8. Segmentação Temporal

A dimensão temporal é utilizada nas bases que possuem informações históricas.

Os dados podem ser segmentados por:

```text
Ano
 │
 ├── Mês
 │
 └── Período
```

Essa segmentação permite organizar os dados para análises posteriores de evolução e comparação entre diferentes períodos.

---

# Estrutura da Pasta

A organização da camada `segmented` pode seguir a seguinte estrutura:

```text
data/
└── segmented/
    │
    ├── README.md
    │
    ├── territorial/
    │
    ├── bioma/
    │
    ├── agropecuaria/
    │
    ├── solo/
    │
    ├── cobertura_terra/
    │
    ├── clima/
    │
    └── emissoes/
```

A estrutura pode ser adaptada de acordo com os arquivos efetivamente produzidos durante o projeto.

---

# Critérios de Segmentação

Cada conjunto segmentado deve possuir um critério claramente definido.

| Segmentação              | Critério principal                |
| ------------------------ | --------------------------------- |
| Territorial              | Município, UF e região            |
| Bioma                    | Bioma predominante                |
| Agropecuária             | Cultura, município e período      |
| Solo                     | Classe ou característica do solo  |
| Cobertura e Uso da Terra | Classe de cobertura e uso         |
| Climática                | Estação, município e período      |
| Emissões                 | Município, setor, categoria e ano |
| Temporal                 | Ano, mês ou período               |

---

# Regras da Camada `Segmented`

Para manter a organização e a consistência do projeto, os dados segmentados devem seguir as seguintes regras:

* Utilizar somente dados provenientes de `data/processed/`;
* Não modificar os dados originais de `data/raw/`;
* Não repetir etapas de limpeza já realizadas no processamento;
* Manter a rastreabilidade da base de origem;
* Utilizar identificadores geográficos padronizados;
* Utilizar nomes de arquivos em `snake_case`;
* Manter nomes de colunas em letras minúsculas;
* Utilizar `_` para separar palavras;
* Evitar duplicação desnecessária de dados;
* Documentar o critério utilizado para cada segmentação;
* Manter a granularidade adequada para cada finalidade analítica.

---

# Convenção de Nomenclatura

Os arquivos devem utilizar o padrão:

```text
snake_case
```

### Exemplos

```text
municipios_por_bioma.csv
municipios_por_uf.csv
producao_soja.csv
producao_cana.csv
producao_por_tipo_solo.csv
cobertura_uso_terra_municipio.csv
dados_climaticos_municipio.csv
emissoes_por_municipio.csv
```

Evitar:

```text
DadosSoja.csv
ProducaoSojaFinal.csv
MapaBiomasDados.csv
```

Preferir:

```text
producao_soja.csv
mapbiomas_cobertura_terra.csv
```

---

# Rastreabilidade

Cada arquivo ou conjunto de dados segmentado deve permitir identificar sua origem.

### Exemplo — Territorial + Bioma

```text
IBGE — Malha Municipal
          +
IBGE — Bioma
          │
          ▼
data/processed/
          │
          ▼
Segmentação
          │
          ▼
municipios_por_bioma.csv
```

### Exemplo — Agropecuária + Solo

```text
IBGE — PAM
    +
MapBiomas — Solo
    │
    ▼
data/processed/
    │
    ▼
Segmentação
    │
    ▼
producao_por_tipo_solo.csv
```

Dessa forma, é possível identificar a **fonte dos dados, as integrações realizadas e o recorte utilizado na segmentação**.

---

# Relação com a Análise

A camada `segmented` prepara os dados para a etapa seguinte do projeto:

```text
PROCESSED
    │
    ▼
SEGMENTED
    │
    ▼
ANÁLISE / EDA
    │
    ▼
INDICADORES
    │
    ▼
POWER BI
```

A camada `segmented` é responsável pela **organização e criação dos recortes dos dados**.

A etapa de análise será responsável por **explorar esses recortes, identificar padrões, realizar comparações e gerar informações para apoiar os indicadores do Eco_Raiz_360**.

---

# Links das Bases Segmentadas

As bases segmentadas são disponibilizadas externamente por meio do **Google Drive**. Os arquivos foram organizados de acordo com os principais recortes utilizados no projeto **Eco_Raiz_360**.

Algumas bases segmentadas são resultado da **integração de diferentes fontes durante a etapa de processamento**. Nesses casos, a descrição identifica as fontes que compõem o conjunto de dados.

| Segmentação                  | Descrição                                                                                                                 | Google Drive                                                                                           |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| **Territorial + Bioma**      | Dados municipais resultantes da integração entre **IBGE — Malha Municipal** e **IBGE — Bioma Predominante por Município** | [Acessar dados](https://drive.google.com/file/d/1VHZEaH_21DzEh1fHfd1wbJe7mKq3C85o/view?usp=drive_link)                                                                      |
| **Agropecuária + Solo**      | Dados resultantes da integração entre **IBGE — PAM** e **MapBiomas — Solo**, segmentados por cultura, município e período | [Acessar dados](https://drive.google.com/file/d/1moTqxYt3yYA_zSs30oxG0XshMccElOo5/view?usp=drive_link)                                                                      |
| **Cobertura e Uso da Terra** | Dados do **MapBiomas**, segmentados por classe de cobertura e uso da terra                                                | [Acessar dados](https://drive.google.com/file/d/14tCmbejMM2vF-NHH7T1uppEAB3AShkMq/view?usp=drive_link) |
| **Climática**                | Dados do **INMET**, segmentados por estação, município e período                                                          | [Acessar dados](https://drive.google.com/file/d/168INo4hlodNTdnNwGLmvonZMqwRksyLp/view?usp=drive_link) |
| **Emissões**                 | Dados do **SEEG**, segmentados por município, setor, categoria e ano                                                      | [Acessar dados](https://drive.google.com/file/d/19_2W99ufqyDxhsQOZzpz4enkd5_TmIVN/view?usp=sharing)    |

---

# Organização dos Dados Segmentados

Os dados estão organizados de acordo com suas respectivas dimensões analíticas:

```text
data/segmented/

├── territorial/
├── bioma/
├── agropecuaria/
├── solo/
├── cobertura_terra/
├── clima/
└── emissoes/
```

Cada conjunto de dados possui como origem uma ou mais bases disponíveis em `data/processed/`, mantendo a rastreabilidade entre:

```text
Fonte
  ↓
Processamento
  ↓
Integração
  ↓
Segmentação
  ↓
Análise
```

---

# Resultado Esperado

Ao final da segmentação, os dados devem estar organizados de forma que seja possível trabalhar separadamente com diferentes dimensões do projeto:

**Território → Bioma → Produção → Solo → Cobertura da Terra → Clima → Emissões**

Essa organização facilita a etapa de análise e permite construir uma visão integrada dos municípios analisados no **Eco_Raiz_360**.

A camada `segmented` funciona, portanto, como uma **ponte entre os dados processados e a etapa de análise**, garantindo que os dados estejam organizados de acordo com os recortes necessários para responder às perguntas analíticas e apoiar a construção dos indicadores do projeto.
