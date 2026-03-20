# Cesta Básica - Pipeline de Dados
**Avaliação Prática · BI e DV · UniSENAI SC · 2025/1**

## Estrutura do Projeto

```
cesta_basica/
├── scripts/
│   ├── 01_criar_banco.py       # Cria o schema SQLite via SQLAlchemy
│   ├── 02_coletar_ipca.py      # Consome API do Banco Central (série 433)
│   ├── 03_scraping_giassi.py   # Spider Scrapy – extrai produtos do Giassi
│   ├── 04_carregar_produtos.py # Carrega JSON do Scrapy → banco de dados
│   └── 05_relatorios.py        # Gera relatórios e estimativas históricas
├── relatorios/                 # CSVs gerados (criado automaticamente)
├── cache/                      # Cache HTTP do Scrapy (criado automaticamente)
├── requirements.txt
└── README.md
```

## Dependências

```
pip install -r requirements.txt
```

## Como Executar (em ordem)

### 1. Criar o banco de dados
```bash
python scripts/01_criar_banco.py
```
Cria `cesta_basica.db` com as tabelas `ipca`, `categoria` e `produto`.

### 2. Coletar série histórica do IPCA
```bash
python scripts/02_coletar_ipca.py
```
Consulta `https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados` e armazena
todos os registros mensais desde janeiro de 2000.

### 3. Executar o web scraping do Giassi
```bash
scrapy runspider scripts/03_scraping_giassi.py -o relatorios/produtos_raw.json
```
> Usa cache HTTP (24 h). Durante o desenvolvimento, o cache evita sobrecarregar
> o site do Giassi. Após validar a lógica de extração, aumente `CONCURRENT_REQUESTS`.

### 4. Carregar produtos no banco
```bash
python scripts/04_carregar_produtos.py
```
Lê `relatorios/produtos_raw.json` e insere os produtos na tabela `produto`.

### 5. Gerar relatórios
```bash
python scripts/05_relatorios.py
```
Gera três arquivos CSV em `relatorios/`:
- `01_cesta_menor.csv` – composição de menor custo
- `02_cesta_maior.csv` – composição de maior custo
- `03_historico_ipca.csv` – estimativa anual via deflação

---

## Descrição das Tabelas

### `ipca`
| Coluna | Tipo    | Descrição                       |
|--------|---------|---------------------------------|
| id     | INTEGER | Chave primária                  |
| data   | DATE    | Data de referência (único)      |
| valor  | FLOAT   | Variação % mensal do IPCA       |

### `categoria`
| Coluna           | Tipo    | Descrição                              |
|------------------|---------|----------------------------------------|
| id               | INTEGER | Chave primária                         |
| nome             | TEXT    | Nome da categoria (único)              |
| quantidade_cesta | FLOAT   | Quantidade exigida na cesta            |
| unidade_cesta    | TEXT    | Unidade (kg, l, g)                     |
| bonus            | INTEGER | 0 = obrigatório / 1 = bônus            |

### `produto`
| Coluna       | Tipo    | Descrição                                  |
|--------------|---------|--------------------------------------------|
| id           | INTEGER | Chave primária                             |
| categoria_id | INTEGER | FK → categoria.id                          |
| nome         | TEXT    | Nome completo do produto                   |
| marca        | TEXT    | Marca do produto                           |
| preco        | FLOAT   | Preço atual (R$)                           |
| preco_kg     | FLOAT   | Preço normalizado por kg ou litro          |
| quantidade   | FLOAT   | Peso/volume da embalagem (em kg ou l)      |
| unidade      | TEXT    | Unidade normalizada (kg ou l)              |
| url          | TEXT    | URL da página do produto                   |
| data_coleta  | DATE    | Data da extração                           |

---

## Lógica de Deflação (Relatório 3)

O enunciado pede o valor estimado nos **anos anteriores**, usando o preço **atual**
como base. Isso é deflação: quanto custaria hoje em dinheiro de um ano passado?

```
valor_ano_X = valor_atual / (fator_IPCA de X até hoje)
```

O fator acumulado é calculado com juros sobre juros (produto dos fatores mensais):

```python
fator_ano = produto de (1 + ipca_mes/100) para cada mês do ano
fator_acumulado *= fator_ano  # acumula de trás para frente no tempo
```

Quanto mais longe do presente, maior o divisor → menor o valor estimado,
refletindo que o poder de compra era maior antes da inflação.

---

## Consultas SQL dos Relatórios

As queries SQL completas estão incorporadas no script `05_relatorios.py`
como strings nas variáveis `SQL_CESTA_MENOR`, `SQL_CESTA_MAIOR` e `SQL_IPCA_ANUAL`.