import os
import sys
import chromadb
from chromadb.config import Settings
import logging
from pathlib import Path
from typing import List, Dict, Any
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class DocumentLoader:
    """Helper class to load documents into ChromaDB"""
    
    def __init__(self, db_path: str = "./chroma_db"):
        self.db_path = db_path
        self.client = None
        self.collection = None
        # Use local embeddings to avoid network issues
        self.embedding_function = None
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading local sentence-transformers model...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading local model: {e}")
            raise
    
    def initialize_database(self, collection_name: str = "documents") -> bool:
        """Initialize or reset the Chroma database"""
        try:
            # Create backup of existing database
            self._backup_database()
            
            # Remove existing database
            if os.path.exists(self.db_path):
                shutil.rmtree(self.db_path)
            
            # Create new database directory
            os.makedirs(self.db_path, exist_ok=True)
            
            # Initialize Chroma client
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Create a new collection with local embeddings
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
                # Use local embeddings function
                embedding_function=self._local_embeddings
            )
            
            logger.info(f"Initialized new Chroma database at {os.path.abspath(self.db_path)}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            self._restore_backup()
            return False
    
    def _backup_database(self) -> None:
        """Create a backup of the existing database"""
        backup_path = f"{self.db_path}_backup"
        if os.path.exists(self.db_path):
            logger.info(f"Creating backup at {backup_path}")
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
            shutil.copytree(self.db_path, backup_path)
    
    def _local_embeddings(self, texts):
        """Generate embeddings using local sentence-transformers model"""
        if not hasattr(self, 'embedding_model'):
            raise ValueError("Local embedding model not loaded")
        
        # Convert single string to list if needed
        if isinstance(texts, str):
            texts = [texts]
            
        # Generate embeddings
        embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()
    
    def _restore_backup(self) -> None:
        """Restore database from backup if available"""
        backup_path = f"{self.db_path}_backup"
        if os.path.exists(backup_path):
            logger.info("Restoring from backup...")
            if os.path.exists(self.db_path):
                shutil.rmtree(self.db_path)
            shutil.copytree(backup_path, self.db_path)
    
    def load_documents_from_directory(self, directory: str) -> bool:
        """Load all documents from a directory into the database"""
        try:
            if not self.collection:
                logger.error("Database not initialized. Call initialize_database() first.")
                return False
            
            directory_path = Path(directory)
            logger.info(f"Looking for documents in: {directory_path.absolute()}")
            
            if not directory_path.exists():
                logger.error(f"Directory does not exist: {directory_path.absolute()}")
                return False
                
            if not directory_path.is_dir():
                logger.error(f"Path is not a directory: {directory_path.absolute()}")
                return False
            
            # List all files in the directory for debugging
            all_files = list(directory_path.iterdir())
            logger.info(f"Found {len(all_files)} items in directory:")
            for item in all_files:
                logger.info(f"  - {item.name} (dir: {item.is_dir()}, size: {item.stat().st_size if item.is_file() else 0} bytes)")
            
            # Get all markdown and text files
            md_files = list(directory_path.glob("*.md"))
            txt_files = list(directory_path.glob("*.txt"))
            file_paths = md_files + txt_files
            
            logger.info(f"Found {len(md_files)} .md files and {len(txt_files)} .txt files")
            
            if not file_paths:
                logger.warning(f"No .md or .txt files found in {directory_path.absolute()}")
                return False
            
            documents = []
            metadatas = []
            ids = []
            
            for i, file_path in enumerate(file_paths):
                try:
                    logger.info(f"\nProcessing file {i+1}/{len(file_paths)}: {file_path.name}")
                    
                    # Check file size
                    file_size = file_path.stat().st_size
                    logger.info(f"  File size: {file_size} bytes")
                    
                    if file_size == 0:
                        logger.warning("  File is empty, skipping")
                        continue
                    
                    # Read file with explicit UTF-8 encoding and error handling
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        logger.info(f"  Successfully read {len(content)} characters")
                    except UnicodeDecodeError as ude:
                        logger.error(f"  Error reading file (not UTF-8): {ude}")
                        # Try with different encoding
                        try:
                            with open(file_path, 'r', encoding='cp1251') as f:
                                content = f.read()
                            logger.info(f"  Successfully read with cp1251 encoding: {len(content)} characters")
                        except Exception as e2:
                            logger.error(f"  Failed to read file with cp1251 encoding: {e2}")
                            continue
                    except Exception as e:
                        logger.error(f"  Error reading file: {e}")
                        continue
                    
                    # Add to batch
                    documents.append(content)
                    metadatas.append({"source": str(file_path.name), "size_bytes": len(content)})
                    ids.append(f"doc_{i+1}_{file_path.stem}")
                    
                    logger.info(f"  Added to batch: {file_path.name} ({len(content)} characters)")
                    
                except Exception as e:
                    logger.error(f"  Error processing {file_path}: {e}", exc_info=True)
            
            if not documents:
                logger.error("No valid documents to add to the collection")
                return False
            
            # Add documents to collection in smaller batches to avoid timeouts
            batch_size = 5
            success_count = 0
            
            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i:i+batch_size]
                batch_metas = metadatas[i:i+batch_size]
                batch_ids = ids[i:i+batch_size]
                
                try:
                    logger.info(f"\nAdding batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1} with {len(batch_docs)} documents")
                    
                    self.collection.add(
                        documents=batch_docs,
                        metadatas=batch_metas,
                        ids=batch_ids
                    )
                    
                    success_count += len(batch_docs)
                    logger.info(f"  Successfully added batch to collection")
                    
                except Exception as e:
                    logger.error(f"  Error adding batch to collection: {e}", exc_info=True)
            
            logger.info(f"\nSuccessfully added {success_count}/{len(documents)} documents to the collection")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Unexpected error in load_documents_from_directory: {e}", exc_info=True)
            return False

def main():
    # Set console to use UTF-8 encoding
    import codecs
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    
    # Initialize document loader
    loader = DocumentLoader()
    
    # Initialize database
    if not loader.initialize_database():
        logger.error("Failed to initialize database")
        return
    
    # Load documents from knowledge base
    knowledge_dir = "./knowledge_base"
    logger.info(f"Loading documents from {knowledge_dir}...")
    if loader.load_documents_from_directory(knowledge_dir):
        logger.info("Document loading completed successfully!")
    else:
        logger.error("Failed to load documents")

if __name__ == "__main__":
    main()
