import requests
from rag_orchestrator.config import JINA_API_KEY, JINA_RERANKER_MODEL, FINAL_K
from rag_orchestrator.schema import RetrievedChunk, RerankedResult


def rerank_chunks(query: str, chunks: list[RetrievedChunk]) -> list[RerankedResult]:
    """
    Takes a list of merged chunks and a query, uses the Jina Reranker API
    to find the most relevant chunks, and returns the top FINAL_K chunks
    with their relevance scores attached.
    """

    if not chunks:
        return []

    url = "https://api.jina.ai/v1/rerank"

    headers = {
        "Authorization": f"Bearer {JINA_API_KEY}",
        "Content-Type": "application/json"
    }


    documents = [chunk.text for chunk in chunks]

    payload = {
        "model": JINA_RERANKER_MODEL,
        "query": query,
        "documents": documents,
        "top_n": FINAL_K
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        results = response.json()

        """results is a list of the indexes of chunks and the relevance score from the original documents order """
        top_chunks = []
        for result in results["results"]:
            original_index = result["index"]
            score = result["relevance_score"]


            original_chunk = chunks[original_index]

            reranked_chunk = RerankedResult(
                text=original_chunk.text,
                headline=original_chunk.headline,
                summary=original_chunk.summary,
                source=original_chunk.source,
                relevance_score=score
            )
            top_chunks.append(reranked_chunk)

        print(f"Reranked {len(chunks)} chunks down to top {len(top_chunks)}.")
        return top_chunks

    except requests.exceptions.RequestException as e:
        print(f"Error calling Jina Reranker: {e}")

        print("Falling back to unranked retrieval...")
        fallback_chunks = []
        for chunk in chunks[:FINAL_K]:
            fallback_chunks.append(
                RerankedResult(
                    text=chunk.text,
                    headline=chunk.headline,
                    summary=chunk.summary,
                    source=chunk.source,
                    relevance_score=0.0
                )
            )
        return fallback_chunks