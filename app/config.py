from langchain.chat_models import init_chat_model
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.vectorstores import Qdrant
from qdrant_client import QdrantClient

from app.settings import settings


def init_llm():
    return init_chat_model(
        model="groq:meta-llama/llama-4-maverick-17b-128e-instruct", 
        api_key=settings.groq_api_key,
        temperature=0.2
)

def init_embedding():
    return HuggingFaceEmbeddings(model_name="Qwen/Qwen3-Embedding-0.6B")

def init_vector_store():
    client = QdrantClient(url=settings.qdrant_url, prefer_grpc=True)
    return Qdrant(client, "my_documents", init_embedding())

