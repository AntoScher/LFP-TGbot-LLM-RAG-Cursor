import os
import shutil
from pathlib import Path

def clean_knowledge_base():
    knowledge_dir = Path("./knowledge_base")
    
    if not knowledge_dir.exists():
        print(f"Directory {knowledge_dir} not found!")
        return
    
    # Keep only .md and system prompt files
    keep_extensions = {'.md', '.txt'}
    removed_count = 0
    
    for file_path in knowledge_dir.glob('*'):
        if file_path.is_file() and file_path.suffix.lower() not in keep_extensions:
            try:
                os.remove(file_path)
                print(f"Removed: {file_path}")
                removed_count += 1
            except Exception as e:
                print(f"Error removing {file_path}: {e}")
    
    print(f"\nCleanup complete. Removed {removed_count} files.")
    
    # List remaining files
    remaining_files = list(knowledge_dir.glob('*'))
    print(f"\nRemaining files in knowledge_base (total: {len(remaining_files)}):")
    for file in remaining_files:
        print(f"- {file.name} ({file.stat().st_size} bytes)")

if __name__ == "__main__":
    clean_knowledge_base()
