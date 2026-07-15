import os
from pathlib import Path
from dotenv import load_dotenv


load_dotenv(override=True)


ROOT_DIR = Path(__file__).parent.parent
DB_PATH = str(ROOT_DIR / "finance_db")


JINA_API_KEY = os.getenv("jina")
QDRANT_URL=os.getenv("QDRANT_URL")
QDRANT_API_KEY=os.getenv("QDRANT_API_KEY")



JINA_EMBEDDING_MODEL = "jina-embeddings-v4"
JINA_RERANKER_MODEL = "jina-reranker-v2-base-multilingual"
LLM_MODEL = "gemini/gemini-3.1-flash-lite"


RETRIEVAL_K = 20
FINAL_K = 10