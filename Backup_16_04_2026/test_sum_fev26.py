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

if fev26_col and jan26_col:
    df_a369[fev26_col] = pd.to_numeric(df_a369[fev26_col], errors='coerce').fillna(0)
    df_a369[jan26_col] = pd.to_numeric(df_a369[jan26_col], errors='coerce').fillna(0)
    
    raw_fev26 = df_a369[fev26_col].sum()
    raw_jan26 = df_a369[jan26_col].sum()
    
    delta_fev = df_a369[fev26_col] - df_a369[jan26_col]
    positive_deltas = delta_fev[delta_fev > 0]
    
    print(f"Soma bruta da coluna {fev26_col}: {raw_fev26:,.2f}")
    print(f"Soma bruta da coluna {jan26_col}: {raw_jan26:,.2f}")
    print(f"Soma dos deltas positivos (Fev26 - Jan26): {positive_deltas.sum():,.2f}")
    print(f"Soma de todos os deltas (Fev26 - Jan26): {delta_fev.sum():,.2f}")

    # Check for specific logic: Fev/26 delta but only for contracts that were billed positively? 
    # Or maybe it's the raw FEV/26 column - Jan/26 column only for subset?
else:
    print("Columns not found.")

