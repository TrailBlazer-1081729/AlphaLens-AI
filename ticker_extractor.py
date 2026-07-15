from litellm import completion
from pydantic import BaseModel, Field
from rag_orchestrator.config import LLM_MODEL


class TickerResponse(BaseModel):
    ticker: str = Field(description="The exact stock ticker symbol in uppercase (e.g., MSFT, AAPL)")


def get_ticker(company_name: str) -> str:
    """Extracts the stock ticker symbol from a full company name."""
    
    prompt = f"""
    Extract the exact stock ticker symbol for the following company. 
    Company Name: {company_name}

    If you cannot confidently determine the ticker, return "UNKNOWN".
    Respond ONLY with the JSON object.
    """
    response = completion(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format=TickerResponse
    )

    result = TickerResponse.model_validate_json(response.choices[0].message.content)
    return result.ticker.upper()