# ==============================================================================
# ETL - ECO_360 (DOWNLOAD AUTOMÁTICO DO GOOGLE DRIVE + CARGA MYSQL)
# Modelo relacional normalizado: dim_municipio + tabelas fato
# ==============================================================================
import sys
import os
import glob
import logging
import gdown
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Configuração de Log
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] - %(message)s'
)

# ==============================================================================
# 1. DOWNLOAD DOS ARQUIVOS DO GOOGLE DRIVE
# ==============================================================================
PASTA_BASE = os.path.abspath("./base")
os.makedirs(PASTA_BASE, exist_ok=True)

# Insira o link da pasta do Google Drive aqui:
LINK_PASTA_DRIVE = "https://drive.google.com/drive/folders/1wSHcvrLdmFlmVMZHQwzzD9b-S3kQRmm4?usp=sharing"

logging.info("1. Verificando e baixando pasta de arquivos do Google Drive...")
if LINK_PASTA_DRIVE.strip():
    try:
        gdown.download_folder(
            url=LINK_PASTA_DRIVE,
            output=PASTA_BASE,
            quiet=False,
            use_cookies=False
        )
    except Exception as e:
        logging.warning(f"Aviso ao tentar sincronizar pasta do Drive: {e}")
        logging.info("Prosseguindo com a leitura dos arquivos locais existentes...")
else:
    logging.info("Nenhum link fornecido em LINK_PASTA_DRIVE. Lendo arquivos locais na pasta './base'...")

# ==============================================================================
# 2. CONFIGURAÇÕES DE CONEXÃO COM O MYSQL
# ==============================================================================
DB_HOST = "127.0.0.1"
DB_PORT = "3306"
DB_USER = "root"
DB_PASS = "root"          # <-- Substitua pela sua senha local se for diferente
DB_NAME = "eco_361"

logging.info(f"2. Conectando ao MySQL em {DB_HOST}:{DB_PORT} com o usuário '{DB_USER}'...")

try:
    engine_root = create_engine(f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}")
    with engine_root.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` DEFAULT CHARACTER SET utf8mb4;"))
        conn.commit()
        logging.info(f"-> Banco de dados '{DB_NAME}' verificado/criado com sucesso.")
except Exception as e:
    logging.critical(f"❌ Erro ao conectar ao MySQL: {e}")
    sys.exit(1)

DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# ==============================================================================
# 3. FUNÇÕES AUXILIARES DE LEITURA E CARGA
# ==============================================================================
def ler_csv_drive(nome_arquivo):
    caminho = os.path.join(PASTA_BASE, nome_arquivo)

    if not os.path.exists(caminho):
        termo = nome_arquivo.split('.')[0]
        encontrados = glob.glob(os.path.join(PASTA_BASE, f"**/*{termo}*"), recursive=True)
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

    # Normalizar nomes de colunas para padrão SQL (minúsculas e sem espaços)
    df.columns = [c.strip().lower().replace(" ", "_").replace("-", "_").replace(".", "_") for c in df.columns]
    return df


def carregar_dataframe_mysql(df: pd.DataFrame, table_name: str):
    """Carrega o DataFrame no MySQL substituindo a tabela existente se já houver."""
    if df.empty:
        logging.warning(f"DataFrame para '{table_name}' está vazio. Etapa pulada.")
        return

    try:
        logging.info(f"-> Carregando tabela '{table_name}' ({len(df)} registros)...")
        df.to_sql(
            name=table_name,
            con=engine,
            if_exists='replace',
            index=False,
            chunksize=5000
        )
        logging.info(f"-> Tabela '{table_name}' carregada com sucesso!")
    except SQLAlchemyError as e:
        logging.error(f"Erro ao carregar dados na tabela '{table_name}': {e}")
        raise


def aplicar_chave_primaria(table_name: str, colunas_pk: list):
    """Aplica PRIMARY KEY na tabela após a carga (to_sql não define PK)."""
    try:
        pk_cols = ", ".join(f"`{c}`" for c in colunas_pk)
        with engine.connect() as conn:
            conn.execute(text(f"ALTER TABLE `{table_name}` MODIFY {pk_cols.split(',')[0].strip('`')} VARCHAR(255) NOT NULL;")) \
                if len(colunas_pk) == 1 else None
            conn.execute(text(f"ALTER TABLE `{table_name}` ADD PRIMARY KEY ({pk_cols});"))
            conn.commit()
        logging.info(f"-> Chave primária ({pk_cols}) aplicada em '{table_name}'.")
    except SQLAlchemyError as e:
        logging.warning(f"Não foi possível aplicar PK em '{table_name}': {e}")


# ==============================================================================
# 4. EXECUÇÃO DO ETL
# ==============================================================================
if __name__ == '__main__':
    logging.info("3. Lendo arquivos CSV da pasta Base (modelo normalizado)...")

    # Nomes exatos dos arquivos normalizados (dimensão + tabelas fato)
    # A ordem importa: dim_municipio precisa ser carregada antes das tabelas fato
    # que dependem dela (FK codigo_ibge).
    arquivos = {
        'dim_municipio':        'dim_municipio.csv',
        'fato_soja':            'fato_soja.csv',
        'fato_clima':           'fato_clima.csv',
        'fato_cobertura':       'fato_cobertura.csv',
        'fato_emissao_soja':    'fato_emissao_soja.csv',
        'fato_emissao_estado':  'fato_emissao_estado.csv',
    }

    # Chaves primárias de cada tabela (aplicadas após a carga)
    chaves_primarias = {
        'dim_municipio':       ['codigo_ibge'],
        'fato_soja':           ['codigo_ibge', 'ano'],
        'fato_clima':          ['codigo_ibge', 'ano'],
        'fato_cobertura':      ['codigo_ibge', 'ano'],
        'fato_emissao_soja':   ['id_emissao'],
        'fato_emissao_estado': ['uf'],
    }

    dataframes_carregados = {}

    for nome_tabela, nome_csv in arquivos.items():
        try:
            df_atual = ler_csv_drive(nome_csv)
            carregar_dataframe_mysql(df_atual, nome_tabela)
            dataframes_carregados[nome_tabela] = df_atual
        except FileNotFoundError as fnf:
            logging.error(f"❌ {fnf}")
        except Exception as e:
            logging.error(f"❌ Erro ao processar o arquivo '{nome_csv}': {e}")

    logging.info("4. Aplicando chaves primárias nas tabelas carregadas...")
    for nome_tabela, colunas_pk in chaves_primarias.items():
        if nome_tabela in dataframes_carregados:
            aplicar_chave_primaria(nome_tabela, colunas_pk)

    print("\n" + "="*65)
    logging.info(" PROCESSO CONCLUÍDO COM SUCESSO! ")
    logging.info(f" Tabelas carregadas em '{DB_NAME}': {list(dataframes_carregados.keys())}")
    print("="*65)
