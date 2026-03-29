import json
import os
from sqlalchemy.orm import Session
from models import Categoria, Produto, criar_banco, get_engine

def carregar_produtos(caminho_json="produtos_cesta.json"):
    # 1. Garante a criação do banco e das tabelas
    criar_banco()
    engine = get_engine()
    
    if not os.path.exists(caminho_json):
        print(f"❌ Arquivo {caminho_json} não encontrado!")
        return

    # 2. Abre o arquivo JSON
    with open(caminho_json, "r", encoding="utf-8") as f:
        try:
            produtos_raw = json.load(f)
        except json.JSONDecodeError:
            print(f"❌ Erro ao ler o JSON em {caminho_json}")
            return

    novos, ignorados = 0, 0
    with Session(engine) as session:
        for item in produtos_raw:
            # CORREÇÃO: Adicionado ':' e removido erro de sintaxe
            if not item.get("nome"):
                ignorados += 1
                continue
            
            # Busca a categoria no banco (deve bater com o nome no JSON)
            categoria = session.query(Categoria).filter_by(nome=item["categoria"]).first()
            
            # Verifica se a categoria existe e se o produto já não foi cadastrado (evitar duplicados)
            if not categoria or session.query(Produto).filter_by(nome=item["nome"]).first():
                ignorados += 1
                continue

            # Adiciona o produto ao banco
            session.add(Produto(
                categoria_id=categoria.id,
                nome=item["nome"],
                marca=item.get("marca", ""),
                preco=item.get("preco", 0.0), # Garante um valor padrão caso falte
                unidade_volume=item.get("volume"),
                preco_por_kg=item.get("preco_por_kg", 0.0),
                url=item.get("url")
            ))
            novos += 1
        
        # Salva as alterações no banco de dados
        session.commit()
        
    print(f"✅ Sucesso: {novos} novos produtos cadastrados, {ignorados} ignorados.")

if __name__ == "__main__":
    carregar_produtos()