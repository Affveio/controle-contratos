import pandas as pd

file_path = r'c:\Users\Obra 369\Desktop\Planilha contrato\Contratos.xlsx'
xl = pd.ExcelFile(file_path)

for sheet in xl.sheet_names:
    temp_df = xl.parse(sheet, nrows=5)
    if any('OBRA' in str(c).upper() for c in temp_df.columns):
        df = xl.parse(sheet)
        break

df_a369 = df[df['OBRA'] == 'A369'].copy()

fev26_col = None
jan26_col = None

for c in df_a369.columns:
    clean = str(c).replace('\n', '').strip().upper()
    if 'FEV' in clean and '26' in clean:
        fev26_col = c
    if 'JAN' in clean and '26' in clean:
        jan26_col = c

print(f"Found FEV/26: {fev26_col}")
print(f"Found JAN/26: {jan26_col}")

if fev26_col and jan26_col:
    df_a369[fev26_col] = pd.to_numeric(df_a369[fev26_col], errors='coerce').fillna(0)
    df_a369[jan26_col] = pd.to_numeric(df_a369[jan26_col], errors='coerce').fillna(0)
    
    delta_fev = df_a369[fev26_col] - df_a369[jan26_col]
    positive_deltas = delta_fev[delta_fev > 0]
    
    print(f"Total delta for FEV/26 (FEV26 - JAN26) = {delta_fev.sum():,.2f}")
    print(f"Number of contracts with positive Medição in FEV/26: {len(positive_deltas)}")
    if len(positive_deltas) > 0:
        for idx in positive_deltas.index:
             name = df_a369.loc[idx, 'SUBCONTRATADO']
             print(f" - {name}: {positive_deltas[idx]:,.2f}")
else:
    print("Could not find both columns.")
