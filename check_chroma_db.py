import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_chroma_db():
    # Load environment variables
    load_dotenv()
    
    # Initialize embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    # Path to the Chroma database
    persist_dir = "./chroma_db"
    
    if not os.path.exists(persist_dir):
        logger.error(f"Chroma database not found at {persist_dir}")
        return
    
    try:
        # Load the Chroma database
        logger.info(f"Loading Chroma database from {persist_dir}")
        vectordb = Chroma(
            persist_directory=persist_dir,
            embedding_function=embeddings
        )
        
        # Get collection info
        collection = vectordb._collection
        if collection is None:
            logger.error("Failed to load Chroma collection")
            return
        
        # Get document count
        count = collection.count()
        logger.info(f"Found {count} documents in the Chroma database")
        
        # Get some sample documents
        if count > 0:
            logger.info("\nSample documents from the database:")
            results = collection.get(limit=min(3, count))
            
            for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
                source = metadata.get('source', 'unknown')
                chunk_size = len(doc.split())
                logger.info(f"\n--- Document {i+1} (Source: {source}, {chunk_size} words) ---")
                logger.info(doc[:300] + ("..." if len(doc) > 300 else ""))
                
    except Exception as e:
        logger.error(f"Error checking Chroma database: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    check_chroma_db()
