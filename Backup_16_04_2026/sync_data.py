import pandas as pd
import json
import os
import time
import datetime

# Configurações de Caminho
BASE_DIR = r'c:\Users\Obra 369\Desktop\Planilha contrato'
EXCEL_FILE = os.path.join(BASE_DIR, 'Contratos.xlsx')
ASSET_EXCEL = os.path.join(BASE_DIR, 'Planilha de ativos.xlsx')
DAILY_ASSET_EXCEL = os.path.join(BASE_DIR, 'Parte diaria de equipamentos.xlsx')
OUTPUT_JS = os.path.join(BASE_DIR, 'data.js')


def make_unique(cols):
    seen = {}
    unique_cols = []
    for col in cols:
        if col in seen:
            seen[col] += 1
            unique_cols.append(f"{col}.{seen[col]}")
        else:
            seen[col] = 0
            unique_cols.append(col)
    return unique_cols


def process_df(df_in):
    df_temp = df_in.copy()
    months_br = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']
    new_cols = []

    for col in df_temp.columns:
        clean_name = str(col).replace('\n', ' ').strip()
        try:
            dt = pd.to_datetime(str(col), errors='coerce')
            if pd.notna(dt) and dt.year > 2000:
                new_cols.append(f"{months_br[dt.month - 1]}/{str(dt.year)[2:]}".upper())
                continue
        except Exception:
            pass
        new_cols.append(clean_name)

    df_temp.columns = make_unique(new_cols)

    is_month = lambda c: any(m.upper() + '/' in str(c).upper() for m in months_br)
    col_mapping = {}
    for c in df_temp.columns:
        if 'INICIO' in str(c).upper() and 'CONTRATO' in str(c).upper():
            col_mapping[c] = 'INICIO_CONTRATO'
        elif 'TERMINO' in str(c).upper() and 'CONTRATO' in str(c).upper():
            col_mapping[c] = 'TERMINO_CONTRATO'
        elif 'MINO DE CONTRATO' in str(c).upper():
            col_mapping[c] = 'TERMINO_CONTRATO'
    df_temp.rename(columns=col_mapping, inplace=True)

    other_cols = [c for c in df_temp.columns if not is_month(c)]
    month_cols = [c for c in df_temp.columns if is_month(c)]
    month_mapping = {c: c.split('.')[0].upper() for c in month_cols}

    for c in month_cols:
        df_temp[c] = pd.to_numeric(df_temp[c], errors='coerce').fillna(0)

    df_final = df_temp[other_cols].copy()
    df_months = df_temp[month_cols].rename(columns=month_mapping)
    if not df_months.empty:
        df_months = df_months.T.groupby(level=0).sum().T
        df_temp = pd.concat([df_final, df_months], axis=1)
    else:
        df_temp = df_final

    if 'SETOR' in df_temp.columns:
        df_temp['SETOR'] = df_temp['SETOR'].apply(lambda x: str(x).strip() if pd.notnull(x) else None)

    for d_col in ['INICIO_CONTRATO', 'TERMINO_CONTRATO']:
        if d_col in df_temp.columns:
            df_temp[d_col] = pd.to_datetime(df_temp[d_col], errors='coerce').dt.strftime('%Y-%m-%d')

    df_temp = df_temp.where(pd.notnull(df_temp), None)
    check_cols = [c for c in ['OBRA', 'SUBCONTRATADO', 'CENTRO DE CUSTO'] if c in df_temp.columns]
    if check_cols:
        df_temp = df_temp.dropna(subset=check_cols, how='all')
    return df_temp
