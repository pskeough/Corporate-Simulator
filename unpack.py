import os
import re

# This is the name of the file you uploaded.
SOURCE_FILE = "corporate_simulator_project V1.0.txt"

# Regex to find the start of a new file in the export
# Looks for: ################################################################################
#             # FILE: old_codebase\engines\action_processor.py
file_header_regex = re.compile(
    r"#{80}\n# FILE: (.*?)\n# Size: \d+ bytes\n#{80}\n\n(.*?)\n\n(?=#{80})",
    re.DOTALL
)

def unpack_project():
    print(f"Starting to unpack '{SOURCE_FILE}'...")
    
    try:
        with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: '{SOURCE_FILE}' not found.")
        print("Please make sure the export file is in the same directory as this script.")
        return
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # Find all file matches
    matches = file_header_regex.findall(content)
    
    if not matches:
        print("Error: Could not find any file headers in the source file.")
        print("Please check the file format.")
        return

    print(f"Found {len(matches)} files to create.")
    created_count = 0

    for match in matches:
        file_path_str, file_content = match
        
        # Clean up the file path (remove extra spaces)
        file_path_str = file_path_str.strip()
        
        # We need to remove the "old_codebase\" prefix for os.path.join
        # and then re-add it to ensure correct directory creation.
        
        # Normalize paths for OS
        file_path = os.path.normpath(file_path_str)
        
        try:
            # Get the directory part of the path
            directory = os.path.dirname(file_path)
            
            # Create the directory if it doesn't exist
            if directory:
                os.makedirs(directory, exist_ok=True)
                
            # Write the file content
            with open(file_path, 'w', encoding='utf-8') as out_f:
                out_f.write(file_content)
                
            print(f"  [OK] Created: {file_path}")
            created_count += 1
            
        except Exception as e:
            print(f"  [FAIL] Error creating {file_path}: {e}")

    print(f"\nUnpack complete. Created {created_count} files.")

if __name__ == "__main__":
    unpack_project()