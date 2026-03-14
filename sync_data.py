import pandas as pd
import json
import os
import time

# Configurações de Caminho
BASE_DIR = r'c:\Users\Obra 369\Desktop\Planilha contrato'
EXCEL_FILE = os.path.join(BASE_DIR, 'Contratos.xlsx')
OUTPUT_JS = os.path.join(BASE_DIR, 'data.js')

def make_unique(cols):
    seen = {}
    unique_cols = []
    for col in cols:
        new_col = col
        if col in seen:
            seen[col] += 1
            new_col = f"{col}.{seen[col]}"
        else:
            seen[col] = 0
        unique_cols.append(new_col)
    return unique_cols

def sync():
    print(f"Sincronizando dados de: {EXCEL_FILE}...")
    try:
        if not os.path.exists(EXCEL_FILE):
            print(f"Erro: Arquivo {EXCEL_FILE} nao encontrado.")
            return

        # Carregar Excel e identificar abas
        xl = pd.ExcelFile(EXCEL_FILE)
        sheet_names = xl.sheet_names
        
        df = None
        cc_sheet_name = None
        
        # 1. Identificar aba de contratos (procurando pela coluna 'OBRA')
        for sheet in sheet_names:
            temp_df = xl.parse(sheet, nrows=5) 
            if any('OBRA' in str(c).upper() for c in temp_df.columns):
                df = xl.parse(sheet)
                print(f"Aba de contratos identificada: '{sheet}'")
                break
        
        if df is None:
            df = xl.parse(sheet_names[0])
            print(f"Aviso: Coluna 'OBRA' não encontrada. Usando primeira aba: '{sheet_names[0]}'")

        # 2. Identificar aba de Centros de Custo
        for sheet in sheet_names:
            if 'CENTRO' in sheet.upper():
                cc_sheet_name = sheet
                break

        # 3. Formatar colunas e consolidar meses
        months_br = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
        
        def process_df(df_in):
            df_temp = df_in.copy()
            new_cols = []
            for col in df_temp.columns:
                clean_name = str(col).replace('\n', ' ').strip()
                try:
                    dt = pd.to_datetime(col)
                    if not pd.isna(dt) and dt.year > 2000:
                        fmt = f"{months_br[dt.month - 1]}/{str(dt.year)[2:]}".upper()
                        new_cols.append(fmt)
                        continue
                except:
                    pass
                new_cols.append(clean_name)

            df_temp.columns = make_unique(new_cols)

            # Agrupar colunas de meses duplicadas
            is_month = lambda c: any(m.upper()+'/' in str(c).upper() for m in months_br)
            other_cols = [c for c in df_temp.columns if not is_month(c)]
            month_cols = [c for c in df_temp.columns if is_month(c)]
            
            month_mapping = {c: c.split('.')[0].upper() for c in month_cols}
            
            for c in month_cols:
                df_temp[c] = pd.to_numeric(df_temp[c], errors='coerce').fillna(0)
                
            df_final = df_temp[other_cols].copy()
            df_months = df_temp[month_cols].rename(columns=month_mapping)
            if not df_months.empty:
                df_months = df_months.groupby(axis=1, level=0).sum()
                df_temp = pd.concat([df_final, df_months], axis=1)
            else:
                df_temp = df_final

            # Limpeza de dados final e padronização de Setores
            if 'SETOR' in df_temp.columns:
                df_temp['SETOR'] = df_temp['SETOR'].apply(lambda x: str(x).strip() if pd.notnull(x) else None)
                
            df_temp = df_temp.where(pd.notnull(df_temp), None)
            check_cols = [c for c in ['OBRA', 'SUBCONTRATADO', 'CENTRO DE CUSTO'] if c in df_temp.columns]
            if check_cols:
                df_temp = df_temp.dropna(subset=check_cols, how='all')
            return df_temp

        df = process_df(df)

        # 4. Processar aba de Custo Previsto
        df_previsto = None
        for sheet in sheet_names:
            if 'PREVISTO' in sheet.upper():
                df_previsto_raw = xl.parse(sheet)
                df_previsto = process_df(df_previsto_raw)
                print(f"Aba Custo Previsto identificada: '{sheet}'")
                break

        # 5. Exportar mapeamento de nomes
        mapping = {}
        if cc_sheet_name:
            try:
                df_cc_names = xl.parse(cc_sheet_name)
                for _, row in df_cc_names.iterrows():
                    try:
                        cc_code = str(row.iloc[2]).strip().upper()
                        cc_name = str(row.iloc[3]).strip()
                        if cc_code and cc_name and cc_code != 'NAN' and cc_name != 'nan':
                            mapping[cc_code] = cc_name
                    except: continue
            except Exception as e:
                print(f"Aviso aba CC: {e}")

        # 6. Gravar arquivo final
        with open(OUTPUT_JS, 'w', encoding='utf-8') as f:
            f.write(f"window.CONTRACT_DATA = {df.to_json(orient='records', force_ascii=False)};\n")
            if df_previsto is not None:
                f.write(f"window.PREVISTO_DATA = {df_previsto.to_json(orient='records', force_ascii=False)};\n")
            else:
                f.write("window.PREVISTO_DATA = [];\n")
            f.write(f"window.COST_CENTER_NAMES = {json.dumps(mapping, ensure_ascii=False)};\n")

        print(f"Sucesso! Dashboard atualizado: {time.strftime('%H:%M:%S')} ({len(mapping)} CCs mapeados)")
    except Exception as e:
        print(f"Erro na sincronização: {str(e)}")

if __name__ == "__main__":
    sync()
