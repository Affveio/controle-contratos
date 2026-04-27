import pandas as pd

file_path = r'c:\Users\Obra 369\Desktop\Planilha contrato\Contratos.xlsx'
xl = pd.ExcelFile(file_path)

df = None
for sheet in xl.sheet_names:
    temp_df = xl.parse(sheet, nrows=5)
    if any('OBRA' in str(c).upper() for c in temp_df.columns):
        df = xl.parse(sheet)
        break

df_a369 = df[df['OBRA'] == 'A369'].copy()

# Fix types
mar25_col = [c for c in df_a369.columns if 'MAR' in str(c).upper() and '25' in str(c)][0]
df_a369[mar25_col] = pd.to_numeric(df_a369[mar25_col], errors='coerce').fillna(0)

# All active in MAR/25
d_inicio_col = [c for c in df_a369.columns if 'IN\u00cdCIO' in str(c).upper() or 'INICIO' in str(c).upper()][0]
df_a369['Date_Inicio'] = pd.to_datetime(df_a369[d_inicio_col], errors='coerce')

# Total medido MAR/25 active
active_mar25 = df_a369[(df_a369['Date_Inicio'] <= '2025-03-31')] 
sum_all_mar25 = active_mar25[mar25_col].sum()

print(f"Soma MEDIDO MAR/25 (Todos os contratos ativos até final de março): {sum_all_mar25:,.2f}")

# Only started in MAR/25
started_mar25 = df_a369[(df_a369['Date_Inicio'] >= '2025-03-01') & (df_a369['Date_Inicio'] <= '2025-03-31')]
sum_new_mar25 = started_mar25[mar25_col].sum()
sum_contrato_new_mar25 = pd.to_numeric(started_mar25['VALOR DO CONTRATO'], errors='coerce').fillna(0).sum()

print(f"Soma MEDIDO MAR/25 (Somente contratos que INICIARAM em março): {sum_new_mar25:,.2f}")
print(f"Soma VALOR CONTRATO MAR/25 (Somente iniciados em março): {sum_contrato_new_mar25:,.2f}")
