import os
from tkinter import Tk, filedialog, messagebox
from tkinter import ttk
import tkinter as tk

def select_input_file():
    root = Tk()
    root.withdraw()  # Hide the main window
    root.attributes('-topmost', True)  # Bring the dialog to the front
    
    file_path = filedialog.askopenfilename(
        title="Select a text file",
        filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
    )
    
    if not file_path:  # User cancelled the dialog
        return None
    
    return file_path

def convert_to_hosts_format(input_file_path, output_file_path):
    try:
        # Open the input file with utf-8 encoding to handle special characters
        with open(input_file_path, 'r', encoding='utf-8') as infile:
            lines = infile.readlines()
        
        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            for line in lines:
                line = line.strip()
                # Only process lines that start with '||' and end with '^'
                if line.startswith('||') and line.endswith('^'):
                    # Remove '||' at the beginning and '^' at the end
                    domain = line.lstrip('||').rstrip('^')
                    # Convert the domain to the Windows hosts file format (127.0.0.1 domain)
                    outfile.write(f"127.0.0.1 {domain}\n")
        
        messagebox.showinfo("Success", f"Conversion successful. The output is saved to {output_file_path}")
    
    except Exception as e:
        messagebox.showerror("Error", f"Error occurred: {e}")

def get_output_file_path():
    root = Tk()
    root.withdraw()  # Hide the main window
    root.attributes('-topmost', True)  # Bring the dialog to the front
    
    # Set default output file name
    default_output = "hosts_output.txt"
    
    output_path = filedialog.asksaveasfilename(
        title="Save output file",
        initialfile=default_output,
        defaultextension=".txt",
        filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
    )
    
    return output_path

def main():
    # Step 1: Select input file using GUI
    input_file = select_input_file()
    if not input_file:
        return  # Exit if no file was selected

    # Step 2: Select output file using GUI
    output_file = get_output_file_path()
    if not output_file:
        return  # Exit if user cancelled the save dialog

    # Step 3: Convert the AdGuard list to the Windows hosts format
    convert_to_hosts_format(input_file, output_file)

if __name__ == "__main__":
    main()