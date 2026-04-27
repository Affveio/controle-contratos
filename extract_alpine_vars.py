
import re
import sys
import os

# Forçar saída UTF-8 no terminal
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, 'equipamentos.html'), 'r', encoding='utf-8') as f:
    content = f.read()

patterns = [
    r'x-show="([^"]+)"',
    r'x-if="([^"]+)"',
    r'x-model="([^"]+)"',
    r'x-text="([^"]+)"',
    r'@click="([^"]+)"',
    r'x-data="([^"]+)"',
    r':class="([^"]+)"',
    r'x-bind:class="([^"]+)"',
    r'x-for="([^"]+)"',
]

variables = set()
for p in patterns:
    matches = re.findall(p, content)
    for m in matches:
        # Extrair palavras que parecem variáveis
        parts = re.split(r'[^a-zA-Z0-9_$]+', m)
        for part in parts:
            if part and not part[0].isdigit() and part not in ['true', 'false', 'null', 'undefined', 'all', 'in']:
                variables.add(part)

for v in sorted(list(variables)):
    print(v)
