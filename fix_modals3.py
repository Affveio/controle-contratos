import re
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, 'equipamentos.html'), 'r', encoding='utf-8') as f:
    backup = f.read()

# Extraindo a visão ativo completa do backup
start_tag = r"<!-- Visão Ativo \(Calendário/Histórico\) -->"
end_tag = r"</template>\s*</div>\s*<!-- Footer -->"
match = re.search(f"({start_tag}.*?</template>)", backup, re.DOTALL)
if match:
    visao_completa = match.group(1)
else:
    print("Falha ao encontrar Visão Ativo no backup.")
    exit(1)

with open('equipamentos.html', 'r', encoding='utf-8') as f:
    current = f.read()

# Substituir no arquivo atual
# O pedaço truncado terminava com `<!-- Visão Ativo (Calendário/Histórico) -->` até logo antes do `</div> </div> <!-- Modal Footer -->`
pattern = r"<!-- Visão Ativo \(Calendário/Histórico\).*?</div>\s*</div>\s*<!-- Modal Footer -->"

new_suffix = visao_completa + "\n</div>\n</div>\n<!-- Modal Footer -->"

new_current = re.sub(pattern, new_suffix, current, flags=re.DOTALL)

with open('equipamentos.html', 'w', encoding='utf-8') as f:
    f.write(new_current)

print("Estrutura da ficha de ativo restaurada integralmente!")
