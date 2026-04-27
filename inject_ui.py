import sys

with open('controle_contratos_backup_20260413 - contrato e equipamento.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace 1: Hide KPIs for Contracts
t1 = '<!-- KPI Cards -->\n        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8"'
r1 = '<!-- KPI Cards -->\n        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8" x-show="dataView === \'contracts\'"'
if t1 in text:
    text = text.replace(t1, r1)
else:
    t1_alt = '<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">'
    r1_alt = '<div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8" x-show="dataView === \'contracts\'">'
    text = text.replace(t1_alt, r1_alt, 1)

# Replace 2: Inject Equipment Dashboards
t2 = '            </template>\n        </div>\n\n        <!-- Floating Filters Bar'
r2 = '''            </template>
        </div>

        <!-- Equipment Global Dashboards & KPIs -->
        <div x-show="dataView === 'assets'" x-cloak class="mb-12 animate-fade-in-up">
            <!-- Globals -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div class="glass p-6 rounded-3xl animate-fade-in card-gradient overflow-hidden relative">
                    <p class="text-slate-400 text-sm font-medium mb-2 uppercase tracking-wide">Total de Equipamentos</p>
                    <h3 class="text-3xl font-bold text-white mb-2" x-text="filteredAssets.length"></h3>
                </div>
                <div class="glass p-6 rounded-3xl animate-fade-in card-gradient overflow-hidden relative">
                    <p class="text-slate-400 text-sm font-medium mb-2 uppercase tracking-wide">Horas Trabalhadas</p>
                    <h3 class="text-3xl font-bold text-sky-400 mb-2" x-text="filteredAssets.reduce((sum, a) => sum + (parseFloat(a.HorasTrabalhadas)||0), 0).toLocaleString('pt-BR', {maximumFractionDigits:1}) + 'h'"></h3>
                </div>
                <div class="glass p-6 rounded-3xl animate-fade-in card-gradient overflow-hidden relative">
                    <p class="text-slate-400 text-sm font-medium mb-2 uppercase tracking-wide">Horas em Garantia</p>
                    <h3 class="text-3xl font-bold text-rose-400 mb-2" x-text="filteredAssets.reduce((sum, a) => sum + Math.max(0, 200 - (parseFloat(a.HorasTrabalhadas)||0)), 0).toLocaleString('pt-BR', {maximumFractionDigits:1}) + 'h'"></h3>
                </div>
            </div>
            
            <h3 class="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4">Métricas por Família</h3>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                <template x-for="fam in getAssetFamilyMetrics" :key="fam.name">
                    <div class="bg-slate-900/50 border border-white/5 rounded-2xl p-4 flex flex-col justify-between hover:bg-slate-800/50 transition-all border-l-4 border-l-sky-500">
                        <div class="flex justify-between items-start mb-4">
                            <span class="text-xs font-bold text-slate-200" x-text="fam.name"></span>
                            <span class="text-[10px] bg-sky-500/10 text-sky-400 px-2 py-0.5 rounded-full font-bold whitespace-nowrap" x-text="fam.percentTotal + '% Frota'"></span>
                        </div>
                        
                        <div class="flex items-end gap-3 mb-4">
                            <div class="text-3xl font-black text-white" x-text="fam.count"></div>
                            <div class="text-[10px] text-slate-400 font-bold uppercase mb-1">Unidades</div>
                        </div>

                        <div class="space-y-3 mt-auto">
                            <div class="flex justify-between text-[10px] uppercase font-bold tracking-wider">
                                <span class="text-emerald-400">Trab: <span x-text="fam.horasT.toLocaleString('pt-BR', {maximumFractionDigits:0}) + 'h'"></span></span>
                                <span class="text-rose-400">Gar: <span x-text="fam.horasG.toLocaleString('pt-BR', {maximumFractionDigits:0}) + 'h'"></span></span>
                            </div>
                            <div class="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden flex">
                                <div class="h-full bg-emerald-500 transition-all duration-1000" :style="`width: ${(fam.horasT / (fam.horasT + fam.horasG + 0.1) * 100)}%`"></div>
                                <div class="h-full bg-rose-500 transition-all duration-1000" :style="`width: ${(fam.horasG / (fam.horasT + fam.horasG + 0.1) * 100)}%`"></div>
                            </div>
                        </div>
                    </div>
                </template>
            </div>
        </div>

        <!-- Floating Filters Bar'''
if '<!-- Equipment Global Dashboards & KPIs -->' not in text:
    text = text.replace(t2, r2)
    
with open('controle_contratos_backup_20260413 - contrato e equipamento.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Success!')
