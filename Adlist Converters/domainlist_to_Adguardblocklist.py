import tkinter as tk
from tkinter import filedialog

def convert_to_adguard_rules():
    root = tk.Tk()
    root.withdraw()
    
    input_file = filedialog.askopenfilename(
        title="Select URL list file",
        filetypes=[("Text files", "*.txt")]
    )
    
    if not input_file:
        print("No file selected")
        return
        
    with open(input_file, 'r') as f:
        # Read the file and remove comments by splitting at '#' and keeping only the part before it
        urls = [line.split('#')[0].strip() for line in f if line.split('#')[0].strip()]
    
    # Create AdGuard rules from the URLs
    rules = [f"||{url}^" for url in urls]
    
    output_file = input_file.rsplit('.', 1)[0] + '_adguard.txt'
    with open(output_file, 'w') as f:
        f.write('\n'.join(rules))
    
    print(f"Converted rules saved to: {output_file}")

if __name__ == "__main__":
    convert_to_adguard_rules()
