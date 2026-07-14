from litellm import completion
from tenacity import retry, wait_exponential, stop_after_attempt
from rag_orchestrator.config import LLM_MODEL

wait = wait_exponential(multiplier=1, min=2, max=10)


@retry(wait=wait, stop=stop_after_attempt(3), reraise=True)
def generate_answer(messages: list[dict]) -> str:
    """
    Takes the final formatted messages and calls the LLM
    to generate the response.
    """
    response = completion(
        model=LLM_MODEL,
        messages=messages
    )

    return response.choices[0].message.content