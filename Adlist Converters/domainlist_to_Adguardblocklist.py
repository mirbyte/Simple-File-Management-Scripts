import tkinter as tk
from tkinter import filedialog, messagebox

def convert_to_adguard_rules():
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)

    input_file = filedialog.askopenfilename(
        title="Select URL list file",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )

    if not input_file:
        return

    output_file = input_file.rsplit('.', 1)[0] + '_adguard.txt'

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            urls = [line.split('#')[0].strip() for line in f if line.split('#')[0].strip()]

        rules = [f"||{url}^" for url in urls]

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(rules))

        messagebox.showinfo("Success", f"Converted rules saved to:\n{output_file}")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

if __name__ == "__main__":
    convert_to_adguard_rules()
