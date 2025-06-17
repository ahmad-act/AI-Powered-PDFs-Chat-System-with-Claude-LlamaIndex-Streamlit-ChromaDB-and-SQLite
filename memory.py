# memory.py
import chromadb
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_vector_index(persist_dir: str = "chroma_store"):
    try:
        if not os.path.exists(persist_dir):
            os.makedirs(persist_dir)

        # Initialize Chroma client
        chroma_client = chromadb.PersistentClient(path=persist_dir)
        chroma_collection = chroma_client.get_or_create_collection("pdf_docs")

        # Initialize vector store
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

        # Configure global settings for embedding model
        Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

        # Initialize storage context
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        # Create or load index
        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            storage_context=storage_context
        )
        logger.info("Vector index loaded successfully")
        return index
    except Exception as e:
        logger.error(f"Error loading vector index: {str(e)}")
        raise