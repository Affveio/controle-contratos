import os

with open('controle_contratos_backup_20260413 - contrato e equipamento.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix 1: Global KPI Total Equipamentos
t1 = 'x-text="filteredAssets.length"></h3>'
r1 = 'x-text="(new Set(filteredAssets.map(a => a.AL))).size"></h3>'
if t1 in text:
    text = text.replace(t1, r1)

# Fix 2: Family Metric Array
t2 = '''                    get getAssetFamilyMetrics() {
                        if (this.dataView !== 'assets' || !this.filteredAssets.length) return [];
                        
                        let totalFleetHours = 0;
                        let totalFleetCount = this.filteredAssets.length;
                        
                        const map = new Map();
                        
                        for (const a of this.filteredAssets) {
                            const fam = this.getAssetEquipmentGroup(a) || '-';
                            if (!map.has(fam)) map.set(fam, { name: fam, count: 0, horasT: 0, horasG: 0 });
                            
                            const m = map.get(fam);
                            m.count++;'''

r2 = '''                    get getAssetFamilyMetrics() {
                        if (this.dataView !== 'assets' || !this.filteredAssets.length) return [];
                        
                        let totalFleetHours = 0;
                        let totalFleetCount = (new Set(this.filteredAssets.map(a => a.AL))).size;
                        
                        const map = new Map();
                        
                        for (const a of this.filteredAssets) {
                            const fam = this.getAssetEquipmentGroup(a) || '-';
                            if (!map.has(fam)) map.set(fam, { name: fam, count: 0, horasT: 0, horasG: 0, als: new Set() });
                            
                            const m = map.get(fam);
                            m.als.add(a.AL);
                            m.count = m.als.size;'''

if t2 in text:
    text = text.replace(t2, r2)
else:
    print('T2 not found exactly! Falling back to regex or manual replace')
    # Use substring replace
    text = text.replace('let totalFleetCount = this.filteredAssets.length;', 'let totalFleetCount = (new Set(this.filteredAssets.map(a => a.AL))).size;')
    text = text.replace('if (!map.has(fam)) map.set(fam, { name: fam, count: 0, horasT: 0, horasG: 0 });', 'if (!map.has(fam)) map.set(fam, { name: fam, count: 0, horasT: 0, horasG: 0, _als: new Set() });')
    text = text.replace('m.count++;', 'if (a.AL) m._als.add(a.AL); m.count = m._als.size || 0;')

with open('controle_contratos_backup_20260413 - contrato e equipamento.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Success')
