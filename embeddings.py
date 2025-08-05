import os
import logging
import shutil
from functools import lru_cache
from typing import Optional, Any
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.schema.vectorstore import VectorStoreRetriever
import traceback

logger = logging.getLogger(__name__)

class VectorStoreInitializationError(Exception):
    """Custom exception for vector store initialization errors"""
    pass


@lru_cache(maxsize=1)
def init_vector_store(persist_dir: str = "./chroma_db") -> VectorStoreRetriever:
    """
    Инициализирует или загружает векторное хранилище Chroma.
    
    Args:
        persist_dir: Директория для сохранения векторной БД
        
    Returns:
        VectorStoreRetriever: Инициализированный ретривер для поиска
        
    Raises:
        VectorStoreInitializationError: Если не удалось инициализировать хранилище
    """
    try:
        logger.info(f"Initializing vector store in directory: {persist_dir}")
        
        # Проверяем доступность директории
        os.makedirs(persist_dir, exist_ok=True)
        
        # Инициализируем модель эмбеддингов
        try:
            logger.info("Loading HuggingFace embeddings model...")
            # Устанавливаем переменные окружения для принудительного использования CPU
            os.environ["CUDA_VISIBLE_DEVICES"] = ""  # Отключаем CUDA
            os.environ["TOKENIZERS_PARALLELISM"] = "false"  # Отключаем параллелизм токенизатора
            
            # Загружаем модель с явным указанием CPU и отключенным кешем CUDA
            embedder = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={
                    "device": "cpu"
                },
                encode_kwargs={
                    "normalize_embeddings": True
                },
                # Отключаем кеширование модели, чтобы избежать проблем с загрузкой
                cache_folder=None
            )
            
            # В новой версии HuggingFaceEmbeddings не требуется явно перемещать модель на CPU,
            # так как это уже обрабатывается в model_kwargs
            logger.info("Embeddings model loaded successfully in CPU mode")
        except Exception as e:
            error_msg = f"Failed to load embeddings model: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())  # Добавляем полный стек вызовов для отладки
            raise VectorStoreInitializationError(error_msg) from e
        
        # Проверяем существование базы данных
        db_exists = os.path.exists(persist_dir) and os.listdir(persist_dir)
        
        if db_exists:
            try:
                logger.info("Loading existing vector database...")
                vectordb = Chroma(
                    persist_directory=persist_dir,
                    embedding_function=embedder
                )
                retriever = vectordb.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 5}
                )
                logger.info("Vector database loaded successfully")
                return retriever
            except Exception as e:
                error_msg = f"Failed to load existing vector database: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                # Продолжаем создание новой БД в случае ошибки загрузки
                logger.warning("Creating new vector database due to loading error")
        
        # Создаем новую пустую базу данных
        try:
            logger.info("Creating new empty vector database...")
            
            # First, try to create the vector store with a specific collection name
            collection_name = "document_embeddings"
            
            # Clean up any existing database files if they exist
            if os.path.exists(persist_dir):
                logger.warning(f"Attempting to clean up existing database directory: {persist_dir}")
                
                # Try to close any existing ChromaDB client first
                try:
                    from chromadb import Client
                    client = Client()
                    client.heartbeat()  # This will fail if no server is running
                    client.reset()
                    logger.info("Reset existing ChromaDB client")
                except Exception as e:
                    logger.debug(f"No active ChromaDB client to reset: {e}")
                
                # Use a more robust cleanup approach
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        # Try to remove individual files first
                        if os.path.isfile(os.path.join(persist_dir, 'chroma.sqlite3')):
                            os.unlink(os.path.join(persist_dir, 'chroma.sqlite3'))
                        if os.path.isfile(os.path.join(persist_dir, 'chroma.sqlite3-shm')):
                            os.unlink(os.path.join(persist_dir, 'chroma.sqlite3-shm'))
                        if os.path.isfile(os.path.join(persist_dir, 'chroma.sqlite3-wal')):
                            os.unlink(os.path.join(persist_dir, 'chroma.sqlite3-wal'))
                        
                        # Then try to remove the directory
                        if os.path.exists(persist_dir):
                            shutil.rmtree(persist_dir, ignore_errors=True)
                        
                        # If we get here, the cleanup was successful
                        break
                        
                    except Exception as e:
                        if attempt == max_retries - 1:  # Last attempt
                            logger.error(f"Failed to clean up database directory after {max_retries} attempts: {e}")
                            # Continue anyway and let Chroma handle the existing files
                        else:
                            import time
                            time.sleep(1)  # Wait a bit before retrying
            
            # Recreate the directory with fresh permissions
            if os.path.exists(persist_dir):
                logger.warning(f"Directory {persist_dir} still exists, using existing directory")
            else:
                os.makedirs(persist_dir, exist_ok=True)
            
            # Create the vector store with explicit collection name
            logger.info(f"Creating new Chroma collection: {collection_name}")
            vectordb = Chroma(
                embedding_function=embedder,
                persist_directory=persist_dir,
                collection_name=collection_name
            )
            
            # Add a dummy document to initialize the collection
            logger.info("Adding initial document to the collection...")
            vectordb.add_texts(["Initial empty document"])
            
            # In newer versions of ChromaDB, persistence is handled automatically
            logger.info("Vector database initialized successfully")
            
            # Create the retriever
            retriever = vectordb.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}
            )
            
            logger.info("New empty vector database created successfully")
            return retriever
            
        except Exception as e:
            error_msg = f"Failed to create new vector database: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            # Try to provide more specific error messages for common issues
            if "_type" in str(e):
                error_msg += "\nThis error is often caused by incompatible ChromaDB versions or corrupted database files. "
                error_msg += "The database directory has been cleared. Please try again."
            
            raise VectorStoreInitializationError(error_msg) from e
            
    except Exception as e:
        error_msg = f"Critical error in vector store initialization: {str(e)}"
        logger.critical(error_msg)
        logger.critical(traceback.format_exc())
        raise VectorStoreInitializationError(error_msg) from e