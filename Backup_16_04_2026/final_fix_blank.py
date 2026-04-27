import os

with open('controle_contratos_backup_20260413 - contrato e equipamento.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Initialize category in assetFilters state
t1 = "assetFilters: { month: 'all', equipment: 'all', company: 'all', work: 'all', status: 'all' }"
r1 = "assetFilters: { month: 'all', equipment: 'all', company: 'all', work: 'all', status: 'all', category: 'all' }"
if t1 in text:
    text = text.replace(t1, r1)

# 2. Add parseExcelDate helper
t2 = "formatAssetDate(raw) {"
r2 = """parseExcelDate(val) {
                if (!val || val === 0 || val === '-') return null;
                if (val instanceof Date) return val;
                if (typeof val === 'number') return new Date(Math.round((val - 25569) * 86400 * 1000));
                const d = new Date(val);
                return isNaN(d.getTime()) ? null : d;
            },

            formatAssetDate(raw) {"""

if t2 in text and "parseExcelDate" not in text:
    text = text.replace(t2, r2)

# 3. Ensure filteredAssets is safe
if "this.assetFilters.category.toUpperCase()" in text:
    text = text.replace("this.assetFilters.category.toUpperCase()", "(this.assetFilters.category || 'all').toUpperCase()")

with open('controle_contratos_backup_20260413 - contrato e equipamento.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Final patch applied successfully")
