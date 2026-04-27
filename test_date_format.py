import json
import re

with open('data.js', 'r', encoding='utf-8') as f:
    text = f.read()

match = re.search(r'window\.CONTRACT_DATA\s*=\s*(\[.*?\]);', text, re.DOTALL)
data = json.loads(match.group(1))

# Check the format of INICIO_CONTRATO
for c in data[:5]:
    print(f"Obra: {c.get('OBRA')}, Inicio: {c.get('INICIO_CONTRATO')}, Termino: {c.get('TERMINO_CONTRATO')}")
