import sys

def find_first_difference(file1_path, file2_path):
    with open(file1_path, 'rb') as file1, open(file2_path, 'rb') as file2:
        byte_number = 0
        while True:
            byte1 = file1.read(1)
            byte2 = file2.read(1)
            
            if byte1 != byte2:
                return byte_number, byte1, byte2
                
            if not byte1:
                break
            
            byte_number += 1

    return None, None, None  # No differences found

if len(sys.argv) < 3:
    print("Must provide the two files on the command line")
    exit(99)

file1_path = sys.argv[1]
file2_path = sys.argv[2]
byte_number, byte1, byte2 = find_first_difference(file1_path, file2_path)

if byte_number is None:
    print("No differences found between the files.")
else:
    print(f"Difference found at byte {hex(byte_number)}: {byte1} vs {byte2}")
