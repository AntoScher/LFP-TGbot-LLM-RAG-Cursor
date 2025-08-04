import os
import logging
from pathlib import Path
from langchain_community.document_loaders import (
    TextLoader,
    UnstructuredMarkdownLoader
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_documents():
    """Load documents from the knowledge_base directory with proper encoding handling"""
    documents = []
    knowledge_dir = Path("./knowledge_base")
    
    if not knowledge_dir.exists():
        logger.error(f"Directory {knowledge_dir} not found!")
        return documents
    
    # Create a text splitter with better chunking for Markdown
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    # Get all markdown and text files
    files = list(knowledge_dir.glob('*.md')) + list(knowledge_dir.glob('*.txt'))
    logger.info(f"Found {len(files)} files to process in {knowledge_dir}")
    
    # Load files with explicit encoding handling
    for file_path in files:
        try:
            logger.info(f"Processing file: {file_path}")
            
            # Read file content with explicit UTF-8 encoding
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Create document from content
            from langchain.docstore.document import Document
            doc = Document(
                page_content=content,
                metadata={"source": str(file_path.name)}
            )
            
            # Split document into chunks
            split_docs = text_splitter.split_documents([doc])
            documents.extend(split_docs)
            logger.info(f"  - Split into {len(split_docs)} chunks")
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
    
    return documents

def main():
    # Инициализируем модель эмбеддингов
    logger.info("Инициализация модели эмбеддингов...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )
    
    # Загружаем документы
    logger.info("Загрузка документов из knowledge_base...")
    documents = load_documents()
    
    if not documents:
        logger.warning("Не найдено документов для загрузки в базу данных!")
        return
    
    # Создаем или обновляем векторную базу
    persist_dir = "./chroma_db"
    logger.info(f"Создание/обновление векторной базы в {persist_dir}...")
    
    try:
        # Удаляем старую базу, если она существует
        if os.path.exists(persist_dir):
            logger.info("Удаление старой базы данных...")
            import shutil
            shutil.rmtree(persist_dir)
        
        # Создаем новую базу
        logger.info(f"Создание новой базы из {len(documents)} фрагментов...")
        vectordb = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=persist_dir
        )
        
        # Сохраняем базу
        vectordb.persist()
        logger.info(f"Успешно загружено {len(documents)} фрагментов в базу данных {persist_dir}")
        
    except Exception as e:
        logger.error(f"Ошибка при создании базы данных: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
