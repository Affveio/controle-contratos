import json
import re

with open('data.js', 'r', encoding='utf-8') as f:
    text = f.read()

match = re.search(r'window\.CONTRACT_DATA\s*=\s*(\[.*?\]);', text, re.DOTALL)
data = json.loads(match.group(1))

print("First Object keys:")
print(list(data[0].keys()))
