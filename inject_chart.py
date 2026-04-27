import os

with open('controle_contratos_backup_20260413 - contrato e equipamento.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace metrics grid with Canvas
grid_start = '<h3 class="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4">Métricas por Família</h3>'
grid_end = '        <!-- Floating Filters Bar '

new_block = '''        <h3 class="text-sm font-bold text-slate-400 uppercase tracking-widest mb-4">Métricas por Família</h3>
        <div class="glass p-6 rounded-3xl animate-fade-in relative">
            <div class="h-[300px] sm:h-[400px]">
                <canvas id="assetFamilyChart"></canvas>
            </div>
        </div>
    </div>

        <!-- Floating Filters Bar '''

if grid_start in text:
    idx_start = text.find(grid_start)
    idx_end = text.find('<!-- Floating Filters Bar', idx_start)
    if idx_start != -1 and idx_end != -1:
        text = text[:idx_start] + new_block + text[idx_end+len('<!-- Floating Filters Bar'):]

# Add watcher for assetFilters
watch_target = "this.$watch('filters.costCenter', () => this.updateCharts());"
watch_replacement = "this.$watch('filters.costCenter', () => this.updateCharts());\n                        this.$watch('assetFilters', () => setTimeout(() => this.updateCharts(), 50), {deep: true});\n                        this.$watch('dataView', () => setTimeout(() => this.updateCharts(), 50));"

if watch_target in text and "this.$watch('assetFilters'" not in text:
    text = text.replace(watch_target, watch_replacement)

# Inject assetFamily chart into updateCharts
update_charts_target = "const closingCanvas = document.getElementById('closingSummaryChart');"
update_charts_replacement = "const closingCanvas = document.getElementById('closingSummaryChart');\n                        const assetFamilyCanvas = document.getElementById('assetFamilyChart');"

if update_charts_target in text and "assetFamilyCanvas" not in text:
    text = text.replace(update_charts_target, update_charts_replacement)

destroy_target = "if (chartInstances.closing) chartInstances.closing.destroy();"
destroy_replacement = "if (chartInstances.closing) chartInstances.closing.destroy();\n                        if (chartInstances.assetFamily) chartInstances.assetFamily.destroy();"
if destroy_target in text and "chartInstances.assetFamily.destroy()" not in text:
    text = text.replace(destroy_target, destroy_replacement)

chart_creation_logic = """
                        // 7. Gráfico de Ativos por Família
                        if (assetFamilyCanvas && this.dataView === 'assets') {
                            const famMetrics = this.getAssetFamilyMetrics;
                            if (famMetrics.length > 0) {
                                const labels = famMetrics.map(f => f.name.substring(0, 15) + (f.name.length>15?'...':''));
                                const dataTrab = famMetrics.map(f => f.horasT);
                                const dataGar = famMetrics.map(f => f.horasG);
                                const dataQnt = famMetrics.map(f => f.count);

                                chartInstances.assetFamily = new Chart(assetFamilyCanvas, {
                                    type: 'bar',
                                    data: {
                                        labels: labels,
                                        datasets: [
                                            {
                                                label: 'Unidades',
                                                type: 'line',
                                                data: dataQnt,
                                                borderColor: '#38bdf8',
                                                backgroundColor: '#38bdf8',
                                                borderWidth: 3,
                                                pointRadius: 6,
                                                pointBackgroundColor: '#0f172a',
                                                pointBorderWidth: 2,
                                                yAxisID: 'yCount',
                                                datalabels: {
                                                    display: true,
                                                    color: '#38bdf8',
                                                    font: { weight: 'bold', size: 14 },
                                                    align: 'top',
                                                    offset: 6
                                                }
                                            },
                                            {
                                                label: 'Horas Trabalhadas',
                                                data: dataTrab,
                                                backgroundColor: '#10b981',
                                                stack: 'Stack 0',
                                                borderRadius: {topLeft: 0, topRight: 0, bottomLeft: 4, bottomRight: 4},
                                                yAxisID: 'yHours',
                                                datalabels: { display: false }
                                            },
                                            {
                                                label: 'Em Garantia',
                                                data: dataGar,
                                                backgroundColor: '#f43f5e',
                                                stack: 'Stack 0',
                                                borderRadius: {topLeft: 4, topRight: 4, bottomLeft: 0, bottomRight: 0},
                                                yAxisID: 'yHours',
                                                datalabels: { display: false }
                                            }
                                        ]
                                    },
                                    options: {
                                        responsive: true,
                                        maintainAspectRatio: false,
                                        interaction: {
                                            mode: 'index',
                                            intersect: false,
                                        },
                                        plugins: {
                                            legend: {
                                                labels: { color: '#94a3b8', font: { family: 'Inter', weight: 'bold' } }
                                            },
                                            tooltip: {
                                                backgroundColor: 'rgba(15, 23, 42, 0.9)',
                                                titleColor: '#e2e8f0',
                                                bodyColor: '#cbd5e1',
                                                padding: 12,
                                                borderColor: 'rgba(255,255,255,0.1)',
                                                borderWidth: 1,
                                                callbacks: {
                                                    label: function(ctx) {
                                                        let label = ctx.dataset.label || '';
                                                        let val = ctx.raw;
                                                        if (label === 'Unidades') return `${label}: ${val}`;
                                                        return `${label}: ${val.toLocaleString('pt-BR', {maximumFractionDigits:1})}h`;
                                                    }
                                                }
                                            }
                                        },
                                        scales: {
                                            x: {
                                                stacked: true,
                                                ticks: { color: '#94a3b8', font: { size: 10 } },
                                                grid: { color: 'rgba(255, 255, 255, 0.05)' }
                                            },
                                            yHours: {
                                                type: 'linear',
                                                display: true,
                                                position: 'left',
                                                stacked: true,
                                                title: { display: true, text: 'Horas Totais', color: '#64748b', font: { size: 10 } },
                                                ticks: { color: '#94a3b8' },
                                                grid: { color: 'rgba(255, 255, 255, 0.05)' }
                                            },
                                            yCount: {
                                                type: 'linear',
                                                display: true,
                                                position: 'right',
                                                title: { display: true, text: 'Unidades', color: '#38bdf8', font: { size: 10 } },
                                                ticks: { color: '#38bdf8' },
                                                grid: { drawOnChartArea: false }
                                            }
                                        }
                                    }
                                });
                            }
                        }
"""

inject_pattern = "const formatCurrency = (val) => {"
if inject_pattern in text and "AssetFamily" not in text.split("chartInstances.closing = ")[-1]:
    # Need to inject right before `return;` inside update logic? No, let's inject it right before `} catch(err)` or at the end of the giant updateCharts body.
    pass

# We will just inject it at the end of the updateCharts try block
split_mark = "requestAnimationFrame(() => this.drawSemicircle"
if split_mark in text:
    idx = text.rfind(split_mark)
    # Find the end of the semicircle block
    end_semi = text.find("}", idx) + 1
    if end_semi != 0 and "if (assetFamilyCanvas" not in text:
        text = text[:end_semi] + chart_creation_logic + text[end_semi:]
else:
    print("WARNING: split mark not found for chart injection")

with open('controle_contratos_backup_20260413 - contrato e equipamento.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Chart replacement successful.')
