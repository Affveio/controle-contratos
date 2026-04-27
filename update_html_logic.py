import os

with open('controle_contratos_backup_20260413 - contrato e equipamento.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Update resetFilters
t1 = "this.assetFilters = { month: 'all', equipment: 'all', company: 'all', work: 'all', status: 'all' }"
r1 = "this.assetFilters = { month: 'all', equipment: 'all', company: 'all', work: 'all', status: 'all', category: 'all' }"
text = text.replace(t1, r1)

# 2. Add uniqueAssetCategories
t2 = "get uniqueAssetStatuses() {\n                    return [...new Set(this.assets.map(a => this.formatAssetStatus(a)).filter(v => v && v !== '-'))].sort();\n                },"
r2 = "get uniqueAssetStatuses() {\n                    return [...new Set(this.assets.map(a => this.formatAssetStatus(a)).filter(v => v && v !== '-'))].sort();\n                },\n\n                get uniqueAssetCategories() {\n                    return [...new Set(this.assets.map(a => a.Categoria).filter(v => v && v !== '-'))].sort();\n                },"
if t2 in text:
    text = text.replace(t2, r2)
else:
    # Try simpler match
    text = text.replace("get uniqueAssetStatuses() {", "get uniqueAssetCategories() { return [...new Set(this.assets.map(a => a.Categoria).filter(v => v && v !== '-'))].sort(); }, get uniqueAssetStatuses() {")

# 3. Update assetFiltersActive
t3 = "|| this.assetFilters.status !== 'all';"
r3 = "|| this.assetFilters.status !== 'all' || this.assetFilters.category !== 'all';"
text = text.replace(t3, r3)

# 4. Inject Categoria Filter UI
t4 = '<select x-model="assetFilters.work"'
if t4 in text:
    # Find the end of the work select div
    idx = text.find(t4)
    end_div = text.find('</div>', idx) + 6
    new_filter = '''
                <div class="min-w-[140px]">
                    <label class="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Categoria</label>
                    <select x-model="assetFilters.category" class="w-full bg-slate-900/50 border border-white/5 rounded-xl text-[11px] px-4 py-2.5 text-slate-200 focus:ring-1 focus:ring-sky-500">
                        <option value="all">Todas</option>
                        <template x-for="cat in uniqueAssetCategories" :key="cat">
                            <option :value="cat" x-text="cat"></option>
                        </template>
                    </select>
                </div>'''
    if 'assetFilters.category' not in text:
        text = text[:end_div] + new_filter + text[end_div:]

# 5. Enhance filteredAssets with Logic
t5 = """                            .filter(a => {
                                if (this.assetFilters.month === 'all') return true;
                                return a.Mes_Referencia === this.assetFilters.month;
                            })"""

r5 = """                            .filter(a => this.assetFilters.category === 'all' || (a.Categoria || '').toUpperCase() === this.assetFilters.category.toUpperCase())
                            .filter(a => {
                                if (this.assetFilters.month === 'all') return true;
                                
                                const targetMonth = this.assetFilters.month;
                                if (a.Mes_Referencia === targetMonth) return true;
                                
                                const arrivalDate = this.parseExcelDate(a['Data de Chegada na Obra'] || a.Chegada);
                                const departureDate = this.parseExcelDate(a.Saida || a['Data Sada. da Obra']);
                                
                                if (!arrivalDate) return false;
                                
                                const monthsBr = ['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ'];
                                const [mStr, yStr] = targetMonth.split('/');
                                const targetDate = new Date(2000 + parseInt(yStr), monthsBr.indexOf(mStr), 15);
                                
                                const startOfMonth = new Date(targetDate.getFullYear(), targetDate.getMonth(), 1);
                                const endOfMonth = new Date(targetDate.getFullYear(), targetDate.getMonth() + 1, 0);
                                
                                return arrivalDate <= endOfMonth && (!departureDate || departureDate >= startOfMonth);
                            })"""

if t5 in text:
    text = text.replace(t5, r5)
else:
    # Try more generic
    text = text.replace("return a.Mes_Referencia === this.assetFilters.month;", "return a.Mes_Referencia === this.assetFilters.month || (this.parseExcelDate(a['Data de Chegada na Obra'] || a.Chegada) <= new Date(2000 + parseInt(this.assetFilters.month.split('/')[1]), ['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ'].indexOf(this.assetFilters.month.split('/')[0]), 28) && (!this.parseExcelDate(a.Saida || a['Data Sada. da Obra']) || this.parseExcelDate(a.Saida || a['Data Sada. da Obra']) >= new Date(2000 + parseInt(this.assetFilters.month.split('/')[1]), ['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ'].indexOf(this.assetFilters.month.split('/')[0]), 1)));")

# 6. Add parseExcelDate helper
t6 = "formatAssetDate(raw) {"
r6 = """parseExcelDate(val) {
                if (!val || val === 0 || val === '-') return null;
                if (val instanceof Date) return val;
                if (typeof val === 'number') return new Date(Math.round((val - 25569) * 86400 * 1000));
                const d = new Date(val);
                return isNaN(d.getTime()) ? null : d;
            },
            formatAssetDate(raw) {"""
if t6 in text and "parseExcelDate" not in text:
    text = text.replace(t6, r6)

with open('controle_contratos_backup_20260413 - contrato e equipamento.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("HTML Update Successful")
