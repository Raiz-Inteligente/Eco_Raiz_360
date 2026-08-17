# Análises Exploratórias

Esta pasta contém os **notebooks de Análise Exploratória de Dados (EDA)** desenvolvidos no projeto **Eco_Raiz_360**.

A etapa de análise exploratória tem como objetivo investigar os dados previamente processados e segmentados, identificar padrões, tendências, inconsistências, relações entre variáveis e informações relevantes para a construção dos indicadores e dashboards do projeto.

Os notebooks utilizam como base os dados disponíveis nas camadas:

```text id="4w0m8n"
data/raw/
      ↓
data/processed/
      ↓
data/segmented/
      ↓
notebooks de análise exploratória
      ↓
indicadores e Power BI
```

---

# Objetivo das Análises

As análises exploratórias têm como principais objetivos:

* Compreender a estrutura dos dados;
* Avaliar a distribuição das variáveis;
* Identificar padrões e tendências;
* Comparar municípios, estados e regiões;
* Avaliar a produção agrícola;
* Investigar características do solo;
* Analisar emissões de gases de efeito estufa;
* Explorar variáveis climáticas;
* Identificar possíveis relações entre produção, clima, solo e emissões;
* Detectar valores extremos ou comportamentos atípicos;
* Validar hipóteses levantadas durante o desenvolvimento do projeto;
* Apoiar a definição dos indicadores utilizados no Power BI.

> **Importante:** esta etapa possui caráter exploratório. Os resultados encontrados nos notebooks servem como suporte à análise e à construção dos indicadores, não substituindo as regras e cálculos definidos no modelo final do projeto.

---

# Organização dos Notebooks

Os notebooks seguem uma sequência lógica de exploração das principais fontes utilizadas no projeto.

```text id="0s2y8k"
notebooks/
│
├── 01_exploracao_ibge_pam.ipynb
│
├── 02_exploracao_mapbiomas_solo.ipynb
│
├── 03_analise_exploratoria_soja_seeg.ipynb
│
└── 04_integracao_inmet_clima.ipynb
```

---

# 01 — Exploração IBGE PAM

**Arquivo:**

`notebooks/01_exploracao_ibge_pam.ipynb`

### Objetivo

Explorar os dados da **Produção Agrícola Municipal (PAM)** utilizados no projeto, com foco nas culturas e indicadores agropecuários relevantes.

### Principais análises

* Estrutura da base;
* Quantidade de municípios;
* Distribuição da produção;
* Área plantada;
* Área colhida;
* Produtividade;
* Comparação entre municípios;
* Comparação entre estados;
* Comparação entre períodos;
* Identificação das principais culturas;
* Identificação de valores extremos.

### Perguntas exploradas

* Quais municípios apresentam maior produção?
* Quais estados concentram a produção?
* Como a produção varia ao longo do tempo?
* Quais municípios apresentam maior produtividade?
* Existe concentração territorial da produção?

### Resultado esperado

Identificar os principais padrões de produção agrícola e os recortes relevantes para as análises posteriores do projeto.

---

# 02 — Exploração MapBiomas Solo

**Arquivo:**

`notebooks/02_exploracao_mapbiomas_solo.ipynb`

### Objetivo

Explorar as informações de **solo do MapBiomas** e compreender sua distribuição territorial e sua relação com os municípios analisados.

### Principais análises

* Estrutura da base;
* Distribuição das classes de solo;
* Quantidade de municípios por classe;
* Distribuição territorial;
* Área associada às classes de solo;
* Relação entre solo e produção agrícola;
* Comparação entre diferentes territórios.

### Perguntas exploradas

* Quais classes de solo possuem maior representação?
* Como as características do solo estão distribuídas territorialmente?
* Quais classes estão presentes nos municípios produtores?
* Existe concentração de determinadas características de solo em regiões específicas?

### Resultado esperado

Compreender a distribuição das características de solo e preparar informações para análises relacionadas à **produção agrícola e características ambientais**.

---

# 03 — Análise Exploratória Soja + SEEG

**Arquivo:**

`notebooks/03_analise_exploratoria_soja_seeg.ipynb`

### Objetivo

Investigar possíveis relações entre a **produção de soja** e os **dados de emissões de gases de efeito estufa do SEEG**.

