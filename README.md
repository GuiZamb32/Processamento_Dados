# Cesta Básica — Pipeline de Dados
**Avaliação Prática · BI e Data Visualization · UniSENAI SC**

## Visão Geral

Este projeto implementa um pipeline completo de dados para análise do custo de uma cesta básica, integrando:

- Coleta de dados econômicos (IPCA) via API pública
- Web scraping de produtos de supermercado
- Persistência em banco de dados relacional
- Processamento e geração de relatórios analíticos

O objetivo é simular um fluxo real de engenharia de dados, desde a ingestão até a análise.

---

## Arquitetura do Projeto

```
cesta_basica/
├── scripts/
│   ├── 01_criar_banco.py
│   ├── 02_coletar_ipca.py
│   ├── 03_scraping_giassi.py
│   ├── 04_carregar_produtos.py
│   └── 05_relatorios.py
├── models.py
├── relatorios/
├── cache/
├── requirements.txt
└── README.md
```

---

## Tecnologias Utilizadas

- Python 3.x
- SQLite
- SQLAlchemy
- Scrapy
- Requests

---

## Pipeline de Execução

### 1. Criação do banco de dados

```bash
python scripts/01_criar_banco.py
```

---

### 2. Coleta de dados do IPCA

```bash
python scripts/02_coletar_ipca.py
```

---

### 3. Web Scraping de produtos

```bash
scrapy runspider scripts/03_scraping_giassi.py -o relatorios/produtos_raw.json
```

---

### 4. Carga de dados no banco

```bash
python scripts/04_carregar_produtos.py
```

---

### 5. Geração de relatórios

```bash
python scripts/05_relatorios.py
```

---

## Modelagem de Dados

### Tabela: ipca

- id (INTEGER)
- data (DATE)
- valor (FLOAT)

### Tabela: categoria

- id (INTEGER)
- nome (TEXT)
- quantidade_cesta (FLOAT)
- unidade_cesta (TEXT)
- bonus (INTEGER)

### Tabela: produto

- id (INTEGER)
- categoria_id (INTEGER)
- nome (TEXT)
- marca (TEXT)
- preco (FLOAT)
- preco_kg (FLOAT)
- quantidade (FLOAT)
- unidade (TEXT)
- url (TEXT)
- data_coleta (DATE)

---

## Lógica de Deflação

valor_passado = valor_atual / fator_acumulado_ipca

---

## Melhorias Futuras

- Docker
- Airflow
- PostgreSQL
- Dashboard (Power BI / Streamlit)

---

## Objetivo

Projeto acadêmico focado em engenharia de dados, integração de APIs, scraping e análise de dados.
