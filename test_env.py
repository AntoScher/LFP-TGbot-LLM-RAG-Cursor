import sys
import torch
from sentence_transformers import SentenceTransformer
from langchain_community.embeddings import HuggingFaceEmbeddings

def test_environment():
    print("=== Проверка окружения ===")
    
    # Проверка версии Python
    print(f"Python версия: {sys.version}")
    
    # Проверка версии PyTorch и доступности GPU
    print(f"\n=== PyTorch ===")
    print(f"Версия PyTorch: {torch.__version__}")
    print(f"Доступен CUDA: {'Да' if torch.cuda.is_available() else 'Нет'}")
    print(f"Доступен MPS: {'Да' if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available() else 'Нет'}")
    print(f"Доступен XPU: {'Да' if hasattr(torch, 'xpu') and torch.xpu.is_available() else 'Нет'}")
    
    # Проверка работы Sentence Transformers
    try:
        print("\n=== Sentence Transformers ===")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode("Проверка работы модели эмбеддингов")
        print(f"Размерность эмбеддинга: {embeddings.shape}")
        print("[OK] Sentence Transformers работает корректно")
    except Exception as e:
        print(f"[ERROR] Ошибка при тестировании Sentence Transformers: {e}")
    
    # Проверка работы LangChain
    try:
        print("\n=== LangChain ===")
        embeddings = HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
        text = "Проверка работы LangChain"
        query_result = embeddings.embed_query(text)
        print(f"Размерность эмбеддинга LangChain: {len(query_result)}")
        print("[OK] LangChain работает корректно")
    except Exception as e:
        print(f"[ERROR] Ошибка при тестировании LangChain: {e}")
    
    print("\n=== Тестирование завершено ===")

if __name__ == "__main__":
    test_environment()
