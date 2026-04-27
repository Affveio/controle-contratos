import pandas as pd

file_path = r'c:\Users\Obra 369\Desktop\Planilha contrato\Contratos.xlsx'
xl = pd.ExcelFile(file_path)

for sheet in xl.sheet_names:
    temp_df = xl.parse(sheet, nrows=5)
    if any('OBRA' in str(c).upper() for c in temp_df.columns):
        df = xl.parse(sheet)
        break

df_a369 = df[df['OBRA'] == 'A369'].copy()

# Find dates
for c in df_a369.columns:
    if 'RMINO' in str(c).upper() and 'CONTRATO' in str(c).upper():
        termino_col = c
        break
    elif 'MINO DE CONTRATO' in str(c).upper():
        termino_col = c
        break

df_a369[termino_col] = pd.to_datetime(df_a369[termino_col], errors='coerce')

fev26_col = None
jan26_col = None

for c in df_a369.columns:
    clean = str(c).replace('\n', '').strip().upper()
    if 'FEV' in clean and '26' in clean:
        fev26_col = c
    if 'JAN' in clean and '26' in clean:
        jan26_col = c

df_a369[fev26_col] = pd.to_numeric(df_a369[fev26_col], errors='coerce').fillna(0)
df_a369[jan26_col] = pd.to_numeric(df_a369[jan26_col], errors='coerce').fillna(0)

delta_fev = df_a369[fev26_col] - df_a369[jan26_col]
positive_deltas = delta_fev[delta_fev > 0]

print(f"Contracts with positive FEV/26 Delta:")
for idx in positive_deltas.index:
    name = df_a369.loc[idx, 'SUBCONTRATADO']
    termino = df_a369.loc[idx, termino_col]
    val = positive_deltas[idx]
    print(f" - {name}: Delta {val:,.2f} | Termino: {termino}")
