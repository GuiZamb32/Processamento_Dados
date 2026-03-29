#  Pipeline de Dados — Cesta Básica

**Avaliação Prática · BI e Data Visualization · UniSENAI SC 2025/1**

Pipeline completo de engenharia de dados para análise do custo da cesta básica em Florianópolis, integrando coleta de dados econômicos via API pública, web scraping de supermercado, persistência em banco relacional e geração de relatórios analíticos.

---

## Estrutura do Projeto

```
PRO_Dados_Teste/
├── models.py                  # Modelos SQLAlchemy (tabelas + função de criação do banco)
├── 01_criar_banco.py          # Cria o schema SQLite e popula as categorias
├── 02_coletar_ipca.py         # Consulta API do Banco Central e salva série histórica
├── 03_scraper_giassi.py       # Spider Scrapy — coleta produtos do Giassi
├── 04_carregar_produtos.py    # ETL: carrega produtos_cesta.json no banco
├── 05_gerar_relatorios.py     # Gera os 5 relatórios analíticos
├── cesta_basica.db            # Banco SQLite gerado pelo pipeline
├── produtos_cesta.json        # Saída bruta do scraper
├── cache/                     # Cache HTTP do Scrapy (24h)
└── scrapy-giassi.log          # Log de execução do scraper
```

---

## Tecnologias

| Biblioteca     | Uso                                      |
|----------------|------------------------------------------|
| `sqlalchemy`   | ORM e interação com o banco SQLite       |
| `scrapy`       | Web scraping do site do Giassi           |
| `pandas`       | Processamento e leitura das queries SQL  |
| `requests`     | Consumo da API do Banco Central          |

---

## Instalação

```powershell
py -m pip install scrapy sqlalchemy pandas requests w3lib
```

---

## Execução do Pipeline

Execute os scripts na ordem abaixo a partir da pasta do projeto.

### 1. Criar o banco de dados
Cria as tabelas `ipca`, `categoria` e `produto` no SQLite e insere as 8 categorias da cesta.

```powershell
py 01_criar_banco.py
```

### 2. Coletar série histórica do IPCA
Consulta a API de dados abertos do Banco Central (SGS 433) de 2015 a 2024 e persiste os 120 registros mensais.

```powershell
py 02_coletar_ipca.py
```

### 3. Coletar preços do Giassi (Web Scraping)
Percorre o sitemap do Giassi, filtra apenas produtos das categorias da cesta e salva em `produtos_cesta.json`. Usa cache HTTP de 24h para não sobrecarregar o site.

```powershell
py -m scrapy runspider .\03_scraper_giassi.py
```

> ⚠️ A primeira execução pode levar vários minutos. As seguintes são instantâneas graças ao cache.

### 4. Carregar produtos no banco
Lê o `produtos_cesta.json` e insere os produtos no banco, vinculando cada um à sua categoria.

```powershell
py 04_carregar_produtos.py
```

### 5. Gerar relatórios
Processa os dados e exibe os 5 relatórios no terminal.

```powershell
py 05_gerar_relatorios.py
```

---

## Relatórios Gerados

| # | Relatório |
|---|-----------|
| 1 | Composição da cesta básica de **menor valor** (5 itens) |
| 2 | Cesta de menor valor **com complemento** (8 itens) |
| 3 | Composição da cesta básica de **maior valor** (5 itens) |
| 4 | Cesta de maior valor **com complemento** (8 itens) |
| 5 | Progressão histórica estimada por **deflação IPCA** (2016–2024) |

Cada relatório de cesta exibe: categoria, nome do produto, preço unitário, volume/embalagem e custo total por item. Os totais são apresentados separando cesta básica e complemento.

---

## Modelagem de Dados

```
ipca
├── id          INTEGER  PK
├── data        DATE     UNIQUE   ← primeiro dia do mês de referência
└── valor       FLOAT             ← variação % mensal

categoria
├── id                    INTEGER  PK
├── nome                  TEXT     UNIQUE
├── quantidade_necessaria FLOAT             ← ex: 5 (para 5kg de arroz)
├── unidade               TEXT              ← "kg" ou "L"
└── complemento           INTEGER           ← 0 = cesta básica | 1 = complemento

produto
├── id             INTEGER  PK
├── categoria_id   INTEGER  FK → categoria
├── nome           TEXT
├── marca          TEXT
├── preco          FLOAT
├── unidade_volume TEXT              ← ex: "1.0kg", "0.9L"
├── preco_por_kg   FLOAT             ← preço normalizado para comparação
└── url            TEXT
```

---

## Lógica de Deflação Histórica

Com base nos preços atuais coletados no Giassi, o Relatório 5 estima quanto a cesta teria custado em anos anteriores usando deflação:

```
valor_ano_passado = valor_atual ÷ ∏(1 + IPCA_ano / 100)
```

O IPCA acumulado anual é calculado pelo produto dos fatores mensais (juros compostos):

```
ipca_acumulado_ano = ∏(1 + taxa_mensal / 100) − 1
```

---

## Fontes de Dados

- **IPCA**: [API de Dados Abertos — Banco Central do Brasil (SGS 433)](https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados?formato=json)
- **Preços**: [Giassi Supermercados — Florianópolis/SC](https://www.giassi.com.br)
