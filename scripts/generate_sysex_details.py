import sys

def calc_csum(hex_array):
    s = sum(hex_array)
    return (128 - (s % 128)) % 128

def make_rq1(addr, size):
    addr_arr = [int(x, 16) for x in addr.split()]
    size_arr = [int(x, 16) for x in size.split()]
    csum = calc_csum(addr_arr + size_arr)
    return f'F0 41 10 00 00 00 5E 11 {addr} {size} {csum:02X} F7'

def make_dt1(addr, data):
    addr_arr = [int(x, 16) for x in addr.split()]
    data_arr = [int(x, 16) for x in data.split()]
    csum = calc_csum(addr_arr + data_arr)
    return f'F0 41 10 00 00 00 5E 12 {addr} {data} {csum:02X} F7'

# Track 2 Tone Partial 1 is at 32 11 20 00
# Track 1 Drum Kit Clip is at 32 10 00 00
# Generate list of exact packets for documentation

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

params_tone = [
    ('Level', '32 11 20 00', '0-127', '00 00 00 01', '00', '7F'),
    ('Coarse Tune', '32 11 20 01', '-48 to +48 (Offset 64)', '00 00 00 01', '10', '70'),
    ('Fine Tune', '32 11 20 02', '-50 to +50 (Offset 64)', '00 00 00 01', '0E', '72'),
    ('Pan', '32 11 20 07', 'L64 - 63R (0=Left, 64=Center, 127=Right)', '00 00 00 01', '00', '7F'),
    ('Pan Keyfollow', '32 11 20 09', '-100 to +100 (Offset 128)', '00 00 00 01', '1C', 'E4'),
    ('Random Pan Depth', '32 11 20 0A', '0 to 63', '00 00 00 01', '00', '3F'),
    ('Alternate Pan Depth', '32 11 20 0B', 'L64 - 63R (0=Left, 64=Center, 127=Right)', '00 00 00 01', '00', '7F'),
    ('Envelope Mode', '32 11 20 0C', '0=NO-SUS, 1=SUSTAIN', '00 00 00 01', '00', '01'),
    ('Wave Group Type', '32 11 20 1B', '0=INT, 1=EXP, 2=SAMP, 3=MSAMP', '00 00 00 01', '00', '03'),
    ('Wave Number', '32 11 20 23', '0-16383 (Two Bytes)', '00 00 00 02', '00 00', '7F 7F'),
    ('Cutoff Frequency', '32 11 20 35', '0-1023 (Two Bytes)', '00 00 00 02', '00 00', '07 7F'),
    ('Resonance', '32 11 20 40', '0-1023 (Two Bytes)', '00 00 00 02', '00 00', '07 7F'),
]

for name, addr, desc, size, d_min, d_max in params_tone:
    q = make_rq1(addr, size)
    # Special case handling for DT1s requiring multi-byte sizes
    d_min_dt1 = make_dt1(addr, d_min)
    d_max_dt1 = make_dt1(addr, d_max)

    out += f'#### {name}\n'
    out += f'- **Target Address**: `{addr}`\n'
    out += f'- **Expected Range/Values**: {desc}\n'
    out += f'- **Query Command (RQ1)**: `{q}`\n'
    out += f'- **Set Command (DT1) to Min Value ({d_min.replace(" ","")})**: `{d_min_dt1}`\n'
    out += f'- **Set Command (DT1) to Max Value ({d_max.replace(" ","")})**: `{d_max_dt1}`\n\n'

out += """
---

### Track 1 (Drum Kit Track) 
Base Address: `32 10 00 00` (First Key/Note Pad)

"""

params_drum = [
    ('Play Mode', '32 10 00 01', '0=ONE_SHOT, 1=SUSTAIN', '00 00 00 01', '00', '01'),
    ('Assign Type', '32 10 00 02', '0=MULTI, 1=SINGLE', '00 00 00 01', '00', '01'),
    ('Mute Group', '32 10 00 03', '0=OFF, 1-31=Group 1-31', '00 00 00 01', '00', '1F'),
    ('Env Mode', '32 10 00 04', '0=NO-SUS, 1=SUSTAIN', '00 00 00 01', '00', '01'),
    ('Pan', '32 10 00 09', 'L64 - 63R (0=Left, 64=Center, 127=Right)', '00 00 00 01', '00', '7F'),
    ('Alternate Pan Depth', '32 10 00 0B', 'L64 - 63R (0=Left, 64=Center, 127=Right)', '00 00 00 01', '00', '7F'),
]

for name, addr, desc, size, d_min, d_max in params_drum:
    q = make_rq1(addr, size)
    d_min_dt1 = make_dt1(addr, d_min)
    d_max_dt1 = make_dt1(addr, d_max)

    out += f'#### {name}\n'
    out += f'- **Target Address**: `{addr}`\n'
    out += f'- **Expected Range/Values**: {desc}\n'
    out += f'- **Query Command (RQ1)**: `{q}`\n'
    out += f'- **Set Command (DT1) to Min Value ({d_min.replace(" ","")})**: `{d_min_dt1}`\n'
    out += f'- **Set Command (DT1) to Max Value ({d_max.replace(" ","")})**: `{d_max_dt1}`\n\n'

# Adding a note about the checksum formulation at the end
out += """
---
## SysEx Payload Breakdowns

If setting `Pan` to Center (`64` or `0x40`) for Tone Partial 1:
- `F0 41 10 00 00 00 5E 12`: Standard Header for DT1
- `32 11 20 07`: Tone Track 2, Partial 1 Pan Position
- `40`: Decimal 64 (Center Pan)
- `56`: Checksum (`128 - ((116) % 128)`)
- `F7`: End of Exclusive

*(Note: Ensure a minimum of 20ms delay is programmed between sequentially transmitted SysEx messages to allow the MC-101 buffer to process them without throwing buffer overflow errors. Ensure `FE` Active Sensing messages are filtered from inputs prior to parser delivery).*
"""

with open('sysex_details.txt', 'w') as f:
    f.write(out)
print('Generated sysex_details.txt')
