import re
import sys

def calc_csum(hex_array):
    s = sum(hex_array)
    return (128 - (s % 128)) % 128

def hex_to_arr(s):
    return [int(x, 16) for x in s.split()]

def make_rq1(addr, size):
    addr_arr = hex_to_arr(addr)
    size_arr = hex_to_arr(size)
    csum = calc_csum(addr_arr + size_arr)
    return f'F0 41 10 00 00 00 5E 11 {addr} {size} {csum:02X} F7'

def make_dt1(addr, data):
    addr_arr = hex_to_arr(addr)
    data_arr = hex_to_arr(data)
    csum = calc_csum(addr_arr + data_arr)
    return f'F0 41 10 00 00 00 5E 12 {addr} {data} {csum:02X} F7'

out = """

---

### Track 1 (Drum Kit) Pad/Partial 1
Base Address: `32 10 00 00` (First Key/Note Pad)

"""

# Let's extract Drum Kit Partial parameters from phantom.sysex.txt
# They start at line 3746: * [Drum Kit Partial]
with open('phantom.sysex.txt', 'r') as f:
    lines = f.readlines()

in_drum_partial = False
params = []

for i, line in enumerate(lines):
    if line.startswith('* [Drum Kit Partial]'):
        in_drum_partial = True
        continue
    if in_drum_partial and line.startswith('| 00 00 01 00 |Total Size |'):
        break
    
    if in_drum_partial and line.startswith('| '):
        # Match offset
        m_offset = re.search(r'\|(#?\s*[0-9A-Fa-f]{2}\s+[0-9A-Fa-f]{2})\s*\|', line)
        if m_offset:
            offset_str = m_offset.group(1).replace('#', '').strip()
            offset_parts = offset_str.split()
            if len(offset_parts) != 2:
                continue
            
            desc_match = re.search(r'\|\s*([^\|]+?)\s*\(\s*(-?\d+)\s*[-~]\s*(-?\d+)\s*\)', line)
            
            if not desc_match:
                desc_match = re.search(r'\|\s*([^\|]+?)\s*\|$', line)
                if desc_match and not "aaa" in desc_match.group(1) and not "bbb" in desc_match.group(1) and "Reserved" not in desc_match.group(1):
                    pass
            
            if desc_match:
                name = desc_match.group(1).strip()
                
                if "aaa" in name or "bbb" in name or "Total Size" in name:
                    continue
                
                addr = f"32 10 00 {offset_parts[1]}"
                
                range_match = re.search(r'\(\s*(-?\d+)\s*[-~]\s*(-?\d+)[^\)]*\)', line)
                if range_match:
                    try:
                        m1 = int(range_match.group(1))
                        m2 = int(range_match.group(2))
                        val_desc = f"{m1} to {m2}"
                    except:
                        val_desc = "Unknown Range"
                else:
                    val_desc = "Unknown Range"
                    
                if len(offset_parts) == 2:
                    params.append({
                        'name': name.replace(" (", "").strip(),
                        'addr': addr,
                        'desc': val_desc,
                        'size': '00 00 00 01'
                    })

for p in params:
    q = make_rq1(p['addr'], p['size'])
    d_min_dt1 = make_dt1(p['addr'], "00")
    d_max_dt1 = make_dt1(p['addr'], "01")

    out += f"#### {p['name']}\n"
    out += f"- **Target Address**: `{p['addr']}`\n"
    out += f"- **Expected Range/Values**: {p['desc']}\n"
    out += f"- **Query Command (RQ1)**: `{q}`\n"
    out += f"- **Set Command (DT1) Example (00)**: `{d_min_dt1}`\n"
    out += f"- **Set Command (DT1) Example (01)**: `{d_max_dt1}`\n\n"

with open('sysex_details.txt', 'a') as f:
    f.write(out)
print('Appended drum kit parameters to sysex_details.txt')
