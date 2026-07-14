from rag_orchestrator.rewrite import rewrite_query
from rag_orchestrator.retriever import retrieve_chunks
from rag_orchestrator.merger import merge_chunks
from rag_orchestrator.reranker import rerank_chunks
from rag_orchestrator.prompt_builder import build_rag_messages
from rag_orchestrator.generator import generate_answer
from rag_orchestrator.schema import RerankedResult


def run_rag_pipeline(
        question: str,
        ticker: str,
        year: int,
        history: list[dict] = []
) -> tuple[str, list[RerankedResult]]:
    """
    The main RAG orchestrator.
    Executes the pipeline step-by-step and returns the final answer
    along with the chunks used (useful for showing sources in Gradio).
    """

    print("=" * 60)
    print(f"🚀 STARTING RAG PIPELINE")
    print(f"📝 Question: {question}")
    print(f"📂 Target: {ticker} {year} 10-K")
    print("=" * 60)


    print("\n[1/6] Rewriting query for optimized vector search...")
    rewritten_query_obj = rewrite_query(question, history)
    print(f"      ➡️  Rewritten to: '{rewritten_query_obj.refined_query}'")


    print("\n[2/6] Fetching chunks for ORIGINAL query...")
    print("[3/6] Fetching chunks for REWRITTEN query...")
    original_chunks, rewritten_chunks = retrieve_chunks(
        question,
        rewritten_query_obj,
        ticker,
        year
    )


    print("\n[4/6] Merging and deduplicating retrieved chunks...")
    merged_chunks = merge_chunks(original_chunks, rewritten_chunks)


    print("\n[5/6] Reranking chunks using Jina Cross-Encoder...")
    top_chunks = rerank_chunks(question, merged_chunks)


    for i, chunk in enumerate(top_chunks, 1):
        print(f"      ➡️  Chunk {i}: {chunk.headline} (Score: {chunk.relevance_score:.3f})")


    print("\n[6/6] Building formatted prompt and calling final LLM...")
    messages = build_rag_messages(question, history, top_chunks)


    final_answer = generate_answer(messages)

    print("\n" + "=" * 60)
    print("✅ PIPELINE COMPLETE")
    print("=" * 60 + "\n")

    
    return final_answer, top_chunks