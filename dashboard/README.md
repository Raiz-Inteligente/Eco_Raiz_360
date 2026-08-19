# 🌱 Eco360 — Inteligência Agroambiental da Soja

Dashboard em Power BI desenvolvido para a **Raiz Inteligente**, consultoria de inteligência agroambiental, com foco na cultura da **soja** nas regiões **Centro-Oeste e Sul do Brasil**.

O projeto vai além de um painel descritivo: o objetivo final é subsidiar a **avaliação de potencial de investimento em crédito de carbono** nas áreas de produção analisadas, cruzando dados de produtividade agrícola, clima, cobertura do solo e emissões.

> Case desenvolvido para avaliação por banca de empresas e professores.

---

## Sobre o Eco360

O **Índice de Oportunidade Agroambiental (IOA_Score)** é o coração analítico do projeto: um indicador em DAX que combina, de forma normalizada, cinco pilares:

1. Produtividade agrícola
2. Clima
3. Emissão (invertida — quanto menor, melhor)
4. Carbono no solo
5. Cobertura natural

O índice permite comparar municípios não apenas pela produção de soja, mas pelo seu potencial socioambiental combinado — a base para leitura do potencial de crédito de carbono.

---

## Estrutura do dashboard

O relatório é organizado em 9 páginas:

| Página | Conteúdo |
|---|---|
| **Menu** | Navegação central entre as páginas do relatório |
| **Contato** | Página de encerramento/contato |
| **Visão 360** | Painel executivo: gauge do IOA, mapa (Azure Maps), cards de indicadores-chave, tabela e filtros por UF/região/ano |
| **Metodologia** | Notas metodológicas e transparência sobre os cálculos |
| **Clima** | Confiabilidade climática, dispersão (scatter) entre variáveis climáticas, série temporal e tabela dinâmica (pivot) |
| **Produção** | Produção total, ranking de municípios, variação YoY, comparativo por gráfico de barras/combinado e série de área |
| **Meio Ambiente** | Cobertura natural, potencial de carbono no solo, treemap, dispersão e mapa geográfico |
| **Emissões** | Emissão total (municipal e estadual), intensidade de emissão, gráficos de barras e coluna 100% empilhada |
| **Território** | Mapa geográfico (Azure Maps) com filtros por UF/região |

**Filtros (slicers) disponíveis:** UF, região, ano, município e classificação de carbono no solo — aplicados de forma consistente entre as páginas analíticas.

**Visuais utilizados:** cards, gauge, tabelas, mapas (Azure Maps – *custom visual*), gráficos de barras (clusterizado, 100% empilhado), coluna, combinado linha+coluna, área, dispersão (scatter) e treemap.

---

## Modelo de dados

Modelagem em **esquema estrela (star schema)**:

- `dim_tempo`
- `dim_municipio`
- `fato_soja`
- `fato_clima`
- `fato_cobertura`
- `fato_emissao_soja`
- `fato_emissao_estado`

### Pipeline (4 camadas)

```
RAW → Limpeza → Modelo Normalizado → Carga
```

Todo o processo é documentado e carregado em um banco **MySQL** (`eco_360`), a partir do qual o modelo do Power BI é alimentado.

### Fontes de dados

- **PAM** (Produção Agrícola Municipal) — 1.505 municípios
- **INMET** (dados climáticos) — 1.661 municípios
- **MapBiomas** (cobertura do solo) — 1.660 municípios
- **IBGE** — códigos e divisão territorial

A base de `dim_municipio` foi construída via `UNION` dessas três fontes, resultando em **1.661 municípios únicos**.

> A base de queimadas do INPE era uma fonte opcional e foi deliberadamente **não utilizada** neste projeto.

---

## ⚠️ Notas metodológicas e limitações conhecidas

- `fato_emissao_estado` está relacionada a `dim_municipio`, porém possui **granularidade estadual** (não possui `codigo_ibge` municipal) — deve ser interpretada nesse nível de agregação.
- A razão `emissao_t / quantidade_produzida_t` é **quase constante** (~0,095 tCO2e/t em 99,6% dos ~8.669 registros), refletindo um fator fixo de emissão aplicado pela metodologia da base de origem (padrão tipo IPCC) — **não deve ser usada como diferenciador de eficiência de manejo por município**.
- 5 municípios apresentam produção ausente na PAM mesmo com `status_dado = "disponivel"`; nesses casos, a disponibilidade real do dado é controlada pela coluna `tem_dado_producao`.
- `fato_emissao_soja[codigo_ibge]` aceita valores nulos para registros da base de emissão sem correspondência confirmada em `dim_municipio`.

---

## Padrão visual

O dashboard segue um guia visual institucional próprio, com paleta em tons de verde, definição de gráficos recomendados por página e grid de montagem padronizado, garantindo consistência visual entre todas as páginas.

---

## Tecnologias

- **Power BI Desktop** (modelagem, DAX, visualização)
- **MySQL** (camada de armazenamento/carga do pipeline)
- **DAX** (medidas, incluindo o IOA_Score)
- **Azure Maps** (visual customizado para mapas geográficos)

---

## Como abrir

1. Instale o [Power BI Desktop](https://powerbi.microsoft.com/desktop/) (versão mais recente recomendada).
2. Abra o arquivo `eco_360.pbix`.
3. Caso o modelo esteja conectado a uma fonte MySQL externa, configure as credenciais de conexão quando solicitado.

---

## Escopo

O modelo atual está segmentado como amostra: cultura de **soja** e regiões **Centro-Oeste e Sul do Brasil**, servindo como prova de conceito para expansão futura a outras culturas e regiões.
