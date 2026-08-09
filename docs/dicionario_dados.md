# Dicionário de Dados — Base Meteorológica

## 1. Identificação

**Nome da base:** Dados Meteorológicos Processados
**Origem:** Dados de estações meteorológicas
**Camada:** `databases_processed`
**Formato:** CSV
**Padrão de nomenclatura:** `snake_case`

---

## 2. Variáveis da Base

| Variável                    | Tipo   | Unidade      | Descrição                                                                                                       |
| --------------------------- | ------ | ------------ | --------------------------------------------------------------------------------------------------------------- |
| `codigo_wmo`                | string | —            | Código de identificação da estação meteorológica segundo o padrão WMO.                                          |
| `uf`                        | string | —            | Unidade Federativa onde a estação está localizada.                                                              |
| `regiao`                    | string | —            | Região geográfica brasileira à qual a estação pertence.                                                         |
| `latitude`                  | float  | graus        | Latitude geográfica da estação meteorológica.                                                                   |
| `longitude`                 | float  | graus        | Longitude geográfica da estação meteorológica.                                                                  |
| `altitude_m`                | float  | m            | Altitude da estação em relação ao nível do mar.                                                                 |
| `data`                      | date   | `YYYY-MM-DD` | Data de referência das observações meteorológicas.                                                              |
| `precipitacao_total_mm`     | float  | mm           | Volume total de precipitação registrado no período.                                                             |
| `pressao_media_mb`          | float  | mb           | Valor médio da pressão atmosférica registrado no período.                                                       |
| `pressao_max_mb`            | float  | mb           | Maior valor de pressão atmosférica registrado no período.                                                       |
| `pressao_min_mb`            | float  | mb           | Menor valor de pressão atmosférica registrado no período.                                                       |
| `radiacao_total_kj_m2`      | float  | kJ/m²        | Quantidade total de radiação solar registrada no período.                                                       |
| `temperatura_media_c`       | float  | °C           | Temperatura média registrada no período.                                                                        |
| `temperatura_maxima_c`      | float  | °C           | Temperatura máxima registrada no período.                                                                       |
| `temperatura_minima_c`      | float  | °C           | Temperatura mínima registrada no período.                                                                       |
| `ponto_orvalho_medio_c`     | float  | °C           | Temperatura média do ponto de orvalho.                                                                          |
| `umidade_media_pct`         | float  | %            | Umidade relativa média do ar registrada no período.                                                             |
| `umidade_max_pct`           | float  | %            | Maior valor de umidade relativa registrado no período.                                                          |
| `umidade_min_pct`           | float  | %            | Menor valor de umidade relativa registrado no período.                                                          |
| `rajada_maxima_ms`          | float  | m/s          | Maior velocidade de rajada de vento registrada no período.                                                      |
| `velocidade_vento_media_ms` | float  | m/s          | Velocidade média do vento registrada no período.                                                                |
| `horas_observadas`          | int    | horas        | Quantidade de horas com observações meteorológicas disponíveis.                                                 |
| `completude_pct`            | float  | %            | Percentual de observações esperadas que foram efetivamente registradas.                                         |
| `direcao_vento_media_graus` | float  | graus        | Direção média do vento registrada durante o período.                                                            |
| `choveu`                    | string | —            | Indicador que informa se houve precipitação no período. Valores esperados: `sim` ou `nao`.                      |
| `chuva_forte`               | string | —            | Indicador de ocorrência de chuva forte. Valores esperados: `sim` ou `nao`.                                      |
| `classe_chuva`              | string | —            | Classificação da intensidade da precipitação registrada.                                                        |
| `temperatura_extrema_alta`  | string | —            | Indicador de ocorrência de temperatura classificada como extremamente alta. Valores esperados: `sim` ou `nao`.  |
| `temperatura_extrema_baixa` | string | —            | Indicador de ocorrência de temperatura classificada como extremamente baixa. Valores esperados: `sim` ou `nao`. |
| `amplitude_termica_c`       | float  | °C           | Diferença entre a temperatura máxima e a temperatura mínima registrada.                                         |
| `ventania_extrema`          | string | —            | Indicador de ocorrência de ventania classificada como extrema. Valores esperados: `sim` ou `nao`.               |
| `vento_forte`               | string | —            | Indicador de ocorrência de vento forte. Valores esperados: `sim` ou `nao`.                                      |
| `classe_vento`              | string | —            | Classificação da intensidade do vento registrada no período.                                                    |
| `umidade_muito_alta`        | string | —            | Indicador de ocorrência de umidade relativa muito alta. Valores esperados: `sim` ou `nao`.                      |
| `umidade_baixa`             | string | —            | Indicador de ocorrência de umidade relativa baixa. Valores esperados: `sim` ou `nao`.                           |
| `radiacao_total_mj_m2`      | float  | MJ/m²        | Radiação solar total convertida de kJ/m² para MJ/m².                                                            |
| `status_dados`              | string | —            | Indicador da qualidade e completude das observações meteorológicas do registro.                                 |

---

## 3. Variáveis Derivadas

Algumas variáveis não representam diretamente uma medição original, sendo calculadas durante o processamento dos dados.

### `amplitude_termica_c`

Calculada pela diferença entre a temperatura máxima e mínima:

```text
amplitude_termica_c = temperatura_maxima_c - temperatura_minima_c
```

Exemplo:

```text
26,2 °C - 17,8 °C = 8,4 °C
```

---

### `radiacao_total_mj_m2`

Conversão da radiação de kJ/m² para MJ/m²:

```text
radiacao_total_mj_m2 = radiacao_total_kj_m2 / 1000
```

Exemplo:

```text
15506,3 kJ/m² / 1000 = 15,5063 MJ/m²
```

---

### Variáveis de classificação

