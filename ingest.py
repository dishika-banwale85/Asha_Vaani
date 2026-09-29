from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import os

print("1. Loading PDFs from the data folder...")
# This reads all the text out of every PDF in the 'data' folder

loader = PyPDFDirectoryLoader("data")
documents = loader.load()
documents += TextLoader("data/ASHA_MP_Admin_Guidelines.txt", encoding="utf-8").load()
print(f"Loaded {len(documents)} pages in total.")

print("2. Chunking text into smaller paragraphs...")
# We slice the massive PDFs into 1000-character chunks so the AI can digest them easily
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = text_splitter.split_documents(documents)
print(f"Created {len(chunks)} text chunks.")

print("3. Setting up the embedding model...")
# We use a free, lightweight local model to create the mathematical vectors
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

print("4. Building and saving to ChromaDB (this might take a few minutes)...")
# This creates a local folder called 'chroma_db' to store our searchable database
vectorstore = Chroma.from_documents(
    documents=chunks, 
    embedding=embeddings, 
    persist_directory="./chroma_db"
)

print("✅ Success! Your ChromaDB Vector Database is ready.")


