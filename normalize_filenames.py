#!/usr/bin/env python3
"""
Script to normalize filenames in /home/cobuccio_relatorios/importacao_remessa_portal_fidc
Removes accents and special characters, converting to ASCII-only filenames.
"""

import os
import sys
import unicodedata
import re
from pathlib import Path
from collections import defaultdict
import argparse

def normalize_filename(filename):
    """
    Normalize a filename by removing accents, converting to ASCII, and changing .txt to .REM.

    Args:
        filename (str): Original filename

    Returns:
        str: Normalized filename
    """
    # Split filename and extension
    name_parts = filename.rsplit('.', 1) if '.' in filename else [filename]

    if len(name_parts) == 2:
        name, extension = name_parts
    else:
        name = name_parts[0]
        extension = ""

    # Normalize unicode characters (decompose accented characters)
    normalized = unicodedata.normalize('NFD', name)

    # Remove diacritical marks (accents)
    ascii_name = ''.join(char for char in normalized
                        if unicodedata.category(char) != 'Mn')

    # Replace any remaining non-ASCII characters with safe alternatives
    ascii_name = ascii_name.encode('ascii', 'ignore').decode('ascii')

    # Clean up any problematic characters for filesystem
    ascii_name = re.sub(r'[<>:"/\\|?*]', '_', ascii_name)

    # Remove multiple consecutive underscores and trim
    ascii_name = re.sub(r'_+', '_', ascii_name).strip('_')

    # Convert .txt extension to .REM
    if extension.lower() == 'txt':
        extension = 'REM'

    # Reconstruct filename with extension
    if extension:
        return f"{ascii_name}.{extension}"
    else:
        return ascii_name

def scan_directory(directory_path):
    """
    Scan directory and return files that need normalization or extension changes.

    Args:
        directory_path (str): Path to directory to scan

    Returns:
        dict: Dictionary with subdirectory as key and list of (old_name, new_name, full_path) tuples
    """
    target_path = Path(directory_path)
    files_to_process = defaultdict(list)

    if not target_path.exists():
        raise FileNotFoundError(f"Directory '{directory_path}' does not exist.")

    # Process root directory and subdirectories
    for root, dirs, files in os.walk(target_path):
        relative_root = os.path.relpath(root, directory_path)

        for filename in files:
            try:
                # Handle potential encoding issues in filenames
                safe_filename = filename.encode('utf-8', errors='replace').decode('utf-8')
                full_path = os.path.join(root, filename)
                normalized_name = normalize_filename(safe_filename)

                # Add if normalization OR extension change would modify the filename
                if safe_filename != normalized_name:
                    files_to_process[relative_root].append((safe_filename, normalized_name, full_path))
            except Exception as e:
                print(f"Warning: Skipping file with encoding issues: {repr(filename)} - {e}")
                continue

    return files_to_process

def check_conflicts(files_to_process):
    """
    Check for potential filename conflicts after normalization.
    
    Args:
        files_to_process (dict): Files to be processed
        
    Returns:
        list: List of conflicts found
    """
    conflicts = []
    
    for subdir, file_list in files_to_process.items():
        # Check for conflicts within the same directory
        new_names = {}
        for old_name, new_name, full_path in file_list:
            directory = os.path.dirname(full_path)
            
            if new_name in new_names:
                conflicts.append({
                    'directory': directory,
                    'new_name': new_name,
                    'conflicting_files': [new_names[new_name], old_name]
                })
            else:
                new_names[new_name] = old_name
                
            # Check if normalized name conflicts with existing files
            new_full_path = os.path.join(directory, new_name)
            if os.path.exists(new_full_path) and new_full_path != full_path:
                conflicts.append({
                    'directory': directory,
                    'new_name': new_name,
                    'conflict_type': 'existing_file',
                    'original_file': old_name
                })
    
    return conflicts

def print_preview(files_to_process):
    """Print a preview of changes to be made."""
    print("\n" + "="*80)
    print("PREVIEW OF FILENAME CHANGES (Character Normalization + .txt → .REM)")
    print("="*80)
    
    total_files = 0
    for subdir, file_list in files_to_process.items():
        if file_list:
            print(f"\nDirectory: {subdir if subdir != '.' else 'ROOT'}")
            print("-" * 50)
            
            for old_name, new_name, full_path in file_list:
                try:
                    print(f"  {old_name} → {new_name}")
                except UnicodeEncodeError:
                    print(f"  {repr(old_name)} → {new_name}")
                total_files += 1
    
    print(f"\nTotal files to be renamed: {total_files}")
    return total_files

