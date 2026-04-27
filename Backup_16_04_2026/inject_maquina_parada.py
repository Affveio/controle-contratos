import os

with open('sync_data.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    if "df_diaria = None" in line:
        new_lines.append(line)
        new_lines.append("    df_parada = None\n")
        new_lines.append("""
    if os.path.exists('Maquina parada.xlsx'):
        try:
            import pandas as pd
            df_parada = pd.read_excel('Maquina parada.xlsx', sheet_name=0)
            if len(df_parada.columns) >= 16:
                col_al = df_parada.columns[4]
                col_respons = df_parada.columns[10]
                col_inicio = df_parada.columns[11]
                col_duracao = df_parada.columns[15]

                df_parada['AL'] = df_parada[col_al].astype(str).str.strip().str.upper()
                df_parada['Responsabilidade'] = df_parada[col_respons].fillna('')
                df_parada['TempoManutencao'] = pd.to_numeric(df_parada[col_duracao], errors='coerce').fillna(0) / 24.0

                def _calc_mes_parada(dt):
                    try:
                        dt = pd.to_datetime(dt)
                        if pd.isna(dt): return None
                        d, m, y = dt.day, dt.month, dt.year
                        if d > 20:
                            m += 1
                            if m > 12: m = 1; y += 1
                        months_br = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
                        return f"{months_br[m-1]}/{str(y)[2:]}"
                    except: return None

                df_parada['Mes_Referencia'] = df_parada[col_inicio].apply(_calc_mes_parada)
                
                df_parada = df_parada.groupby(['AL', 'Mes_Referencia'], as_index=False).agg({
                    'TempoManutencao': 'sum',
                    'Responsabilidade': lambda x: ' / '.join(pd.unique([str(v).strip() for v in x if str(v).strip()]))
                })
            print("Máquina parada carregada com sucesso.")
        except Exception as e:
            print(f"Erro ao carregar Maquina parada: {e}")
""")
    elif "# Para no quebrar o fluxo atual" in line or "# Para não quebrar o fluxo atual" in line or "df_assets = pd.merge(df_cadastro, df_diaria, on=['AL']" in line:
        if "df_assets = pd.merge(df_cadastro, df_diaria" in line:
            # Inject merge before
            new_lines.append("""
        if df_diaria is not None and df_parada is not None:
            df_diaria = pd.merge(df_diaria, df_parada, on=['AL', 'Mes_Referencia'], how='outer')
        elif df_parada is not None:
            df_diaria = df_parada
""")
            new_lines.append(line)
        else:
            new_lines.append(line)
    elif "if 'Saida' in df_assets.columns: agg_rules['Saida'] = 'first'" in line:
        new_lines.append(line)
        new_lines.append("    if 'Responsabilidade' in df_assets.columns: agg_rules['Responsabilidade'] = 'first'\n")
    else:
        new_lines.append(line)

with open('sync_data.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print('sync_data.py updated.')
