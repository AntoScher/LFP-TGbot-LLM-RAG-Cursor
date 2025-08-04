import os
import sys
import logging
import codecs
from pathlib import Path
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings

# Set up stdout to handle UTF-8 encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def check_chroma_db():
    """Directly check the Chroma database contents"""
    db_path = Path("./chroma_db")
    
    if not db_path.exists():
        logger.error(f"Chroma database not found at {db_path}")
        return
    
    try:
        # Initialize Chroma client
        logger.info("Initializing Chroma client...")
        client = chromadb.PersistentClient(path=str(db_path), settings=Settings(allow_reset=True, anonymized_telemetry=False))
        
        # List all collections
        collections = client.list_collections()
        if not collections:
            logger.warning("No collections found in the database.")
            return
        
        logger.info(f"Found {len(collections)} collection(s) in the database.")
        
        # Inspect each collection
        for collection in collections:
            logger.info(f"\nInspecting collection: {collection.name}")
            
            # Get collection info
            collection = client.get_collection(collection.name)
            count = collection.count()
            logger.info(f"- Document count: {count}")
            
            if count == 0:
                logger.warning("Collection is empty.")
                continue
            
            # Get sample documents
            try:
                logger.info("Fetching sample documents...")
                results = collection.get(limit=min(3, count))
                
                if not results or 'documents' not in results or not results['documents']:
                    logger.warning("No documents found in the collection.")
                    continue
                
                # Display sample documents
                logger.info("\nSample documents:")
                for i, doc in enumerate(results['documents'][:3]):
                    try:
                        print(f"\n--- Document {i+1} ---")
                        print("Content (first 500 chars):")
                        # Try to print with UTF-8 encoding
                        if isinstance(doc, str):
                            print(doc[:500].encode('utf-8', errors='replace').decode('utf-8'))
                        else:
                            print(str(doc)[:500].encode('utf-8', errors='replace').decode('utf-8'))
                        
                        # Print metadata if available
                        if 'metadatas' in results and results['metadatas'] and i < len(results['metadatas']):
                            print("\nMetadata:")
                            print(str(results['metadatas'][i]).encode('utf-8', errors='replace').decode('utf-8'))
                        
                        print("-" * 80)
                    except Exception as e:
                        logger.error(f"Error displaying document {i+1}: {e}")
                        logger.error(f"Document type: {type(doc)}")
                        logger.error(f"Document content (first 100 chars): {str(doc)[:100]}")
                
                # Test search functionality
                logger.info("\nTesting search functionality...")
                query = "доставка"
                logger.info(f"Searching for: {query}")
                
                try:
                    search_results = collection.query(
                        query_texts=[query],
                        n_results=2,
                        include=["documents", "metadatas", "distances"]
                    )
                    
                    if search_results and 'documents' in search_results and search_results['documents']:
                        logger.info("\nSearch results:")
                        for i, doc in enumerate(search_results['documents'][0]):
                            print(f"\n--- Result {i+1} ---")
                            try:
                                print(f"Content (first 300 chars): {str(doc)[:300].encode('utf-8', errors='replace').decode('utf-8')}")
                            except Exception as e:
                                print(f"Error displaying content: {e}")
                            if 'metadatas' in search_results and search_results['metadatas'] and i < len(search_results['metadatas'][0]):
                                try:
                                    print(f"Metadata: {str(search_results['metadatas'][0][i]).encode('utf-8', errors='replace').decode('utf-8')}")
                                except Exception as e:
                                    print(f"Error displaying metadata: {e}")
                            if 'distances' in search_results and search_results['distances'] and i < len(search_results['distances'][0]):
                                print(f"Distance: {search_results['distances'][0][i]}")
                    else:
                        logger.warning("No search results returned.")
                        
                except Exception as e:
                    logger.error(f"Error during search: {e}")
                    
            except Exception as e:
                logger.error(f"Error fetching documents: {e}")
    
    except Exception as e:
        logger.error(f"Error initializing Chroma client: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Check if the script is being run directly
    if __package__ is None:
        # Add the parent directory to the Python path
        import sys
        from os import path
        sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
    
    # Run the check
    check_chroma_db()
