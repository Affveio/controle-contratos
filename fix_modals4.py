import re
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, 'equipamentos.html'), 'r', encoding='utf-8') as f:
    backup = f.read()

# No backup, a visão ativo começa na linha ~1594 e termina na linha ~1676.
# Como sei o começo e o fim, vou usar string.find para extrair sem regex.
start_str = '<!-- Visão Ativo (Calendário/Histórico) -->'
end_str = '<!-- Footer do Modal -->'

start_idx = backup.find(start_str)
end_idx = backup.find(end_str, start_idx)

if start_idx == -1 or end_idx == -1:
    print("Falha ao encontrar inicio ou fim no backup")
    exit(1)

# Pego todo o bloco do Visão Ativo (do start até o end, que pega todo o HTML perfeitamente fechado)
visao_ativo_html = backup[start_idx:end_idx]
# Removo os </div> que fecham o modal no backup, pegando apenas até o </template> final da visão ativo.
# Vamos achar o último </template> dentro desse bloco:
last_template_idx = visao_ativo_html.rfind('</template>')
visao_ativo_html = visao_ativo_html[:last_template_idx + len('</template>')]

with open('equipamentos.html', 'r', encoding='utf-8') as f:
    current = f.read()

# Agora vou substituir o miolo quebrado atual
# O miolo atual começa com <!-- Visão Ativo (Calendário/Histórico) -->
# e vai até o <!-- Modal Footer --> (vamos extrair tudo entre eles e colocar a visão ativo html)
c_start_idx = current.find('<!-- Visão Ativo (Calendário/Histórico) -->')
c_end_idx = current.find('<!-- Modal Footer -->', c_start_idx)

# PRECISAMOS também fechar o `space-y-4` do Modal Content corretamente.
# O `Modal Content` tem uma `div class="p-4..."><template x-if="drilldown.type === 'family'"><div class="space-y-4">`
# A div `space-y-4` deve ser fechada ANTES do `</template>` da visão família, na linha 243.
# O template da família termina antes de <!-- Visão Ativo (Calendário/Histórico) -->.
template_family_end_idx = current.rfind('</template>', 0, c_start_idx)
# Inserindo o </div> antes dele
new_current = current[:template_family_end_idx] + '</div>\n' + current[template_family_end_idx:c_start_idx]

# Recalcular c_start_idx após modificar o tamanho da string
c_start_idx = new_current.find('<!-- Visão Ativo (Calendário/Histórico) -->')
c_end_idx = new_current.find('<!-- Modal Footer -->', c_start_idx)

# No final, temos que fechar a div `p-4 overflow-y-auto` que abriga os templates.
new_suffix = visao_ativo_html + '\n</div>\n'
new_current = new_current[:c_start_idx] + new_suffix + new_current[c_end_idx:]

with open('equipamentos.html', 'w', encoding='utf-8') as f:
    f.write(new_current)

print("HTML consertado de vez.")
