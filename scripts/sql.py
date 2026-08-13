# ==============================================================================
# ETL - ECO_360 (DOWNLOAD AUTOMÁTICO DO GOOGLE DRIVE + CARGA MYSQL)
# ==============================================================================
import sys
import os
import glob
import gdown
import pandas as pd
from sqlalchemy import create_engine, inspect, text

# ==============================================================================
# 1. DOWNLOAD DOS ARQUIVOS DO GOOGLE DRIVE
# ==============================================================================
PASTA_BASE = os.path.abspath("./base")
os.makedirs(PASTA_BASE, exist_ok=True)

# Link da pasta pública do Google Drive
LINK_PASTA_DRIVE = "https://drive.google.com/drive/folders/1iilcMepijmd5vRQwxkUNaX9Um-tsj2c3?usp=sharing"

print("1. Verificando e baixando pasta de arquivos do Google Drive...")
try:
    gdown.download_folder(
        url=LINK_PASTA_DRIVE, 
        output=PASTA_BASE, 
        quiet=False, 
        use_cookies=False
    )
except Exception as e:
    print(f"Aviso ao tentar sincronizar pasta do Drive: {e}")
    print("Prosseguindo com a leitura dos arquivos locais existentes...")

# ==============================================================================
# 2. CONFIGURAÇÕES DE CONEXÃO COM O MYSQL
# ==============================================================================
DB_HOST = "127.0.0.1"
DB_PORT = "3306"
DB_USER = "root"
DB_PASS = "root"          # <-- Substitua pela sua senha local do MySQL se for diferente
DB_NAME = "eco_360"

print(f"\n2. Conectando ao MySQL em {DB_HOST}:{DB_PORT} com o usuário '{DB_USER}'...")