def perform_rename(files_to_process, dry_run=False):
    """
    Perform the actual file renaming.
    
    Args:
        files_to_process (dict): Files to be processed
        dry_run (bool): If True, only simulate the operation
        
    Returns:
        dict: Statistics about the operation
    """
    stats = {
        'total_processed': 0,
        'successfully_renamed': 0,
        'errors': [],
        'skipped': 0
    }
    
    for subdir, file_list in files_to_process.items():
        for old_name, new_name, old_full_path in file_list:
            stats['total_processed'] += 1
            
            directory = os.path.dirname(old_full_path)
            new_full_path = os.path.join(directory, new_name)
            
            try:
                if not dry_run:
                    os.rename(old_full_path, new_full_path)
                    try:
                        print(f"✓ Renamed: {old_name} → {new_name}")
                    except UnicodeEncodeError:
                        print(f"✓ Renamed: {repr(old_name)} → {new_name}")
                else:
                    try:
                        print(f"[DRY RUN] Would rename: {old_name} → {new_name}")
                    except UnicodeEncodeError:
                        print(f"[DRY RUN] Would rename: {repr(old_name)} → {new_name}")
                
                stats['successfully_renamed'] += 1
                
            except Exception as e:
                error_msg = f"Failed to rename {old_name}: {str(e)}"
                stats['errors'].append(error_msg)
                print(f"✗ {error_msg}")
    
    return stats

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Normalize filenames by removing accents and special characters"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without actually renaming files'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip confirmation prompt'
    )
    parser.add_argument(
        '--directory',
        default='/home/cobuccio_relatorios/importacao_remessa_portal_fidc',
        help='Directory to process (default: /home/cobuccio_relatorios/importacao_remessa_portal_fidc)'
    )

    args = parser.parse_args()

    print("Filename Normalization Tool")
    print("="*50)
    print(f"Target directory: {args.directory}")

    try:
        # Scan directory for files that need normalization or extension changes
        print("\n📁 Scanning directory for files that need normalization or extension changes...")
        files_to_process = scan_directory(args.directory)

        # Count total files that need processing
        total_files = sum(len(file_list) for file_list in files_to_process.values())

        if total_files == 0:
            print("✅ No files found that need processing. All filenames are already normalized and have correct extensions.")
            return

        # Print preview of changes
        print_preview(files_to_process)

        # Check for conflicts
        print("\n🔍 Checking for potential filename conflicts...")
        conflicts = check_conflicts(files_to_process)

        if conflicts:
            print("⚠️  WARNING: Filename conflicts detected!")
            for conflict in conflicts:
                if conflict.get('conflict_type') == 'existing_file':
                    print(f"  - '{conflict['new_name']}' already exists in {conflict['directory']}")
                else:
                    print(f"  - Multiple files would be renamed to '{conflict['new_name']}' in {conflict['directory']}")
                    print(f"    Conflicting files: {', '.join(conflict['conflicting_files'])}")

            if not args.force:
                print("\nPlease resolve conflicts before proceeding or use --force to continue anyway.")
                return

        # Show operation info (no confirmation needed)
        if not args.dry_run:
            print(f"\n🔄 Proceeding to rename {total_files} files...")

        # Perform the operation
        print(f"\n🔄 {'Simulating' if args.dry_run else 'Performing'} filename normalization and extension changes...")
        stats = perform_rename(files_to_process, dry_run=args.dry_run)

        # Print summary
        print("\n" + "="*50)
        print("OPERATION SUMMARY")
        print("="*50)
        print(f"Total files processed: {stats['total_processed']}")
        print(f"Successfully {'simulated' if args.dry_run else 'renamed'}: {stats['successfully_renamed']}")
        print(f"Errors encountered: {len(stats['errors'])}")

        if stats['errors']:
            print("\nErrors:")
            for error in stats['errors']:
                print(f"  - {error}")

        if args.dry_run:
            print(f"\n💡 This was a dry run. Use without --dry-run to actually rename files.")
        else:
            print(f"\n✅ Filename normalization and extension changes completed!")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