def load_assets():
    df_diaria = None
    df_parada = None

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
    df_cadastro = None
    
    # 1. Carregar Parte Diária (Horas e Datas)
    if os.path.exists(DAILY_ASSET_EXCEL):
        try:
            xl_d = pd.ExcelFile(DAILY_ASSET_EXCEL)
            # Tentar encontrar a aba correta (mesma lógica de score)
            asset_sheet = xl_d.sheet_names[0]
            df_diaria = xl_d.parse(asset_sheet, header=5)
            # Normalizar prefixo na diária
            df_diaria.rename(columns={'PREFIXO': 'AL'}, inplace=True)
            print("Parte Diária carregada para processamento de horas.")
        except Exception as e:
            print(f"Erro ao carregar Parte Diária: {e}")

    # 2. Carregar Planilha de Ativos (Cadastro Mestre: Obra, Empresa, Status)
    if os.path.exists(ASSET_EXCEL):
        try:
            df_cadastro = pd.read_excel(ASSET_EXCEL)
            # Normalizar prefixo no cadastro
            col_pref = 'Prefixo Aterpa' if 'Prefixo Aterpa' in df_cadastro.columns else 'Prefixo'
            df_cadastro.rename(columns={col_pref: 'AL'}, inplace=True)
            # Procurar colunas de equipamentos
            # Prioridade 1: Descrição Completa
            # Prioridade 2: Tipo (sigla curta)
            candidate_desc = [c for c in df_cadastro.columns if 'DESCRI' in str(c).upper()]
            candidate_tipo = [c for c in df_cadastro.columns if 'TIPO' in str(c).upper()]
            
            final_col = None
            if candidate_desc: final_col = candidate_desc[0]
            elif candidate_tipo: final_col = candidate_tipo[0]
            
            if final_col:
                df_cadastro.rename(columns={final_col: 'Equipamento'}, inplace=True)
            
            # CRIAR ID ÚNICO POR LINHA DO CADASTRO MESTRE
            # Usamos o índice atual para que cada linha física da planilha seja única
            df_cadastro['asset_id'] = [f"CAD_{i}" for i in range(len(df_cadastro))]
            
            # Normalizar colunas importantes no cadastro
            if len(df_cadastro.columns) > 21:
                cad_map = {'Obra': 'Obra', 'Status Mob/Desmob.': 'Status', 'Modelo': 'Modelo', 'Marca': 'Marca', 
                           df_cadastro.columns[0]: 'Categoria',
                           df_cadastro.columns[9]: 'Empresa', 
                           df_cadastro.columns[18]: 'Data de Chegada na Obra', 
                           df_cadastro.columns[21]: 'Saida'}
            else:
                cad_map = {df_cadastro.columns[0]: 'Categoria', 'Obra': 'Obra', 'Status Mob/Desmob.': 'Status', 'Modelo': 'Modelo', 'Marca': 'Marca'}
            df_cadastro.rename(columns=cad_map, inplace=True)
            
            # NORMALIZAÇÃO DE OBRA: Capturar qualquer variação de 375 ou 369
            if 'Obra' in df_cadastro.columns:
                df_cadastro['Obra'] = df_cadastro['Obra'].astype(str).str.upper().str.strip()
                df_cadastro.loc[df_cadastro['Obra'].str.contains('375'), 'Obra'] = 'OBRA A375'
                df_cadastro.loc[df_cadastro['Obra'].str.contains('369'), 'Obra'] = 'OBRA A369'
            
            # NORMALIZAÇÃO DE STATUS: Garantir que MOBILIZADO seja capturado sempre
            if 'Status' in df_cadastro.columns:
                df_cadastro['Status'] = df_cadastro['Status'].astype(str).str.upper().str.strip()
                # Se contém MOBIL, mas não DESMOBIL, marca como MOBILIZADO
                mask_mob = df_cadastro['Status'].str.contains('MOBIL', na=False) & ~df_cadastro['Status'].str.contains('DESMOBIL', na=False)
                df_cadastro.loc[mask_mob, 'Status'] = 'MOBILIZADO'
                df_cadastro.loc[df_cadastro['Status'].str.contains('DESMOBIL', na=False), 'Status'] = 'DESMOBILIZADO'

            print("Cadastro de Ativos carregado para metadados.")
        except Exception as e:
            print(f"Erro ao carregar Cadastro de Ativos: {e}")

    # 3. Cruzamento de Dados
    if df_diaria is not None and df_cadastro is not None:
        # Normalizar nomes de colunas na diária
        # Procurar AL por PREFIXO ou AL
        target_al = [c for c in df_diaria.columns if 'PREFIXO' in str(c).upper() or str(c).upper() == 'AL']
        if target_al: df_diaria.rename(columns={target_al[0]: 'AL'}, inplace=True)
        
        # Procurar Equipamento por DESCRI ou TIPO
        target_eq = [c for c in df_diaria.columns if 'DESCRI' in str(c).upper() or 'TIPO' in str(c).upper()]
        if target_eq:
             if 'Equipamento' in df_diaria.columns and target_eq[0] != 'Equipamento':
                 df_diaria.drop(columns=['Equipamento'], inplace=True)
             df_diaria.rename(columns={target_eq[0]: 'Equipamento'}, inplace=True)

        # Garantir colunas únicas na diária
        df_diaria = df_diaria.loc[:, ~df_diaria.columns.duplicated()]
        
        # Garantir AL e Equipamento como strings limpas (REMOVENDO ACENTOS para merge robusto)
        def normalize_str(s):
            if pd.isna(s): return ""
            import unicodedata
            import re
            s = str(s).strip().upper()
            # Normalizar para decompor acentos
            s = unicodedata.normalize('NFD', s)
            # Remover caracteres de acentuação (non-spacing marks)
            s = "".join([c for c in s if unicodedata.category(c) != 'Mn'])
            # Manter apenas letras, números, espaços e hífen
            return re.sub(r'[^A-Z0-9\s-]', '', s).strip()

        for d in [df_diaria, df_cadastro]:
            if 'AL' in d.columns: d['AL'] = d['AL'].astype(str).str.strip().str.upper()
            if 'Equipamento' in d.columns: 
                d['Equip_Merge'] = d['Equipamento'].apply(normalize_str)
        
        # Manter apenas as colunas que queremos do cadastro (Mestre)
        cols_cad = ['asset_id', 'AL', 'Equip_Merge', 'Equipamento', 'Obra', 'Status', 'Empresa', 'Modelo', 'Marca']
        df_cad_subset = df_cadastro[[c for c in cols_cad if c in df_cadastro.columns]].copy()
        
        # LIMPEZA: No cadastro mestre, garantir que AL e Equipamento sejam strings limpas
        df_cadastro['AL'] = df_cadastro['AL'].astype(str).str.strip().str.upper()
        df_cadastro['Equipamento'] = df_cadastro['Equipamento'].astype(str).str.strip().str.upper()

        # BASE FIXA: O Dashboard deve refletir exatamente o que está no cadastro mestre
        df_assets = df_cadastro.copy()
        
        # BUSCAR HORAS NA DIÁRIA: Agrupar diária por AL e Mês para obter horas
        if df_diaria is not None:
             # Normalizar diária
             df_diaria['AL'] = df_diaria['AL'].astype(str).str.strip().str.upper()
             # Extrair colunas G (índice 6) e N (índice 13) como solicitado
             col_data = df_diaria.columns[6] if len(df_diaria.columns) > 6 else 'DATA'
             col_horas = df_diaria.columns[13] if len(df_diaria.columns) > 13 else 'TOTAL HORAS TRABALHADAS'

             def _calc_mes_diaria(dt):
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
             
             df_diaria['Mes_Referencia'] = df_diaria[col_data].apply(_calc_mes_diaria)
             df_diaria['HorasTrabalhadas'] = pd.to_numeric(df_diaria[col_horas], errors='coerce').fillna(0)
             
             # Novo Cálculo de Improdutividade Diária (Segunda a Sábado)
             def _calc_improdutividade_diaria(row):
                 try:
                     dt = pd.to_datetime(row[col_data])
                     if pd.isna(dt) or dt.weekday() == 6: # 6 é Domingo em Python
                         return 0
                     worked = float(row['HorasTrabalhadas'])
                     # Meta diária: 200h / 30 dias = 6.66666...
                     return max(0, 6.66666666666667 - worked)
                 except:
                     return 0
             
             df_diaria['HorasImprodutivas'] = df_diaria.apply(_calc_improdutividade_diaria, axis=1)

             # Agrupar a diária por AL e Mês somando horas trabalhadas e improdutivas
             df_diaria = df_diaria.groupby(['AL', 'Mes_Referencia'], as_index=False).agg({
                 'HorasTrabalhadas': 'sum',
                 'HorasImprodutivas': 'sum'
             })
             df_diaria['HorasImprodutivas'] = df_diaria.apply(_calc_improdutividade_diaria, axis=1)
             df_diaria['DiasPresentes'] = 1

             # Agrupar a diária por AL e Mês somando horas trabalhadas, improdutivas e contando dias
             df_diaria = df_diaria.groupby(['AL', 'Mes_Referencia'], as_index=False).agg({
                 'HorasTrabalhadas': 'sum',
                 'HorasImprodutivas': 'sum',
                 'DiasPresentes': 'sum'
             })
        # Para não quebrar o fluxo atual, vamos manter o merge mas garantir que o Cadastro não seja filtrado

        if df_diaria is not None and df_parada is not None:
            df_diaria = pd.merge(df_diaria, df_parada, on=['AL', 'Mes_Referencia'], how='outer')
        elif df_parada is not None:
            df_diaria = df_parada
        df_assets = pd.merge(df_cadastro, df_diaria, on=['AL'], how='left', suffixes=('', '_diaria'))
        
        # Consolidação: Se vier da diária (Left join: Cadastro manda), usamos dados da diária apenas para horas
        # mas as informações de Obra e Status vem SEMPRE do cadastro.
        for col in ['Obra', 'Status', 'Equipamento', 'Modelo', 'Marca', 'Empresa', 'HorasImprodutivas', 'DiasPresentes']:
            col_diaria = col + '_diaria' if col + '_diaria' in df_assets.columns else col
            if col != col_diaria:
                # O cadastro tem prioridade absoluta para metadados, mas a diária manda em horas
                df_assets[col] = df_assets[col_diaria] if col in ['HorasImprodutivas', 'DiasPresentes'] else df_assets[col].fillna(df_assets[col_diaria])
        # Garantir IDs únicos para tudo
        mask_no_id = df_assets['asset_id'].isna()
        if mask_no_id.any():
            df_assets.loc[mask_no_id, 'asset_id'] = [f"NEW_{i}" for i in range(mask_no_id.sum())]

        # REPARAÇÃO: Garantir que a coluna 'Equipamento' (exibição) seja preservada 
        # e não a versão normalizada de merge
        if 'Equipamento_diaria' in df_assets.columns:
            df_assets['Equipamento'] = df_assets['Equipamento'].fillna(df_assets['Equipamento_diaria'])

        # CONSOLIDAÇÃO DE FAMÍLIA: Agrupar Grupo Gerador e variações em "GERADOR"
        df_assets['Equipamento'] = df_assets['Equipamento'].apply(
            lambda x: 'GERADOR' if pd.notnull(x) and (str(x).strip().upper() == 'GRUPO GERADOR' or 'GERADOR' in str(x).upper()) else x
        )

        # Garantir que 'Obra' seja normalizado para todos
        df_assets['Obra'] = df_assets['Obra'].fillna('OBRA NÃO CADASTRADA')
    elif df_diaria is not None:
        df_assets = df_diaria
        df_assets['asset_id'] = [f"DIARIA_{i}" for i in range(len(df_assets))]
    elif df_cadastro is not None:
        df_assets = df_cadastro
    else:
        return None

    # 4. Normalização Final de Colunas (padrão do dashboard)
    df_assets = df_assets.where(pd.notnull(df_assets), None)
    
    # Preencher colunas numéricas com 0
    numeric_cols = ['HorasTrabalhadas', 'HorasGarantia', 'TempoManutencao', 'HorasImprodutivas']
    for col in numeric_cols:
        if col in df_assets.columns:
            df_assets[col] = pd.to_numeric(df_assets[col], errors='coerce').fillna(0)
        elif any(c.upper().replace(' ', '') == col.upper() for c in df_assets.columns):
            # Tentar encontrar a coluna mesmo com nome ligeiramente diferente
            orig = [c for c in df_assets.columns if c.upper().replace(' ', '') == col.upper()][0]
            df_assets[col] = pd.to_numeric(df_assets[orig], errors='coerce').fillna(0)

    new_cols = []
    for col in df_assets.columns:
        c_name = str(col).strip()
        val = c_name.upper()
        if val == 'ASSET_ID': new_cols.append('asset_id')
        elif val == 'AL' or val.startswith('AL ') or 'PREFIXO' in val: new_cols.append('AL')
        elif val == 'EQUIPAMENTO': new_cols.append('Equipamento')
        elif 'DATA' in val: new_cols.append('Data de Chegada na Obra')
        elif 'HORA' in val and 'TRAB' in val: new_cols.append('HorasTrabalhadas')
        else: new_cols.append(c_name)
    
    df_assets.columns = make_unique(new_cols)

    # Cálculo do Mês de Referência (21-20 - Regra solicitada: 21/02 a 20/03 = Março)
    # A base deve ser a coluna DATA da Parte Diária (Coluna G)
    date_col = 'DATA' if 'DATA' in df_assets.columns else ('Data de Chegada na Obra' if 'Data de Chegada na Obra' in df_assets.columns else None)
    
    if date_col:
        def calc_ref_month(dt):
            try:
                dt = pd.to_datetime(dt)
                if pd.isna(dt): return None
                day, month, year = dt.day, dt.month, dt.year
                
                # Regra: Se dia > 20, vira o mês seguinte
                if day > 20:
                    month += 1
                    if month > 12: month = 1; year += 1
                
                months_br = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
                return f"{months_br[month-1]}/{str(year)[2:]}"
            except: return None
            
        fallback_months = df_assets[date_col].apply(calc_ref_month)
        if 'Mes_Referencia' in df_assets.columns:
            df_assets['Mes_Referencia'] = df_assets['Mes_Referencia'].fillna(fallback_months)
        else:
            df_assets['Mes_Referencia'] = fallback_months

    # Status (Lógica de fallback)
    if 'Status' not in df_assets.columns:
        if 'DESMOBILIZADO' in df_assets.columns:
            df_assets['Status'] = df_assets['DESMOBILIZADO'].apply(lambda x: 'DESMOBILIZADO' if pd.notna(x) and str(x).strip() != '' else 'MOBILIZADO')
        else:
            df_assets['Status'] = 'MOBILIZADO'

    # Normalização de Nomes de Obra (A369 -> OBRA A369)
    if 'Obra' in df_assets.columns:
        df_assets['Obra'] = df_assets['Obra'].astype(str).str.strip().str.upper()
        df_assets['Obra'] = df_assets['Obra'].apply(lambda x: f"OBRA {x}" if x in ['A369', 'A375'] else x)

    # Agrupamento para eliminar duplicidade (mesmo asset_id no mesmo mês deve ser uma única linha)
    # IMPORTANTE: Como agora asset_id é CAD_{idx}, cada linha da planilha é única por definição.
    # O agrupamento só ocorrerá se o mesmo asset_id aparecer várias vezes (o que não deve ocorrer aqui).
    group_cols = ['asset_id', 'AL', 'Equipamento', 'Modelo', 'Empresa', 'Status', 'Obra', 'Mes_Referencia', 'Categoria']
    group_cols = [c for c in group_cols if c in df_assets.columns]
    
    agg_rules = {}
    for num_col in ['HorasTrabalhadas', 'HorasGarantia', 'TempoManutencao', 'HorasImprodutivas', 'DiasPresentes']:
        if num_col in df_assets.columns: agg_rules[num_col] = 'sum'
    if 'Data de Chegada na Obra' in df_assets.columns: agg_rules['Data de Chegada na Obra'] = 'first'
    if 'Saida' in df_assets.columns: agg_rules['Saida'] = 'first'
    if 'Responsabilidade' in df_assets.columns: agg_rules['Responsabilidade'] = 'first'
    
    if agg_rules and group_cols:
        for gc in group_cols:
            df_assets[gc] = df_assets[gc].fillna('')
        df_assets = df_assets.groupby(group_cols, as_index=False).agg(agg_rules)
    
    # Preenchimento de Lacunas (Dias sem registro na Planilha Diária)
    def _fill_improdutividade_lacunas(row):
        try:
            arrival = pd.to_datetime(row.get('Data de Chegada na Obra'))
            departure = pd.to_datetime(row.get('Saida'))
            month_ref = str(row.get('Mes_Referencia'))
            
            if pd.isna(arrival) or month_ref == 'None' or month_ref == '':
                return 0
            
            # Determinar o intervalo do mês de referência
            months_br = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
            parts = month_ref.split('/')
            if len(parts) != 2: return 0
            m_idx = months_br.index(parts[0].upper())
            year = 2000 + int(parts[1])
            
            start_month = pd.Timestamp(year, m_idx + 1, 1)
            end_month = start_month + pd.offsets.MonthEnd(0)
            
            overlap_start = max(start_month, arrival)
            overlap_end = min(end_month, departure) if pd.notna(departure) else end_month
            
            if overlap_start > overlap_end:
                return 0
            
            # Contar dias úteis (Seg-Sab) no intervalo
            all_days = pd.date_range(overlap_start, overlap_end)
            work_days = len([d for d in all_days if d.weekday() != 6])
            
            dias_presentes = float(row.get('DiasPresentes', 0))
            lacunas = max(0, work_days - dias_presentes)
            return lacunas * 6.66666666666667
        except:
            return 0
            
    df_assets['HorasImprodutivas'] = df_assets['HorasImprodutivas'] + df_assets.apply(_fill_improdutividade_lacunas, axis=1)

    # Garantir que asset_id seja string para o JSON
    df_assets['asset_id'] = df_assets['asset_id'].astype(str)
    
    return df_assets