try:
    engine_root = create_engine(f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}")
    with engine_root.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` DEFAULT CHARACTER SET utf8mb4;"))
        conn.commit()
        print(f"-> Banco de dados '{DB_NAME}' verificado/criado com sucesso.")
except Exception as e:
    print(f"\n❌ Erro ao conectar ao MySQL: {e}")
    print("Dica: Verifique se o serviço do MySQL está rodando e se a senha em DB_PASS está correta.")
    sys.exit(1)

DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

# ==============================================================================
# 3. ESTRUTURA DDL (CRIAÇÃO DAS TABELAS)
# ==============================================================================
def criar_tabelas():
    ddl_dim_municipio = """
    CREATE TABLE IF NOT EXISTS dim_municipio (
        id_municipio_ibge INT PRIMARY KEY,
        nome_municipio VARCHAR(150),
        sigla_uf VARCHAR(2),
        regiao_nm VARCHAR(50)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    ddl_fato_pam_soja = """
    CREATE TABLE IF NOT EXISTS fato_pam_soja (
        id_municipio_ibge INT,
        ano INT,
        area_plantada_ha DOUBLE,
        area_colhida_ha DOUBLE,
        quantidade_produzida_t DOUBLE,
        rendimento_medio_kg_ha DOUBLE,
        valor_producao_mil_reais DOUBLE,
        PRIMARY KEY (id_municipio_ibge, ano),
        CONSTRAINT fk_pam_municipio
            FOREIGN KEY (id_municipio_ibge) REFERENCES dim_municipio (id_municipio_ibge)
            ON DELETE CASCADE ON UPDATE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    ddl_fato_mapbiomas_solo = """
    CREATE TABLE IF NOT EXISTS fato_mapbiomas_solo (
        id_municipio_ibge INT,
        ano INT,
        estoque_carbono_medio_t_ha DOUBLE,
        area_ha DOUBLE,
        carbono_total_t DOUBLE,
        PRIMARY KEY (id_municipio_ibge, ano),
        CONSTRAINT fk_mapbiomas_municipio
            FOREIGN KEY (id_municipio_ibge) REFERENCES dim_municipio (id_municipio_ibge)
            ON DELETE CASCADE ON UPDATE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    ddl_fato_priorizacao = """
    CREATE TABLE IF NOT EXISTS fato_priorizacao_agroambiental (
        id_municipio_ibge INT PRIMARY KEY,
        cultura VARCHAR(50),
        producao_total_t DOUBLE,
        area_plantada_total_ha DOUBLE,
        area_colhida_total_ha DOUBLE,
        carbono_solo_medio_t_ha DOUBLE,
        carbono_2019_t_ha DOUBLE,
        carbono_2024_t_ha DOUBLE,
        variacao_carbono_t_ha DOUBLE,
        variacao_carbono_pct DOUBLE,
        score_producao DOUBLE,
        score_area DOUBLE,
        reducao_carbono_t_ha DOUBLE,
        score_reducao_carbono DOUBLE,
        indice_priorizacao_agroambiental DOUBLE,
        classe_priorizacao VARCHAR(50),
        CONSTRAINT fk_prio_municipio
            FOREIGN KEY (id_municipio_ibge) REFERENCES dim_municipio (id_municipio_ibge)
            ON DELETE CASCADE ON UPDATE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """

    print("\n3. Criando tabelas no MySQL...")
    with engine.begin() as conn:
        conn.execute(text(ddl_dim_municipio))
        conn.execute(text(ddl_fato_pam_soja))
        conn.execute(text(ddl_fato_mapbiomas_solo))
        conn.execute(text(ddl_fato_priorizacao))
    print("-> Estruturas DDL aplicadas com sucesso.")

# ==============================================================================
# 4. FUNÇÕES AUXILIARES
# ==============================================================================
def ler_csv_drive(nome_arquivo):
    caminho = os.path.join(PASTA_BASE, nome_arquivo)

    # Procura também recursivamente caso os arquivos baixem dentro de subpastas
    if not os.path.exists(caminho):
        termo = nome_arquivo.split('_')[0]
        encontrados = glob.glob(os.path.join(PASTA_BASE, f"**/*{termo}*.csv"), recursive=True)
        if encontrados:
            caminho = encontrados[0]
        else:
            raise FileNotFoundError(f"Arquivo '{nome_arquivo}' não foi localizado em '{PASTA_BASE}'.")

    try:
        df = pd.read_csv(caminho, sep=',', encoding='utf-8-sig')
        if len(df.columns) == 1:
            df = pd.read_csv(caminho, sep=';', encoding='utf-8-sig')
    except Exception:
        df = pd.read_csv(caminho, sep=';', encoding='latin1')

    df.columns = df.columns.str.strip().str.replace('\ufeff', '')
    return df

def obter_colunas_tabela(nome_tabela):
    inspector = inspect(engine)
    if inspector.has_table(nome_tabela):
        return [col['name'] for col in inspector.get_columns(nome_tabela)]
    return []

def filtrar_existentes_composta(df, nome_tabela, chaves):
    if df.empty:
        return df

    cols_str = ", ".join(chaves)
    try:
        existentes = pd.read_sql(f"SELECT {cols_str} FROM {nome_tabela}", con=engine)
        if not existentes.empty:
            df = df.merge(existentes, on=chaves, how='left', indicator=True)
            df = df[df['_merge'] == 'left_only'].drop(columns=['_merge'])
    except Exception:
        pass

    return df

# ==============================================================================
# 5. EXECUÇÃO DO ETL E CARGA
# ==============================================================================
if __name__ == '__main__':
    criar_tabelas()

    print("\n4. Carregando arquivos CSV...")
    df_pam = ler_csv_drive('pam_curated_soja_centro_oeste_sul_2019_2024.csv')
    df_solo = ler_csv_drive('mapbiomas_solo_municipios_centro_oeste_sul_2019_2024_curated.csv')
    df_prio = ler_csv_drive('priorizacao_agroambiental_soja_centro_oeste_sul_2019_2024.csv')

    mapa_colunas = {
        'codigo_ibge': 'id_municipio_ibge',
        'id_municipio': 'id_municipio_ibge',
        'municipio': 'nome_municipio',
        'uf': 'sigla_uf',
        'regiao': 'regiao_nm',
        'estoque_carbono': 'estoque_carbono_medio_t_ha',
        'estoque_carbono_t_ha': 'estoque_carbono_medio_t_ha',
        'area': 'area_ha',
        'carbono_total': 'carbono_total_t'
    }

    df_pam.rename(columns=mapa_colunas, inplace=True)
    df_solo.rename(columns=mapa_colunas, inplace=True)
    df_prio.rename(columns=mapa_colunas, inplace=True)

    # 5.1 Carga: dim_municipio
    print("\n5. Povoando tabela 'dim_municipio'...")
    cols_muni = obter_colunas_tabela('dim_municipio')
    dfs_muni = [df[[c for c in cols_muni if c in df.columns]] for df in [df_pam, df_solo, df_prio] if 'id_municipio_ibge' in df.columns]
    
    if dfs_muni:
        df_muni_completo = pd.concat(dfs_muni, ignore_index=True).drop_duplicates(subset=['id_municipio_ibge']).dropna(subset=['id_municipio_ibge'])
        df_muni_completo = filtrar_existentes_composta(df_muni_completo, 'dim_municipio', ['id_municipio_ibge'])

        if not df_muni_completo.empty:
            df_muni_completo.to_sql('dim_municipio', con=engine, if_exists='append', index=False, chunksize=1000)
            print(f"-> dim_municipio: {len(df_muni_completo)} novos registros inseridos.")
        else:
            print("-> dim_municipio: Todos os registros já existem no banco.")

    muni_validos = set(pd.read_sql("SELECT id_municipio_ibge FROM dim_municipio", con=engine)['id_municipio_ibge'])

    # 5.2 Carga: fato_pam_soja
    print("\n6. Povoando tabela 'fato_pam_soja'...")
    cols_pam = obter_colunas_tabela('fato_pam_soja')
    df_pam_fato = df_pam[[c for c in cols_pam if c in df_pam.columns]].drop_duplicates(subset=['id_municipio_ibge', 'ano'])
    df_pam_fato = df_pam_fato[df_pam_fato['id_municipio_ibge'].isin(muni_validos)]
    df_pam_fato = filtrar_existentes_composta(df_pam_fato, 'fato_pam_soja', ['id_municipio_ibge', 'ano'])

    if not df_pam_fato.empty:
        df_pam_fato.to_sql('fato_pam_soja', con=engine, if_exists='append', index=False, chunksize=2000)
        print(f"-> fato_pam_soja: {len(df_pam_fato)} novos registros inseridos.")
    else:
        print("-> fato_pam_soja: Todos os registros já existem no banco.")

    # 5.3 Carga: fato_mapbiomas_solo
    print("\n7. Povoando tabela 'fato_mapbiomas_solo'...")
    cols_solo = obter_colunas_tabela('fato_mapbiomas_solo')
    df_solo_fato = df_solo[[c for c in cols_solo if c in df_solo.columns]].drop_duplicates(subset=['id_municipio_ibge', 'ano'])
    df_solo_fato = df_solo_fato[df_solo_fato['id_municipio_ibge'].isin(muni_validos)]
    df_solo_fato = filtrar_existentes_composta(df_solo_fato, 'fato_mapbiomas_solo', ['id_municipio_ibge', 'ano'])

    if not df_solo_fato.empty:
        df_solo_fato.to_sql('fato_mapbiomas_solo', con=engine, if_exists='append', index=False, chunksize=2000)
        print(f"-> fato_mapbiomas_solo: {len(df_solo_fato)} novos registros inseridos.")
    else:
        print("-> fato_mapbiomas_solo: Todos os registros já existem no banco.")

    # 5.4 Carga: fato_priorizacao_agroambiental
    print("\n8. Povoando tabela 'fato_priorizacao_agroambiental'...")
    cols_prio = obter_colunas_tabela('fato_priorizacao_agroambiental')
    df_prio_fato = df_prio[[c for c in cols_prio if c in df_prio.columns]].drop_duplicates(subset=['id_municipio_ibge'])
    df_prio_fato = df_prio_fato[df_prio_fato['id_municipio_ibge'].isin(muni_validos)]
    df_prio_fato = filtrar_existentes_composta(df_prio_fato, 'fato_priorizacao_agroambiental', ['id_municipio_ibge'])

    if not df_prio_fato.empty:
        df_prio_fato.to_sql('fato_priorizacao_agroambiental', con=engine, if_exists='append', index=False, chunksize=1000)
        print(f"-> fato_priorizacao_agroambiental: {len(df_prio_fato)} novos registros inseridos.")
    else:
        print("-> fato_priorizacao_agroambiental: Todos os registros já existem no banco.")

    print("\n" + "="*65)
    print(" PROCESSO CONCLUÍDO COM SUCESSO! ")
    print("="*65)