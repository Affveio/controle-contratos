import json
import re

with open('data.js', 'r', encoding='utf-8') as f:
    text = f.read()

match = re.search(r'window\.CONTRACT_DATA\s*=\s*(\[.*?\]);', text, re.DOTALL)
data = json.loads(match.group(1))

# replicate JS sort exactly
months_order = ['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ']
all_keys = list(data[0].keys()) if len(data) > 0 else []

month_cols = []
for k in all_keys:
    if re.match(r'^[A-Z]{3}/\d{2}$', k):
        month_cols.append(k)

def sort_key(k):
    m, y = k.split('/')
    return (int(y), months_order.index(m))

month_cols.sort(key=sort_key)
print("monthColumns:", month_cols)

filter_month = 'FEV/26'
filter_idx = month_cols.index(filter_month)

month_start = '2026-02-01'
month_end = '2026-02-28'

emtel = None
for c in data:
    if c.get('SUBCONTRATADO') and 'EMTEL' in c['SUBCONTRATADO']:
        emtel = c
        break

if not emtel:
    print("EMTEL not found")
    exit()

def parse_date_str(d_str):
    if not d_str: return None
    d_str = str(d_str)
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})', d_str)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return d_str

d_inicio = parse_date_str(emtel.get('INICIO_CONTRATO'))
d_fim = parse_date_str(emtel.get('TERMINO_CONTRATO'))
print("dInicio:", d_inicio, "dFim:", d_fim, "monthStart:", month_start, "monthEnd:", month_end)

valid = True
if d_inicio and d_inicio > month_end: valid = False
if d_fim and d_fim < month_start: valid = False

print("Valid after date bounds:", valid)

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

baseAcumuladoNoMes = parse_num(emtel.get(filter_month))
prev_m_str = month_cols[filter_idx - 1] if filter_idx > 0 else None
prevM = parse_num(emtel.get(prev_m_str)) if prev_m_str else 0
tempMedido = baseAcumuladoNoMes - prevM

print(f"baseAcumuladoNoMes ({filter_month}):", baseAcumuladoNoMes, "prev_m_str:", prev_m_str, "prevM:", prevM, "tempMedido:", tempMedido)

didStartThisMonth = False
if d_inicio and (month_start <= d_inicio <= month_end):
    didStartThisMonth = True

print("didStartThisMonth:", didStartThisMonth)

if tempMedido <= 0 and not didStartThisMonth:
    valid = False

print("Final Valid:", valid)

