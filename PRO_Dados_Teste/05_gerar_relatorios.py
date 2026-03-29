import pandas as pd
from sqlalchemy import text
from models import get_engine

engine = get_engine()

# Queries Corrigidas (Singular e sem erros de sintaxe)
SQL_MENOR = """
SELECT categoria, quantidade_necessaria, produto, preco_unitario, preco_por_kg FROM (
    SELECT c.nome AS categoria, c.quantidade_necessaria, p.nome AS produto, p.preco AS preco_unitario, p.preco_por_kg,
    ROW_NUMBER() OVER (PARTITION BY c.id ORDER BY p.preco_por_kg ASC) AS rn
    FROM categoria c JOIN produto p ON p.categoria_id = c.id WHERE c.complemento = 0
) WHERE rn = 1; """

SQL_MAIOR = """
SELECT categoria, quantidade_necessaria, produto, preco_unitario, preco_por_kg FROM (
    SELECT c.nome AS categoria, c.quantidade_necessaria, p.nome AS produto, p.preco AS preco_unitario, p.preco_por_kg,
    ROW_NUMBER() OVER (PARTITION BY c.id ORDER BY p.preco_por_kg DESC) AS rn
    FROM categoria c JOIN produto p ON p.categoria_id = c.id WHERE c.complemento = 0
) WHERE rn = 1; """

def calcular_deflacao(valor_atual, df_ipca):
    # Lógica de IPCA acumulado anual (Produtório)
    df_ipca['ano'] = pd.to_datetime(df_ipca['data']).dt.year
    inflacao_anual = df_ipca.groupby('ano')['valor'].apply(lambda x: (1 + x/100).prod())
    
    resultados = {2025: valor_atual}
    valor_loop = valor_atual
    for ano in sorted(inflacao_anual.index, reverse=True):
        valor_loop /= inflacao_anual[ano]
        resultados[ano-1] = valor_loop
    return resultados

def exibir():
    with engine.connect() as conn:
        df_min = pd.read_sql(text(SQL_MENOR), conn)
        df_max = pd.read_sql(text(SQL_MAIOR), conn)
        df_ipca = pd.read_sql(text("SELECT * FROM ipca"), conn)

    if df_min.empty: return print("Execute o carregamento primeiro.")

    total_min = (df_min['preco_por_kg'] * df_min['quantidade_necessaria']).sum()
    total_max = (df_max['preco_por_kg'] * df_max['quantidade_necessaria']).sum()

    print(f"\n🛒 CESTA MENOR: R$ {total_min:.2f} | CESTA MAIOR: R$ {total_max:.2f}")
    
    print("\n📉 HISTÓRICO DEFLACIONADO (Cesta Menor):")
    historico = calcular_deflacao(total_min, df_ipca)
    for ano, val in sorted(historico.items(), reverse=True):
        print(f"Ano {ano}: R$ {val:.2f}")

if __name__ == "__main__":
    exibir()