#!/usr/bin/env python3
"""
Script to list all files in the /home/cobuccio_relatorios/importacao_remessa_portal_fidc directory
"""

import os
import sys
from pathlib import Path

def list_files_in_directory(directory_path):
    """
    List all files in the specified directory and its subdirectories
    
    Args:
        directory_path (str): Path to the directory to scan
    """
    try:
        target_path = Path(directory_path)
        
        if not target_path.exists():
            print(f"Error: Directory '{directory_path}' does not exist.")
            return False
            
        if not target_path.is_dir():
            print(f"Error: '{directory_path}' is not a directory.")
            return False
            
        print(f"Listing files in: {directory_path}")
        print("=" * 60)
        
        file_count = 0
        dir_count = 0
        
        # Walk through directory tree
        for root, dirs, files in os.walk(target_path):
            # Count directories
            dir_count += len(dirs)
            
            # List files in current directory
            if files:
                relative_root = os.path.relpath(root, directory_path)
                if relative_root == ".":
                    print(f"\nFiles in root directory:")
                else:
                    print(f"\nFiles in subdirectory: {relative_root}")
                print("-" * 40)
                
                for file in sorted(files):
                    try:
                        file_path = os.path.join(root, file)
                        file_size = os.path.getsize(file_path)
                        # Handle potential encoding issues in filenames
                        safe_filename = file.encode('utf-8', errors='replace').decode('utf-8')
                        print(f"  {safe_filename} ({file_size} bytes)")
                        file_count += 1
                    except Exception as e:
                        print(f"  [Error reading file: {e}]")
                        file_count += 1
        
        print("\n" + "=" * 60)
        print(f"Summary:")
        print(f"  Total files: {file_count}")
        print(f"  Total directories: {dir_count}")
        
        return True
        
    except PermissionError:
        print(f"Error: Permission denied accessing '{directory_path}'")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    """Main function"""
    target_directory = "/home/cobuccio_relatorios/importacao_remessa_portal_fidc"
    
    print("File Listing Script")
    print("=" * 60)
    
    success = list_files_in_directory(target_directory)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
