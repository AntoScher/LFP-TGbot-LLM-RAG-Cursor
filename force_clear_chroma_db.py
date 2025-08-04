import os
import shutil
import time
import psutil

def kill_processes_using_path(path):
    """Kill processes that have the given path open"""
    path = os.path.abspath(path)
    killed = set()
    
    for proc in psutil.process_iter(['pid', 'name', 'open_files']):
        try:
            if proc.open_files() is not None:
                for f in proc.open_files():
                    if path in f.path:
                        print(f"Killing process {proc.pid} ({proc.name()}) using {f.path}")
                        proc.kill()
                        killed.add(proc.pid)
                        break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    return len(killed) > 0

def force_clear_chroma_db():
    db_path = "./chroma_db"
    
    if not os.path.exists(db_path):
        print(f"Database directory {db_path} does not exist.")
        return
    
    print(f"Attempting to clear Chroma database at {os.path.abspath(db_path)}")
    
    # First try normal removal
    try:
        shutil.rmtree(db_path)
        print("Successfully removed chroma_db directory.")
        return
    except PermissionError as e:
        print(f"Permission error: {e}")
        print("Attempting to kill processes using the database...")
        
    # If normal removal fails, try killing processes
    if kill_processes_using_path(db_path):
        print("Killed processes using the database. Retrying removal...")
        time.sleep(2)  # Give processes time to terminate
        
        try:
            shutil.rmtree(db_path)
            print("Successfully removed chroma_db directory after killing processes.")
            return
        except Exception as e:
            print(f"Failed to remove directory even after killing processes: {e}")
    else:
        print("No processes found using the database, but still can't remove it.")
    
    print("\nIf the problem persists, you may need to:")
    print("1. Close any Python processes or Jupyter notebooks")
    print("2. Restart your IDE/terminal")
    print("3. Or restart your computer if needed")

if __name__ == "__main__":
    force_clear_chroma_db()
