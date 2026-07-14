from pydantic import BaseModel, Field

class RetrievedChunk(BaseModel):
    """Standardized format for a chunk coming out of ChromaDB."""

    text: str
    headline: str
    summary: str
    source: str
    broad_topic: str

class RewrittenQuery(BaseModel):
    """The output format from the Query Rewriter LLM."""

    refined_query: str = Field(description="The short, specific question optimized for vector search.")


class RerankedResult(BaseModel):
    """The output format from the Jina Reranker."""


    text: str
    headline: str
    summary: str
    source: str
    relevance_score: float = Field(description="The relevance score returned by Jina (0.0 to 1.0)")