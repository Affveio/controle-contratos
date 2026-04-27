import pandas as pd
from itertools import combinations

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

for c in df_a369.columns:
    clean = str(c).replace('\n', '').strip().upper()
    if 'MAR' in clean and '25' in clean:
        mar25_col = c
    if 'FEV' in clean and '25' in clean:
        fev25_col = c

df_a369[mar25_col] = pd.to_numeric(df_a369[mar25_col], errors='coerce').fillna(0)
df_a369[fev25_col] = pd.to_numeric(df_a369[fev25_col], errors='coerce').fillna(0)

# Real monthly production is Mar - Fev
df_a369['RealMedidoMar'] = df_a369[mar25_col] - df_a369[fev25_col]
df_a369['VALOR DO CONTRATO'] = pd.to_numeric(df_a369['VALOR DO CONTRATO'], errors='coerce').fillna(0)

target_start = pd.to_datetime('2025-03-01')
target_end = pd.to_datetime('2025-03-31')

active_mar = df_a369[
    (df_a369['INICIO_CONTRATO'] <= target_end) & 
    (df_a369['TERMINO_CONTRATO'] >= target_start)
]

# We are looking for exactly 292,412.10. 
# Let's see if there's a simple subset, or if we can find 292k in 'RealMedidoMar' at all.
valid_rows = active_mar[active_mar['RealMedidoMar'] > 0]
total_real_medido = valid_rows['RealMedidoMar'].sum()
print(f"Total delta Medido (Mar-Fev) for ALL active contracts = {total_real_medido:,.2f}")
print(f"Total Contrato for those = {valid_rows['VALOR DO CONTRATO'].sum():,.2f}")

# Test combinations of valid_rows to hit 292412.10
target_medido = 292412.10
rows = []
for index, row in valid_rows.iterrows():
    rows.append({
        'sub': row.get('SUBCONTRATADO', 'Sem Nome'),
        'med': round(row['RealMedidoMar'], 2),
        'con': round(row['VALOR DO CONTRATO'], 2)
    })

print(f"Testing {len(rows)} active contracts delta for 292k...")
found = False
for r in range(1, len(rows) + 1):
    for sub in combinations(rows, r):
        s_med = sum(x['med'] for x in sub)
        if abs(s_med - target_medido) < 0.10:
            s_con = sum(x['con'] for x in sub)
            print(f"MATCH FOUND! Medido: {s_med}, Contrato: {s_con}")
            for x in sub:
                 print(f" - {x['sub']} (Med: {x['med']})")
            found = True
            break
    if found: break

if not found:
    print("No combination of deltas matches 292k.")

