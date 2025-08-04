import os
import sys
from pathlib import Path
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,  # Set to DEBUG for more detailed output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)  # Insert at beginning to take precedence

# Print Python path for debugging
logger.debug(f"Python path: {sys.path}")

# Import bot modules
try:
    # Try direct import first
    try:
        from utils.embeddings import get_embeddings, get_vectorstore
        logger.info("Successfully imported bot modules from utils.embeddings")
    except ImportError:
        # If that fails, try importing from the project root
        logger.warning("Direct import failed, trying relative import...")
        from src.utils.embeddings import get_embeddings, get_vectorstore
        logger.info("Successfully imported bot modules from src.utils.embeddings")
        
except ImportError as e:
    logger.error(f"Error importing bot modules: {e}")
    logger.error("Current working directory: %s", os.getcwd())
    logger.error("Files in current directory: %s", os.listdir('.'))
    if os.path.exists('utils'):
        logger.error("Contents of utils directory: %s", os.listdir('utils'))
    sys.exit(1)

def test_retrieval(query: str = "доставка", k: int = 3):
    """Test document retrieval with the given query"""
    try:
        logger.info(f"Testing retrieval with query: '{query}'")
        
        # Initialize embeddings and vector store
        logger.info("Initializing embeddings...")
        embeddings = get_embeddings()
        
        logger.info("Loading vector store...")
        vectordb = get_vectorstore(embeddings)
        
        if vectordb is None:
            logger.error("Failed to initialize vector store")
            return
        
        # Perform similarity search
        logger.info("Performing similarity search...")
        docs = vectordb.similarity_search(query, k=k)
        
        if not docs:
            logger.warning("No documents found for the query")
            return
        
        # Display results
        logger.info(f"\nFound {len(docs)} relevant documents:")
        for i, doc in enumerate(docs, 1):
            print(f"\n--- Document {i} ---")
            print(f"Source: {doc.metadata.get('source', 'Unknown')}")
            print("-" * 40)
            print(doc.page_content[:500])  # Print first 500 chars
            print("-" * 40)
        
        return docs
        
    except Exception as e:
        logger.error(f"Error during retrieval test: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

if __name__ == "__main__":
    # Test with a default query or use command line argument
    query = sys.argv[1] if len(sys.argv) > 1 else "доставка"
    test_retrieval(query=query)
