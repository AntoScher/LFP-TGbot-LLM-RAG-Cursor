import os
import codecs
from pathlib import Path

def convert_file_to_utf8(file_path):
    """Convert a single file to UTF-8 encoding"""
    try:
        # Read the file with detected encoding
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Try to decode with common encodings for Russian text
        for encoding in ['utf-8', 'cp1251', 'cp866', 'koi8-r', 'iso-8859-5']:
            try:
                # Try to decode with current encoding
                decoded_content = content.decode(encoding)
                
                # If we got here, decoding was successful
                # Now write back with UTF-8 encoding
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(decoded_content)
                
                print(f"Converted {file_path} from {encoding} to UTF-8")
                return True
                
            except UnicodeDecodeError:
                continue
        
        # If we get here, none of the encodings worked
        print(f"Failed to determine encoding for {file_path}")
        return False
        
    except Exception as e:
        print(f"Error converting {file_path}: {str(e)}")
        return False

def convert_knowledge_base():
    knowledge_dir = Path("./knowledge_base")
    if not knowledge_dir.exists():
        print(f"Directory {knowledge_dir} not found!")
        return
    
    # Create backup directory
    backup_dir = knowledge_dir / "backup"
    backup_dir.mkdir(exist_ok=True)
    
    print(f"Backing up original files to {backup_dir}")
    
    # Convert all files in the knowledge base
    converted = 0
    failed = 0
    
    for file_path in knowledge_dir.glob('*'):
        if file_path.is_file() and file_path.suffix.lower() in ['.md', '.txt']:
            try:
                # Skip backup files
                if file_path.parent == backup_dir:
                    continue
                    
                # Create backup
                backup_path = backup_dir / file_path.name
                if not backup_path.exists():
                    import shutil
                    shutil.copy2(file_path, backup_path)
                
                # Convert the file
                if convert_file_to_utf8(file_path):
                    converted += 1
                else:
                    failed += 1
                    
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
                failed += 1
    
    print(f"\nConversion complete!")
    print(f"- Successfully converted: {converted} files")
    print(f"- Failed to convert: {failed} files")
    print(f"\nBackup of original files is available in: {backup_dir}")

if __name__ == "__main__":
    convert_knowledge_base()
