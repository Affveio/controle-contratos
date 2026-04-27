import os

with open('controle_contratos_backup_20260413 - contrato e equipamento.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Fix initialization in data()
t1 = "{ month: 'all', equipment: 'all', company: 'all', work: 'all', status: 'all' }"
r1 = "{ month: 'all', equipment: 'all', company: 'all', work: 'all', status: 'all', category: 'all' }"
if t1 in text:
    text = text.replace(t1, r1)

# 2. Make filteredAssets null-safe for category
t2 = ".filter(a => this.assetFilters.category === 'all' || (a.Categoria || '').toUpperCase() === this.assetFilters.category.toUpperCase())"
# Note: I might have used a different variant in my last attempt if the match failed.
# Let's check what's actually there.

# Actually, I'll just look for any .toUpperCase() on category filter.
if "this.assetFilters.category.toUpperCase()" in text:
    text = text.replace("this.assetFilters.category.toUpperCase()", "(this.assetFilters.category || 'all').toUpperCase()")

with open('controle_contratos_backup_20260413 - contrato e equipamento.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Fix applied")
