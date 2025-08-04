from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import chromadb

def check_knowledge_base():
    print("Проверка содержимого базы знаний...")
    
    # Инициализируем модель эмбеддингов
    embedder = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )
    
    # Пытаемся загрузить базу данных
    persist_dir = "./chroma_db"
    try:
        print(f"Загрузка базы данных из {persist_dir}...")
        
        # Создаем клиент Chroma
        client = chromadb.PersistentClient(path=persist_dir)
        
        # Получаем список коллекций
        collections = client.list_collections()
        
        if not collections:
            print("В базе данных нет коллекций!")
            return
            
        print(f"Найдено коллекций: {len(collections)}")
        
        # Проверяем каждую коллекцию
        for collection in collections:
            print(f"\nПроверка коллекции: {collection.name}")
            
            # Получаем количество документов в коллекции
            num_docs = collection.count()
            print(f"Количество документов: {num_docs}")
            
            if num_docs > 0:
                # Получаем примеры документов
                results = collection.get(include=["metadatas", "documents"])
                
                print("\nПримеры документов:")
                for i, (doc, metadata) in enumerate(zip(results["documents"], results["metadatas"])):
                    print(f"\nДокумент {i+1}:")
                    print(f"Содержимое: {str(doc)[:200]}...")
                    print(f"Метаданные: {metadata}")
                    
                    # Ограничиваем вывод первыми тремя документами
                    if i >= 2:
                        print("\n... и еще", num_docs - 3, "документов")
                        break
            else:
                print("В коллекции нет документов!")
                
    except Exception as e:
        import traceback
        print(f"Ошибка при загрузке базы данных: {str(e)}")
        print("\nПодробная информация об ошибке:")
        traceback.print_exc()

if __name__ == "__main__":
    check_knowledge_base()
