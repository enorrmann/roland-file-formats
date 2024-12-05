#!/usr/bin/env python3
import sys
import argparse
from colorama import init, Fore, Style

# Initialize colorama for cross-platform color support
init(autoreset=True)

def compare_binary_files(file1_path, file2_path, offset=0, group_size=16):
    """
    Compare two binary files starting from a specified offset, 
    showing grouped bytes with differences.
    
    Args:
    file1_path (str): Path to the first binary file
    file2_path (str): Path to the second binary file
    offset (int): Byte position to start comparison from
    group_size (int): Number of bytes in each group
    """
    try:
        with open(file1_path, 'rb') as file1, open(file2_path, 'rb') as file2:
            # Check file sizes
            file1.seek(0, 2)  # Move to end of file
            file2.seek(0, 2)
            size1 = file1.tell()
            size2 = file2.tell()
            
            if size1 != size2:
                raise ValueError(f"Files have different sizes: {size1} vs {size2} bytes")
            
            # Reset to offset
            file1.seek(offset)
            file2.seek(offset)
            
            # Read files in group_size byte chunks
            current_pos = offset
            while True:
                chunk1 = file1.read(group_size)
                chunk2 = file2.read(group_size)
                
                # Break if both files are exhausted
                if not chunk1 and not chunk2:
                    break
                
                # Check if chunks are different
                if chunk1 != chunk2:
                    # Print the current position
                    print(f"{Fore.YELLOW}Difference at byte {current_pos}:{Style.RESET_ALL}")
                    
                    # Prepare hex representations with color highlighting
                    hex1 = []
                    hex2 = []
                    for i in range(group_size):
                        if i < len(chunk1) and i < len(chunk2):
                            if chunk1[i] != chunk2[i]:
                                # Highlight different bytes
                                hex1.append(f"{Fore.RED}{chunk1[i]:02x}{Style.RESET_ALL}")
                                hex2.append(f"{Fore.RED}{chunk2[i]:02x}{Style.RESET_ALL}")
                            else:
                                hex1.append(f"{chunk1[i]:02x}")
                                hex2.append(f"{chunk2[i]:02x}")
                        else:
                            # This should not happen due to earlier size check
                            hex1.append("??")
                            hex2.append("??")
                    
                    # Print hex representation of full chunks
                    print("File 1:", ' '.join(hex1))
                    print("File 2:", ' '.join(hex2))
                    
                    # Print decimal values of different bytes
                    print(f"{Fore.CYAN}Differing bytes (decimal):{Style.RESET_ALL}")
                    for i in range(group_size):
                        if i < len(chunk1) and i < len(chunk2) and chunk1[i] != chunk2[i]:
                            print(f"Byte {i}: File 1 = {chunk1[i]}, File 2 = {chunk2[i]}")
                    
                    print()  # Blank line for readability
                
                # Move position forward
                current_pos += group_size

    except FileNotFoundError as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        sys.exit(1)
    except IOError as e:
        print(f"{Fore.RED}I/O error: {e}{Style.RESET_ALL}")
        sys.exit(1)
    except ValueError as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        sys.exit(1)

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Compare two binary files byte by byte')
    parser.add_argument('file1', help='Path to the first binary file')
    parser.add_argument('file2', help='Path to the second binary file')
    parser.add_argument('--offset', type=int, default=0, 
                        help='Byte position to start comparison from (default: 0)')
    parser.add_argument('--group-size', type=int, default=16, 
                        help='Number of bytes to group for comparison (default: 16)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Call comparison function
    compare_binary_files(args.file1, args.file2, args.offset, args.group_size)

if __name__ == '__main__':
    main()
