import os

# github/mirbyte
# first version
# lacks proper testing


def scan_txt_files():
    """Scan current directory for .txt files"""
    txt_files = [f for f in os.listdir('.') if f.endswith('.txt')]
    return sorted(txt_files)

def display_menu(txt_files):
    """Display numbered menu of available .txt files"""
    if not txt_files:
        print("No .txt files found in current directory.")
        return None
    
    print("\n=== Text File Splitter ===")
    print("\nAvailable .txt files:")
    print("-" * 40)
    for idx, filename in enumerate(txt_files, 1):
        file_size = os.path.getsize(filename)
        print(f"{idx}. {filename} ({file_size:,} bytes)")
    print("-" * 40)
    
    return txt_files

def get_user_choice(txt_files):
    """Get user's file selection"""
    while True:
        try:
            choice = input(f"\nSelect file number (1-{len(txt_files)}) or 'q' to quit: ").strip()
            if choice.lower() == 'q':
                return None
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(txt_files):
                return txt_files[choice_num - 1]
            else:
                print(f"Please enter a number between 1 and {len(txt_files)}")
        except ValueError:
            print("Invalid input. Please enter a number or 'q' to quit.")

def get_split_count():
    """Ask user how many parts to split the file into"""
    while True:
        try:
            choice = input("\nHow many parts do you want to split the file into? (2-20): ").strip()
            num_parts = int(choice)
            if 2 <= num_parts <= 20:
                return num_parts
            else:
                print("Please enter a number between 2 and 20")
        except ValueError:
            print("Invalid input. Please enter a number.")

def find_best_split_position(content, target_pos, search_start, search_end):
    """Find the best position to split, prioritizing paragraph breaks near target"""
    # Search for double newline (paragraph break) near target position
    # Search window: ±10% of target position or ±500 chars, whichever is larger
    window_size = max(500, int(target_pos * 0.1))
    
    search_start_pos = max(search_start, target_pos - window_size)
    search_end_pos = min(search_end, target_pos + window_size)
    
    # Look for double newline
    back_pos = content.rfind('\n\n', search_start_pos, target_pos)
    forward_pos = content.find('\n\n', target_pos, search_end_pos)
    
    # If no paragraph break found, look for single newline
    if back_pos == -1:
        back_pos = content.rfind('\n', search_start_pos, target_pos)
    if forward_pos == -1:
        forward_pos = content.find('\n', target_pos, search_end_pos)
    
    # Choose the position closest to target
    if back_pos == -1 and forward_pos == -1:
        return target_pos
    elif back_pos == -1:
        return forward_pos + 1 if forward_pos < len(content) else forward_pos
    elif forward_pos == -1:
        return back_pos + 1 if back_pos < len(content) else back_pos
    else:
        back_distance = target_pos - back_pos
        forward_distance = forward_pos - target_pos
        if back_distance <= forward_distance:
            return back_pos + 1 if back_pos < len(content) else back_pos
        else:
            return forward_pos + 1 if forward_pos < len(content) else forward_pos

def split_text_file(file_path, num_parts):
    """Split the selected text file into specified number of parts as evenly as possible"""
    try:
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        total_length = len(content)
        
        if total_length == 0:
            print("\n✗ Error: File is empty")
            return False
        
        # Calculate ideal size per part
        ideal_part_size = total_length / num_parts
        
        # Find optimal split positions
        split_positions = [0]  # Start with beginning
        
        for i in range(1, num_parts):
            # Calculate target position for this split
            target_pos = int(i * ideal_part_size)
            
            # Find best actual split position near target
            actual_pos = find_best_split_position(
                content, 
                target_pos, 
                split_positions[-1],  # Don't go before last split
                total_length
            )
            
            split_positions.append(actual_pos)
        
        split_positions.append(total_length)  # Add end position
        
        # Generate output file names and write files
        base_name = os.path.splitext(file_path)[0]
        ext = os.path.splitext(file_path)[1]
        
        created_files = []
        
        for i in range(num_parts):
            start_pos = split_positions[i]
            end_pos = split_positions[i + 1]
            
            # Extract content for this part
            part_content = content[start_pos:end_pos].strip()
            
            # Generate filename
            part_file = f"{base_name}_part{i+1}{ext}"
            
            # Write file
            with open(part_file, 'w', encoding='utf-8') as f:
                f.write(part_content)
            
            created_files.append((os.path.basename(part_file), len(part_content)))
        
        # Show success message with statistics
        print("\n" + "=" * 50)
        print("✓ File split successfully!")
        print("=" * 50)
        print(f"\nCreated {num_parts} parts:")
        for filename, size in created_files:
            percentage = (size / total_length) * 100
            print(f"  • {filename} ({size:,} chars, {percentage:.1f}%)")
        
        # Calculate size statistics
        sizes = [size for _, size in created_files]
        avg_size = sum(sizes) / len(sizes)
        max_size = max(sizes)
        min_size = min(sizes)
        max_diff = max_size - min_size
        variance_pct = (max_diff / avg_size) * 100
        
        print(f"\nStatistics:")
        print(f"  • Average size: {avg_size:,.0f} chars")
        print(f"  • Size range: {min_size:,} - {max_size:,} chars")
        print(f"  • Max difference: {max_diff:,} chars ({variance_pct:.1f}%)")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return False

def main():
    """Main function"""
    # Scan for .txt files
    txt_files = scan_txt_files()
    
    # Display menu
    txt_files = display_menu(txt_files)
    if not txt_files:
        input("\nPress Enter to exit...")
        return
    
    # Get user choice
    selected_file = get_user_choice(txt_files)
    if not selected_file:
        print("\nOperation cancelled.")
        input("\nPress Enter to exit...")
        return
    
    # Get number of parts to split into
    num_parts = get_split_count()
    
    # Split the file
    print(f"\nProcessing: {selected_file} into {num_parts} parts...")
    success = split_text_file(selected_file, num_parts)
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
