from pathlib import Path

from dotenv import load_dotenv
import os

load_dotenv(override=True)


class Config:
    """
    Central configuration for the AlphaLens ingestion pipeline.
    """

    # ------------------------------------------------------------------
    # Project Paths
    # ------------------------------------------------------------------

    PROJECT_ROOT = Path(__file__).resolve().parent.parent

    KNOWLEDGE_BASE_PATH = PROJECT_ROOT / "knowledge-base" / "finance_reports"

    DB_PATH = PROJECT_ROOT / "finance_db"

    CACHE_PATH = PROJECT_ROOT / "cache"

    DATA_PATH = PROJECT_ROOT / "data"

    LOG_PATH = PROJECT_ROOT / "logs"

    # ------------------------------------------------------------------
    # LLM
    # ------------------------------------------------------------------

    LLM_MODEL = "gemini/gemini-2.5-flash"

    LLM_BATCH_SIZE = 8

    MAX_RETRIES = 5

    RETRY_DELAY = 2

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------

    EMBEDDING_MODEL = "jina-embeddings-v4"

    EMBEDDING_BATCH_SIZE = 100

    # ------------------------------------------------------------------
    # Vector Store
    # ------------------------------------------------------------------

    COLLECTION_NAME = "finance_docs"

    DISTANCE_METRIC = "cosine"

    RETRIEVAL_K = 20

    FINAL_CONTEXT_K = 10

    # ------------------------------------------------------------------
    # Chunking
    # ------------------------------------------------------------------

    MAX_CHARS = 5500

    MIN_CHARS = 600

    OVERLAP = 200

    # ------------------------------------------------------------------
    # Pipeline
    # ------------------------------------------------------------------

    PIPELINE_VERSION = "v1.0"

    CACHE_FILENAME = f"chunks_cache_{PIPELINE_VERSION}.json"

    # ------------------------------------------------------------------
    # API Keys
    # ------------------------------------------------------------------

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    JINA_API_KEY = os.getenv("JINA_API_KEY")

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    LOG_LEVEL = "INFO"

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @classmethod
    def validate(cls) -> None:
        """
        Validate required configuration before the pipeline starts.
        """

        missing = []

        if not cls.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")

        if not cls.JINA_API_KEY:
            missing.append("JINA_API_KEY")

        if missing:
            raise ValueError(
                "Missing environment variables: "
                + ", ".join(missing)
            )

        cls.CACHE_PATH.mkdir(parents=True, exist_ok=True)
        cls.DB_PATH.mkdir(parents=True, exist_ok=True)
        cls.DATA_PATH.mkdir(parents=True, exist_ok=True)
        cls.LOG_PATH.mkdir(parents=True, exist_ok=True)