import tkinter as tk
from tkinter import filedialog

def convert_to_domain_list():
    root = tk.Tk()
    root.withdraw()
    
    input_file = filedialog.askopenfilename(
        title="Select hosts file",
        filetypes=[("Text files", "*.txt")]
    )
    
    if not input_file:
        print("No file selected")
        return
        
    with open(input_file, 'r') as f:
        # Extract domains from hosts file format (skip comments and empty lines)
        domains = [line.split('#')[0].strip().split()[-1] for line in f 
                  if line.strip() and not line.strip().startswith('#')
                  and len(line.split()) >= 2]
    
    output_file = input_file.rsplit('.', 1)[0] + '_domains.txt'
    with open(output_file, 'w') as f:
        f.write('\n'.join(domains))
    
    print(f"Domain list saved to: {output_file}")

if __name__ == "__main__":
    convert_to_domain_list()