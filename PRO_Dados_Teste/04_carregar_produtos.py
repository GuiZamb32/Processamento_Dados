"""
04_carregar_produtos.py
Lê produtos_cesta.json gerado pelo spider e persiste no banco SQLite.
"""

import json
import os
from sqlalchemy.orm import Session
from models import Categoria, Produto, criar_banco, get_engine

def carregar_produtos(caminho_json: str = "produtos_cesta.json") -> None:
    # 1. Garante que o banco e as tabelas existam [cite: 52]
    criar_banco()
    engine = get_engine()

    # 2. Verifica se o arquivo de dados existe
    if not os.path.exists(caminho_json):
        print(f"❌ Erro: Arquivo {caminho_json} não encontrado!")
        return

    with open(caminho_json, "r", encoding="utf-8") as f:
        try:
            produtos_raw = json.load(f)
        except json.JSONDecodeError:
            print(f"❌ Erro: O arquivo {caminho_json} está mal formatado ou vazio.")
            return

    novos = 0
    ignorados = 0

    with Session(engine) as session:
        for item in produtos_raw:
            # Validação básica de integridade [cite: 17]
            if not item.get("nome") or not item.get("preco"):
                ignorados += 1
                continue

            # Busca a categoria correspondente para manter a chave estrangeira [cite: 129]
            categoria = session.query(Categoria).filter_by(nome=item["categoria"]).first()
            if not categoria:
                # Se a categoria não existe no banco, não podemos vincular o produto
                ignorados += 1
                continue

            # Evita duplicidade de produtos (limpeza e normalização) [cite: 17]
            existe = session.query(Produto).filter_by(
                nome=item["nome"]
            ).first()
            
            if existe:
                ignorados += 1
                continue

            # Adiciona o novo produto ao banco de dados [cite: 30]
            session.add(Produto(
                categoria_id=categoria.id,
                nome=item["nome"],
                marca=item.get("marca", ""),
                preco=item["preco"],
                unidade_volume=item.get("volume"),  # Alinhado com a saída do Scrapy
                preco_por_kg=item.get("preco_por_kg"),
                url=item.get("url"),
            ))
            novos += 1

        session.commit()

    print(f"✅ Processamento concluído: {novos} novos produtos salvos, {ignorados} ignorados.")

if __name__ == "__main__":
    carregar_produtos()