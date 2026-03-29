"""
05_gerar_relatorios.py
Relatórios da cesta básica com dados reais do Giassi + IPCA do Banco Central.

Relatórios gerados:
  1. Cesta básica de MENOR valor (5 itens)
  2. Cesta básica de MENOR valor + complemento (8 itens)
  3. Cesta básica de MAIOR valor (5 itens)
  4. Cesta básica de MAIOR valor + complemento (8 itens)
  5. Progressão histórica estimada por deflação IPCA (2016–atual)
"""

import pandas as pd
from sqlalchemy import text
from models import get_engine

engine = get_engine()

# ─────────────────────────────────────────────
# QUERIES SQL
# ─────────────────────────────────────────────

SQL_CESTA_MENOR = """
SELECT
    c.nome            AS categoria,
    c.quantidade_necessaria,
    c.unidade,
    p.nome            AS produto,
    p.marca,
    p.preco           AS preco_unitario,
    p.unidade_volume,
    p.preco_por_kg,
    ROUND(c.quantidade_necessaria / CAST(REPLACE(p.unidade_volume, 'kg', '') AS REAL), 0) AS unidades_necessarias,
    p.url
FROM (
    SELECT p2.*, ROW_NUMBER() OVER (PARTITION BY p2.categoria_id ORDER BY p2.preco_por_kg ASC) AS rn
    FROM produto p2
    WHERE p2.preco_por_kg > 0 AND p2.preco > 0
) p
JOIN categoria c ON p.categoria_id = c.id
WHERE p.rn = 1 AND c.complemento = 0
ORDER BY c.nome;
"""

SQL_CESTA_MAIOR = """
SELECT
    c.nome            AS categoria,
    c.quantidade_necessaria,
    c.unidade,
    p.nome            AS produto,
    p.marca,
    p.preco           AS preco_unitario,
    p.unidade_volume,
    p.preco_por_kg,
    ROUND(c.quantidade_necessaria / CAST(REPLACE(p.unidade_volume, 'kg', '') AS REAL), 0) AS unidades_necessarias,
    p.url
FROM (
    SELECT p2.*, ROW_NUMBER() OVER (PARTITION BY p2.categoria_id ORDER BY p2.preco_por_kg DESC) AS rn
    FROM produto p2
    WHERE p2.preco_por_kg > 0 AND p2.preco > 0
) p
JOIN categoria c ON p.categoria_id = c.id
WHERE p.rn = 1 AND c.complemento = 0
ORDER BY c.nome;
"""

SQL_COMPLEMENTO_MENOR = """
SELECT
    c.nome AS categoria, c.quantidade_necessaria, c.unidade,
    p.nome AS produto, p.marca, p.preco AS preco_unitario,
    p.unidade_volume, p.preco_por_kg
FROM (
    SELECT p2.*, ROW_NUMBER() OVER (PARTITION BY p2.categoria_id ORDER BY p2.preco_por_kg ASC) AS rn
    FROM produto p2
    WHERE p2.preco_por_kg > 0 AND p2.preco > 0
) p
JOIN categoria c ON p.categoria_id = c.id
WHERE p.rn = 1 AND c.complemento = 1
ORDER BY c.nome;
"""

SQL_COMPLEMENTO_MAIOR = """
SELECT
    c.nome AS categoria, c.quantidade_necessaria, c.unidade,
    p.nome AS produto, p.marca, p.preco AS preco_unitario,
    p.unidade_volume, p.preco_por_kg
FROM (
    SELECT p2.*, ROW_NUMBER() OVER (PARTITION BY p2.categoria_id ORDER BY p2.preco_por_kg DESC) AS rn
    FROM produto p2
    WHERE p2.preco_por_kg > 0 AND p2.preco > 0
) p
JOIN categoria c ON p.categoria_id = c.id
WHERE p.rn = 1 AND c.complemento = 1
ORDER BY c.nome;
"""

SQL_IPCA = """
SELECT strftime('%Y', data) AS ano, data, valor
FROM ipca
ORDER BY data;
"""

# ─────────────────────────────────────────────
# FUNÇÕES AUXILIARES
# ─────────────────────────────────────────────

def calcular_total(df: pd.DataFrame) -> float:
    total = 0.0
    for _, row in df.iterrows():
        ref = row.get("preco_por_kg") or row.get("preco_unitario") or 0
        total += float(ref) * float(row["quantidade_necessaria"])
    return round(total, 2)


def calcular_acumulado_anual(df_ipca: pd.DataFrame) -> dict[int, float]:
    """Juros compostos mensais → IPCA acumulado por ano."""
    df_ipca["ano"] = pd.to_datetime(df_ipca["data"]).dt.year
    acumulado = {}
    for ano, grupo in df_ipca.groupby("ano"):
        fator = 1.0
        for v in grupo["valor"]:
            fator *= (1 + float(v) / 100)
        acumulado[int(ano)] = round((fator - 1) * 100, 4)
    return acumulado


def deflacionar(valor_atual: float, acumulado: dict, ano_base: int, ano_min: int = 2016) -> dict:
    """
    Estima o valor da cesta nos anos anteriores usando deflação.
    valor_passado = valor_atual / ∏(1 + ipca_ano/100) para anos > ano_passado
    Só retorna anos >= ano_min.
    """
    anos = sorted([a for a in acumulado if a >= ano_min and a < ano_base], reverse=True)
    resultado = {ano_base: round(valor_atual, 2)}
    v = valor_atual
    for ano in anos:
        v = v / (1 + acumulado[ano] / 100)
        resultado[ano] = round(v, 2)
    return resultado


def linha(char="─", n=70):
    print(char * n)


def titulo(txt):
    print()
    linha("═")
    print(f"  {txt}")
    linha("═")


