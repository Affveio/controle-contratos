import json
import re

with open('data.js', 'r', encoding='utf-8') as f:
    text = f.read()
match = re.search(r'window\.CONTRACT_DATA\s*=\s*(\[.*?\]);', text, re.DOTALL)
data = json.loads(match.group(1))

def parse_num(val):
    if val is None: return 0
    if isinstance(val, (int, float)): return float(val)
    s = str(val).replace(' ', '').replace('R$', '')
    if ',' in s and '.' in s: s = s.replace('.', '').replace(',', '.')
    elif ',' in s: s = s.replace(',', '.')
    try: return float(s)
    except: return 0.0

def parse_date_str(d_str):
    if not d_str: return None
    d_str = str(d_str)
    m = re.match(r'^(\d{4})-(\d{2})-(\d{2})', d_str)
    if m: return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return d_str

month_start = '2026-02-01'
month_end = '2026-02-28'

dropped = []
for c in data:
    if c.get('OBRA') != 'A369': continue
    
    val = parse_num(c.get('FEV/26'))
    if val <= 0: continue
    
    d_fim = parse_date_str(c.get('TERMINO_CONTRATO'))
    
    if d_fim and d_fim < month_start:
        dropped.append((c.get('SUBCONTRATADO'), val, d_fim))

print("Dropped contracts with FEV/26 > 0:")
for name, val, dfm in dropped:
    print(f"{name}: {val} (ends {dfm})")

