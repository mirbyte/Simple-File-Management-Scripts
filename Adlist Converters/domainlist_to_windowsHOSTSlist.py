import tkinter as tk
from tkinter import filedialog

def convert_to_hosts_format():
    root = tk.Tk()
    root.withdraw()
    
    input_file = filedialog.askopenfilename(
        title="Select domain list file",
        filetypes=[("Text files", "*.txt")]
    )
    
    if not input_file:
        print("No file selected")
        return
        
    with open(input_file, 'r') as f:
        domains = [line.split('#')[0].strip() for line in f if line.split('#')[0].strip()]
    
    hosts_entries = [f"127.0.0.1 {domain}" for domain in domains]
    
    output_file = input_file.rsplit('.', 1)[0] + '_hosts.txt'
    with open(output_file, 'w') as f:
        f.write('\n'.join(hosts_entries))
    
    print(f"Hosts file saved to: {output_file}")

if __name__ == "__main__":
    convert_to_hosts_format()