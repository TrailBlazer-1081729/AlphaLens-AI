from rag_orchestrator.schema import RerankedResult

SYSTEM_PROMPT_TEMPLATE = """
You are a highly precise financial analyst AI assistant. Your sole purpose is to answer questions based STRICTLY on the provided excerpts from corporate 10-K annual reports.

RULES FOR ANSWERING:
1. **Accuracy is paramount:** Only use the information provided in the context below. Do not hallucinate, guess, or use outside knowledge.
2. **Financial specifics:** If the user asks for numbers, percentages, or financial metrics, If you cannot find specific requested information in the provided excerpts, state 'I could not locate [X] in the retrieved context' — do NOT claim the information is absent from the document, as the context provided may be incomplete
3. **Completeness:** Ensure you fully answer the question using the relevant excerpts. If multiple excerpts apply, synthesize them.
4. **Clarity:** Write your response in a clear, professional, and concise manner.

Here are the relevant excerpts from the 10-K filings:

{context}
"""


def build_rag_messages(
        question: str,
        history: list[dict],
        chunks: list[RerankedResult]
) -> list[dict]:
    """
    Takes the top reranked chunks and formats them into a structured
    context string, then builds the final messages array for the LLM.
    """


    context_parts = []
    for i, chunk in enumerate(chunks, start=1):

        formatted_chunk = f"""
--- EXCERPT {i} (Relevance Score: {chunk.relevance_score:.2f}) ---
**Topic:** {chunk.headline}
**Summary:** {chunk.summary}
**Original Text:**
{chunk.text}
"""
        context_parts.append(formatted_chunk)


    final_context = "\n".join(context_parts)


    system_message = {
        "role": "system",
        "content": SYSTEM_PROMPT_TEMPLATE.format(context=final_context)
    }

    
    messages = [system_message] + history + [{"role": "user", "content": question}]

    return messages