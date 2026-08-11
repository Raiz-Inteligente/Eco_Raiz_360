# ==========================================================
# ETAPA FINAL - CONSOLIDAÇÃO DOS CSVs DO INMET
# ==========================================================

from pathlib import Path
import pandas as pd


# ----------------------------------------------------------
# 1. CAMINHO PRINCIPAL DO INMET
# ----------------------------------------------------------

PASTA_INMET = Path(
    r"F:\Eco_Raiz_360\data\databases_curated\INMET"
)

PASTA_CENTRO_OESTE = PASTA_INMET / "centro_oeste"
PASTA_SUL = PASTA_INMET / "sul"

# Pasta onde será criado o banco consolidado
PASTA_JUNTOS = PASTA_INMET / "databases_juntos"

# Cria a pasta automaticamente
PASTA_JUNTOS.mkdir(
    parents=True,
    exist_ok=True
)

# Arquivo final
ARQUIVO_FINAL = PASTA_JUNTOS / "INMET_completo.csv"


# ==========================================================
# 2. LOCALIZAR TODOS OS CSVs
# ==========================================================

arquivos_csv = []

# CSVs do Centro-Oeste
if PASTA_CENTRO_OESTE.exists():

    arquivos_csv.extend(
        PASTA_CENTRO_OESTE.rglob("*.csv")
    )

else:

    print(
        f"Atenção: pasta não encontrada: "
        f"{PASTA_CENTRO_OESTE}"
    )


# CSVs do Sul
if PASTA_SUL.exists():

    arquivos_csv.extend(
        PASTA_SUL.rglob("*.csv")
    )

else:

    print(
        f"Atenção: pasta não encontrada: "
        f"{PASTA_SUL}"
    )


# ----------------------------------------------------------
# Evitar que arquivos da pasta databases_juntos
# sejam considerados na consolidação
# ----------------------------------------------------------

arquivos_csv = [
    arquivo
    for arquivo in arquivos_csv
    if PASTA_JUNTOS not in arquivo.parents
]


# ==========================================================
# 3. VERIFICAR SE EXISTEM ARQUIVOS
# ==========================================================

if not arquivos_csv:

    print("\nNenhum arquivo CSV foi encontrado.")
    print(
        f"Verifique as pastas:\n"
        f"{PASTA_CENTRO_OESTE}\n"
        f"{PASTA_SUL}"
    )

else:

    print("\n" + "=" * 70)
    print("CONSOLIDAÇÃO DOS DADOS DO INMET")
    print("=" * 70)

    print(
        f"\nQuantidade de arquivos encontrados: "
        f"{len(arquivos_csv):,}"
    )


    # ======================================================
    # 4. IDENTIFICAR TODAS AS COLUNAS
    # ======================================================

    todas_colunas = []

    for arquivo in arquivos_csv:

        try:

            df_temp = pd.read_csv(
                arquivo,
                encoding="utf-8-sig",
                low_memory=False
            )

        except UnicodeDecodeError:

            df_temp = pd.read_csv(
                arquivo,
                encoding="latin1",
                low_memory=False
            )

        for coluna in df_temp.columns:

            if coluna not in todas_colunas:

                todas_colunas.append(coluna)


    print(
        f"\nTotal de colunas encontradas: "
        f"{len(todas_colunas)}"
    )


    # ======================================================
    # 5. PREPARAR ARQUIVO FINAL
    # ======================================================

    # Se já existir um arquivo anterior,
    # ele será substituído.
    if ARQUIVO_FINAL.exists():

        ARQUIVO_FINAL.unlink()

        print(
            "\nArquivo consolidado anterior "
            "foi removido."
        )


    primeira_escrita = True

    total_registros = 0

    arquivos_processados = 0


    # ======================================================
    # 6. PROCESSAR CADA CSV
    # ======================================================

    for numero, arquivo in enumerate(
        arquivos_csv,
        start=1
    ):

        print(
            f"\n[{numero}/{len(arquivos_csv)}] "
            f"{arquivo}"
        )


        # --------------------------------------------------
        # Ler arquivo
        # --------------------------------------------------

        try:

            df = pd.read_csv(
                arquivo,
                encoding="utf-8-sig",
                low_memory=False
            )

        except UnicodeDecodeError:

            df = pd.read_csv(
                arquivo,
                encoding="latin1",
                low_memory=False
            )


        quantidade_registros = len(df)


        # --------------------------------------------------
        # Garantir que todas as colunas existam
        # --------------------------------------------------

        for coluna in todas_colunas:

            if coluna not in df.columns:

                df[coluna] = pd.NA


        # --------------------------------------------------
        # Organizar as colunas
        # --------------------------------------------------

        df = df[todas_colunas]


        # --------------------------------------------------
        # Registrar origem do dado
        # --------------------------------------------------

        df["arquivo_origem"] = arquivo.name


        # --------------------------------------------------
        # Adicionar ao arquivo final
        # --------------------------------------------------

        if primeira_escrita:

            df.to_csv(
                ARQUIVO_FINAL,
                index=False,
                encoding="utf-8-sig"
            )

            primeira_escrita = False

        else:

            df.to_csv(
                ARQUIVO_FINAL,
                mode="a",
                header=False,
                index=False,
                encoding="utf-8-sig"
            )


        # --------------------------------------------------
        # Contadores
        # --------------------------------------------------

        total_registros += quantidade_registros

        arquivos_processados += 1


        print(
            f"    Registros adicionados: "
            f"{quantidade_registros:,}"
        )


    # ======================================================
    # 7. CONFERÊNCIA DO ARQUIVO FINAL
    # ======================================================

    print("\n" + "=" * 70)
    print("CONSOLIDAÇÃO CONCLUÍDA")
    print("=" * 70)

    print(
        f"\nArquivos encontrados: "
        f"{len(arquivos_csv):,}"
    )

    print(
        f"Arquivos processados: "
        f"{arquivos_processados:,}"
    )

    print(
        f"Total de registros adicionados: "
        f"{total_registros:,}"
    )

    print(
        f"\nArquivo final:"
    )

    print(ARQUIVO_FINAL)

    print(
        "\nNenhum registro foi removido."
    )

    print(
        "Nenhum duplicado foi excluído."
    )

    print(
        "\nConsolidação finalizada com sucesso!"
    )