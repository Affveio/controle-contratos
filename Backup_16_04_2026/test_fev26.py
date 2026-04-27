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

# Find fev26 col
fev26_col = None
for c in df_a369.columns:
    clean = str(c).replace('\n', '').strip().upper()
    if 'FEV' in clean and '26' in clean:
        fev26_col = c

if fev26_col:
    df_a369[fev26_col] = pd.to_numeric(df_a369[fev26_col], errors='coerce').fillna(0)
    df_a369['VALOR DO CONTRATO'] = pd.to_numeric(df_a369['VALOR DO CONTRATO'], errors='coerce').fillna(0)

    # 1. Active during FEV/26
    target_start = pd.to_datetime('2026-02-01')
    target_end = pd.to_datetime('2026-02-28')

    active_fev = df_a369[
        (df_a369['INICIO_CONTRATO'] <= target_end) & 
        (df_a369['TERMINO_CONTRATO'] >= target_start)
    ]
    print(f"Active in FEV/26: Medido={active_fev[fev26_col].sum():,.2f}, Contrato={active_fev['VALOR DO CONTRATO'].sum():,.2f}")

    # 2. Started in FEV/26
    started_fev = df_a369[
        (df_a369['INICIO_CONTRATO'].dt.month == 2) & 
        (df_a369['INICIO_CONTRATO'].dt.year == 2026)
    ]
    print(f"Started in FEV/26: Medido={started_fev[fev26_col].sum():,.2f}, Contrato={started_fev['VALOR DO CONTRATO'].sum():,.2f}")

    # 3. Has Medicao in FEV/26
    has_med_fev = df_a369[df_a369[fev26_col] > 0]
    print(f"Has Medido in FEV/26: Medido={has_med_fev[fev26_col].sum():,.2f}, Contrato={has_med_fev['VALOR DO CONTRATO'].sum():,.2f}")
else:
    print("FEV/26 col not found.")
