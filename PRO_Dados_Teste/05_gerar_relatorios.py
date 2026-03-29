"""
05_gerar_relatorios.py
Gera os 3 relatórios exigidos pelo desafio.
"""

import pandas as pd
from sqlalchemy import text

from models import get_engine

engine = get_engine()

SQL_MENOR_CESTA = """
SELECT categoria, quantidade_necessaria, unidade, produto, marca, preco_unitario, unidade_volume, preco_por_kg, url
FROM (
    SELECT
        c.nome AS categoria, c.quantidade_necessaria, c.unidade,
        p.nome AS produto, p.marca, p.preco AS preco_unitario,
        p.unidade_volume, p.preco_por_kg, p.url,
        ROW_NUMBER() OVER (
            PARTITION BY c.nome ORDER BY p.preco_por_kg ASC
        ) AS rn
    FROM categorias AS c 
    INNER JOIN produtos AS p ON p.categoria_id = c.id
    WHERE c.complemento = 0
) AS ranked
WHERE rn = 1 
ORDER BY categoria;
"""

SQL_MAIOR_CESTA = """
SELECT categoria, quantidade_necessaria, unidade, produto, marca, preco_unitario, unidade_volume, preco_por_kg, url
FROM (
    SELECT
        c.nome AS categoria, c.quantidade_necessaria, c.unidade,
        p.nome AS produto, p.marca, p.preco AS preco_unitario,
        p.unidade_volume, p.preco_por_kg, p.url,
        ROW_NUMBER() OVER (
            PARTITION BY c.nome ORDER BY p.preco_por_kg DESC
        ) AS rn
    FROM categorias AS c 
    INNER JOIN produtos AS p ON p.categoria_id = c.id
    WHERE c.complemento = 0
) AS ranked
WHERE rn = 1 
ORDER BY categoria;
"""

SQL_COMPLEMENTO_MENOR = """
SELECT * FROM (
    SELECT c.nome AS categoria, c.quantidade_necessaria, c.unidade,
           p.nome AS produto, p.marca, p.preco AS preco_unitario,
           p.unidade_volume, p.preco_por_kg,
           ROW_NUMBER() OVER (PARTITION BY c.id ORDER BY p.preco_por_kg ASC) AS rn
    FROM categorias c JOIN produtos p ON p.categoria_id = c.id WHERE c.complemento = 1
) WHERE rn = 1 ORDER BY categoria;
"""

SQL_COMPLEMENTO_MAIOR = """
SELECT * FROM (
    SELECT c.nome AS categoria, c.quantidade_necessaria, c.unidade,
           p.nome AS produto, p.marca, p.preco AS preco_unitario,
           p.unidade_volume, p.preco_por_kg,
           ROW_NUMBER() OVER (PARTITION BY c.id ORDER BY p.preco_por_kg DESC) AS rn
    FROM categorias c JOIN produtos p ON p.categoria_id = c.id WHERE c.complemento = 1
) WHERE rn = 1 ORDER BY categoria;
"""

SQL_IPCA = """
SELECT strftime('%Y', data) AS ano, data, valor
FROM ipca ORDER BY data;
"""


def calcular_total(df: pd.DataFrame) -> float:
    total = 0.0
    for _, row in df.iterrows():
        ref = row.get("preco_por_kg") or row.get("preco_unitario", 0)
        total += (ref or 0) * row["quantidade_necessaria"]
    return round(total, 2)


def calcular_acumulado(df_ipca: pd.DataFrame) -> dict[int, float]:
    from itertools import groupby
    df_ipca["ano"] = df_ipca["ano"].astype(int)
    acumulado = {}
    for ano, grupo in df_ipca.groupby("ano"):
        fator = 1.0
        for v in grupo["valor"]:
            fator *= (1 + float(v) / 100)
        acumulado[ano] = round((fator - 1) * 100, 4)
    return acumulado


def deflacionar(valor: float, acumulado: dict, ano_base: int) -> dict[int, float]:
    anos = sorted([a for a in acumulado if a < ano_base], reverse=True)
    resultado = {ano_base: round(valor, 2)}
    v = valor
    for ano in anos:
        v = v / (1 + acumulado[ano] / 100)
        resultado[ano] = round(v, 2)
    return resultado


def sep(titulo: str):
    print("\n" + "=" * 65)
    print(f"  {titulo}")
    print("=" * 65)


def relatorio_cesta(label, sql_cesta, sql_comp):
    sep(label)
    with engine.connect() as conn:
        df = pd.read_sql(text(sql_cesta), conn)
        df_comp = pd.read_sql(text(sql_comp), conn)

    if df.empty:
        print("⚠️  Nenhum produto encontrado. Execute o scraper primeiro.")
        return 0.0

    print(df[["categoria", "produto", "marca", "preco_unitario", "unidade_volume", "quantidade_necessaria"]].to_string(index=False))
    total_b = calcular_total(df)
    total_c = calcular_total(df_comp)
    print(f"\n💰 Cesta Básica:               R$ {total_b:.2f}")
    print(f"➕ Complemento:                R$ {total_c:.2f}")
    print(f"🛒 Cesta Básica + Complemento: R$ {total_b + total_c:.2f}")
    return total_b


def relatorio_ipca(valor_menor: float, valor_maior: float):
    sep("RELATÓRIO 3 — Progressão Anual Estimada (Deflação IPCA)")
    with engine.connect() as conn:
        df_ipca = pd.read_sql(text(SQL_IPCA), conn)

    if df_ipca.empty:
        print("⚠️  Sem dados de IPCA. Execute 02_coletar_ipca.py primeiro.")
        return

    acumulado = calcular_acumulado(df_ipca)
    ano_base = max(acumulado.keys())
    h_menor = deflacionar(valor_menor, acumulado, ano_base)
    h_maior = deflacionar(valor_maior, acumulado, ano_base)

    print(f"\n{'Ano':<8}{'IPCA Acum.':>14}{'Cesta Menor':>18}{'Cesta Maior':>18}")
    print("-" * 60)
    for ano in sorted(h_menor):
        ipca = f"{acumulado.get(ano, 0):.2f}%" if ano in acumulado else "—"
        print(f"{ano:<8}{ipca:>14}  R$ {h_menor[ano]:>12.2f}  R$ {h_maior[ano]:>12.2f}")


if __name__ == "__main__":
    print("\n🧺 ANÁLISE DA CESTA BÁSICA — Giassi Florianópolis")

    v_menor = relatorio_cesta(
        "RELATÓRIO 1 — Cesta Básica de MENOR Valor",
        SQL_MENOR_CESTA, SQL_COMPLEMENTO_MENOR
    )
    v_maior = relatorio_cesta(
        "RELATÓRIO 2 — Cesta Básica de MAIOR Valor",
        SQL_MAIOR_CESTA, SQL_COMPLEMENTO_MAIOR
    )

    if v_menor > 0 and v_maior > 0:
        relatorio_ipca(v_menor, v_maior)

    print("\n\n📋 SQL — Cesta Menor:\n", SQL_MENOR_CESTA)
    print("📋 SQL — Cesta Maior:\n", SQL_MAIOR_CESTA)
    print("📋 SQL — IPCA:\n", SQL_IPCA)
