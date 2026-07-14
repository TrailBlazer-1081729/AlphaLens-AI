import re
from openai import OpenAI
from chromadb import PersistentClient
from rag_orchestrator.config import JINA_API_KEY, JINA_EMBEDDING_MODEL, DB_PATH, RETRIEVAL_K
from rag_orchestrator.schema import RetrievedChunk, RewrittenQuery


jina_client = OpenAI(api_key=JINA_API_KEY, base_url="https://api.jina.ai/v1")
chroma_client = PersistentClient(path=DB_PATH)


def _sanitize_collection_name(ticker: str, year: int) -> str:
    """Replicates the exact sanitization logic from stage3_embedding.py"""

    raw_name = f"{ticker}_{year}_10K"
    name = re.sub(r'[^a-zA-Z0-9]', '_', raw_name)
    name = re.sub(r'_+', '_', name)
    if name[0].isdigit():
        name = "doc_" + name
    return name.lower()


def _fetch_single_query(query: str, collection_name: str) -> list[RetrievedChunk]:

    """Embeds a single query and fetches chunks from ChromaDB."""

    """Here the response is the object returned by the embedding model"""
    response = jina_client.embeddings.create(model=JINA_EMBEDDING_MODEL, input=[query])
    query_embedding = response.data[0].embedding


    collection = chroma_client.get_collection(collection_name)
    results = collection.query(query_embeddings=[query_embedding], n_results=RETRIEVAL_K)


    chunks = []
    if results["documents"] and results["documents"][0]:
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            try:
                chunk = RetrievedChunk(
                    text=doc,
                    headline=meta.get("headline", "No Headline"),
                    summary=meta.get("summary", "No Summary"),
                    source=meta.get("source", "Unknown"),
                    broad_topic=meta.get("broad_topic", "Unknown")
                )
                chunks.append(chunk)
            except Exception as e:
                print(f"Failed to parse a chunk: {e}")
                continue

    return chunks


def retrieve_chunks(
        original_query: str,
        rewritten_query: RewrittenQuery,
        ticker: str,
        year: int
) -> tuple[list[RetrievedChunk], list[RetrievedChunk]]:

    """
    Fetches chunks for BOTH the original and rewritten queries.
    Returns them as two separate lists for the merger to handle.
    """

    collection_name = _sanitize_collection_name(ticker, year)


    existing = [c.name for c in chroma_client.list_collections()]
    if collection_name not in existing:
        raise ValueError(f"Collection '{collection_name}' not found")


    print(f"Retrieving chunks for original query...")
    original_chunks = _fetch_single_query(original_query, collection_name)

    print(f"Retrieving chunks for rewritten query ('{rewritten_query.refined_query}')...")
    rewritten_chunks = _fetch_single_query(rewritten_query.refined_query, collection_name)

    return original_chunks, rewritten_chunks