Esta análise busca integrar duas dimensões importantes do projeto:

```text id="b9xj7n"
Produção de Soja
       │
       ├── Município
       ├── Estado
       ├── Ano
       └── Produção
              │
              ▼
        Comparação
              │
              ▼
       Emissões SEEG
       ├── Município
       ├── Setor
       ├── Categoria
       └── Ano
```

### Principais análises

* Produção de soja por município;
* Emissões por município;
* Emissões por setor;
* Emissões por categoria;
* Comparação entre produção e emissões;
* Distribuição territorial;
* Evolução temporal;
* Identificação de municípios com alta produção;
* Identificação de municípios com maiores emissões.

### Perguntas exploradas

* Quais municípios apresentam maior produção de soja?
* Quais municípios apresentam maiores emissões?
* Existe concentração territorial de produção e emissões?
* Como produção e emissões se comportam ao longo do tempo?
* Existem municípios com alta produção e alta emissão?
* Existem municípios com alta produção e menor emissão relativa?

### Resultado esperado

Identificar padrões que possam contribuir para a construção de indicadores relacionados à **produção agrícola, emissões e potencial ambiental**.

> **Observação:** correlação ou associação observada durante a exploração não deve ser interpretada automaticamente como causalidade.

---

# 04 — Integração INMET + Clima

**Arquivo:**

`notebooks/04_integracao_inmet_clima.ipynb`

### Objetivo

Explorar e preparar os dados climáticos provenientes do **INMET**, avaliando sua integração com as demais informações territoriais e agropecuárias utilizadas no projeto.

### Principais análises

* Estrutura dos dados meteorológicos;
* Distribuição das estações;
* Cobertura territorial;
* Período disponível;
* Temperatura;
* Precipitação;
* Umidade;
* Variações temporais;
* Identificação de valores ausentes;
* Identificação de valores extremos;
* Relação entre estação e município.

### Perguntas exploradas

* Quais municípios possuem cobertura de dados climáticos?
* Quais períodos possuem maior disponibilidade de dados?
* Como as variáveis climáticas variam ao longo do tempo?
* Existem diferenças climáticas relevantes entre os territórios?
* Como os dados climáticos podem ser relacionados aos municípios produtores?

### Resultado esperado

Preparar as informações climáticas para análises posteriores envolvendo **clima, território e produção agrícola**.

---

# Metodologia Geral das Análises

Os notebooks seguem uma estrutura exploratória padronizada.

## 1. Importação dos dados

Os dados são carregados a partir das bases processadas ou segmentadas.

```text id="f6byh8"
data/processed/
       +
data/segmented/
       ↓
Notebook EDA
```

## 2. Inspeção inicial

São verificados:

* Número de linhas;
* Número de colunas;
* Tipos de dados;
* Nomes das variáveis;
* Valores ausentes;
* Duplicidades;
* Chaves;
* Granularidade.

## 3. Estatística descritiva

São analisadas medidas como:

* Média;
* Mediana;
* Mínimo;
* Máximo;
* Quartis;
* Desvio padrão.

## 4. Análise de distribuição

São utilizados recursos como:

* Histogramas;
* Boxplots;
* Tabelas de frequência;
* Estatísticas descritivas.

## 5. Análise temporal

Quando disponível:

* Evolução anual;
* Evolução mensal;
* Variação entre períodos;
* Tendências.

## 6. Análise territorial

São realizadas comparações por:

* Município;
* Estado;
* Região;
* Bioma.

## 7. Análise de relações

Quando aplicável, são investigadas relações entre variáveis por meio de:

* Gráficos de dispersão;
* Correlação;
* Comparações entre grupos;
* Agregações;
* Análises cruzadas.

---

# Principais Dimensões Exploradas

| Dimensão                 | Fontes principais |
| ------------------------ | ----------------- |
| Produção agrícola        | IBGE PAM          |
| Solo                     | MapBiomas Solo    |
| Emissões                 | SEEG              |
| Clima                    | INMET             |
| Território               | IBGE              |
| Bioma                    | IBGE              |
| Cobertura e uso da terra | MapBiomas         |

---

# Fluxo das Análises

