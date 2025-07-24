import os
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from functools import lru_cache


@lru_cache(maxsize=1)
def init_vector_store(persist_dir: str = "./chroma_db"):
    if os.path.exists(persist_dir) and os.listdir(persist_dir):
        # Загружаем существующую БД
        embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        return Chroma(
            persist_directory=persist_dir,
            embedding_function=embedder
        ).as_retriever(
            search_type="mmr",
            search_kwargs={"k": 3, "fetch_k": 10}
        )

    # Создаем новую векторную БД
    loader = DirectoryLoader(
        "knowledge_base/",
        glob="**/*.*",
        use_multithreading=True
    )
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        add_start_index=True
    )
    chunks = splitter.split_documents(docs)

    embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embedder,
        persist_directory=persist_dir
    )
    vectordb.persist()
    return vectordb.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 3, "fetch_k": 10}
    )