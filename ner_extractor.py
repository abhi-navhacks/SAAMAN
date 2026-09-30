import re
from typing import Dict, Any

class NERExtractor:
    def __init__(self):
        # Material Types
        self.type_patterns = {
            'connector': r'\b(connector|cnctr|conn)\b',
            'fuse': r'\b(fuse)\b',
            'cable': r'\b(cable|wire)\b',
            'valve': r'\b(valve)\b',
            'bearing': r'\b(bearing|brg)\b',
            'terminal': r'\b(terminal|trmnl)\b',
            'switch': r'\b(switch|sw)\b',
            'seal': r'\b(seal|o-ring)\b',
            'ring': r'\b(ring)\b',
            'pump': r'\b(pump)\b',
            'pipe': r'\b(pipe|tube)\b'
        }
        
        # Grades
        self.grade_patterns = {
            'SS316L': r'\b(ss316l|ss 316l)\b',
            'SS316': r'\b(ss316|ss 316)\b',
            'SS': r'\b(ss|stainless steel)\b',
            'CS': r'\b(cs|carbon steel)\b',
            'MS': r'\b(ms|mild steel)\b',
            'Copper': r'\b(copper|cu)\b',
            'Tin Plated Copper': r'\b(tin plated copper)\b'
        }
        
        # Dimensions
        self.dim_pattern = r'(\d+(?:\.\d+)?)\s*(mm|inch|inch|sq\s*mm|sqmm|awg)'
        
        # Standard
        self.std_pattern = r'\b(is:?\s*\d+|astm\s*\w+|din\s*\d+|iso\s*\d+)\b'
        
        # Ratings
        self.volt_pattern = r'(\d+(?:\.\d+)?)\s*(v|kv|volts|volt)\b'
        self.curr_pattern = r'(\d+(?:\.\d+)?)\s*(a|amp|amps|ampere|ma)\b'
        
        # Connectors
        self.pin_pattern = r'(\d+)\s*(pin|pole|way)'
        self.pitch_pattern = r'(\d+(?:\.\d+)?)\s*mm\s*pitch'
        
        self.conn_type_patterns = {
            'D-Sub': r'\b(d-sub|dsub)\b',
            'DIN41612': r'\b(din41612)\b',
            'Mini-Fit Jr': r'\b(mini-fit jr|minifit jr)\b',
            'Berg': r'\b(berg)\b',
            'RJ45': r'\b(rj45)\b',
            'USB': r'\b(usb)\b',
            'BNC': r'\b(bnc)\b',
            'Euro': r'\b(euro)\b',
            'IDC': r'\b(idc)\b'
        }
        
        self.mount_patterns = {
            'PCB': r'\b(pcb)\b',
            'SMD': r'\b(smd|surface mount)\b',
            'TH': r'\b(th|through-hole|through hole)\b',
            'Panel': r'\b(panel mount)\b'
        }

    def convert_to_metric(self, value: float, unit: str) -> str:
        unit = unit.lower().replace(' ', '')
        if unit in ['inch', '"']:
            return f"{value * 25.4:.2f}mm"
        elif unit == 'awg':
            # Approximation for AWG to mm2
            return f"awg_{value}" 
        return f"{value}{unit}"

    def extract(self, text: str) -> Dict[str, Any]:
        text = str(text).lower()
        attrs = {}
        
        # Material Type
        for m_type, pat in self.type_patterns.items():
            if re.search(pat, text):
                attrs['material_type'] = m_type
                break
                
        # Grade
        for grade, pat in self.grade_patterns.items():
            if re.search(pat, text):
                attrs['material_grade'] = grade
                break
                
        # Dimensions
        dims = re.findall(self.dim_pattern, text)
        if dims:
            attrs['dimensions'] = [self.convert_to_metric(float(d[0]), d[1]) for d in dims]
            
        # Standard
        std = re.search(self.std_pattern, text)
        if std:
            attrs['standard'] = std.group(1).upper()
            
        # Ratings
        volt = re.search(self.volt_pattern, text)
        if volt:
            attrs['voltage_rating'] = f"{volt.group(1)}{volt.group(2)}"
            
        curr = re.search(self.curr_pattern, text)
        if curr:
            attrs['current_rating'] = f"{curr.group(1)}{curr.group(2)}"
            
        # Pins
        pins = re.search(self.pin_pattern, text)
        if pins:
            attrs['pin_count'] = int(pins.group(1))
            
        # Pitch
        pitch = re.search(self.pitch_pattern, text)
        if pitch:
            attrs['pitch'] = f"{pitch.group(1)}mm"
            
        # Connector Type
        for c_type, pat in self.conn_type_patterns.items():
            if re.search(pat, text):
                attrs['connector_type'] = c_type
                break
                
        # Mounting
        for m_type, pat in self.mount_patterns.items():
            if re.search(pat, text):
                attrs['mounting_type'] = m_type
                break
                
        return attrs