```text id="5g9qcb"
                 DADOS PROCESSADOS
                        │
                        ▼
                DADOS SEGMENTADOS
                        │
                        ▼
              ┌───────────────────┐
              │   ANÁLISE EDA     │
              └─────────┬─────────┘
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
      Produção        Solo         Emissões
          │             │             │
          └─────────────┼─────────────┘
                        │
                        ▼
                      Clima
                        │
                        ▼
               Análises Integradas
                        │
                        ▼
                 Indicadores
                        │
                        ▼
                    Power BI
```

---

# Tecnologias Utilizadas

As análises exploratórias podem utilizar:

* **Python**
* **Pandas**
* **NumPy**
* **Matplotlib**
* **Jupyter Notebook**
* **Google Colab**
* **VS Code**

As bibliotecas utilizadas devem ser mantidas documentadas nos notebooks ou no ambiente de desenvolvimento do projeto.

---

# Padronização dos Notebooks

Os notebooks devem seguir uma estrutura consistente.

### Estrutura recomendada

```text id="vqlb0x"
1. Título e objetivo
2. Importação das bibliotecas
3. Carregamento dos dados
4. Conhecimento da base
5. Tratamento específico, quando necessário
6. Análise descritiva
7. Visualizações
8. Análise das relações
9. Principais descobertas
10. Conclusão
```

---

# Boas Práticas

Os notebooks devem:

* Utilizar nomes em `snake_case`;
* Manter variáveis em letras minúsculas;
* Documentar as principais etapas;
* Evitar alterações permanentes nos dados de origem;
* Não sobrescrever arquivos da camada `processed`;
* Registrar as principais descobertas;
* Utilizar gráficos adequados ao tipo de variável;
* Informar a origem dos dados;
* Manter a rastreabilidade das integrações;
* Evitar conclusões causais sem evidências suficientes.

---

# Rastreabilidade

As análises devem manter uma relação clara entre fonte, processamento, segmentação e exploração.

```text id="7m8l6d"
Fonte original
     │
     ▼
data/raw/
     │
     ▼
Processamento
     │
     ▼
data/processed/
     │
     ▼
Segmentação
     │
     ▼
data/segmented/
     │
     ▼
Notebook EDA
     │
     ▼
Resultados exploratórios
     │
     ▼
Indicadores / Power BI
```

Quando uma análise utilizar dados provenientes de uma integração, isso deve ser identificado no notebook.

Exemplo:

```text id="qj0n1j"
IBGE PAM
    +
MapBiomas Solo
    ↓
Base integrada
    ↓
Análise exploratória
```

---

# Resultados das Análises

As principais descobertas obtidas durante a exploração devem ser registradas ao final de cada notebook.

Recomenda-se documentar:

* Principais padrões encontrados;
* Municípios ou regiões de destaque;
* Tendências observadas;
* Variáveis relevantes;
* Possíveis inconsistências;
* Relações identificadas;
* Limitações da análise;
* Indicadores que podem ser desenvolvidos a partir dos resultados.

---

# Notebooks Disponíveis

| Notebook                                  | Objetivo                                               |
| ----------------------------------------- | ------------------------------------------------------ |
| `01_exploracao_ibge_pam.ipynb`            | Exploração da produção agrícola municipal              |
| `02_exploracao_mapbiomas_solo.ipynb`      | Exploração das características do solo                 |
| `03_analise_exploratoria_soja_seeg.ipynb` | Análise exploratória entre produção de soja e emissões |
| `04_integracao_inmet_clima.ipynb`         | Exploração e integração dos dados climáticos           |

---

# Resultado Esperado

A etapa de Análises Exploratórias deve transformar os dados segmentados em **informações relevantes para a tomada de decisão**, identificando padrões e relações que possam apoiar a construção dos indicadores do **Eco_Raiz_360**.

O fluxo final esperado é:

```text id="3t3d7v"
Dados
  ↓
Processamento
  ↓
Segmentação
  ↓
Análise Exploratória
  ↓
Descobertas
  ↓
Indicadores
  ↓
Power BI
```

A análise exploratória funciona, portanto, como uma etapa de **investigação e validação**, conectando os dados preparados às decisões analíticas e aos indicadores apresentados no dashboard do projeto.
