import sys

input_file = '/home/emilio/git/roland-file-formats/sysex_details.txt'
output_file = '/home/emilio/git/roland-file-formats/parameter_offsets.csv'

result = []
current_param = None

with open(input_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line.startswith("#### "):
            current_param = line[5:].strip()
        elif line.startswith("- **Target Address**: `") and current_param:
            addr = line.split("`")[1]
            addr_parts = addr.split()
            # The user wants "el offset correspondiente para ese parametro" without the channel/partial parts.
            # Looking at FANTOM/MC101 architecture, the param offset is usually the last byte (or last two bytes if it's a 2-byte param).
            # e.g., '32 11 20 00' -> '00' is the offset for Level in Partial
            # We'll extract only the last byte as the "offset". If there's a need for more, they are just the final bytes of the address.
            
            # As requested "del parametro en si, no se debe incluir todo el offset de canal ni parte"
            offset = addr_parts[-1] 
            
            # Escribir "nombre del parametro seguido a una coma y luego el offset"
            result.append(f"{current_param},{offset}")
            current_param = None

with open(output_file, 'w', encoding='utf-8') as f:
    for item in result:
        f.write(item + "\n")

print(f"Generado {output_file} con {len(result)} registros.")
