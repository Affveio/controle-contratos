import pandas as pd
import json
import os
import time
import datetime

# Configurações de Caminho - Dinâmico
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_FILE = os.path.join(BASE_DIR, 'Contratos.xlsx')
ASSET_EXCEL = os.path.join(BASE_DIR, 'Planilha de ativos.xlsx')
DAILY_ASSET_EXCEL = os.path.join(BASE_DIR, 'Parte diaria de equipamentos.xlsx')
VALOR_EXCEL = os.path.join(BASE_DIR, 'Valor equipamentos.xlsx')
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

def load_values():
    val_map = {}
    path = 'Valor equipamentos.xlsx'
    if os.path.exists(path):
        try:
            df = pd.read_excel(path)
            for _, row in df.iterrows():
                try:
                    # Agora usamos:
                    # iloc[0]: TIPO (hora ou mes)
                    # iloc[1]: VALOR
                    # iloc[2]: PREFIXO (AL)
                    tipo = str(row.iloc[0]).strip().upper()
                    val = pd.to_numeric(row.iloc[1], errors='coerce')
                    al = str(row.iloc[2]).strip()
                    
                    if al.startswith('AL-') and pd.notna(val):
                        # Se for mensal, converte para valor hora (base 200h) para o dashboard
                        if 'M' in tipo or 'MES' in tipo:
                            val = val / 200.0
                        val_map[al] = val
                except: continue
            print(f"Valores financeiros carregados: {len(val_map)} equipamentos mapeados.")
        except Exception as e:
            print(f"Erro ao carregar valores: {e}")
    return val_map

def load_discounts():
    discounts_map = {}
    path = 'Desconto equipamentos.xlsx'
    if os.path.exists(path):
        try:
            # Lendo sem cabeçalho para usar os índices passados pelo usuário (F=5, I=8, K=10, L=11, M=12, O=14)
            df = pd.read_excel(path, header=None)
            
            def _parse_period_to_month(period_str):
                try:
                    if not period_str or pd.isna(period_str): return None
                    # Ex: "21/05/2025  20/06/2025" -> Pegamos a última data
                    parts = str(period_str).split()
                    last_date_str = parts[-1]
                    dt = pd.to_datetime(last_date_str, format='%d/%m/%Y', errors='coerce')
                    if pd.isna(dt): return None
                    
                    d, m, y = dt.day, dt.month, dt.year
                    # Regra: dia > 20 vira o mês seguinte
                    if d > 20:
                        m += 1
                        if m > 12: m = 1; y += 1
                    months_br = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ']
                    return f"{months_br[m-1]}/{str(y)[2:]}"
                except: return None

            # Começa da linha 4 (index 3) para pular possíveis cabeçalhos
            for i in range(3, len(df)):
                row = df.iloc[i]
                al = str(row.iloc[5]).strip().upper()
                if not al or al == 'NAN' or 'EQUIPAMENTO' in al: continue
                
                valor = pd.to_numeric(row.iloc[11], errors='coerce')
                if pd.isna(valor) or valor == 0: continue
                
                mes_ref = _parse_period_to_month(row.iloc[14])
                if not mes_ref: continue
                
                key = (al, mes_ref)
                if key not in discounts_map:
                    discounts_map[key] = []
                
                discounts_map[key].append({
                    'motivo': str(row.iloc[10]).strip(),
                    'valor': valor,
                    'responsavel': str(row.iloc[12]).strip().upper()
                })
            print(f"Descontos carregados: {len(discounts_map)} chaves (AL/Mês) encontradas.")
        except Exception as e:
            print(f"Erro ao carregar descontos: {e}")
    return discounts_map
