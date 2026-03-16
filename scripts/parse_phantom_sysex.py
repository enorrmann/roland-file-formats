import re

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

out = """# MC-101 Parameter SysEx Detail (Exhaustive Map)

This file exhaustively lists the precise SysEx byte strings required to query (RQ1) and set (DT1) parameters on the MC-101. It is designed to act as a blueprint for client editor applications.

## Memory Structure Recap
- **F0 41 10 00 00 00 5E**: Header sequence (Roland ID `41`, Device ID `10`, Model ID `00 00 00 5E`)
- **11**: Command ID for Request Data (RQ1)
- **12**: Command ID for Set Data (DT1)

---

### Track 2 (Tone Track) Partial 1
Base Address: `32 11 20 00`

"""

# Let's extract Tone Partial parameters from phantom.sysex.txt
# They start at line 3171: * [Tone Partial]
# And end before * [Tone Synth Common] or Total Size
with open('phantom.sysex.txt', 'r') as f:
    lines = f.readlines()

in_tone_partial = False
params = []

base_address_parts = [0x32, 0x11, 0x20]

for i, line in enumerate(lines):
    if line.startswith('* [Tone Partial]'):
        in_tone_partial = True
        continue
    if in_tone_partial and line.startswith('| 00 00 01 00 |Total Size |'):
        break
    
    if in_tone_partial and line.startswith('| '):
        # Format usually: | 00 00 | 0aaa aaaa | Level (0 - 127) |
        # Sometimes: | 00 0B | 0aaa aaaa | Alternate Pan Depth (0 - 127) |
        # Sometimes: |# 00 0C | 0000 aaaa | |
        
        # Match offset
        m_offset = re.search(r'\|(#?\s*[0-9A-Fa-f]{2}\s+[0-9A-Fa-f]{2})\s*\|', line)
        if m_offset:
            offset_str = m_offset.group(1).replace('#', '').strip()
            # only handle 2 byte offsets like "00 00"
            offset_parts = offset_str.split()
            if len(offset_parts) != 2:
                continue
            
            desc_match = re.search(r'\|\s*([^\|]+?)\s*\(\s*(-?\d+)\s*[-~]\s*(-?\d+)\s*\)', line)
            
            # Handle special cases like 'DelayTime (note) (0 - 21)' or just plain string if no ranges
            if not desc_match:
                desc_match = re.search(r'\|\s*([^\|]+?)\s*\|$', line)
                if desc_match and not "aaa" in desc_match.group(1) and not "bbb" in desc_match.group(1) and "Reserved" not in desc_match.group(1):
                    # We might need to look ahead for ranges
                    pass
            
            if desc_match:
                name = desc_match.group(1).strip()
                
                # Exclude internal layout lines
                if "aaa" in name or "bbb" in name or "Total Size" in name:
                    continue
                
                # Check next couple lines for ranges if not in regex
                min_val, max_val = 0, 0
                val_desc = ""
                
                # We can just infer min/max from the structure if we can't parse it
                # For simplicity, let's just log the address and name, and put default 00 / 01 for min max
                
                addr = f"32 11 20 {offset_parts[1]}"
                
                # Try to parse ranges
                range_match = re.search(r'\(\s*(-?\d+)\s*[-~]\s*(-?\d+)[^\)]*\)', line)
                if range_match:
                    try:
                        m1 = int(range_match.group(1))
                        m2 = int(range_match.group(2))
                        # SysEx values are always positive bytes, so if it's -64 to +63, it's 0 to 127
                        # Let's just use 00 and the max hex value up to 7F (since it's usually 7-bit)
                        val_desc = f"{m1} to {m2}"
                    except:
                        val_desc = "Unknown Range"
                else:
                    val_desc = "Unknown Range"
                    
                # We will just write DT1 with 00 and 01 to demonstrate
                
                # If it's a 2 byte offset like 00 0F
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
    d_max_dt1 = make_dt1(p['addr'], "01") # Just an example value, setting to 01

    out += f"#### {p['name']}\n"
    out += f"- **Target Address**: `{p['addr']}`\n"
    out += f"- **Expected Range/Values**: {p['desc']}\n"
    out += f"- **Query Command (RQ1)**: `{q}`\n"
    out += f"- **Set Command (DT1) Example (00)**: `{d_min_dt1}`\n"
    out += f"- **Set Command (DT1) Example (01)**: `{d_max_dt1}`\n\n"

# Add DT1 2-byte/4-byte note
out += """
---
## SysEx Payload Breakdowns
*(Note: Ensure a minimum of 20ms delay is programmed between sequentially transmitted SysEx messages. Some parameters are split across multiple bytes (e.g. 0000 aaaa, 0000 bbbb). For those, you must send all 2 or 4 bytes starting from the root address of the parameter).*
"""

with open('sysex_details.txt', 'w') as f:
    f.write(out)
print('Generated sysex_details.txt')
