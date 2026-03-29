import pandas
import json
from unidecode import unidecode

with open("dias_horarios.json", "r") as file:
    data = json.load(file)


# Normaliza o dataset com relação ao objeto horários, gerando uma linha para cada dia (Dia de Semana ou Domingos e Feriados)
df = pandas.json_normalize(data, record_path=["horarios"], meta=["linha", "itinerario"]) #meta[] mantém as colunas linha e itinerario inalteradas

df["itinerario"] = df["itinerario"].apply(
    lambda x: list(map(lambda y: unidecode(y).strip(), x)) #Normaliza sintaxe das ruas no itinerário, removendo acentos e espaço
)

df["virgilio_varzea"] = df["itinerario"].apply(lambda x: "ROD. VIRGILIO VARZEA" in x) # Busca linhas que passem pela rod. Virgilio Varzea
df["sc_401"] = df["itinerario"].apply(
    lambda x: any(                                                               #Linhas que passam pela SC-401.
        "SC 401" in parada or "SC-401" in parada or "JOSE CARLOS DAUX" in parada # Grafia é diferente para cada linha, pode ter ficado alguma para trás
        for parada in x
    )
)

# "Explode" o dataframe em relação ao horário de partida, gerando uma linha para cada horário
df = df.explode('time')
df = df.reset_index(drop=True)

df['horario_partida'] = pandas.to_datetime(df['time'], format="%H:%M", errors='coerce')
df = df.dropna(subset=['horario_partida'])

# Definição dos parâmetros da heurística
DIAS_EVENTO = ['Sábado', 'Domingos e Feriados']
HORA_MIN_PARTIDA = pandas.to_datetime('10:00', format='%H:%M').time()
HORA_MAX_PARTIDA = pandas.to_datetime('13:00', format='%H:%M').time() # Partida mais tarde

print(f"🔎 Buscando partidas entre {HORA_MIN_PARTIDA} e {HORA_MAX_PARTIDA} nos dias: {DIAS_EVENTO}\n")

# Filtro 1: Relevância do Local
# Seleciona linhas que passam por PELO MENOS um dos locais
df_loc_ok = df.loc[
    (df['sc_401'] == True) | (df['virgilio_varzea'] == True)
]

# Filtro 2: Relevância do Dia
df_dia_ok = df_loc_ok.loc[df_loc_ok['day'].isin(DIAS_EVENTO)]

# Filtro 3: Relevância do Horário (A Janela de Partida)
# Usamos .dt.time para comparar apenas a parte de tempo dos objetos datetime
df_heuristic_results = df_dia_ok.loc[
    (df['horario_partida'].dt.time >= HORA_MIN_PARTIDA) &
    (df['horario_partida'].dt.time <= HORA_MAX_PARTIDA)
]

# --- 3. Análise dos Resultados ---

if df_heuristic_results.empty:
    print("Nenhuma linha encontrada que atenda a todos os critérios da heurística.")
else:
    # Estatística Descritiva: Quais linhas têm mais opções?
    print("--- 📊 Ranking de Linhas (Maior Frequência na Janela) ---")
    
    # Agrupamos para contar quantas partidas CADA linha oferece na janela
    ranking_linhas = df_heuristic_results.groupby(
        ['day', 'linha']
    )['horario_partida'].count().reset_index()
    
    ranking_linhas = ranking_linhas.rename(columns={'horario_partida': 'num_partidas_recomendadas'})
    
    # Ordena para mostrar os dias e, dentro deles, as linhas com mais opções
    print(ranking_linhas.sort_values(by=['day', 'num_partidas_recomendadas'], ascending=[True, False]))
    
    print("\n--- 📋 Detalhe das Partidas Sugeridas ---")
    # Mostra a lista final de ônibus recomendados
    print(df_heuristic_results[
        ['day', 'linha', 'partida', 'time']
    ].sort_values(by=['day', 'time']))