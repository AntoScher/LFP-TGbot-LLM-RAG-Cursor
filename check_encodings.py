import os
import chardet
from pathlib import Path

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        rawdata = f.read()
    return chardet.detect(rawdata)

def check_knowledge_base_encodings():
    knowledge_dir = Path("./knowledge_base")
    if not knowledge_dir.exists():
        print(f"Directory {knowledge_dir} not found!")
        return
    
    # Check all files in the knowledge base
    for file_path in knowledge_dir.glob('*'):
        if file_path.is_file():
            try:
                # Detect encoding
                result = detect_encoding(file_path)
                
                # Read file content to check for issues
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    encoding = 'utf-8'
                    status = "OK"
                except UnicodeDecodeError:
                    try:
                        with open(file_path, 'r', encoding='cp1251') as f:
                            content = f.read()
                        encoding = 'cp1251'
                        status = "OK (cp1251)"
                    except Exception as e:
                        encoding = result['encoding']
                        status = f"Error: {str(e)}"
                
                print(f"File: {file_path.name}")
                print(f"  - Detected encoding: {result['encoding']} (confidence: {result['confidence']:.2f})")
                print(f"  - Read with: {encoding}")
                print(f"  - Status: {status}")
                print(f"  - Size: {os.path.getsize(file_path)} bytes")
                print()
                
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
                print()

if __name__ == "__main__":
    check_knowledge_base_encodings()
