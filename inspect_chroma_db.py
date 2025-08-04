import os
import sqlite3
import json
from pathlib import Path
import chromadb
from chromadb.config import Settings

def inspect_chroma_db():
    db_path = Path("./chroma_db")
    
    if not db_path.exists():
        print(f"Chroma database not found at {db_path}")
        return
    
    # Initialize Chroma client
    print("Initializing Chroma client...")
    client = chromadb.PersistentClient(path=str(db_path))
    
    # List all collections
    print("\nAvailable collections:")
    collections = client.list_collections()
    for collection in collections:
        print(f"- {collection.name} (id: {collection.id})")
    
    if not collections:
        print("No collections found in the database.")
        return
    
    # Inspect the first collection
    collection_name = collections[0].name
    print(f"\nInspecting collection: {collection_name}")
    
    try:
        collection = client.get_collection(collection_name)
        
        # Get collection info
        print(f"Collection count: {collection.count()}")
        
        # Get sample documents
        print("\nFetching sample documents...")
        results = collection.get(include=["documents", "metadatas"], limit=3)
        
        if not results.get('documents'):
            print("No documents found in the collection.")
            return
        
        # Display sample documents
        print(f"\nSample documents (first {len(results['documents'])}):")
        for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
            print(f"\n--- Document {i+1} ---")
            print("Content (first 300 chars):")
            print(doc[:300])
            print("\nMetadata:")
            print(metadata)
        
        # Check for encoding issues
        print("\nChecking for encoding issues...")
        encoding_issues = False
        
        for i, doc in enumerate(results['documents']):
            try:
                # Try to encode as UTF-8 to check for issues
                doc.encode('utf-8')
            except UnicodeEncodeError as e:
                encoding_issues = True
                print(f"\nEncoding issue in document {i+1}:")
                print(f"Error: {e}")
                print("Problematic content (first 100 chars):")
                print(doc[:100])
        
        if not encoding_issues:
            print("No encoding issues detected in the document content.")
        
        # Check search functionality
        print("\nTesting search functionality...")
        try:
            query = "доставка"  # A common Russian word that should be in the knowledge base
            print(f"Searching for: {query}")
            
            search_results = collection.query(
                query_texts=[query],
                n_results=2,
                include=["documents", "metadatas", "distances"]
            )
            
            if search_results and 'documents' in search_results:
                print("\nSearch results:")
                for i, doc in enumerate(search_results['documents'][0]):
                    print(f"\n--- Result {i+1} ---")
                    print(f"Content (first 300 chars): {doc[:300]}")
                    print(f"Metadata: {search_results['metadatas'][0][i]}")
                    print(f"Distance: {search_results['distances'][0][i]}")
            else:
                print("No search results returned.")
                
        except Exception as e:
            print(f"Error during search: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"Error inspecting collection: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_chroma_db()