As seguintes variáveis são indicadores derivados das medições meteorológicas:

* `choveu`
* `chuva_forte`
* `classe_chuva`
* `temperatura_extrema_alta`
* `temperatura_extrema_baixa`
* `ventania_extrema`
* `vento_forte`
* `classe_vento`
* `umidade_muito_alta`
* `umidade_baixa`

Essas variáveis permitem transformar medições contínuas em categorias úteis para análise, visualização e tomada de decisão.

---

## 4. Tratamento de Dados Ausentes

A ausência de uma medição não deve ser confundida com um valor real igual a zero.

### Valor `0`

Representa uma medição real.

Exemplo:

```text
precipitacao_total_mm = 0.0
```

Significa que não houve precipitação registrada no período.

### `dados_nao_captados`

Representa ausência de medição ou falha na captura dos dados.

Esse valor deve ser utilizado quando a estação não forneceu uma determinada observação.

### `status_dados`

A variável `status_dados` permite identificar a situação geral da captura das informações meteorológicas.

Exemplo:

```text
dados_completamente_captados
```

indica que o conjunto de observações esperado para aquele registro foi obtido.

---

## 5. Identificação Geográfica

As variáveis utilizadas para localização das estações são:

* `codigo_wmo`
* `uf`
* `regiao`
* `latitude`
* `longitude`
* `altitude_m`

Essas informações permitem relacionar as condições meteorológicas às diferentes regiões e localidades analisadas.

---

## 6. Variáveis Meteorológicas

### Precipitação

* `precipitacao_total_mm`
* `choveu`
* `chuva_forte`
* `classe_chuva`

### Pressão atmosférica

* `pressao_media_mb`
* `pressao_max_mb`
* `pressao_min_mb`

### Temperatura

* `temperatura_media_c`
* `temperatura_maxima_c`
* `temperatura_minima_c`
* `ponto_orvalho_medio_c`
* `amplitude_termica_c`
* `temperatura_extrema_alta`
* `temperatura_extrema_baixa`

### Umidade

* `umidade_media_pct`
* `umidade_max_pct`
* `umidade_min_pct`
* `umidade_muito_alta`
* `umidade_baixa`

### Vento

* `rajada_maxima_ms`
* `velocidade_vento_media_ms`
* `direcao_vento_media_graus`
* `ventania_extrema`
* `vento_forte`
* `classe_vento`

### Radiação solar

* `radiacao_total_kj_m2`
* `radiacao_total_mj_m2`

---

## 7. Qualidade e Completude

As variáveis relacionadas à qualidade da captura são:

### `horas_observadas`

Quantidade de horas em que foram obtidas observações meteorológicas.

### `completude_pct`

Percentual de observações efetivamente disponíveis em relação ao total esperado.

### `status_dados`

Classificação geral do estado de captura dos dados.

Essas variáveis são utilizadas para auxiliar na auditoria e na avaliação da confiabilidade da base.

---

## 8. Coluna Removida

### `estacao`

A coluna `estacao` foi removida da base processada porque não apresentava informações nos registros analisados.

A remoção evita manter uma coluna sem valor analítico e reduz ruído desnecessário na estrutura final da base.

O identificador `codigo_wmo` permanece como identificador principal da estação.

---

## 9. Regras de Padronização

A base processada segue as seguintes regras:

* Todas as colunas utilizam `snake_case`.
* Não são utilizados acentos nos nomes das variáveis.
* Não são utilizados espaços nos nomes das colunas.
* Não são utilizados caracteres especiais.
* Valores booleanos textuais utilizam `sim` e `nao`.
* Ausência de captura é representada por `dados_nao_captados`.
* Valores numéricos permanecem em tipos numéricos.
* Datas seguem o padrão `YYYY-MM-DD`.
* Valores iguais a zero são preservados quando representam medições reais.
* A camada `raw` permanece inalterada.
* A base `processed` contém os dados higienizados e padronizados.
* A base `curated` é derivada da base `processed` para aplicações analíticas específicas.

---

## 10. Camadas do Pipeline

```text
data/raw
    │
    │ Dados originais
    ▼
data/databases_processed
    │
    │ Dados limpos, padronizados e validados
    ▼
data/databases_curated
    │
    │ Dados preparados para consumo específico
    ▼
Dashboard / Análises / Modelos
```

### Raw

Mantém os dados exatamente como foram recebidos.

### Processed

Contém os dados após:

* limpeza;
* padronização dos nomes;
* tratamento de valores ausentes;
* correção dos tipos;
* remoção de inconsistências;
* remoção de colunas sem informação;
* validações de qualidade.

### Curated

É construída a partir da camada `processed` e recebe transformações específicas para o objetivo analítico, como agregações, indicadores e tabelas destinadas ao dashboard.

---

## 11. Exemplo de Registro Processado

Um registro processado pode apresentar a seguinte estrutura:

```text
codigo_wmo: A001
uf: DF
regiao: centro_oeste
latitude: -15.789343
longitude: -47.925756
altitude_m: 1160.96
data: 2019-01-01
precipitacao_total_mm: 0.0
temperatura_media_c: 20.52
temperatura_maxima_c: 26.2
temperatura_minima_c: 17.8
umidade_media_pct: 82.21
velocidade_vento_media_ms: 1.59
choveu: nao
classe_chuva: sem_chuva
amplitude_termica_c: 8.4
classe_vento: moderado
radiacao_total_mj_m2: 15.5063
status_dados: dados_completamente_captados
```

---

## 12. Observação sobre o Dicionário

Este documento deve ser atualizado sempre que uma nova variável for adicionada, removida ou tiver sua regra de cálculo modificada.

O dicionário de dados é parte da documentação do pipeline e deve acompanhar as alterações realizadas na estrutura da base.
