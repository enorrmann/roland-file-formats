import subprocess
import time

def calc_csum(hex_array):
    s = sum(hex_array)
    return (128 - (s % 128)) % 128

def hex_to_arr(s):
    return [int(x, 16) for x in s.split()]

def make_dt1(addr, data):
    addr_arr = hex_to_arr(addr)
    data_arr = hex_to_arr(data)
    csum = calc_csum(addr_arr + data_arr)
    return f"F0 41 10 00 00 00 5E 12 {addr} {data} {csum:02X} F7"

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

def send_only(msg):
    cmd = ["amidi", "-p", "hw:3,0,0", "-S", msg.replace(" ", "")]
    subprocess.run(cmd)

if __name__ == "__main__":
    target_address_query = "32 11 20 00" # Full block
    target_address_write = "32 11 20 07" # Tone Partial 1 -> Pan

    print("1. Querying Tone Partial 1 at", target_address_query)
    out1 = send_and_receive(make_rq1(target_address_query, "00 00 00 7F"))
    original_val = "40" # Fallback center pan
    if out1:
        print(" -> Response:", out1[0])
        parts = out1[0].split()
        if len(parts) > 19:
            # Address is 12 + 07 = 19
            original_val = parts[19]
            print(f" -> Byte at offset 07 (Pan) is: {original_val}")
        
    print("\n2. Sending DT1 to change Pan to 7F (Hard Right)")
    dt1_msg = make_dt1(target_address_write, "7F")
    print(" -> Sending:", dt1_msg)
    send_only(dt1_msg)
    time.sleep(1.0)

    print("\n3. Querying Tone Partial 1 again to verify change")
    out2 = send_and_receive(make_rq1(target_address_query, "00 00 00 7F"))
    if out2:
        parts2 = out2[0].split()
        if len(parts2) > 19:
            print(f" -> Byte at offset 07 (Pan) is now: {parts2[19]}")

    # Revert back to original
    print(f"\n4. Reverting Pan to {original_val}")
    dt1_msg_revert = make_dt1(target_address_write, original_val)
    send_only(dt1_msg_revert)
    time.sleep(1.0)
