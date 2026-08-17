#### 💡 Justificativas de Engenharia da Modelagem

1. **Eliminação de Redundâncias:** Atributos geográficos estáticos (como `area_km2`, `latitude` e `longitude`) não mudam anualmente. Armazená-los a cada ano em tabelas separadas causaria inflação do banco e riscos de inconsistência.
2. **Chave Primária Universal (`codigo_ibge`):** Nomes de municípios possuem duplicidades no Brasil (ex: *Ouro Verde* existe em SP e SC). O uso do código oficial do IBGE como chave primária garante unicidade e evita erros de cruzamento.
3. **Integridade Referencial:** Chaves Estrangeiras (`FOREIGN KEY`) vinculam todas as tabelas fato à dimensão `dim_municipio`, simplificando a modelagem e os relacionamentos de 1:N no Power BI[cite: 5].

---

### 📋 Dicionário de Tabelas

| Tabela | Tipo | Descrição | Chave Primária (PK) |
| :--- | :--- | :--- | :--- |
| **`dim_municipio`** | Dimensão | Cadastro consolidado de 1.661 municípios com atributos territoriais e coordenadas geográficas centróides do IBGE[cite: 5]. | `codigo_ibge` |
| **`fato_soja`** | Fato | Dados agrícolas anuais da PAM/IBGE (área plantada/colhida, produção, rendimento e estoques de carbono no solo)[cite: 5]. | (`codigo_ibge`, `ano`) |
| **`fato_clima`** | Fato | Métricas de precipitação, temperatura, umidade e índices de qualidade climática do INMET[cite: 5]. | (`codigo_ibge`, `ano`) |
| **`fato_cobertura`** | Fato | Uso e cobertura da terra do MapBiomas (área de agricultura, pastagem, soja e cobertura vegetal nativa)[cite: 5]. | (`codigo_ibge`, `ano`) |
| **`fato_emissao_soja`** | Fato | Emissões de gases de efeito estufa (tCO2e) agregadas por município, metodologia e tipo de emissão[cite: 5]. | `id_emissao` |
| **`fato_emissao_estado`** | Fato | Agregado estadual de emissões, taxas de conversão e intervalos de confiança (7 UFs)[cite: 5]. | `uf` |

---

#### 🛠️ Script DDL de Criação do Banco de Dados (Schema)

```sql
CREATE DATABASE IF NOT EXISTS eco_360;
USE eco_360;

-- ==========================================
-- 1. Tabela Dimensão: Município
-- ==========================================
CREATE TABLE dim_municipio (
    codigo_ibge INT PRIMARY KEY,
    municipio VARCHAR(100) NOT NULL,
    uf CHAR(2) NOT NULL,
    regiao VARCHAR(20) NOT NULL,
    area_km2 DECIMAL(10,3),
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6)
);

-- ==========================================
-- 2. Tabela Fato: Soja (IBGE / PAM)
-- ==========================================
CREATE TABLE fato_soja (
    codigo_ibge INT NOT NULL,
    ano SMALLINT NOT NULL,
    area_plantada_ha DECIMAL(12,2),
    area_colhida_ha DECIMAL(12,2),
    area_nao_colhida_ha DECIMAL(12,2),
    aproveitamento_area_pct DECIMAL(6,2),
    quantidade_produzida_t DECIMAL(14,2),
    rendimento_medio_kg_ha DECIMAL(10,2),
    valor_producao_mil_reais DECIMAL(14,2),
    carbono_solo_t_ha DECIMAL(8,2),
    tem_dado_producao TINYINT(1) NOT NULL DEFAULT 1,
    PRIMARY KEY (codigo_ibge, ano),
    FOREIGN KEY (codigo_ibge) REFERENCES dim_municipio(codigo_ibge)
);

-- ==========================================
-- 3. Tabela Fato: Clima (INMET)
-- ==========================================
CREATE TABLE fato_clima (
    codigo_ibge INT NOT NULL,
    ano SMALLINT NOT NULL,
    precipitacao_anual_mm DECIMAL(8,2),
    origem_precipitacao VARCHAR(30),
    numero_estacoes_observadas_precipitacao SMALLINT,
    numero_estacoes_idw_precipitacao SMALLINT,
    temperatura_media_anual_c DECIMAL(5,2),
    origem_temperatura VARCHAR(30),
    umidade_media_anual_pct DECIMAL(5,2),
    origem_umidade VARCHAR(30),
    score_qualidade_climatica TINYINT,
    qualidade_climatica_geral VARCHAR(20),
    tipo_representacao_climatica VARCHAR(30),
    PRIMARY KEY (codigo_ibge, ano),
    FOREIGN KEY (codigo_ibge) REFERENCES dim_municipio(codigo_ibge)
);

-- ==========================================
-- 4. Tabela Fato: Cobertura do Solo (MapBiomas)
-- ==========================================
CREATE TABLE fato_cobertura (
    codigo_ibge INT NOT NULL,
    ano SMALLINT NOT NULL,
    area_agricultura_ha DECIMAL(12,2),
    area_soja_mapbiomas_ha DECIMAL(12,2),
    area_cobertura_natural_ha DECIMAL(12,2),
    area_pastagem_ha DECIMAL(12,2),
    pct_agricultura DECIMAL(6,3),
    pct_soja_mapbiomas DECIMAL(6,3),
    pct_cobertura_natural DECIMAL(6,3),
    pct_pastagem DECIMAL(6,3),
    biomas_presentes VARCHAR(100),
    quantidade_biomas TINYINT,
    PRIMARY KEY (codigo_ibge, ano),
    FOREIGN KEY (codigo_ibge) REFERENCES dim_municipio(codigo_ibge)
);

-- ==========================================
-- 5. Tabela Fato: Emissões de Soja (SEEG/BRLUC)
-- ==========================================
CREATE TABLE fato_emissao_soja (
    id_emissao INT PRIMARY KEY AUTO_INCREMENT,
    codigo_ibge INT,
    ano SMALLINT NOT NULL,
    metodologia VARCHAR(10) NOT NULL,
    metrica VARCHAR(10) NOT NULL,
    unidade VARCHAR(10) NOT NULL,
    tipo_emissao VARCHAR(20) NOT NULL,
    bioma VARCHAR(30),
    emissao_t DECIMAL(16,2),
    FOREIGN KEY (codigo_ibge) REFERENCES dim_municipio(codigo_ibge)
);

-- ==========================================
-- 6. Tabela Fato: Emissões por Estado
-- ==========================================
CREATE TABLE fato_emissao_estado (
    uf CHAR(2) PRIMARY KEY,
    estado VARCHAR(30) NOT NULL,
    regiao VARCHAR(20) NOT NULL,
    cultura VARCHAR(20) NOT NULL,
    taxa_emissao DECIMAL(8,2),
    taxa_ic_inferior DECIMAL(8,2),
    taxa_ic_superior DECIMAL(8,2),
    emissao_absoluta DECIMAL(16,2),
    emissao_ic_inferior DECIMAL(16,2),
    emissao_ic_superior DECIMAL(16,2),
    area_conversao DECIMAL(14,2)
);
