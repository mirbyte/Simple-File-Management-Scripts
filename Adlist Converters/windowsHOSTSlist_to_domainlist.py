import tkinter as tk
from tkinter import filedialog, messagebox

def convert_to_domain_list():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    input_file = filedialog.askopenfilename(
        title="Select hosts file",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )

    if not input_file:
        return

    output_file = input_file.rsplit('.', 1)[0] + '_domains.txt'

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            domains = [line.split('#')[0].strip().split()[-1] for line in f
                      if line.strip() and not line.strip().startswith('#')
                      and len(line.split()) >= 2]

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(domains))

        messagebox.showinfo("Success", f"Domain list saved to:\n{output_file}")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

if __name__ == "__main__":
    convert_to_domain_list()