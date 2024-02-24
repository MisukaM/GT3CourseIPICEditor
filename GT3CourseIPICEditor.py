import os
import struct
import sys
import re

MAGIC = b'ipua'
ENTRY_SIZE = 32
HEADER_SIZE = 8
BLANK_BYTES = 56  # Number of blank bytes after the file table

def extract_course_ipic(file_path):
    with open(file_path, 'rb') as f:
        magic = f.read(4)
        if magic != MAGIC:
            print("Invalid file format.")
            return
        
        file_count = struct.unpack('<I', f.read(4))[0]
        print(f"File Count: {file_count}")
        
        print("File Table:")
        print("File Pointer | Filename")
        print("-------------|---------")
        
        file_table = []
        for i in range(file_count):
            file_pointer, = struct.unpack('<I', f.read(4))
            filename_bytes = f.read(28)
            try:
                filename = filename_bytes.rstrip(b'\x00').decode('utf-8', errors='ignore')
            except UnicodeDecodeError as e:
                print(f"Error decoding filename at index {i}: {e}")
                print("Hex representation of bytes:")
                print(filename_bytes.hex())
                continue
                
            file_table.append((file_pointer, filename))
            print(f"{file_pointer} | {filename}")
            
        print("\nExtracting Files...")
        for i, (file_pointer, filename) in enumerate(file_table):
            f.seek(file_pointer)
            if i == len(file_table) - 1:  # Last file, read until end of file
                file_data = f.read()
            else:
                next_file_pointer = file_table[i+1][0]
                file_data = f.read(next_file_pointer - file_pointer)
            
            # Remove numbering and underscore from filename
            filename = re.sub(r'^\d+_', '', filename)
            
            out_dir = 'out'
            os.makedirs(out_dir, exist_ok=True)  # Create 'out' directory if it doesn't exist
            output_filename = os.path.join(out_dir, filename)
            with open(output_filename, 'wb') as outfile:
                outfile.write(file_data)
                print(f"Extracted: {output_filename}")

def create_course_ipic(directory):
    files = os.listdir(directory)
    
    # Custom sorting function
    def custom_sort(filename):
        parts = re.split(r'(\d+)', filename)  # Split on digits
        return [s.lower() if not s.isdigit() else int(s) for s in parts]
    
    files.sort(key=custom_sort)
    
    with open('course.ipic', 'wb') as f:
        f.write(MAGIC)
        f.write(struct.pack('<I', len(files)))
        
        file_offset = HEADER_SIZE + len(files) * ENTRY_SIZE + BLANK_BYTES  # Include blank bytes in offset
        
        for filename in files:
            if filename.startswith(("._", ".DS_Store")):
                continue
            
            with open(os.path.join(directory, filename), 'rb') as infile:
                file_data = infile.read()
                f.write(struct.pack('<I', file_offset))
                filename_bytes = filename.encode('utf-8')
                f.write(filename_bytes.ljust(28, b'\x00'))
                
                # Update file offset
                file_offset += len(file_data)
        
        # Write blank bytes
        f.write(b'\x00' * BLANK_BYTES)
        
        # Write file data
        for filename in files:
            if filename.startswith(("._", ".DS_Store")):
                continue
            
            with open(os.path.join(directory, filename), 'rb') as infile:
                file_data = infile.read()
                f.write(file_data)

def main():
    if len(sys.argv) == 2:
        input_file = sys.argv[1]
        if os.path.isfile(input_file):
            extract_course_ipic(input_file)
        else:
            print("Invalid input file.")
    else:
        if not os.path.exists('out'):
            print("No 'out' folder found.")
            return
        
        create_course_ipic('out')
        print("Archive 'course.ipic' created.")

if __name__ == "__main__":
    main()
