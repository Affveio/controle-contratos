import json
import re

with open('data.js', 'r', encoding='utf-8') as f:
    text = f.read()

match = re.search(r'window\.CONTRACT_DATA\s*=\s*(\[.*?\]);', text, re.DOTALL)
data = json.loads(match.group(1))

for c in data:
    if c.get('SUBCONTRATADO') and 'EMTEL' in c['SUBCONTRATADO']:
        print(json.dumps(c, indent=2))
        break