def load_assets():
    df_diaria = None
    df_parada = None

    if os.path.exists('Maquina parada.xlsx'):
        try:
            import pandas as pd
            df_parada = pd.read_excel('Maquina parada.xlsx', sheet_name=0)
            if len(df_parada.columns) >= 16:
                col_obra = df_parada.columns[1]
                col_al = df_parada.columns[4]
                col_descricao = df_parada.columns[6]
                col_causa = df_parada.columns[9]
                col_respons = df_parada.columns[10]
                col_inicio = df_parada.columns[11]
                col_duracao = df_parada.columns[15]

                df_parada['AL'] = df_parada[col_al].astype(str).str.strip().str.upper()
                df_parada['Obra'] = df_parada[col_obra].astype(str).str.strip().str.upper()
                # Normalização de Obra
                df_parada['Obra'] = df_parada['Obra'].apply(lambda x: f"OBRA {x}" if x in ['A369', 'A375'] else x)
                
                df_parada['Responsabilidade'] = df_parada[col_respons].fillna('')
                df_parada['Causa'] = df_parada[col_causa].fillna('')
                df_parada['Descricao'] = df_parada[col_descricao].fillna('')
                df_parada['TempoManutencao'] = pd.to_numeric(df_parada[col_duracao], errors='coerce').fillna(0)
                
                # Novas métricas de causa específica
                df_parada['TempoDesgaste'] = df_parada.apply(lambda r: r['TempoManutencao'] if 'DESGASTE' in str(r['Causa']).upper() else 0, axis=1)
                df_parada['TempoFalha'] = df_parada.apply(lambda r: r['TempoManutencao'] if 'FALHA' in str(r['Causa']).upper() or 'OPERA' in str(r['Causa']).upper() else 0, axis=1)

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
                
                df_parada = df_parada.groupby(['AL', 'Mes_Referencia', 'Obra'], as_index=False).agg({
                    'TempoManutencao': 'sum',
                    'TempoDesgaste': 'sum',
                    'TempoFalha': 'sum',
                    'Responsabilidade': lambda x: ' / '.join(pd.unique([str(v).strip() for v in x if str(v).strip()])),
                    'Causa': lambda x: ' / '.join(pd.unique([str(v).strip() for v in x if str(v).strip()])),
                    'Descricao': lambda x: ' / '.join(pd.unique([str(v).strip() for v in x if str(v).strip()]))
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
            
            # Mapeamento por índices fixos conforme solicitado pelo usuário:
            # AL: Coluna B (índice 1)
            # Equipamento: Coluna F (índice 5)
            # Empresa: Coluna J (índice 9)
            if len(df_cadastro.columns) >= 10:
                df_cadastro.rename(columns={
                    df_cadastro.columns[1]: 'AL',
                    df_cadastro.columns[5]: 'Equipamento',
                    df_cadastro.columns[9]: 'Empresa'
                }, inplace=True)
            else:
                # Fallback para nomes de colunas caso a planilha seja menor
                col_pref = 'Prefixo Aterpa' if 'Prefixo Aterpa' in df_cadastro.columns else 'Prefixo'
                df_cadastro.rename(columns={col_pref: 'AL'}, inplace=True)
            
            # CRIAR ID ÚNICO POR LINHA DO CADASTRO MESTRE
            df_cadastro['asset_id'] = [f"CAD_{i}" for i in range(len(df_cadastro))]
            
            # Normalizar demais colunas importantes
            if len(df_cadastro.columns) > 21:
                cad_map = {'Obra': 'Obra', 'Status Mob/Desmob.': 'Status', 'Modelo': 'Modelo', 'Marca': 'Marca', 
                           df_cadastro.columns[0]: 'Categoria',
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
             # Extrair colunas G (índice 6), H (índice 7), I (índice 8) e N (índice 13)
             col_data = df_diaria.columns[6] if len(df_diaria.columns) > 6 else 'DATA'
             col_h_ini = df_diaria.columns[7] if len(df_diaria.columns) > 7 else 'HORÍMETRO INICIAL'
             col_h_fim = df_diaria.columns[8] if len(df_diaria.columns) > 8 else 'HORÍMETRO FINAL'
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
            
             def _is_rainy_season(mes_ref):
                 if not mes_ref: return False
                 # Período de chuva acordado: Nov/25 a Mar/26 (apenas neste período não há hora garantia)
                 rainy_periods = ['NOV/25', 'DEZ/25', 'JAN/26', 'FEV/26', 'MAR/26']
                 return any(p in mes_ref.upper() for p in rainy_periods)

             df_diaria['Mes_Referencia'] = df_diaria[col_data].apply(_calc_mes_diaria)
             df_diaria['HorasTrabalhadas'] = pd.to_numeric(df_diaria[col_horas], errors='coerce').fillna(0)
             
             # Novo Cálculo de Improdutividade Diária (Segunda a Sábado)
             def _calc_improdutividade_diaria(row):
                 try:
                     dt = pd.to_datetime(row[col_data])
                     if pd.isna(dt) or dt.weekday() == 6: # 6 é Domingo em Python
                         return 0
                     worked = float(row['HorasTrabalhadas'])
                     # Meta diária: 200h / 26 dias úteis = 7.6923...
                     # REGRA CHUVA: Se for mês de chuva, não há garantia/improdutividade para pagar
                     if _is_rainy_season(row.get('Mes_Referencia')):
                         return 0
                     return max(0, (200.0 / 26.0) - worked)
                 except:
                     return 0
             
             df_diaria['HorasImprodutivas'] = df_diaria.apply(_calc_improdutividade_diaria, axis=1)

             # Coletar histórico de horímetros antes de agrupar
             def _get_history(group):
                 hist = []
                 for _, r in group.iterrows():
                     dt_fmt = pd.to_datetime(r[col_data]).strftime('%d/%m/%Y') if pd.notna(r[col_data]) else '-'
                     hist.append({
                         'data': dt_fmt,
                         'inicial': float(r[col_h_ini]) if pd.notna(r[col_h_ini]) else 0,
                         'final': float(r[col_h_fim]) if pd.notna(r[col_h_fim]) else 0,
                         'horas': float(r['HorasTrabalhadas'])
                     })
                 return hist

             # Agrupar a diária por AL e Mês somando horas trabalhadas e coletando histórico
             df_diaria_grouped = df_diaria.groupby(['AL', 'Mes_Referencia'], as_index=False).agg({
                 'HorasTrabalhadas': 'sum',
                 'HorasImprodutivas': 'sum'
             })
             
             # Adicionar o histórico como uma lista
             hist_data = df_diaria.groupby(['AL', 'Mes_Referencia']).apply(_get_history).reset_index(name='HistoricoHorimetros')
             df_diaria = pd.merge(df_diaria_grouped, hist_data, on=['AL', 'Mes_Referencia'], how='left')
             
             df_diaria['DiasPresentes'] = df_diaria['HistoricoHorimetros'].apply(len)

        # Para não quebrar o fluxo atual, vamos manter o merge mas garantir que o Cadastro não seja filtrado

        if df_diaria is not None and df_parada is not None:
            df_diaria = pd.merge(df_diaria, df_parada, on=['AL', 'Mes_Referencia'], how='outer')
        elif df_parada is not None:
            df_diaria = df_parada
        
        # Alterado para 'outer' para garantir que ativos apenas na manutenção apareçam
        df_assets = pd.merge(df_cadastro, df_diaria, on=['AL'], how='outer', suffixes=('', '_diaria'))
        
        # Consolidação: Se vier da diária/manutenção (Outer join)
        for col in ['Obra', 'Status', 'Equipamento', 'Modelo', 'Marca', 'Empresa', 'HorasImprodutivas', 'DiasPresentes', 'Categoria']:
            col_diaria = col + '_diaria' if col + '_diaria' in df_assets.columns else col
            if col in df_assets.columns:
                df_assets[col] = df_assets[col_diaria] if col in ['HorasImprodutivas', 'DiasPresentes'] else df_assets[col].fillna(df_assets[col_diaria])
            elif col_diaria in df_assets.columns:
                df_assets[col] = df_assets[col_diaria]

        # REPARAÇÃO: Garantir que AL, Equipamento e Categoria nunca sejam nulos
        df_assets['AL'] = df_assets['AL'].fillna(df_assets.get('AL_diaria', ''))
        df_assets['Equipamento'] = df_assets['Equipamento'].fillna(df_assets.get('AL', 'DESCONHECIDO'))
        df_assets['Categoria'] = df_assets['Categoria'].fillna('NÃO CADASTRADO')
        df_assets['Obra'] = df_assets['Obra'].fillna('OBRA NÃO CADASTRADA')

        # Garantir IDs únicos para tudo
        mask_no_id = df_assets['asset_id'].isna()
        if mask_no_id.any():
            df_assets.loc[mask_no_id, 'asset_id'] = [f"MNT_{i}" for i in range(mask_no_id.sum())]

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
    numeric_cols = ['HorasTrabalhadas', 'HorasGarantia', 'TempoManutencao', 'TempoDesgaste', 'TempoFalha', 'HorasImprodutivas']
    for col in numeric_cols:
        if col in df_assets.columns:
            df_assets[col] = pd.to_numeric(df_assets[col], errors='coerce').fillna(0)
        elif any(c.upper().replace(' ', '') == col.upper() for c in df_assets.columns):
            # Tentar encontrar a coluna mesmo com nome ligeiramente diferente
            orig = [c for c in df_assets.columns if c.upper().replace(' ', '') == col.upper()][0]
            df_assets[col] = pd.to_numeric(df_assets[orig], errors='coerce').fillna(0)

    print(f"Colunas detectadas antes da normalização: {df_assets.columns.tolist()}")
    new_cols = []
    for col in df_assets.columns:
        c_name = str(col).strip()
        val = c_name.upper()
        if val == 'ASSET_ID': new_cols.append('asset_id')
        elif val == 'AL' or val.startswith('AL ') or 'PREFIXO' in val: new_cols.append('AL')
        elif val == 'EQUIPAMENTO': new_cols.append('Equipamento')
        elif 'DATA' in val: new_cols.append('Data de Chegada na Obra')
        elif 'HORA' in val and 'TRAB' in val: new_cols.append('HorasTrabalhadas')
        elif val == 'TEMPODESGASTE': new_cols.append('TempoDesgaste')
        elif val == 'TEMPOFALHA': new_cols.append('TempoFalha')
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
    for num_col in ['HorasTrabalhadas', 'HorasGarantia', 'TempoManutencao', 'TempoDesgaste', 'TempoFalha', 'HorasImprodutivas', 'DiasPresentes']:
        if num_col in df_assets.columns: agg_rules[num_col] = 'sum'
    if 'Data de Chegada na Obra' in df_assets.columns: agg_rules['Data de Chegada na Obra'] = 'first'
    if 'Saida' in df_assets.columns: agg_rules['Saida'] = 'first'
    if 'Responsabilidade' in df_assets.columns: agg_rules['Responsabilidade'] = 'first'
    if 'Causa' in df_assets.columns: agg_rules['Causa'] = 'first'
    if 'Descricao' in df_assets.columns: agg_rules['Descricao'] = 'first'
    if 'HistoricoHorimetros' in df_assets.columns: agg_rules['HistoricoHorimetros'] = 'first'
    
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
            
            # REGRA CHUVA: Se for mês de chuva, não há garantia/improdutividade para pagar
            if _is_rainy_season(month_ref):
                return 0
                
            return lacunas * (200.0 / 26.0)
        except:
            return 0
            
    df_assets['HorasImprodutivas'] = df_assets['HorasImprodutivas'] + df_assets.apply(_fill_improdutividade_lacunas, axis=1)

    # Carregar Mapeamento de Valores Financeiros
    valor_map = load_values()
    df_assets['ValorHora'] = df_assets['AL'].map(valor_map).fillna(0)
    
    # Integrar Descontos
    discounts_data = load_discounts()
    def _get_asset_discounts(row):
        key = (str(row['AL']).strip().upper(), str(row['Mes_Referencia']).strip().upper())
        return discounts_data.get(key, [])
    
    df_assets['Descontos'] = df_assets.apply(_get_asset_discounts, axis=1)
    
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
