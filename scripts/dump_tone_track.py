import subprocess

def calc_csum(hex_array):
    s = sum(hex_array)
    return (128 - (s % 128)) % 128

def hex_to_arr(s):
    return [int(x, 16) for x in s.split()]

def make_rq1(addr, size):
    addr_arr = hex_to_arr(addr)
    size_arr = hex_to_arr(size)
    csum = calc_csum(addr_arr + size_arr)
    return f"F0 41 10 00 00 00 5E 11 {addr} {size} {csum:02X} F7"

def send_and_receive(msg):
    cmd = ["amidi", "-p", "hw:3,0,0", "-S", msg.replace(" ", ""), "-d"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=2) # 2s max timeout
        out = res.stdout.strip()
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode('utf-8') if e.stdout else ""
    return [line.strip() for line in out.split("\n") if line.strip() and line.strip() != "FE"]

if __name__ == "__main__":
    print("Testing Track 2 Partial offsets...")
    addresses = [
        "32 11 20 00", # Tone Partial 1
        "32 11 21 00", # Tone Partial 2
        "32 11 24 00", # Partial 1 Pitch Env
        "32 11 28 00", # Partial 1 Filter Env
        "32 11 2C 00", # Partial 1 Amp Env
    ]

    for addr in addresses:
        print(f"\nRequesting {addr} size 7F...")
        out = send_and_receive(make_rq1(addr, "00 00 00 7F"))
        if out:
            print(f" -> Got {len(out)} DT1 packets")
            for p in out:
                print("   ", p)
        else:
            print(" -> No response")
