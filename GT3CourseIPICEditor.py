import tkinter as tk
from tkinter import filedialog
import struct
import os

class GT3CourseIPICEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("GT3CourseIPICEditor")
        self.file_entries = []

        # GUI Components
        self.listbox = tk.Listbox(root)
        self.listbox.pack(side=tk.LEFT, padx=10)

        self.up_button = tk.Button(root, text="Up", command=self.move_up)
        self.up_button.pack(side=tk.LEFT)

        self.down_button = tk.Button(root, text="Down", command=self.move_down)
        self.down_button.pack(side=tk.LEFT)

        self.import_button = tk.Button(root, text="Import", command=self.import_file)
        self.import_button.pack(side=tk.LEFT)

        self.export_button = tk.Button(root, text="Export", command=self.export_file)
        self.export_button.pack(side=tk.LEFT)

        self.save_button = tk.Button(root, text="Save", command=self.save_file)
        self.save_button.pack(side=tk.LEFT)

        # Initialize file dialog after GUI components are created
        self.filename = None
        self.initialize_file_dialog()

    def initialize_file_dialog(self):
        self.filename = filedialog.askopenfilename()

        if self.filename:
            self.load_file()

    def load_file(self):
        with open(self.filename, 'rb') as file:
            # Read header
            magic, num_files = struct.unpack('4sI', file.read(8))
            if magic != b'ipua':
                raise ValueError("Invalid file format")
            
            for _ in range(num_files):
                pointer, = struct.unpack('I', file.read(4))
                name = file.read(28).rstrip(b'\x00').decode('utf-8')
                self.file_entries.append((pointer, name))
                self.listbox.insert(tk.END, name)

    def move_up(self):
        selected_index = self.listbox.curselection()
        if selected_index:
            selected_index = int(selected_index[0])
            if selected_index > 0:
                self.swap_entries(selected_index, selected_index - 1)
                self.update_listbox()

    def move_down(self):
        selected_index = self.listbox.curselection()
        if selected_index:
            selected_index = int(selected_index[0])
            if selected_index < len(self.file_entries) - 1:
                self.swap_entries(selected_index, selected_index + 1)
                self.update_listbox()

    def swap_entries(self, index1, index2):
        # Swap file entries in the list
        self.file_entries[index1], self.file_entries[index2] = self.file_entries[index2], self.file_entries[index1]

        # Update pointers and file data in the file itself
        with open(self.filename, 'r+b') as file:
            file.seek(8 + index1 * 32)  # 8 bytes for header + 32 bytes per entry
            pointer1, name1 = self.file_entries[index1]
            file.write(struct.pack('I', pointer1))
            
            file.seek(8 + index2 * 32)
            pointer2, name2 = self.file_entries[index2]
            file.write(struct.pack('I', pointer2))

            # Read data to be moved
            file.seek(pointer1)
            data1 = file.read(len(name1.encode('utf-8')))

            file.seek(pointer2)
            data2 = file.read(len(name2.encode('utf-8')))

            # Update data at the target positions
            file.seek(pointer2)
            file.write(data1)

            file.seek(pointer1)
            file.write(data2)

    def import_file(self):
        file_to_import = filedialog.askopenfilename()
        if file_to_import:
            filename = os.path.splitext(os.path.basename(file_to_import))[0]  # Remove extension
            new_file_data = None
            with open(file_to_import, 'rb') as file:
                new_file_data = file.read()

            selected_index = self.listbox.curselection()
            if selected_index:
                selected_index = int(selected_index[0])
                existing_pointer, existing_filename = self.file_entries[selected_index]

                # Calculate the new pointer and adjust subsequent pointers if necessary
                new_data_length = len(new_file_data)
                if len(existing_filename.encode('utf-8')) != new_data_length:
                    for i in range(selected_index + 1, len(self.file_entries)):
                        pointer, name = self.file_entries[i]
                        new_pointer = pointer + (new_data_length - len(name.encode('utf-8')))
                        self.file_entries[i] = (new_pointer, name)

                # Replace the existing file data with the new file data
                with open(self.filename, 'r+b') as file:
                    file.seek(existing_pointer)
                    file.write(new_file_data)

                # Update the name in the filename table
                self.file_entries[selected_index] = (existing_pointer, filename)
                self.update_listbox()

    def get_selected_file_data(self):
        selected_index = self.listbox.curselection()
        if selected_index:
            selected_index = int(selected_index[0])
            pointer, _ = self.file_entries[selected_index]

            next_pointer = None
            if selected_index < len(self.file_entries) - 1:
                next_pointer, _ = self.file_entries[selected_index + 1]
            else:
                # For the last file, set next_pointer to the end of the selected file
                next_pointer = pointer + len(self.file_entries[selected_index][1].encode('utf-8'))

            with open(self.filename, 'rb') as file:
                file.seek(pointer)
                return file.read(next_pointer - pointer)
        return b''

    def export_file(self):
        selected_index = self.listbox.curselection()
        if selected_index:
            selected_index = int(selected_index[0])
            pointer, _ = self.file_entries[selected_index]

            next_pointer = None
            if selected_index < len(self.file_entries) - 1:
                next_pointer, _ = self.file_entries[selected_index + 1]
            else:
                # For the last file, set next_pointer to the end of the selected file
                next_pointer = pointer + len(self.get_selected_file_data())

            if next_pointer - pointer > 0:
                with open(self.filename, 'rb') as file:
                    file.seek(pointer)
                    data = file.read(next_pointer - pointer)

                # Open a file dialog to specify the export location and filename
                export_filename = filedialog.asksaveasfilename(defaultextension=".bin", filetypes=[("All Files", "*.*")], initialdir=os.getcwd(), initialfile=self.file_entries[selected_index][1], title="Save File As")
                if export_filename:
                    with open(export_filename, 'wb') as export_file:
                        export_file.write(data)

    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for _, name in self.file_entries:
            self.listbox.insert(tk.END, name)

    def save_file(self):
        with open(self.filename, 'r+b') as file:
            # Skip header
            file.seek(8)
            for pointer, name in self.file_entries:
                # Write pointer
                file.write(struct.pack('I', pointer))
                # Write name (28 bytes)
                file.write(struct.pack('28s', name.encode('utf-8')))
            # Padding (if necessary)
            padding = b'\x00' * (16 - (file.tell() % 16))
            file.write(padding)

if __name__ == "__main__":
    root = tk.Tk()
    app = GT3CourseIPICEditor(root)
    root.mainloop()
