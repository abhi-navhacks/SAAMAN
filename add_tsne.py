import os, re
path = r'C:\Users\bit\.gemini\antigravity\scratch\materialnet\templates\dashboard.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add Plotly
if 'plotly' not in content:
    content = content.replace('<script src="https://cdn.tailwindcss.com"></script>', '<script src="https://cdn.tailwindcss.com"></script>\n    <script src="https://cdn.plot.ly/plotly-2.32.0.min.js"></script>')

# 2. Add Tab Buttons
if 'data-tab="viz"' not in content:
    content = content.replace('<button data-tab="live" class="nav-btn', '<button data-tab="viz" class="nav-btn text-gray-300 hover:bg-gray-700 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors">🌌 2D Map</button>\n                        <button data-tab="live" class="nav-btn')
    content = content.replace('<button data-tab="live" class="nav-btn-mobile', '<button data-tab="viz" class="nav-btn-mobile text-gray-300 hover:bg-gray-700 hover:text-white block px-3 py-2 rounded-md text-base font-medium text-left">🌌 2D Map</button>\n                <button data-tab="live" class="nav-btn-mobile')

# 3. Add Tab Content
if 'id="tab-viz"' not in content:
    tab_html = '''        <!-- ==================== TAB: VIZ ==================== -->
        <div id="tab-viz" class="tab-content space-y-4">
            <div class="bg-gray-800 rounded-xl p-4 shadow-lg border border-gray-700 flex justify-between items-center">
                <h2 class="text-xl font-bold">Semantic Embedding Map (t-SNE)</h2>
                <div class="text-sm text-gray-400">Points grouped by material similarity</div>
            </div>
            <div class="bg-gray-800 rounded-xl shadow-lg border border-gray-700 p-2 h-[700px] w-full" id="tsne-plot">
                <!-- Plotly will inject here -->
            </div>
        </div>
        
        <!-- ==================== TAB: LIVE MATCHER ==================== -->'''
    content = content.replace('<!-- ==================== TAB: LIVE MATCHER ==================== -->', tab_html)

# 4. Add JS Logic
if 'loadViz()' not in content:
    js_logic = '''
        if (tabId === 'cnmc' && !$('#cnmc-tbody').dataset.loaded) loadCNMC();
        if (tabId === 'viz' && !$('#tsne-plot').dataset.loaded) loadViz();
'''
    content = content.replace("if (tabId === 'cnmc' && !$('#cnmc-tbody').dataset.loaded) loadCNMC();", js_logic)

if 'async function loadViz' not in content:
    loadviz_func = '''
        // --- VIZ TAB LOGIC ---
        async function loadViz() {
            const plotDiv = $('#tsne-plot');
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
                plotDiv.innerHTML = '<div class="flex items-center justify-center h-full text-red-400">Failed to load t-SNE data</div>';
            }
        }
        
        // --- LIVE MATCHER TAB LOGIC ---'''
    content = content.replace('// --- LIVE MATCHER TAB LOGIC ---', loadviz_func)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Dashboard HTML updated successfully.')
