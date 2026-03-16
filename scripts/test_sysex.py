import subprocess
import time

dev_id = "10"
model_id = "00 00 00 5E" # MC-101

def calc_csum(hex_array):
    s = sum(hex_array)
    return (128 - (s % 128)) % 128

def hex_to_arr(s):
    return [int(x, 16) for x in s.split()]

def make_rq1(addr, size):
    addr_arr = hex_to_arr(addr)
    size_arr = hex_to_arr(size)
    csum = calc_csum(addr_arr + size_arr)
    return f"F0 41 {dev_id} {model_id} 11 {addr} {size} {csum:02X} F7"

def send_and_receive(msg):
    cmd = ["amidi", "-p", "hw:3,0,0", "-S", msg.replace(" ", ""), "-d", "-t", "1"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    out = res.stdout.strip()
    # Filter out empty or whitespace-only lines
    lines = [line.strip() for line in out.split('\n') if line.strip()]
    return " ".join(lines)

addrs = {
    "System (Fantom)": "00 00 00 00",
    "Setup (Fantom)": "01 00 00 00",
    "Vocoder (Fantom)": "01 00 02 00",
    "Temporary Scene (Fantom)": "02 00 00 00",
    "Temporary Z-Core Tone (Zone 1) (Fantom)": "02 10 00 00",
    "Temporary Drum Kit (Zone 1) (Fantom)": "02 30 00 00",
    "Drum Kit Track 1 Clip 1 (from notes.txt)": "32 10 00 00",
    "Drum Kit Track 1 Clip 2? (guess)": "32 10 01 00",
    "Unknown from notes (huge dump)": "32 10 00 00",  # But with size 01 00 00 10
}

results = []

print("Starting MC-101 SysEx Tests...")
for name, addr in addrs.items():
    # Test with size 16 bytes first
    size = "00 00 00 10" if "huge dump" not in name else "01 00 00 10"
    
    req = make_rq1(addr, size)
    print(f"Testing {name}: {req}")
    out = send_and_receive(req)
    if out:
        results.append((name, addr, size, req, out))
        print(f" -> Response length: {len(out)} chars")
    else:
        # If no response, maybe it requires exact size? For some structures, Roland is strict.
        # But let's log empty response for now.
        results.append((name, addr, size, req, "No response"))
        print(" -> No response")
    time.sleep(0.1)

with open("mc101sysex.txt", "w") as f:
    f.write("MC-101 SysEx Test Results\n=========================\n\n")
    f.write("Note: RQ1 format requires calculating a checksum. If the size or address is invalid, the MC-101 usually will not respond.\n\n")
    for name, addr, size, req, out in results:
        f.write(f"Target: {name}\n")
        f.write(f"Address: {addr}\n")
        f.write(f"Size Requested: {size}\n")
        f.write(f"RQ1 Sent: {req}\n")
        f.write(f"Response: {out}\n")
        f.write("-" * 40 + "\n")

print("Done. Wrote mc101sysex.txt")
