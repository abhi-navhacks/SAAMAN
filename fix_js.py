import os
path = r'C:\Users\bit\.gemini\antigravity\scratch\materialnet\templates\dashboard.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

loadviz_func = '''
        async function loadViz() {
            const plotDiv = document.getElementById('tsne-plot');
            if (!plotDiv) return;
            if (plotDiv.dataset.loaded) return;
            plotDiv.innerHTML = '<div class="flex items-center justify-center h-full text-gray-400">Loading map...</div>';
            try {
                const data = await fetchAPI('/tsne');
                const points = data.points;
                
                const traces = {};
                const colors = {'BHEL': '#3b82f6', 'GAIL': '#10b981', 'IOCL': '#f97316', 'HPCL': '#a855f7', 'BPCL': '#ef4444', 'ONGC': '#eab308'};
                
                points.forEach(p => {
                    const cpse = p.cpse || 'Unknown';
                    if (!traces[cpse]) {
                        traces[cpse] = { x: [], y: [], text: [], mode: 'markers', type: 'scattergl', name: cpse, marker: {size: 8, opacity: 0.8, color: colors[cpse] || '#9ca3af'} };
                    }
                    traces[cpse].x.push(p.x);
                    traces[cpse].y.push(p.y);
                    traces[cpse].text.push(`[${p.code}]<br>${p.desc.substring(0,80)}`);
                });
                
                const plotData = Object.values(traces);
                const layout = {
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    font: { color: '#9ca3af' },
                    xaxis: { showgrid: true, gridcolor: '#374151', zeroline: false, showticklabels: false },
                    yaxis: { showgrid: true, gridcolor: '#374151', zeroline: false, showticklabels: false },
                    margin: { l: 20, r: 20, t: 30, b: 20 },
                    hovermode: 'closest'
                };
                
                Plotly.newPlot(plotDiv, plotData, layout, {responsive: true, displayModeBar: false});
                plotDiv.dataset.loaded = 'true';
            } catch(e) {
                console.error(e);
                plotDiv.innerHTML = '<div class="flex items-center justify-center h-full text-red-400">Failed to load t-SNE data. Check server logs.</div>';
            }
        }
'''

if 'async function loadViz' not in content:
    content = content.replace('    </script>\n</body>', loadviz_func + '\n    </script>\n</body>')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Inserted loadViz function')
else:
    print('loadViz already present')
