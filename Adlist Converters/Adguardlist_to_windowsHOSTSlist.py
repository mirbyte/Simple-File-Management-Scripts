import tkinter as tk
from tkinter import filedialog, messagebox

def convert_to_hosts_format():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    input_file = filedialog.askopenfilename(
        title="Select AdGuard blocklist file",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )

    if not input_file:
        return

    output_file = input_file.rsplit('.', 1)[0] + '_hosts.txt'

    try:
        with open(input_file, 'r', encoding='utf-8') as infile:
            lines = infile.readlines()

        with open(output_file, 'w', encoding='utf-8') as outfile:
            for line in lines:
                line = line.strip()
                if line.startswith('||') and line.endswith('^'):
                    domain = line[2:-1]
                    outfile.write(f"127.0.0.1 {domain}\n")

        messagebox.showinfo("Success", f"Conversion successful. Output saved to:\n{output_file}")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

if __name__ == "__main__":
    convert_to_hosts_format()