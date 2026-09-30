import re

path = r'C:\Users\bit\.gemini\antigravity\scratch\materialnet\templates\dashboard.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update CSS badges
old_css = """.cpse-badge-ONGC { background-color: rgba(234, 179, 8, 0.2); color: #facc15; border: 1px solid rgba(234, 179, 8, 0.5); }"""
new_css = """.cpse-badge-ONGC { background-color: rgba(234, 179, 8, 0.2); color: #facc15; border: 1px solid rgba(234, 179, 8, 0.5); }
        .cpse-badge-NTPC { background-color: rgba(6, 182, 212, 0.2); color: #22d3ee; border: 1px solid rgba(6, 182, 212, 0.5); }
        .cpse-badge-SAIL { background-color: rgba(99, 102, 241, 0.2); color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.5); }
        .cpse-badge-Coal_India, .cpse-badge-CoalIndia { background-color: rgba(20, 184, 166, 0.2); color: #2dd4bf; border: 1px solid rgba(20, 184, 166, 0.5); }"""
if '.cpse-badge-NTPC' not in content:
    content = content.replace(old_css, new_css)

# 2. Update getCpseBadge function
old_badge_func = "const valid = ['BHEL', 'GAIL', 'IOCL', 'HPCL', 'BPCL', 'ONGC'];\n            const cls = valid.includes(cpse) ? `cpse-badge-${cpse}` : 'cpse-badge-default';"
new_badge_func = """const valid = ['BHEL', 'GAIL', 'IOCL', 'HPCL', 'BPCL', 'ONGC', 'NTPC', 'SAIL', 'Coal India'];
            const safeClass = (cpse || '').replace(/\\s+/g, '_');
            const cls = valid.includes(cpse) ? `cpse-badge-${safeClass}` : 'cpse-badge-default';"""
content = content.replace(old_badge_func, new_badge_func)

# 3. Update explorer dropdown options
old_opts = """<option value="BPCL">BPCL</option>
                        <option value="ONGC">ONGC</option>"""
new_opts = """<option value="BPCL">BPCL</option>
                        <option value="ONGC">ONGC</option>
                        <option value="NTPC">NTPC</option>
                        <option value="SAIL">SAIL</option>
                        <option value="Coal India">Coal India</option>"""
if '<option value="NTPC">NTPC</option>' not in content:
    content = content.replace(old_opts, new_opts)

# 4. Update colors in loadViz
old_colors = "{'BHEL': '#3b82f6', 'GAIL': '#10b981', 'IOCL': '#f97316', 'HPCL': '#a855f7', 'BPCL': '#ef4444', 'ONGC': '#eab308'};"
new_colors = "{'BHEL': '#3b82f6', 'GAIL': '#10b981', 'IOCL': '#f97316', 'HPCL': '#a855f7', 'BPCL': '#ef4444', 'ONGC': '#eab308', 'NTPC': '#06b6d4', 'SAIL': '#818cf8', 'Coal India': '#2dd4bf'};"
content = content.replace(old_colors, new_colors)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Dashboard template updated with multi-sector CPSE support!")
