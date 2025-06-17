# agent.py
from config import ANTHROPIC_API_KEY
from llama_index.core.prompts import PromptTemplate
from llama_index.llms.anthropic import Anthropic
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_agent_response(query: str, index) -> str:
    try:
        qa_prompt = PromptTemplate(
            "You are a helpful assistant. Use the following context from uploaded PDF documents to answer the query. "
            "Do not rely on external knowledge unless the query cannot be answered from the context. "
            "If the context is insufficient, say so and provide a general answer. "
            "Context: {context_str}\n\nQuery: {query_str}\n\nAnswer:"
        )

        query_engine = index.as_query_engine(
            llm=Anthropic(model="claude-3-opus-20240229", api_key=ANTHROPIC_API_KEY),
            similarity_top_k=5,
            text_qa_template=qa_prompt,
        )

        response = query_engine.query(query)
        logger.info(f"Query: {query}\nResponse: {str(response)}")
        return str(response)
    except Exception as e:
        logger.error(f"Error processing query '{query}': {str(e)}")
        raise
