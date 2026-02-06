#!/usr/bin/env python3
"""
CAFÉCRAFT - Cleanup Old Files Script

This script moves old/unused files from the project root to a backup folder,
keeping only the new modular structure intact.

Structure to keep:
  - main.py
  - config/ (folder with all contents)
  - database/ (folder with all contents)
  - auth/ (folder with all contents)
  - ui/ (folder with all contents)
  - pos/ (folder with all contents)
  - inventory/ (folder with all contents)
  - reports/ (folder with all contents)
  - ml/ (folder with all contents)
  - utils/ (folder with all contents)
  - cafecraft.db (database file)

Files moved to old_files_backup/:
  - All other .py files
  - __pycache__
  - Other old folders/files

Usage:
  python cleanup_old_files.py
"""

import os
import shutil
from pathlib import Path


def cleanup_old_files():
    """Move old files from project root to old_files_backup/ folder."""
    
    # Define the new modular structure to keep
    ALLOWED_FILES = {
        'main.py',
        'cafecraft.db',
        'requirements.txt',
    }
    
    ALLOWED_FOLDERS = {
        'config',
        'database',
        'auth',
        'ui',
        'pos',
        'inventory',
        'reports',
        'ml',
        'utils',
        'old_files_backup',  # Don't move the backup folder itself
    }
    
    # Get current working directory (project root)
    project_root = Path.cwd()
    
    print(f"\n{'='*60}")
    print(f"CAFÉCRAFT - Cleanup Old Files")
    print(f"{'='*60}")
    print(f"Project root: {project_root}\n")
    
    # Create backup folder if it doesn't exist
    backup_dir = project_root / 'old_files_backup'
    if not backup_dir.exists():
        backup_dir.mkdir(parents=True, exist_ok=True)
        print(f"[+] Created backup folder: {backup_dir}\n")
    else:
        print(f"[+] Using existing backup folder: {backup_dir}\n")
    
    # Scan project root
    items_to_move = []
    
    for item in project_root.iterdir():
        # Skip hidden files and the backup folder
        if item.name.startswith('.') or item.name == 'old_files_backup':
            continue
        
        # Check if item is in allowed files/folders
        if item.is_file():
            if item.name not in ALLOWED_FILES:
                items_to_move.append(item)
        elif item.is_dir():
            if item.name not in ALLOWED_FOLDERS:
                items_to_move.append(item)
    
    # Move items to backup folder
    if not items_to_move:
        print("[*] No old files found. Project structure is clean!\n")
        return
    
    print(f"[*] Found {len(items_to_move)} old file(s)/folder(s) to move:\n")
    
    moved_count = 0
    failed_count = 0
    
    for item in items_to_move:
        destination = backup_dir / item.name
        
        # If destination exists, append timestamp
        if destination.exists():
            timestamp = __import__('datetime').datetime.now().strftime('%Y%m%d_%H%M%S')
            if item.is_file():
                name_parts = item.name.rsplit('.', 1)
                if len(name_parts) == 2:
                    destination = backup_dir / f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
                else:
                    destination = backup_dir / f"{item.name}_{timestamp}"
            else:
                destination = backup_dir / f"{item.name}_{timestamp}"
        
        try:
            if item.is_file():
                shutil.move(str(item), str(destination))
                print(f"  [✓] Moved file:   {item.name} -> old_files_backup/{destination.name}")
            else:
                shutil.move(str(item), str(destination))
                print(f"  [✓] Moved folder: {item.name}/ -> old_files_backup/{destination.name}/")
            moved_count += 1
        except Exception as e:
            print(f"  [✗] Failed to move {item.name}: {e}")
            failed_count += 1
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"{'='*60}")
    print(f"Successfully moved: {moved_count} item(s)")
    print(f"Failed to move:     {failed_count} item(s)")
    print(f"Backup location:    {backup_dir}\n")
    
    # Print remaining structure
    print(f"{'='*60}")
    print(f"Project Structure (Remaining):")
    print(f"{'='*60}")
    
    print(f"\nFiles in root:")
    for item in sorted(project_root.iterdir()):
        if item.is_file() and not item.name.startswith('.'):
            print(f"  - {item.name}")
    
    print(f"\nFolders:")
    for item in sorted(project_root.iterdir()):
        if item.is_dir() and not item.name.startswith('.'):
            print(f"  - {item.name}/")
    
    print(f"\n{'='*60}\n")


if __name__ == '__main__':
    try:
        cleanup_old_files()
        print("[✓] Cleanup completed successfully!")
    except Exception as e:
        print(f"\n[✗] Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
