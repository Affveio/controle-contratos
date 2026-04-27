import re

with open('equipamentos.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Encontrar o trecho "Visão Ativo" para extrair
visao_ativo_match = re.search(r'(<!-- Visão Ativo \(Calendário/Histórico\) -->\s*<template x-if="drilldown\.type === \'asset\' && drilldown\.selectedAsset">.*?</template>)', content, re.DOTALL)
if not visao_ativo_match:
    print("Visão ativo não encontrada!")
    exit(1)
visao_ativo = visao_ativo_match.group(1)

# 2. Modificar o primeiro modal (envolver família e adicionar ativo)
# O primeiro modal "Modal Content" começa em <!-- Modal Content --> e termina em <!-- Modal Footer -->
# A div que engloba tudo é a `<div class="space-y-4">` logo após `<div class="p-4 overflow-y-auto custom-scrollbar flex-1">`
primeiro_modal_pattern = r'(<!-- Modal Content -->\s*<div class="p-4 overflow-y-auto custom-scrollbar flex-1">\s*)(<div class="space-y-4">.*?)(</div>\s*</div>\s*<!-- Modal Footer -->)'

def modal_replace(m):
    prefix = m.group(1)
    # A div.space-y-4 fecha com o último </div> capturado dentro do group(2).
    body = m.group(2)
    suffix = m.group(3)
    
    # Envolver o body com template
    novo_body = f'<template x-if="drilldown.type === \'family\'">\n{body}\n</template>\n\n{visao_ativo}\n'
    return prefix + novo_body + suffix

content_modified = re.sub(primeiro_modal_pattern, modal_replace, content, flags=re.DOTALL)

# 3. Remover o SEGUNDO modal duplicado
# O segundo modal começa em <!-- Modal de Drill-down (Detalhamento ao Clicar) --> e termina na tag </script> (L1531 até L1815)
# Vou remover do <!-- Modal de Drill-down (Detalhamento ao Clicar) --> até o fechamento da tag principal que vem antes de <script>
# A estrutura é `<div class="fixed inset-0 ... x-show="drilldown.isOpen"`
segundo_modal_pattern = r'<!-- Modal de Drill-down \(Detalhamento ao Clicar\) -->\s*<div class="fixed inset-0.*?x-show="drilldown\.isOpen".*?<!-- Footer -->.*?</div>\s*</div>\s*</div>\s*(</main>)'
content_modified = re.sub(segundo_modal_pattern, r'\1', content_modified, flags=re.DOTALL)

with open('equipamentos.html', 'w', encoding='utf-8') as f:
    f.write(content_modified)

print("Modificações feitas com sucesso!")