def imprimir_tabela_cesta(df: pd.DataFrame):
    """Imprime os itens da cesta de forma legível."""
    linha()
    print(f"  {'CATEGORIA':<15} {'PRODUTO':<45} {'PREÇO UN.':>10} {'QTD':>6} {'TOTAL':>10}")
    linha()
    for _, row in df.iterrows():
        qtd_ref = float(row.get("quantidade_necessaria", 1))
        preco_ref = float(row.get("preco_por_kg") or row.get("preco_unitario") or 0)
        total_item = round(preco_ref * qtd_ref, 2)
        vol = row.get("unidade_volume") or "—"
        produto_curto = str(row["produto"])[:44]
        print(
            f"  {str(row['categoria']):<15} {produto_curto:<45} "
            f"R${row['preco_unitario']:>8.2f} {vol:>6}  R${total_item:>8.2f}"
        )
    linha()


def imprimir_resumo(total_basica: float, total_comp: float):
    print(f"  💰 Cesta Básica (5 itens):              R$ {total_basica:>8.2f}")
    print(f"  ➕ Complemento (3 itens adicionais):    R$ {total_comp:>8.2f}")
    print(f"  🛒 Cesta Completa (8 itens):            R$ {total_basica + total_comp:>8.2f}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    with engine.connect() as conn:
        df_menor    = pd.read_sql(text(SQL_CESTA_MENOR),       conn)
        df_maior    = pd.read_sql(text(SQL_CESTA_MAIOR),       conn)
        df_comp_min = pd.read_sql(text(SQL_COMPLEMENTO_MENOR), conn)
        df_comp_max = pd.read_sql(text(SQL_COMPLEMENTO_MAIOR), conn)
        df_ipca     = pd.read_sql(text(SQL_IPCA),              conn)

    if df_menor.empty:
        print("⚠️  Nenhum produto no banco. Rode 04_carregar_produtos.py primeiro.")
        return

    total_menor = calcular_total(df_menor)
    total_maior = calcular_total(df_maior)
    total_comp_min = calcular_total(df_comp_min)
    total_comp_max = calcular_total(df_comp_max)

    # ── RELATÓRIO 1: Cesta Menor ──────────────────────────────
    titulo("RELATÓRIO 1 — CESTA BÁSICA DE MENOR VALOR (5 itens)")
    imprimir_tabela_cesta(df_menor)
    print(f"\n  💰 Total Cesta Básica: R$ {total_menor:.2f}\n")

    # ── RELATÓRIO 2: Cesta Menor + Complemento ────────────────
    titulo("RELATÓRIO 2 — CESTA MENOR + COMPLEMENTO (8 itens)")
    print("\n  [ Cesta Básica ]")
    imprimir_tabela_cesta(df_menor)
    print("\n  [ Complemento ]")
    imprimir_tabela_cesta(df_comp_min)
    print()
    imprimir_resumo(total_menor, total_comp_min)

    # ── RELATÓRIO 3: Cesta Maior ──────────────────────────────
    titulo("RELATÓRIO 3 — CESTA BÁSICA DE MAIOR VALOR (5 itens)")
    imprimir_tabela_cesta(df_maior)
    print(f"\n  💰 Total Cesta Básica: R$ {total_maior:.2f}\n")

    # ── RELATÓRIO 4: Cesta Maior + Complemento ────────────────
    titulo("RELATÓRIO 4 — CESTA MAIOR + COMPLEMENTO (8 itens)")
    print("\n  [ Cesta Básica ]")
    imprimir_tabela_cesta(df_maior)
    print("\n  [ Complemento ]")
    imprimir_tabela_cesta(df_comp_max)
    print()
    imprimir_resumo(total_maior, total_comp_max)

    # ── RELATÓRIO 5: Deflação IPCA (2016 → atual) ─────────────
    titulo("RELATÓRIO 5 — PROGRESSÃO HISTÓRICA ESTIMADA (Deflação IPCA 2016–2024)")

    if df_ipca.empty:
        print("⚠️  Sem dados de IPCA. Rode 02_coletar_ipca.py primeiro.")
    else:
        acumulado = calcular_acumulado_anual(df_ipca)
        ano_base  = max(acumulado.keys())

        hist_menor      = deflacionar(total_menor,               acumulado, ano_base, ano_min=2016)
        hist_maior      = deflacionar(total_maior,               acumulado, ano_base, ano_min=2016)
        hist_menor_comp = deflacionar(total_menor + total_comp_min, acumulado, ano_base, ano_min=2016)
        hist_maior_comp = deflacionar(total_maior + total_comp_max, acumulado, ano_base, ano_min=2016)

        print()
        linha()
        print(
            f"  {'Ano':<6} {'IPCA':>8}  "
            f"{'Cesta Menor':>13} {'C.Menor+Comp':>14}  "
            f"{'Cesta Maior':>13} {'C.Maior+Comp':>14}"
        )
        linha()
        for ano in sorted(hist_menor.keys()):
            ipca_str = f"{acumulado.get(ano, 0):.2f}%" if ano in acumulado else "  —   "
            print(
                f"  {ano:<6} {ipca_str:>8}  "
                f"R$ {hist_menor[ano]:>10.2f}  R$ {hist_menor_comp[ano]:>11.2f}  "
                f"R$ {hist_maior[ano]:>10.2f}  R$ {hist_maior_comp[ano]:>11.2f}"
            )
        linha()
        print(f"\n  * Ano base ({ano_base}): preços atuais coletados no Giassi")
        print(f"  * Deflação aplicada: valor_ano = valor_{ano_base} ÷ ∏(1 + IPCA_ano/100)\n")




if __name__ == "__main__":
    main()