from pathlib import Path

from langchain_community.document_loaders import PyPDFDirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DIR = BASE_DIR / "chroma_db"


def main():
    database_file = CHROMA_DIR / "chroma.sqlite3"
    if database_file.exists():
        existing = Chroma(persist_directory=str(CHROMA_DIR))
        existing_count = existing._collection.count()
        if existing_count:
            print(f"Existing Chroma collection already has {existing_count} vectors; skipping ingestion.")
            return

    print(f"1. Loading PDFs from {DATA_DIR}...")
    loader = PyPDFDirectoryLoader(str(DATA_DIR))
    documents = loader.load()
    documents += TextLoader(
        str(DATA_DIR / "ASHA_MP_Admin_Guidelines.txt"), encoding="utf-8"
    ).load()
    print(f"Loaded {len(documents)} pages in total.")

    print("2. Chunking text into smaller paragraphs...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)
    if not chunks:
        raise RuntimeError(f"No document chunks were loaded from {DATA_DIR}")
    print(f"Created {len(chunks)} text chunks.")

    print("3. Setting up the existing embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print("4. Building and saving to ChromaDB...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
    )
    count = vectorstore._collection.count()
    if count == 0:
        raise RuntimeError("Chroma ingestion completed without storing any vectors")
    print(f"✅ Success! ChromaDB contains {count} vectors.")


if __name__ == "__main__":
    main()


