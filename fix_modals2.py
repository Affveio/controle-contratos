import re
import os

# 1. Pegar a Visão Ativo do arquivo original que eu fiz backup para não errar.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, 'equipamentos.html'), 'r', encoding='utf-8') as f:
    backup_content = f.read()

# No backup, a Visão Ativo começava com:
# <template x-if="drilldown.type === 'asset' && drilldown.selectedAsset">
# E terminava antes da tag <!-- Footer do Modal -->
match_ativo = re.search(r'(<template x-if="drilldown\.type === \'asset\' && drilldown\.selectedAsset">.*?</template>\s*)\s*(?:<!-- Footer do Modal -->|</div>\s*</div>\s*<!-- Modal Footer -->)', backup_content, re.DOTALL)

if not match_ativo:
    print("ERRO: não consegui extrair Visão Ativo do backup")
    exit(1)

visao_ativo = match_ativo.group(1)

# 2. Corrigir o arquivo atual:
with open('equipamentos.html', 'r', encoding='utf-8') as f:
    current_content = f.read()

# O arquivo atual está quebrado: a Visão ativo incompleta está lá, logo antes do </div> </div> <!-- Modal Footer -->
# A estrutura que eu tinha inserido começa com <!-- Visão Ativo (Calendário/Histórico) -->
# e termina com </template> (que na vdd era o fechamento do x-for). E depois logo em seguida tem </div> </div> <!-- Modal Footer -->
pattern_to_replace = r'<!-- Visão Ativo \(Calendário/Histórico\) -->.*?</div>\s*</div>\s*<!-- Modal Footer -->'

novo_sufixo = f'<!-- Visão Ativo (Calendário/Histórico) -->\n{visao_ativo}\n</div>\n</div>\n<!-- Modal Footer -->'

new_content = re.sub(pattern_to_replace, novo_sufixo, current_content, flags=re.DOTALL)

with open('equipamentos.html', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Visão ativo consertada usando backup.")