def sync():
    print(f"Sincronizando dados de: {EXCEL_FILE}...")
    try:
        if not os.path.exists(EXCEL_FILE):
            print(f"Erro: Arquivo {EXCEL_FILE} nao encontrado.")
            return

        xl = pd.ExcelFile(EXCEL_FILE)
        sheet_names = xl.sheet_names

        df = None
        cc_sheet_name = None

        for sheet in sheet_names:
            temp_df = xl.parse(sheet, nrows=5)
            if any('OBRA' in str(c).upper() for c in temp_df.columns):
                df = xl.parse(sheet)
                print(f"Aba de contratos identificada: '{sheet}'")
                break

        if df is None:
            df = xl.parse(sheet_names[0])
            print(f"Aviso: Coluna 'OBRA' não encontrada. Usando primeira aba: '{sheet_names[0]}'")

        for sheet in sheet_names:
            if 'CENTRO' in sheet.upper():
                cc_sheet_name = sheet
                break

        df = process_df(df)

        df_previsto = None
        for sheet in sheet_names:
            if 'PREVISTO' in sheet.upper():
                df_previsto_raw = xl.parse(sheet)
                df_previsto = process_df(df_previsto_raw)
                print(f"Aba Custo Previsto identificada: '{sheet}'")
                break

        assets_df = load_assets()

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
                    except Exception:
                        continue
            except Exception as e:
                print(f"Aviso aba CC: {e}")

        months_br = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
        df = df.fillna(0)
        
        # Otimização básica: remover colunas totalmente vazias ou sem nome
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

        if assets_df is not None:
            # O assets_df já vem agrupado e normalizado de load_assets()
            pass

        current_time_str = datetime.datetime.now().strftime('%d/%m/%Y às %H:%M:%S')
        with open(OUTPUT_JS, 'w', encoding='utf-8') as f:
            f.write(f"window.CONTRACT_DATA = {df.to_json(orient='records', force_ascii=False)};\n")
            if df_previsto is not None:
                # Filtrar colunas do previsto também
                previsto_cols = ['OBRA', 'SETOR', 'CENTRO DE CUSTO', 'VALOR DO CONTRATO']
                for c in df_previsto.columns:
                    if any(m + '/' in str(c).upper() for m in months_br):
                        if c not in previsto_cols: previsto_cols.append(c)
                df_previsto = df_previsto[[c for c in previsto_cols if c in df_previsto.columns]]
                f.write(f"window.PREVISTO_DATA = {df_previsto.to_json(orient='records', force_ascii=False)};\n")
            else:
                f.write("window.PREVISTO_DATA = [];\n")

            if assets_df is not None:
                f.write(f"window.ASSETS_DATA = {assets_df.to_json(orient='records', force_ascii=False)};\n")
            else:
                f.write("window.ASSETS_DATA = [];\n")

            f.write(f"window.COST_CENTER_NAMES = {json.dumps(mapping, ensure_ascii=False)};\n")
            f.write(f"window.LAST_UPDATED = '{current_time_str}';\n")

        print(f"Sucesso! Dashboard atualizado: {time.strftime('%H:%M:%S')} ({len(mapping)} CCs mapeados)")
    except Exception as e:
        print(f"Erro na sincronização: {str(e)}")


if __name__ == "__main__":
    sync()
