import pandas as pd

file_path = r'c:\Users\Obra 369\Desktop\Planilha contrato\Contratos.xlsx'
xl = pd.ExcelFile(file_path)

for sheet in xl.sheet_names:
    temp_df = xl.parse(sheet, nrows=5)
    if any('OBRA' in str(c).upper() for c in temp_df.columns):
        df = xl.parse(sheet)
        break

df_a369 = df[df['OBRA'] == 'A369'].copy()

# Rename specific columns
col_mapping = {}
for c in df_a369.columns:
    if 'INICIO' in str(c).upper() and 'CONTRATO' in str(c).upper():
        col_mapping[c] = 'INICIO_CONTRATO'
    elif 'RMINO' in str(c).upper() and 'CONTRATO' in str(c).upper():
        col_mapping[c] = 'TERMINO_CONTRATO'
    elif 'MINO DE CONTRATO' in str(c).upper():
        col_mapping[c] = 'TERMINO_CONTRATO'
df_a369.rename(columns=col_mapping, inplace=True)

df_a369['INICIO_CONTRATO'] = pd.to_datetime(df_a369['INICIO_CONTRATO'], errors='coerce')
df_a369['TERMINO_CONTRATO'] = pd.to_datetime(df_a369['TERMINO_CONTRATO'], errors='coerce')

# Find mar25 col
mar25_col = None
for c in df_a369.columns:
    clean = str(c).replace('\n', '').strip().upper()
    if 'MAR' in clean and '25' in clean:
        mar25_col = c

df_a369[mar25_col] = pd.to_numeric(df_a369[mar25_col], errors='coerce').fillna(0)
df_a369['VALOR DO CONTRATO'] = pd.to_numeric(df_a369['VALOR DO CONTRATO'], errors='coerce').fillna(0)

# 1. Filter: Ativo exatamente em Março de 2025
# (Inicio <= Mar/25 and Termino >= Mar/25)
target_start = pd.to_datetime('2025-03-01')
target_end = pd.to_datetime('2025-03-31')

active_march = df_a369[
    (df_a369['INICIO_CONTRATO'].dt.to_period('M') <= target_end.to_period('M')) & 
    (df_a369['TERMINO_CONTRATO'].dt.to_period('M') >= target_start.to_period('M'))
]

sum_medido = active_march[mar25_col].sum()
sum_contrato = active_march['VALOR DO CONTRATO'].sum()

print("Filtro: Ativos puramente durante MAR/25 (considerando mes de inicio/fim):")
print(f"Medido MAR/25: {sum_medido:,.2f}")
print(f"Valor Contrato: {sum_contrato:,.2f}")

# Check with Exact dates
active_march_strict = df_a369[
    (df_a369['INICIO_CONTRATO'] <= target_end) & 
    (df_a369['TERMINO_CONTRATO'] >= target_start)
]

print("\nFiltro Estrito: Dias cruzando Março (<= 31 Mar, >= 01 Mar):")
print(f"Medido MAR/25: {active_march_strict[mar25_col].sum():,.2f}")
print(f"Valor Contrato: {active_march_strict['VALOR DO CONTRATO'].sum():,.2f}")

# Filter out contracts that started before March to see if the user is treating 'MAR/25' as equivalent to only "Novos contratos de Março"
started_in_march = df_a369[
    (df_a369['INICIO_CONTRATO'].dt.month == 3) & 
    (df_a369['INICIO_CONTRATO'].dt.year == 2025)
]

print("\nFiltro: Iniciados estritamente em MAR/25 (Novos Contratos):")
print(f"Medido MAR/25: {started_in_march[mar25_col].sum():,.2f}")
print(f"Valor Contrato: {started_in_march['VALOR DO CONTRATO'].sum():,.2f}")

