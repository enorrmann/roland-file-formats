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
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=2) # 2s max, active sensing circumvents -t
        out = res.stdout.strip()
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode('utf-8') if e.stdout else ""
    return [line.strip() for line in out.split("\n") if line.strip() and line.strip() != "FE"]

if __name__ == "__main__":
    print("Testing System Common...")
    out1 = send_and_receive(make_rq1("00 00 00 00", "00 00 00 7F"))
    print("System Request size 7F resulted in", len(out1), "packets")
    for p in out1:
        print(p)

    print("\nTesting Drum Kit 32 10 00 00...")
    out2 = send_and_receive(make_rq1("32 10 00 00", "00 00 00 7F"))
    print("Drum Kit 32 10 00 00 size 7F resulted in", len(out2), "packets")
    for p in out2:
        print(p)

    print("\nTesting Drum Kit 32 10 01 00...")
    out3 = send_and_receive(make_rq1("32 10 01 00", "00 00 00 7F"))
    print("Drum Kit 32 10 01 00 size 7F resulted in", len(out3), "packets")
    for p in out3:
        print(p)
