
import sys
import os

# Script para reconstruir o contractDashboard sem erros
state = """
                lastUpdated: window.LAST_UPDATED || new Date().toLocaleString('pt-BR'),
                currentView: 'overview',
                filters: { month: 'all' },
                showFilters: false,
                assets: [],
                assetFilters: {
                    month: 'all',
                    equipment: 'all',
                    company: 'all',
                    work: 'all',
                    status: 'all',
                    category: 'all'
                },
                assetSortBy: 'al',
                assetSortDir: 'asc',
                assetSummarySortBy: 'equipment',
                assetSummarySortDir: 'asc',
                currentAsset: null,
                drilldown: {
                    isOpen: false,
                    type: null,
                    title: '',
                    context: null,
                    selectedId: null,
                    selectedFamily: null,
                    selectedAsset: null,
                    fleet: null,
                    dailyDetail: null
                },
                selectedIndividualAsset: null,
                isIndividualAssetModalOpen: false,
                reportingPeriod: '',
                searchTerm: '',
                sectorColors: {},

                normalizeText(text) {
                    if (!text) return "";
                    return text.toString().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").toUpperCase().trim();
                },

                getReportingMonth(date = new Date(), isAsset = false) {
                    const day = date.getDate();
                    let month = date.getMonth(); 
                    let year = date.getFullYear();
                    if (isAsset && day > 20) {
                        month++;
                        if (month > 11) { month = 0; year++; }
                    }
                    const monthsBr = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ'];
                    return `${monthsBr[month]}/${year.toString().slice(-2)}`;
                },

                getAssetSummarySortIndicator(col) { return ''; },
                setAssetSummarySort(col) { },

                getGuaranteeHours(monthRef) {
                    if (!monthRef || monthRef === 'all') return 200;
                    const rainyPeriods = ['NOV/25', 'DEZ/25', 'JAN/26', 'FEV/26', 'MAR/26'];
                    const upperRef = monthRef.toUpperCase();
                    return rainyPeriods.some(p => upperRef.includes(p)) ? 0 : 200;
                },

                parseMesAno(mesStr) {
                    if (!mesStr) return 0;
                    const m = mesStr.split('/');
                    if (m.length < 2) return 0;
                    const mesMap = {'JAN':1,'FEV':2,'MAR':3,'ABR':4,'MAI':5,'JUN':6,'JUL':7,'AGO':8,'SET':9,'OUT':10,'NOV':11,'DEZ':12};
                    return (parseInt(m[1]) || 0) * 100 + (mesMap[m[0].toUpperCase()] || 0);
                },

                get reportingPeriod() {
                    if (this.assetFilters.month === 'all') return '';
                    const [mStr, yStr] = this.assetFilters.month.split('/');
                    const monthsBr = ['JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ'];
                    const mIdx = monthsBr.indexOf(mStr.toUpperCase());
                    const year = 2000 + parseInt(yStr);
                    const dateInicio = new Date(year, mIdx - 1, 21);
                    const dateFim = new Date(year, mIdx, 20);
                    const fmt = (d) => d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
                    return `${fmt(dateInicio)} a ${fmt(dateFim)}`;
                },

                openFamilyDrilldown(family) {
                    this.drilldown.isOpen = true; 
                    this.drilldown.type = 'family';
                    this.drilldown.context = 'family';
                    this.drilldown.selectedId = family;
                    this.drilldown.selectedFamily = family;
                    this.drilldown.selectedAsset = null;
                    this.drilldown.title = `Detalhamento Família: ${family}`;
                },

                openPartnerDrilldown(partner) {
                    this.drilldown.type = 'family';
                    this.drilldown.context = 'partner';
                    this.drilldown.selectedId = partner;
                    this.drilldown.selectedFamily = null;
                    this.drilldown.selectedAsset = null;
                    this.drilldown.title = `Detalhamento Parceiro: ${partner}`;
                    this.drilldown.isOpen = true;
                },

                openAssetDrilldown(al) {
                    const asset = this.filteredAssets.find(a => (a.AL || a.al) === al);
                    this.drilldown.type = 'asset';
                    this.drilldown.selectedAsset = asset;
                    this.drilldown.selectedFamily = null;
                    this.drilldown.title = `Ativo: ${al}`;
                    this.drilldown.isOpen = true;
                },

                get drilldownAssets() {
                    if (!this.drilldown.selectedId && !this.drilldown.selectedFamily && !this.drilldown.selectedAsset) return [];
                    if (this.drilldown.type === 'asset' && this.drilldown.selectedAsset) return [this.drilldown.selectedAsset];
                    let list = [];
                    if (this.drilldown.context === 'partner') {
                        list = this.filteredAssets.filter(a => this.normalizeCompanyName(a.Empresa) === this.drilldown.selectedId);
                    } else {
                        const famName = this.drilldown.selectedFamily || this.drilldown.selectedId;
                        list = this.filteredAssets.filter(a => this.getAssetEquipmentGroup(a) === famName);
                    }
                    const field = this.assetSortBy;
                    const dir = this.assetSortDir === 'asc' ? 1 : -1;
                    return list.sort((a, b) => {
                        let valA, valB;
                        if (field === 'al') {
                            valA = (a.AL || "").toString().toLowerCase();
                            valB = (b.AL || "").toString().toLowerCase();
                            return valA.localeCompare(valB, 'pt-BR', { numeric: true }) * dir;
                        } else if (field === 'company') {
                            valA = (a.Empresa || "").toString().toLowerCase();
                            valB = (b.Empresa || "").toString().toLowerCase();
                            return valA.localeCompare(valB, 'pt-BR') * dir;
                        } else if (field === 'worked') {
                            valA = parseFloat(a.HorasTrabalhadas) || 0;
                            valB = parseFloat(b.HorasTrabalhadas) || 0;
                            return (valA - valB) * dir;
                        } else if (field === 'guarantee') {
                            valA = Math.max(0, this.getGuaranteeHours(a.Mes_Referencia) - (parseFloat(a.HorasTrabalhadas) || 0));
                            valB = Math.max(0, this.getGuaranteeHours(b.Mes_Referencia) - (parseFloat(b.HorasTrabalhadas) || 0));
                            return (valA - valB) * dir;
                        } else if (field === 'maintenance') {
                            valA = parseFloat(a.TempoManutencao) || 0;
                            valB = parseFloat(b.TempoManutencao) || 0;
                            return (valA - valB) * dir;
                        }
                        return 0;
                    });
                },

                get drilldownMetrics() {
                    const assets = this.drilldownAssets;
                    const metrics = assets.reduce((acc, a) => {
                        const hT = parseFloat(a.HorasTrabalhadas) || 0;
                        const hG = Math.max(0, this.getGuaranteeHours(a.Mes_Referencia) - hT);
                        acc.workedHours += hT;
                        acc.idleHours += hG;
                        return acc;
                    }, { workedHours: 0, idleHours: 0 });
                    const total = metrics.workedHours + metrics.idleHours || 1;
                    metrics.workedPerc = (metrics.workedHours / total * 100).toFixed(1) + '%';
                    metrics.idlePerc = (metrics.idleHours / total * 100).toFixed(1) + '%';
                    metrics.workedEquiv = Math.round(metrics.workedHours / 200);
                    metrics.idleEquiv = Math.round(metrics.idleHours / 200);
                    return metrics;
                },

                init() {
                    this.assets = window.ASSETS_DATA || [];
                    this.filters.month = 'all';
                    this.$watch('assetFilters', () => setTimeout(() => this.updateCharts(), 50), {deep: true});
                    this.$watch('filters', () => this.updateCharts(), { deep: true });
                    this.$watch('currentView', () => this.updateCharts());
                    setTimeout(() => this.updateCharts(), 200);
                },

                formatCurrency(val) {
                    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val || 0);
                },

                parseNumber(val) {
                    if (typeof val === 'number') return isNaN(val) ? 0 : val;
                    if (!val || val === '-' || val === ' ') return 0;
                    let clean = val.toString().replace(/[\\sR\\$]/g, '');
                    if (clean.includes(',') && clean.includes('.')) clean = clean.replace(/\\./g, '').replace(',', '.');
                    else if (clean.includes(',')) clean = clean.replace(',', '.');
                    const num = parseFloat(clean);
                    return isNaN(num) ? 0 : num;
                },

                parseExcelDate(val) {
                    if (!val || val === '-' || val === ' ') return null;
                    if (val instanceof Date) return val;
                    if (typeof val === 'number' && val > 30000 && val < 60000) return new Date((val - 25569) * 86400000);
                    const raw = val.toString().trim();
                    const isoMatch = raw.match(/^(\\d{4})[-/](\\d{2})[-/](\\d{2})$/);
                    if (isoMatch) return new Date(isoMatch[1], isoMatch[2] - 1, isoMatch[3]);
                    const brMatch = raw.match(/^(\\d{2})[-/](\\d{2})[-/](\\d{2,4})$/);
                    if (brMatch) {
                        const y = brMatch[3].length === 2 ? 2000 + parseInt(brMatch[3]) : parseInt(brMatch[3]);
                        return new Date(y, parseInt(brMatch[2]) - 1, parseInt(brMatch[1]));
                    }
                    const d = new Date(raw);
                    return isNaN(d.getTime()) ? null : d;
                },

                cleanInlineText(value) {
                    if (value === null || value === undefined) return '';
                    return value.toString().replace(/[\\r\\n]+/g, ' ').replace(/\\s+/g, ' ').trim();
                },

                formatAssetAL(asset) {
                    return this.cleanInlineText(asset?.AL || '') || '-';
                },

                formatAssetEquipment(asset) {
                    return this.cleanInlineText(asset?.['Equipamento'] || '') || '-';
                },

                getAssetEquipmentGroup(asset) {
                    const raw = this.formatAssetEquipment(asset);
                    if (!raw || raw === '-') return '-';
                    let grouped = raw.toUpperCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');
                    grouped = grouped.replace(/["']/g, ' ').replace(/[.,;:/\\\\-]+/g, ' ').replace(/\\s*\\([^)]*\\)\\s*/g, ' ');
                    grouped = grouped.replace(/\\b\\d+\\s*[Xx]\\s*\\d+\\b/g, ' ').replace(/\\b\\d+[A-Z]*\\b/g, ' ').replace(/\\b(?:X|X\\/)\\d+\\b/g, ' ');
                    grouped = grouped.replace(/\\b(?:KVA|KV|CV|HP|TON|T|KG|G|L|LT|LTS|M3|M2|M|MM|CM|PCM)\\b/g, ' ').replace(/\\s+/g, ' ').trim();
                    return grouped || raw;
                },

                formatAssetCompany(asset) {
                    return this.cleanInlineText(asset?.['Proprietário'] || asset?.['Proprietario'] || asset?.['Empresa'] || '') || '-';
                },

                formatAssetStatus(asset) {
                    const status = this.cleanInlineText(asset?.['Status Mob/Desmob.'] || asset?.Status || '').toUpperCase();
                    return status.includes('DESMOBIL') ? 'DESMOBILIZADO' : 'MOBILIZADO';
                },

                isAssetMobilized(asset) {
                    const st = this.formatAssetStatus(asset).toUpperCase();
                    if (!st || st === '-' || st === 'N/A' || st.includes('DESMOB') || st.includes('NÃO') || st.includes('NAO') || st.includes('SOLICITADO')) return false;
                    return st.includes('MOBIL'); 
                },

                formatAssetDate(value) {
                    if (value && !isNaN(Number(value)) && Number(value) > 1000000000) {
                        const d = new Date(Number(value));
                        if (!isNaN(d.getTime())) return `${String(d.getUTCDate()).padStart(2, '0')}/${String(d.getUTCMonth() + 1).padStart(2, '0')}/${String(d.getUTCFullYear()).slice(-2)}`;
                    }
                    const raw = this.cleanInlineText(value);
                    if (!raw || raw === '-' || raw.toUpperCase() === 'TRANSF.') return raw || '-';
                    const isoMatch = raw.match(/^(\\d{4})[-/](\\d{2})[-/](\\d{2})$/);
                    if (isoMatch) return `${isoMatch[3]}/${isoMatch[2]}/${isoMatch[1].slice(-2)}`;
                    const brMatch = raw.match(/^(\\d{2})[-/](\\d{2})[-/](\\d{2,4})$/);
                    if (brMatch) return `${brMatch[1]}/${brMatch[2]}/${brMatch[3].slice(-2)}`;
                    const parsed = new Date(raw);
                    return isNaN(parsed.getTime()) ? raw : parsed.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: '2-digit' });
                },

                resetFilters() {
                    this.assetFilters = { month: 'all', equipment: 'all', company: 'all', work: 'all', status: 'all', category: 'all' };
                },

                get uniqueAssetEquipments() { return [...new Set(this.assets.map(a => this.getAssetEquipmentGroup(a)).filter(v => v && v !== '-'))].sort(); },
                get uniqueAssetMonths() {
                    return [...new Set(this.assets.map(a => a.Mes_Referencia).filter(v => v && v !== '-'))].sort((a,b) => {
                        const m1 = a.split('/'); const m2 = b.split('/');
                        const nm1 = ['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ'].indexOf(m1[0]);
                        const nm2 = ['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ'].indexOf(m2[0]);
                        return (m1[1] !== m2[1]) ? m1[1].localeCompare(m2[1]) : nm1 - nm2;
                    });
                },
                get uniqueAssetCompanies() { return [...new Set(this.assets.map(a => this.formatAssetCompany(a)).filter(v => v && v !== '-'))].sort(); },
                get uniqueAssetWorks() { return [...new Set(this.assets.map(a => this.cleanInlineText(a.Obra || '-')).filter(v => v && v !== '-'))].sort(); },
                get uniqueAssetCategories() { return [...new Set(this.assets.map(a => a.Categoria).filter(v => v && v !== '-'))].sort(); },
                get uniqueAssetStatuses() { return [...new Set(this.assets.map(a => this.formatAssetStatus(a)).filter(v => v && v !== '-'))].sort(); },
                get assetFiltersActive() {
                    return this.assetFilters.month !== 'all' || this.assetFilters.equipment !== 'all' || this.assetFilters.company !== 'all' || this.assetFilters.work !== 'all' || this.assetFilters.status !== 'all' || this.assetFilters.category !== 'all';
                },

                get getAssetFamilyMetrics() {
                    if (!this.filteredAssets.length) return [];
                    const map = new Map();
                    for (const a of this.filteredAssets) {
                        const fam = this.getAssetEquipmentGroup(a) || '-';
                        if (!map.has(fam)) map.set(fam, { name: fam, count: 0, horasT: 0, horasG: 0, als: new Set() });
                        const m = map.get(fam); m.als.add(a.AL); m.count = m.als.size;
                        const hT = parseFloat(a.HorasTrabalhadas) || 0;
                        const hG = Math.max(0, this.getGuaranteeHours(a.Mes_Referencia) - hT);
                        m.horasT += hT; m.horasG += hG;
                    }
                    return Array.from(map.values()).sort((a, b) => b.horasT - a.horasT);
                },

                get getIndividualAssetMetrics() {
                    if (!this.filteredAssets.length) return [];
                    const map = new Map();
                    for (const a of this.filteredAssets) {
                        const al = this.formatAssetAL(a);
                        const family = this.getAssetEquipmentGroup(a);
                        if (!map.has(al)) map.set(al, { al: al, family: family, horasT: 0, horasG: 0 });
                        const m = map.get(al);
                        const hT = parseFloat(a.HorasTrabalhadas) || 0;
                        const hG = Math.max(0, this.getGuaranteeHours(a.Mes_Referencia) - hT);
                        m.horasT += hT; m.horasG += hG;
                    }
                    return Array.from(map.values()).sort((a, b) => a.family < b.family ? -1 : (a.family > b.family ? 1 : b.horasT - a.horasT));
                },

                get getAssetAvailabilityMetrics() {
                    if (!this.filteredAssets.length) return [];
                    const map = new Map();
                    for (const a of this.filteredAssets) {
                        const al = this.formatAssetAL(a); const fam = this.getAssetEquipmentGroup(a);
                        if (!map.has(al)) map.set(al, { al: al, family: fam, tempoParado: 0, causas: [], descricoes: [], responsabilidades: [], mesesSet: new Set() });
                        const m = map.get(al); m.tempoParado += parseFloat(a.TempoManutencao) || 0;
                        if (a.Mes_Referencia) m.mesesSet.add(a.Mes_Referencia);
                        if (a.Causa && !m.causas.includes(a.Causa)) m.causas.push(a.Causa);
                        if (a.Responsabilidade && !m.responsabilidades.includes(a.Responsabilidade)) m.responsabilidades.push(a.Responsabilidade);
                    }
                    return Array.from(map.values()).map(m => {
                        const numMeses = Math.max(1, m.mesesSet.size);
                        const baseHoras = Array.from(m.mesesSet).reduce((acc, mes) => acc + this.getGuaranteeHours(mes), 0) || (numMeses * 200);
                        return { ...m, dm: parseFloat((Math.max(0, (baseHoras - m.tempoParado) / baseHoras) * 100).toFixed(1)), tooltipData: { causa: m.causas.join(' / '), resp: m.responsabilidades.join(' / '), base: baseHoras } };
                    }).filter(m => m.tempoParado > 0).sort((a, b) => a.family < b.family ? -1 : (a.family > b.family ? 1 : b.dm - a.dm));
                },

                get getAssetMaintenanceCauseMetrics() {
                    if (!this.filteredAssets.length) return [];
                    const map = new Map();
                    for (const a of this.filteredAssets) {
                        const fam = this.getAssetEquipmentGroup(a) || '-';
                        if (!map.has(fam)) map.set(fam, { family: fam, desgaste: 0, falha: 0, outros: 0 });
                        const m = map.get(fam); const dg = parseFloat(a.TempoDesgaste) || 0; const fl = parseFloat(a.TempoFalha) || 0; const totalMnt = parseFloat(a.TempoManutencao) || 0;
                        m.desgaste += dg; m.falha += fl; m.outros += Math.max(0, totalMnt - (dg + fl));
                    }
                    return Array.from(map.values()).filter(m => (m.desgaste + m.falha + m.outros) > 0).sort((a, b) => (b.desgaste + b.falha + b.outros) - (a.desgaste + a.falha + a.outros));
                },

                get getGlobalMaintenanceSummary() {
                    const metrics = this.getAssetMaintenanceCauseMetrics;
                    const summary = { desgaste: 0, falha: 0, outros: 0 };
                    metrics.forEach(m => { summary.desgaste += m.desgaste; summary.falha += m.falha; summary.outros += m.outros; });
                    return summary;
                },

                get getAssetEfficiencyMetrics() {
                    if (!this.filteredAssets.length) return [];
                    const map = new Map();
                    for (const a of this.filteredAssets) {
                        const fam = this.getAssetEquipmentGroup(a) || '-';
                        if (!map.has(fam)) map.set(fam, { family: fam, worked: 0, maintenance: 0, count: 0, totalGuarantee: 0 });
                        const m = map.get(fam); m.worked += parseFloat(a.HorasTrabalhadas) || 0; m.maintenance += parseFloat(a.TempoManutencao) || 0; m.count++;
                        m.totalGuarantee += this.getGuaranteeHours(a.Mes_Referencia);
                    }
                    return Array.from(map.values()).map(m => {
                        const baseG = m.totalGuarantee || (m.count * 200);
                        const pWorked = Math.min(100, (m.worked / baseG) * 100);
                        const pMaintenance = Math.min(100 - pWorked, (m.maintenance / baseG) * 100);
                        return { ...m, total: baseG, pWorked, pMaintenance, pIdle: Math.max(0, 100 - pWorked - pMaintenance), workedHours: m.worked, maintenanceHours: m.maintenance, idleHours: Math.max(0, baseG - m.worked - m.maintenance) };
                    }).sort((a, b) => b.total - a.total).slice(0, 15);
                },

                normalizeCompanyName(name) {
                    if (!name) return "";
                    return name.toUpperCase().replace(/LTDA|S\\.A\\.|S\\/A|EQUIPAMENTOS|CONSTRUTORA|SERVIOS|LOGISTICA|TRANSPORTES|LOCAO|ENGENHARIA|COMRCIO|INDSTRIA|LTDA - EPP/g, "").replace(/[.,&\\/\\\\-]/g, " ").replace(/\\s+/g, " ").trim();
                },

                get getEfficiencyByPartnerMetrics() {
                    const partners = {};
                    this.filteredAssets.forEach(a => {
                        const name = this.normalizeCompanyName(a.Empresa); if (!name) return;
                        if (!partners[name]) partners[name] = { worked: 0, guarantee: 0 };
                        const hW = parseFloat(a.HorasTrabalhadas) || 0;
                        partners[name].worked += hW;
                        partners[name].guarantee += Math.max(0, this.getGuaranteeHours(a.Mes_Referencia) - hW);
                    });
                    return Object.keys(partners).map(k => ({ name: k, ...partners[k] })).sort((a, b) => b.worked - a.worked);
                },

                get getFleetSizingMetrics() {
                    if (!this.filteredAssets.length) return [];
                    const map = new Map();
                    for (const a of this.filteredAssets) {
                        const fam = this.getAssetEquipmentGroup(a) || '-';
                        if (!map.has(fam)) map.set(fam, { family: fam, worked: 0, idle: 0, count: 0, costPerH: 0 });
                        const m = map.get(fam); m.worked += parseFloat(a.HorasTrabalhadas) || 0;
                        const baseG = this.getGuaranteeHours(a.Mes_Referencia);
                        m.idle += Math.max(0, baseG - (parseFloat(a.HorasTrabalhadas) || 0));
                        m.count++; if (a.ValorHora > 0) m.costPerH = a.ValorHora;
                    }
                    return Array.from(map.values()).map(m => {
                        const ideal = Math.ceil(m.worked / 200);
                        return { ...m, idealFleet: ideal, excessFleet: Math.max(0, m.count - ideal), idleCost: m.idle * m.costPerH, saturation: m.count > 0 ? (ideal / m.count) * 100 : 0 };
                    }).sort((a, b) => b.idleCost - a.idleCost);
                },

                get fleetSizingSummary() {
                    return this.getFleetSizingMetrics.reduce((acc, c) => { acc.idleCost += c.idleCost; acc.excess += c.excessFleet; return acc; }, { idleCost: 0, excess: 0 });
                },

                get getAssetMonthlyTrend() {
                    const months = this.uniqueAssetMonths;
                    const filteredBase = this.assets.filter(a => {
                        if (this.currentView !== 'overview') { const obraNum = this.currentView.replace(/[^0-9]/g, ''); if (!(a.Obra || '').toString().includes(obraNum)) return false; }
                        return (this.assetFilters.equipment === 'all' || this.getAssetEquipmentGroup(a) === this.assetFilters.equipment) && (this.assetFilters.company === 'all' || this.formatAssetCompany(a) === this.assetFilters.company) && (this.assetFilters.work === 'all' || this.cleanInlineText(a.Obra || '-') === this.assetFilters.work) && (this.assetFilters.status === 'all' || this.formatAssetStatus(a) === this.assetFilters.status) && (this.assetFilters.category === 'all' || (a.Categoria || '').toUpperCase() === this.assetFilters.category.toUpperCase());
                    });
                    return months.map(m => {
                        const filtered = filteredBase.filter(a => a.Mes_Referencia === m && this.isAssetMobilized(a));
                        const hT = filtered.reduce((s, a) => s + (parseFloat(a.HorasTrabalhadas)||0), 0);
                        const hG = filtered.reduce((s, a) => s + Math.max(0, this.getGuaranteeHours(m) - (parseFloat(a.HorasTrabalhadas)||0)), 0);
                        return { month: m, horasT: hT, horasG: hG, count: (new Set(filtered.map(a => a.AL))).size };
                    });
                },

                get filteredAssets() {
                    return this.assets.filter(a => {
                        if (this.currentView !== 'overview') { const oN = this.currentView.replace(/[^0-9]/g, ''); if (!(a.Obra || '').toString().includes(oN)) return false; }
                        if (this.assetFilters.equipment !== 'all' && this.getAssetEquipmentGroup(a) !== this.assetFilters.equipment) return false;
                        if (this.assetFilters.company !== 'all' && this.formatAssetCompany(a) !== this.assetFilters.company) return false;
                        if (this.assetFilters.work !== 'all' && this.cleanInlineText(a.Obra || '-') !== this.assetFilters.work) return false;
                        if (this.assetFilters.status !== 'all' && this.formatAssetStatus(a) !== this.assetFilters.status) return false;
                        if (this.assetFilters.category !== 'all') {
                            const nA = (a.Categoria || '').toUpperCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');
                            const nF = this.assetFilters.category.toUpperCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g, '');
                            if (nA !== nF) return false;
                        }
                        if (this.assetFilters.month !== 'all') {
                            const tM = this.assetFilters.month;
                            if (a.Mes_Referencia !== tM) {
                                const arrD = this.parseExcelDate(a['Data de Chegada na Obra'] || a.Chegada);
                                const depD = this.parseExcelDate(a.Saida || a['Data Sada. da Obra'] || a['Data Sada da Obra']);
                                const parts = tM.split('/');
                                if (parts.length === 2) {
                                    const mIdx = ['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ'].indexOf(parts[0].toUpperCase());
                                    const year = 2000 + parseInt(parts[1]);
                                    const startM = new Date(year, mIdx, 1); const endM = new Date(year, mIdx + 1, 0);
                                    if (!arrD || arrD > endM || (depD && depD < startM)) return false;
                                } else return false;
                            }
                        }
                        return true;
                    }).sort((a, b) => {
                        const vF = (asset) => {
                            switch (this.assetSortBy) {
                                case 'equipment': return this.getAssetEquipmentGroup(asset).toLowerCase();
                                case 'company': return this.formatAssetCompany(asset).toLowerCase();
                                case 'workedHours': return parseFloat(asset.HorasTrabalhadas) || 0;
                                case 'maintenanceTime': return parseFloat(asset.TempoManutencao) || 0;
                                case 'status': return this.formatAssetStatus(asset).toLowerCase();
                                case 'al': default: return this.formatAssetAL(asset).toLowerCase();
                            }
                        };
                        const va = vF(a), vb = vF(b);
                        const cmp = (typeof va === 'number' && typeof vb === 'number') ? va - vb : va.toString().localeCompare(vb.toString(), 'pt-BR', { numeric: true });
                        return this.assetSortDir === 'asc' ? cmp : -cmp;
                    });
                },

                setAssetSort(column) { if (this.assetSortBy === column) this.assetSortDir = this.assetSortDir === 'asc' ? 'desc' : 'asc'; else { this.assetSortBy = column; this.assetSortDir = 'asc'; } },
                getAssetSortIndicator(column) { return this.assetSortBy !== column ? '' : (this.assetSortDir === 'asc' ? '▲' : '▼'); },

                get viewTitle() { return this.currentView === 'overview' ? 'Dashboard Executivo' : 'Detalhamento Obra ' + this.currentView; },

                updateCharts() {
                    try {
                        const createGradient = (ctx, cS, cE) => { const g = ctx.createLinearGradient(0, 0, 0, 400); g.addColorStop(0, cS); g.addColorStop(1, cE); return g; };
                        ['assetFamily','individualAsset','disponibilidade','assetEvolution','maintenanceGlobal','maintenanceCause','fleetSizing','partnerEfficiency','efficiency'].forEach(k => { if (chartInstances[k]) chartInstances[k].destroy(); });
                        
                        const glassTooltip = { backgroundColor: 'rgba(15, 23, 42, 0.8)', titleColor: '#fff', bodyColor: '#cbd5e1', borderColor: 'rgba(255, 255, 255, 0.1)', borderWidth: 1, padding: 12, backdropFilter: 'blur(8px)' };
                        
                        const cFamily = document.getElementById('assetFamilyChart');
                        if (cFamily) {
                            const ctx = cFamily.getContext('2d'), metrics = this.getAssetFamilyMetrics;
                            chartInstances.assetFamily = new Chart(ctx, { type: 'bar', data: { labels: metrics.map(m => m.name), metricsReference: metrics, datasets: [
                                { label: 'Trabalhadas', data: metrics.map(m => m.horasT), backgroundColor: createGradient(ctx, 'rgba(16, 185, 129, 0.8)', 'rgba(16, 185, 129, 0.2)'), borderRadius: 8 },
                                { label: 'Garantia', data: metrics.map(m => m.horasG), backgroundColor: createGradient(ctx, 'rgba(244, 63, 94, 0.8)', 'rgba(244, 63, 94, 0.2)'), borderRadius: 8 }
                            ]}, options: { responsive: true, maintainAspectRatio: false, scales: { x: { stacked: true }, y: { stacked: true } }, onClick: (e, el, chart) => { const active = el.length > 0 ? el : chart.getElementsAtEventForMode(e, 'index', { intersect: false }, true); if (active.length > 0) this.openFamilyDrilldown(chart.data.metricsReference[active[0].index].name); }, plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8' } }, tooltip: glassTooltip, datalabels: { display: false } } } });
                        }

                        const cIndiv = document.getElementById('individualAssetChart');
                        if (cIndiv) {
                            const ctx = cIndiv.getContext('2d'), metrics = this.getIndividualAssetMetrics;
                            chartInstances.individualAsset = new Chart(ctx, { type: 'bar', data: { labels: metrics.map(m => m.al), metricsReference: metrics, datasets: [
                                { label: 'Trabalhadas', data: metrics.map(m => m.horasT), backgroundColor: 'rgba(16, 185, 129, 0.8)', borderRadius: 4 },
                                { label: 'Garantia', data: metrics.map(m => m.horasG), backgroundColor: 'rgba(244, 63, 94, 0.8)', borderRadius: 4 }
                            ]}, options: { responsive: true, maintainAspectRatio: false, scales: { x: { stacked: true, ticks: { display: false } }, y: { stacked: true, max: 200 } }, onClick: (e, el) => { if (el.length > 0) this.openAssetDrilldown(metrics[el[0].index].al); }, plugins: { legend: { display: false }, tooltip: glassTooltip, datalabels: { display: false } } } });
                        }

                        const cEvol = document.getElementById('assetEvolutionChart');
                        if (cEvol) {
                            const ctx = cEvol.getContext('2d'), trend = this.getAssetMonthlyTrend;
                            chartInstances.assetEvolution = new Chart(ctx, { type: 'bar', data: { labels: trend.map(d => d.month), datasets: [
                                { label: 'Trabalhadas', data: trend.map(d => d.horasT / (d.count || 1)), backgroundColor: 'rgba(16, 185, 129, 0.8)', borderRadius: 8 },
                                { label: 'Garantia', data: trend.map(d => d.horasG / (d.count || 1)), backgroundColor: 'rgba(244, 63, 94, 0.8)', borderRadius: 8 }
                            ]}, options: { responsive: true, maintainAspectRatio: false, scales: { x: { stacked: true }, y: { stacked: true } }, plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8' } }, tooltip: glassTooltip, datalabels: { display: false } } } });
                        }

                        const cPart = document.getElementById('partnerEfficiencyChart');
                        if (cPart) {
                            const ctx = cPart.getContext('2d'), metrics = this.getEfficiencyByPartnerMetrics;
                            chartInstances.partnerEfficiency = new Chart(ctx, { type: 'bar', data: { labels: metrics.map(m => m.name), datasets: [
                                { label: 'Trabalhadas', data: metrics.map(m => m.worked), backgroundColor: 'rgba(16, 185, 129, 0.6)', borderRadius: 4 },
                                { label: 'Garantia', data: metrics.map(m => m.guarantee), backgroundColor: 'rgba(244, 63, 94, 0.6)', borderRadius: 4 }
                            ]}, options: { responsive: true, maintainAspectRatio: false, scales: { x: { stacked: true }, y: { stacked: true } }, plugins: { legend: { position: 'top', labels: { color: '#94a3b8' } }, tooltip: glassTooltip, datalabels: { display: false } } } });
                        }

                        const cFleet = document.getElementById('fleetSizingChart');
                        if (cFleet) {
                            const ctx = cFleet.getContext('2d'), metrics = this.getFleetSizingMetrics.slice(0, 10);
                            chartInstances.fleetSizing = new Chart(ctx, { type: 'bar', data: { labels: metrics.map(m => m.family), datasets: [
                                { label: 'Ideal', data: metrics.map(m => m.idealFleet), backgroundColor: 'rgba(16, 185, 129, 0.8)', borderRadius: 4 },
                                { label: 'Excedente', data: metrics.map(m => m.excessFleet), backgroundColor: 'rgba(244, 63, 94, 0.8)', borderRadius: 4 }
                            ]}, options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, scales: { x: { stacked: true }, y: { stacked: true } }, plugins: { legend: { position: 'bottom', labels: { color: '#94a3b8' } }, tooltip: glassTooltip, datalabels: { display: false } } } });
                        }
                        
                        const cEff = document.getElementById('efficiencyChart');
                        if (cEff) {
                            const ctx = cEff.getContext('2d'), metrics = this.getAssetEfficiencyMetrics;
                            chartInstances.efficiency = new Chart(ctx, { type: 'bar', data: { labels: metrics.map(m => m.family), datasets: [
                                { label: 'Trabalho', data: metrics.map(m => m.pWorked), backgroundColor: 'rgba(16, 185, 129, 0.8)' },
                                { label: 'Manutenção', data: metrics.map(m => m.pMaintenance), backgroundColor: 'rgba(244, 63, 94, 0.8)' },
                                { label: 'Ocioso', data: metrics.map(m => m.pIdle), backgroundColor: 'rgba(71, 85, 105, 0.8)' }
                            ]}, options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false, scales: { x: { stacked: true, max: 100 }, y: { stacked: true } }, plugins: { legend: { display: false }, tooltip: glassTooltip, datalabels: { display: false } } } });
                        }

                    } catch (e) { console.error('ERRO no updateCharts:', e); }
                },

                renderDailyChart(asset) {
                    const canvas = document.getElementById('dailyMeterChart'); if (!canvas) return;
                    const ctx = canvas.getContext('2d'); if (chartInstances.dailyMeter) chartInstances.dailyMeter.destroy();
                    const [mStr, yStr] = asset.Mes_Referencia.split('/');
                    const mIdx = ['JAN','FEV','MAR','ABR','MAI','JUN','JUL','AGO','SET','OUT','NOV','DEZ'].indexOf(mStr.toUpperCase());
                    const year = 2000 + parseInt(yStr); const lastDayPrev = new Date(year, mIdx, 0).getDate();
                    let days = []; for (let d = 21; d <= lastDayPrev; d++) days.push(d); for (let d = 1; d <= 20; d++) days.push(d);
                    const data = days.map(d => parseFloat((asset.HorasDiarias || {})[d] || 0));
                    chartInstances.dailyMeter = new Chart(ctx, { type: 'bar', data: { labels: days, datasets: [{ label: 'Horas', data: data, backgroundColor: data.map(v => v >= 7.7 ? 'rgba(56, 189, 248, 0.8)' : 'rgba(244, 63, 94, 0.8)'), borderRadius: 5 }] }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, max: 24 } } } });
                }
"""

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, 'equipamentos.html'), 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_dashboard_func = False
dashboard_start_index = -1
dashboard_end_index = -1

for i, line in enumerate(lines):
    if 'window.contractDashboard = () => {' in line:
        in_dashboard_func = True
        dashboard_start_index = i
        new_lines.append(line)
        new_lines.append("            return {\n")
        new_lines.append(state)
        continue
    
    if in_dashboard_func:
        if '</script>' in line:
            # Encontrar o fechamento correto do dashboard (antes do script tag)
            # Mas vamos simplificar: procurar pela última chave antes do script
            in_dashboard_func = False
            new_lines.append("            };\n")
            new_lines.append("        };\n")
            new_lines.append(line)
        continue
    
    if not in_dashboard_func:
        new_lines.append(line)

with open(os.path.join(BASE_DIR, 'equipamentos.html'), 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
