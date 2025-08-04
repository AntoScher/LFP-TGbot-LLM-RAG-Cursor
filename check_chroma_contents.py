import os
import sys
import chromadb
from chromadb.config import Settings
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_chroma_contents():
    """Check the contents of the Chroma database"""
    db_path = "./chroma_db"
    
    if not os.path.exists(db_path):
        logger.error(f"Chroma database not found at {db_path}")
        return
    
    try:
        # Initialize Chroma client
        logger.info("Initializing Chroma client...")
        client = chromadb.PersistentClient(path=db_path, settings=Settings(anonymized_telemetry=False))
        
        # List all collections
        collections = client.list_collections()
        logger.info(f"Found {len(collections)} collection(s) in the database.")
        
        if not collections:
            logger.warning("No collections found in the database.")
            return
        
        # Check each collection
        for collection in collections:
            logger.info(f"\nChecking collection: {collection.name}")
            
            # Get the collection
            col = client.get_collection(collection.name)
            
            # Get the count of documents
            count = col.count()
            logger.info(f"- Document count: {count}")
            
            if count == 0:
                logger.warning("Collection is empty.")
                continue
            
            # Get a sample of documents
            try:
                logger.info("Fetching sample documents...")
                results = col.get(limit=min(3, count))
                
                if not results or 'documents' not in results or not results['documents']:
                    logger.warning("No documents found in the collection.")
                    continue
                
                # Display sample documents
                logger.info("\nSample documents:")
                for i, doc in enumerate(results['documents']):
                    print(f"\n--- Document {i+1} ---")
                    print("Content (first 500 chars):")
                    try:
                        # Try to print with UTF-8 encoding
                        print(str(doc)[:500])
                    except Exception as e:
                        print(f"[Error displaying content: {e}]")
                    
                    # Print metadata if available
                    if 'metadatas' in results and results['metadatas'] and i < len(results['metadatas']):
                        print("\nMetadata:")
                        print(results['metadatas'][i])
                    
                    print("-" * 80)
                
            except Exception as e:
                logger.error(f"Error fetching documents: {e}")
                import traceback
                logger.error(traceback.format_exc())
    
    except Exception as e:
        logger.error(f"Error initializing Chroma client: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    check_chroma_contents()
