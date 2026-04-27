import os

with open('controle_contratos_backup_20260413 - contrato e equipamento.html', 'r', encoding='utf-8') as f:
    text = f.read()

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

anchor = "} catch(e) {"
if anchor in text and "assetFamilyCanvas = document.getElementById" in text and "Gráfico de Ativos por Família" not in text:
    text = text.replace(anchor, chart_creation_logic + "\n                        " + anchor)

with open('controle_contratos_backup_20260413 - contrato e equipamento.html', 'w', encoding='utf-8') as f:
    f.write(text)

print('Chart script injection successful.')
