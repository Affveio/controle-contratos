import json
import re

# Load data
with open('data.js', 'r', encoding='utf-8') as f:
    text = f.read()
match = re.search(r'window\.CONTRACT_DATA\s*=\s*(\[.*?\]);', text, re.DOTALL)
data = json.loads(match.group(1))

# replicate JS sort exactly
months_order = ['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ']
month_cols = [k for k in data[0].keys() if re.match(r'^[A-Z]{3}/\d{2}$', str(k).upper())]

def sort_key(k):
    m, y = k.split('/')
    return (int(y), months_order.index(m))

month_cols.sort(key=sort_key)

def parse_num(val):
    if val is None: return 0
    if isinstance(val, (int, float)): return float(val)
    s = str(val).replace(' ', '').replace('R$', '')
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        return float(s)
    except:
        return 0.0

def parse_date_str(d_str):
    if not d_str: return None
    d_str = str(d_str)
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})', d_str)
    if m: return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return d_str

def get_contracts(filter_month, is_accumulated, month_start, month_end):
    valid_contracts = []
    filter_idx = month_cols.index(filter_month)
    
    for c in data:
        if c.get('OBRA') != 'A369': continue
        
        d_inicio = parse_date_str(c.get('INICIO_CONTRATO'))
        d_fim = parse_date_str(c.get('TERMINO_CONTRATO'))
        
        medicao_isolada = parse_num(c.get(filter_month))
        cols_to_sum = month_cols[:filter_idx + 1]
        baseAcumuladoAteMes = sum(parse_num(c.get(col)) for col in cols_to_sum)
        
        if is_accumulated:
            tempMedido = baseAcumuladoAteMes
        else:
            tempMedido = medicao_isolada
            
        if is_accumulated:
            is_active = (not d_inicio or d_inicio <= month_end) and (not d_fim or d_fim >= month_start)
            has_medicao = medicao_isolada > 0
            if not is_active and not has_medicao:
                continue
        else:
            if tempMedido <= 0:
                didStartThisMonth = False
                if d_inicio and (month_start <= d_inicio <= month_end):
                    didStartThisMonth = True
                if not didStartThisMonth:
                    continue
                    
        c_copy = c.copy()
        c_copy['VALOR MEDIDO'] = tempMedido
        valid_contracts.append(c_copy)
        
    return valid_contracts

def calc_kpis(contracts):
    medido = sum(parse_num(c['VALOR MEDIDO']) for c in contracts)
    return medido

# Test FEV/26
fev26_contracts = get_contracts('FEV/26', False, '2026-02-01', '2026-02-28')
fev26_medido = calc_kpis(fev26_contracts)
print(f"FEV/26 Isolado: {fev26_medido:,.2f}")

# Test MAR/25
mar25_contracts = get_contracts('MAR/25', False, '2025-03-01', '2025-03-31')
mar25_medido = calc_kpis(mar25_contracts)
print(f"MAR/25 Isolado: {mar25_medido:,.2f}")

