import os
import sys
import chromadb
from chromadb.config import Settings
import logging
from pathlib import Path
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def reindex_chroma():
    """Reindex the Chroma database with proper UTF-8 encoding"""
    db_path = "./chroma_db"
    backup_path = "./chroma_db_backup"
    
    # Create backup of current database
    try:
        if os.path.exists(db_path):
            logger.info(f"Creating backup of existing database at {backup_path}")
            if os.path.exists(backup_path):
                import shutil
                shutil.rmtree(backup_path)
            os.rename(db_path, backup_path)
            logger.info("Backup created successfully")
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return
    
    # Load environment variables
    load_dotenv()
    
    # Recreate the database directory
    os.makedirs(db_path, exist_ok=True)
    
    try:
        # Initialize Chroma client with the new database
        logger.info("Initializing new Chroma database...")
        client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Create a new collection
        collection_name = "documents"
        collection = client.create_collection(collection_name)
        
        # Load documents from knowledge base
        knowledge_dir = Path("./knowledge_base")
        if not knowledge_dir.exists():
            logger.error(f"Knowledge base directory not found at {knowledge_dir}")
            return
        
        # Process each file in the knowledge base
        files = list(knowledge_dir.glob('*.md')) + list(knowledge_dir.glob('*.txt'))
        logger.info(f"Found {len(files)} files in knowledge base")
        
        for file_path in files:
            try:
                logger.info(f"Processing file: {file_path.name}")
                
                # Read file with explicit UTF-8 encoding
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Add document to collection
                collection.add(
                    documents=[content],
                    metadatas=[{"source": file_path.name}],
                    ids=[f"doc_{file_path.stem}_{i}" for i in range(1)]
                )
                
                logger.info(f"  - Added {file_path.name} to collection")
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
        
        logger.info("\nReindexing complete!")
        logger.info(f"Total documents indexed: {collection.count()}")
        
    except Exception as e:
        logger.error(f"Error during reindexing: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Restore backup if something went wrong
        try:
            if os.path.exists(backup_path):
                logger.info("Restoring backup due to error...")
                if os.path.exists(db_path):
                    shutil.rmtree(db_path)
                os.rename(backup_path, db_path)
                logger.info("Backup restored successfully")
        except Exception as restore_error:
            logger.error(f"Error restoring backup: {restore_error}")

if __name__ == "__main__":
    reindex_chroma()
