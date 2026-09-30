from pypdf import PdfReader
import re

reader = PdfReader(r'C:\Users\bit\.gemini\antigravity\brain\8c3ffc4e-5627-4f97-9328-bf9929cde3bf\.tempmediaStorage\7dd0cd2cc8722df6.pdf')
full_text = ''
for p in reader.pages:
    full_text += p.extract_text() + '\n'

lines = full_text.split('\n')
items = []
current_item = None
code_pattern = re.compile(r'^\s*(\d+)\s+([A-Z0-9]{10,14})\s+')

for line in lines:
    m = code_pattern.match(line)
    if m:
        if current_item:
            items.append(current_item)
        current_item = {'sl': m.group(1), 'code': m.group(2), 'desc': []}
    elif current_item:
        if '---' in line or 'Page No' in line or 'OPEN TENDER' in line or 'Special Instructions' in line:
            continue
        cleaned = line.strip()
        if cleaned:
            current_item['desc'].append(cleaned)

if current_item:
    items.append(current_item)

print(f'Found {len(items)} items in this tender!')
for it in items[:15]:
    desc_str = ' | '.join(it['desc'])[:120]
    print(f"{it['code']}: {desc_str}")
