# knowledge.py
import os
from typing import List
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings
import chromadb
import logging

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD_DIR = "data/pdfs"
CHROMA_DIR = "chroma_store"

def save_uploaded_file(file, session_id):
    try:
        session_dir = os.path.join(UPLOAD_DIR, session_id)
        os.makedirs(session_dir, exist_ok=True)
        filename = f"{session_id}_{file.name}"
        file_path = os.path.join(session_dir, filename)

        with open(file_path, "wb") as f:
            f.write(file.getbuffer())

        logger.info(f"Saved file: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Error saving file {file.name}: {str(e)}")
        raise

def load_pdfs(session_id):
    directory = os.path.join(UPLOAD_DIR, session_id)
    try:
        if not os.path.exists(directory):
            raise FileNotFoundError(f"Directory {directory} does not exist")

        from llama_index.readers.file import PyMuPDFReader
        reader = SimpleDirectoryReader(
            input_dir=directory,
            file_extractor={".pdf": PyMuPDFReader()}
        )
        documents = reader.load_data()
        readable_docs = [doc for doc in documents if doc.text.strip()]
        if not readable_docs:
            raise ValueError("No readable text found in the PDFs.")

        return readable_docs
    except Exception as e:
        logger.error(f"Error loading PDFs for session {session_id}: {str(e)}")
        raise

def build_pdf_index(session_id):
    try:
        documents = load_pdfs(session_id)
        if not documents:
            raise ValueError("No documents to index.")

        persist_path = os.path.join(CHROMA_DIR, session_id)
        os.makedirs(persist_path, exist_ok=True)

        chroma_client = chromadb.PersistentClient(path=persist_path)
        collection = chroma_client.get_or_create_collection("pdf_docs")
        vector_store = ChromaVectorStore(chroma_collection=collection)

        Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context
        )
        logger.info(f"Index built for session {session_id}")
        return index
    except Exception as e:
        logger.error(f"Error building index for session {session_id}: {str(e)}")
        raise
