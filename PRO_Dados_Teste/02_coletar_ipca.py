"""
02_coletar_ipca.py
Consulta a API do Banco Central (SGS 433) e salva a série histórica do IPCA no banco.
"""

import requests
from datetime import datetime
from itertools import groupby
from sqlalchemy.orm import Session

from models import IPCA, criar_banco, get_engine

BCB_API_URL = (
    "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados"
    "?formato=json&dataInicial=01/01/2015&dataFinal=31/12/2024"
)


def fetch_ipca() -> list[dict]:
    print("🌐 Consultando API do Banco Central...")
    response = requests.get(BCB_API_URL, timeout=30)
    response.raise_for_status()
    dados = response.json()
    print(f"   → {len(dados)} registros recebidos.")
    return dados


def salvar_ipca(dados: list[dict]) -> None:
    engine = get_engine()
    novos = 0
    duplicatas = 0

    with Session(engine) as session:
        for item in dados:
            data_ref = datetime.strptime(item["data"], "%d/%m/%Y").date()
            valor = float(item["valor"].replace(",", "."))

            if session.query(IPCA).filter_by(data=data_ref).first():
                duplicatas += 1
                continue

            session.add(IPCA(data=data_ref, valor=valor))
            novos += 1

        session.commit()

    print(f"✅ IPCA salvo: {novos} novos registros, {duplicatas} já existiam.")


def calcular_ipca_acumulado_anual() -> dict[int, float]:
    engine = get_engine()
    acumulado: dict[int, float] = {}

    with Session(engine) as session:
        registros = session.query(IPCA).order_by(IPCA.data).all()

    for ano, meses in groupby(registros, key=lambda r: r.data.year):
        fator = 1.0
        for mes in meses:
            fator *= (1 + mes.valor / 100)
        acumulado[ano] = round((fator - 1) * 100, 4)

    return acumulado


if __name__ == "__main__":
    criar_banco()
    dados = fetch_ipca()
    salvar_ipca(dados)

    print("\n📊 IPCA Acumulado Anual:")
    for ano, taxa in sorted(calcular_ipca_acumulado_anual().items()):
        print(f"   {ano}: {taxa:.2f}%")
