import sys

with open('controle_contratos_backup_20260413 - contrato e equipamento.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. UI Dropdown
ui_target = '''                <div class="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
                    <div class="min-w-[180px]">
                        <label class="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Equipamento</label>'''
ui_replacement = '''                <div class="flex flex-col sm:flex-row gap-3 w-full sm:w-auto flex-wrap">
                    <div class="min-w-[120px]">
                        <label class="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Mês</label>
                        <select x-model="assetFilters.month" class="w-full bg-slate-900/50 border border-white/5 rounded-xl text-[11px] px-4 py-2.5 text-slate-200 focus:ring-1 focus:ring-sky-500">
                            <option value="all">Todos os meses</option>
                            <template x-for="m in uniqueAssetMonths" :key="m">
                                <option :value="m" x-text="m"></option>
                            </template>
                        </select>
                    </div>
                    <div class="min-w-[180px]">
                        <label class="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2">Equipamento</label>'''
if ui_target in text:
    text = text.replace(ui_target, ui_replacement)
else:
    print("Warning: UI Target missing")

# 2. State
text = text.replace("assetFilters: { equipment: 'all', company: 'all', work: 'all', status: 'all' },",
                    "assetFilters: { month: 'all', equipment: 'all', company: 'all', work: 'all', status: 'all' },")
text = text.replace("this.assetFilters = { equipment: 'all', company: 'all', work: 'all', status: 'all' };",
                    "this.assetFilters = { month: 'all', equipment: 'all', company: 'all', work: 'all', status: 'all' };")

# 3. uniqueAssetMonths getter
getter_target = '''                    get uniqueAssetCompanies() {'''
getter_replacement = '''                    get uniqueAssetMonths() {
                        return [...new Set(this.assets.map(a => a.Mes_Referencia).filter(v => v && v !== '-'))]
                            .sort((a,b) => {
                                const m1 = a.split('/'); const m2 = b.split('/');
                                const nm1 = ['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ'].indexOf(m1[0]);
                                const nm2 = ['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ'].indexOf(m2[0]);
                                if (m1[1] !== m2[1]) return m1[1].localeCompare(m2[1]);
                                return nm1 - nm2;
                            });
                    },

                    get uniqueAssetCompanies() {'''
if getter_target in text:
    text = text.replace(getter_target, getter_replacement)
else:
    print("Warning: Getter Target missing")

# 4. Filters logic
text = text.replace(
'''if (this.filters.month !== 'all' && a.Mes_Referencia && a.Mes_Referencia !== this.filters.month) continue;''',
'''if (this.assetFilters.month !== 'all' && a.Mes_Referencia && a.Mes_Referencia !== this.assetFilters.month) continue;'''
)

text = text.replace(
'''if (this.filters.month === 'all' && processedALs.has(uniqueKey)) continue;''',
'''if (this.assetFilters.month === 'all' && processedALs.has(uniqueKey)) continue;'''
)

text = text.replace(
'''                            .filter(a => {
                                if (this.filters.month === 'all') return true;
                                return a.Mes_Referencia === this.filters.month;
                            })''',
'''                            .filter(a => {
                                if (this.assetFilters.month === 'all') return true;
                                return a.Mes_Referencia === this.assetFilters.month;
                            })'''
)

# 5. Active check
text = text.replace(
'''                    get assetFiltersActive() {
                        return this.assetFilters.equipment !== 'all'
                            || this.assetFilters.company !== 'all'
                            || this.assetFilters.work !== 'all'
                            || this.assetFilters.status !== 'all';
                    },''',
'''                    get assetFiltersActive() {
                        return this.assetFilters.month !== 'all'
                            || this.assetFilters.equipment !== 'all'
                            || this.assetFilters.company !== 'all'
                            || this.assetFilters.work !== 'all'
                            || this.assetFilters.status !== 'all';
                    },'''
)

# 6. Reporting Period context
text = text.replace(
'''                    get reportingPeriod() {
                        if (this.dataView !== 'assets' || this.filters.month === 'all') return '';
                        const [mStr, yStr] = this.filters.month.split('/');''',
'''                    get reportingPeriod() {
                        if (this.dataView !== 'assets' || this.assetFilters.month === 'all') return '';
                        const [mStr, yStr] = this.assetFilters.month.split('/');'''
)

with open('controle_contratos_backup_20260413 - contrato e equipamento.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("HTML UI and Filtering updated perfectly.")
