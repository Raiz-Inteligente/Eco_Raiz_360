# Pipeline INMET — Limpeza e Curadoria de Dados Meteorológicos

Este script implementa a etapa de **engenharia de dados** de um projeto de análise climática, responsável por transformar os arquivos brutos do INMET (Instituto Nacional de Meteorologia) em bases limpas, padronizadas e prontas para consumo em dashboards (Power BI, Streamlit, etc).

## Visão geral da arquitetura

O pipeline segue o padrão **RAW → PROCESSED → CURATED**, com os dados organizados em disco da seguinte forma:

```
data/
├── raw/
│   └── INMET/
│       ├── 2019/ ... 2024/
│
├── databases_processed/
│   └── INMET/
│       ├── 2019/ ... 2024/
│
└── databases_curated/
    └── INMET/
        ├── centro_oeste/
        │   └── YYYY-MM-DD.csv
        └── sul/
            └── YYYY-MM-DD.csv
```

**Período coberto:** 2019 a 2024
**Regiões contempladas:** Centro-Oeste (DF, GO, MT, MS) e Sul (PR, SC, RS)

## Fluxo do pipeline

```
RAW (arquivos brutos do INMET)
 ↓
Limpeza e padronização de colunas, textos e números
 ↓
PROCESSED (dados horários limpos, por estação)
 ↓
Agregação diária + cálculo de KPIs + validação de qualidade
 ↓
CURATED (dados diários, por região, prontos para uso)
 ↓
Dashboard / Power BI / Streamlit
```

## Etapa 1 — RAW → PROCESSED

Função principal: `processar_raw()`

Para cada arquivo `.CSV` bruto do INMET, o script:

1. **Extrai metadados do cabeçalho** (`extrair_metadados`) — estação, UF, código WMO, latitude, longitude, altitude.
2. **Lê e padroniza os dados horários** (`ler_inmet`):
   - Padroniza nomes de colunas para `snake_case` (`padronizar_nome_coluna`).
   - Identifica automaticamente as colunas de data e hora.
   - Mapeia as colunas originais do INMET para nomes padronizados (ex.: `precipitacao_mm`, `temperatura_c`, `umidade_pct`, `velocidade_vento_ms`, etc).
   - Converte valores numéricos, tratando `-9999` (código de falha do INMET) como dado ausente (`converter_numero`).
   - Filtra apenas o ano correspondente ao arquivo e apenas estações localizadas nas UFs de interesse (Centro-Oeste e Sul).
3. **Trata valores fisicamente impossíveis** (`tratar_valores_fisicos`) — ex.: umidade fora de 0–100%, pressão fora de 800–1100 mb — convertendo-os em ausência de dado (não descarta a linha).
4. **Remove outliers estatísticos** usando o método IQR por estação (`remover_outliers_iqr`), também convertendo valores suspeitos em `NaN` em vez de excluir o registro.
5. **Cria indicadores de ausência** (`criar_indicadores_ausencia`) — uma coluna `_status` para cada variável meteorológica, marcando `captado` ou `dados_nao_captados`.
6. Remove duplicidades horárias e ordena os dados.
7. Exporta um CSV por estação/arquivo em `databases_processed/INMET/<ano>/`.

## Etapa 2 — PROCESSED → CURATED

Função principal: `processar_processed()`

1. **Agregação diária** (`gerar_dados_diarios`): a partir dos dados horários, calcula por estação e dia:
   - Precipitação total, pressão média/máx/mín, radiação total, temperatura média/máx/mín, ponto de orvalho médio, umidade média/máx/mín, rajada máxima, velocidade média do vento.
   - Direção média do vento calculada via **média circular** (`media_circular`), tratamento correto para variáveis angulares.
   - Percentual de completude do dia (`completude_pct`), com base nas 24 horas esperadas.
2. **Cálculo de KPIs** (`criar_kpis`):
   - Classificação de chuva (`sem_chuva`, `chuva_fraca`, `chuva_moderada`, `chuva_forte`) e flags de chuva/chuva forte.
   - Flags de temperatura extrema (alta ≥ 35°C, baixa ≤ 10°C) e amplitude térmica.
   - Classificação de vento (`calmo_fraco`, `moderado`, `forte`, `ventania_extrema`) e flags de vento forte/ventania.
   - Flags de umidade muito alta (≥90%) e baixa (≤30%).
   - Conversão de radiação para MJ/m².
3. **Status de captura diária** (`criar_status_diario`): classifica cada dia como `dados_completamente_captados`, `dados_parcialmente_captados` ou `dados_nao_captados`.
4. Exporta os dados finais **um arquivo CSV por dia e por região** (`exportar_curated`), em `databases_curated/INMET/<regiao>/YYYY-MM-DD.csv`.

## Regras de negócio principais

| Categoria | Regra |
|---|---|
| Valor ausente na origem | `-9999` → `NaN` |
| Chuva | ≥ 0,1 mm/dia conta como "choveu"; ≥ 50 mm/dia é "chuva forte" |
| Temperatura extrema | ≥ 35°C (alta) / ≤ 10°C (baixa) |
| Vento | ≥ 10 m/s "vento forte"; ≥ 17,2 m/s "ventania extrema" |
| Outliers | Removidos (viram `NaN`) por IQR (1,5×3 = limite de 3×IQR), por estação |
| Limites físicos | Cada variável tem uma faixa fisicamente plausível (ex.: umidade 0–100%, pressão 800–1100 mb) |

> **Importante:** em nenhuma etapa uma linha inteira é descartada por causa de um valor inválido — apenas a medição específica é convertida em ausência (`NaN`), preservando a integridade das agregações (médias, somas etc).

## Relatório de execução

Ao final da execução, `salvar_relatorio()` gera um CSV de auditoria (`outputs/relatorios/relatorio_processamento.csv`) com o status de cada arquivo processado (`ok`, `ignorado`, `erro`), permitindo rastrear falhas e arquivos fora do escopo (ex.: UF não pertencente às regiões analisadas).

## Como executar

```bash
python pipeline_inmet.py
```

O script espera encontrar os arquivos brutos do INMET em `data/raw/INMET/<ano>/` e cria automaticamente as pastas de saída (`databases_processed` e `databases_curated`) caso não existam.

## Resumo técnico

- **Linguagem:** Python (pandas, numpy)
- **Entrada:** arquivos `.CSV` brutos do INMET, separados por `;`, encoding `latin1`
- **Saída:** CSVs padronizados em `utf-8-sig`
- **Logging:** todas as etapas são registradas via módulo `logging`
