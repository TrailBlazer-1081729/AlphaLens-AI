from litellm import completion
from tenacity import retry, wait_exponential, stop_after_attempt
from rag_orchestrator.config import LLM_MODEL
from rag_orchestrator.schema import RewrittenQuery


wait = wait_exponential(multiplier=1, min=2, max=10)


@retry(wait=wait, stop=stop_after_attempt(3), reraise=True)
def rewrite_query(question: str, history: list[dict] = []) -> RewrittenQuery:
    """
    Takes the user's raw question and uses an LLM to rewrite it into a
    highly specific, standalone query optimized for vector search.
    """

    system_prompt = """
    You are an expert search query optimizer for a specialized RAG (Retrieval-Augmented Generation) system.

    PROJECT CONTEXT:
    The knowledge base you are searching consists EXCLUSIVELY of corporate annual reports (specifically SEC Form 10-K filings). 
    These documents contain highly structured financial data, including:
    - Business overviews and product segments (e.g., iPhone, Cloud services)
    - Risk factors (Macroeconomic, Supply Chain, Competitive)
    - Financial statements (Balance Sheet, Income Statement, Cash Flows)
    - Management's Discussion and Analysis (MD&A)
    - Legal proceedings and executive compensation.

    YOUR TASK:
    Take the user's question (and optional chat history) and rewrite it into a short, highly specific search query that will retrieve the exact paragraphs from a 10-K filing.

    RULES:
    - Remove conversational filler (e.g., "Can you tell me", "Thanks").
    - Resolve pronouns using the history if necessary (e.g., change "What about their debt?" to "What is Microsoft's long-term debt structure?").
    - Use official 10-K terminology when possible (e.g., "Cost of sales", "Operating margin", "Geographic revenue segmentation").
    - Focus on core financial entities, metrics, and specific sections of the 10-K.
    - Respond ONLY with the refined search query string.
    """


    user_prompt = f"User's question: {question}\n"
    if history:
        user_prompt += f"Chat history: {history}\n"
    user_prompt += "Provide the optimized search query:"



    response = completion(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format=RewrittenQuery
    )


    return RewrittenQuery.model_validate_json(response.choices[0].message.content)