import sys
import json
from pathlib import Path
from qdrant_client import QdrantClient
from rag_orchestrator.config import QDRANT_URL, QDRANT_API_KEY
from ticker_extractor import get_ticker


from MD_Generator import download_10k
from ingest.stage_1_worker import fetch_documents, get_blueprint, slice_document
from ingest.stage_2_worker import create_sub_chunks, process_single_part
from ingest.stage_3_embed import create_embeddings_for_file, FINAL_CHUNKS_CACHE


KNOWLEDGE_BASE_PATH = Path(__file__).parent / "Knowledge-base" / "finance_reports"


def build_knowledge_base(company_name: str, year: int):
    """Generator function that yields status updates to Gradio while building the KB."""


    yield "🔍 Step 1/5: Extracting stock ticker symbol..."
    ticker = get_ticker(company_name)
    if ticker == "UNKNOWN":
        yield f"❌ Error: Could not find a valid SEC ticker for '{company_name}'. Please check the spelling and try again."
        return

    yield f"✅ Identified Ticker: {ticker}"


    yield "🔍 Step 2/5: Checking cloud database..."
    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    collection_name = f"{ticker.lower()}_{year}_10k"


    existing = [c.name for c in qdrant_client.get_collections().collections]
    if collection_name in existing:
        count = qdrant_client.get_collection(collection_name).points_count
        yield f"✅ Data already exists in cloud! Found {count} chunks for {ticker} {year}. Ready to chat."
        return ticker


    yield f"📥 Step 3/5: Downloading {year} 10-K from SEC EDGAR..."
    try:
        if KNOWLEDGE_BASE_PATH/"{ticker}_{year}_10k.md":
            yield "file already exists"
        else:
            download_10k(ticker, year)
    except Exception as e:
        yield f"❌ Error downloading document: {e}. Ensure {ticker} filed a 10-K for {year}."
        return



    yield "🧠 Step 4/5: Processing document (Slicing & Generating Headlines/Summaries)..."
    try:

        md_path = KNOWLEDGE_BASE_PATH / f"{ticker}_{year}_10K.md"


        with open(md_path, "r", encoding="utf-8") as f:
            text = f.read()

        blueprint = get_blueprint({"text": text, "source": str(md_path), "type": "finance_reports"})
        sliced_parts = slice_document(text, blueprint)
        for part in sliced_parts:
            part["source"] = str(md_path)
            part["type"] = "finance_reports"

        all_final_chunks = []
        for part in sliced_parts:
            processed = process_single_part(part)
            all_final_chunks.extend(processed)

    except Exception as e:
        yield f"❌ Error processing document: {e}"
        return



    yield "☁️ Step 5/5: Embedding and uploading to Qdrant Cloud (this may take a minute)..."
    try:
        temp_cache = Path(__file__).parent / "temp_dynamic_cache.json"
        with open(temp_cache, "w", encoding="utf-8") as f:
            json.dump(all_final_chunks, f, ensure_ascii=False)


        original_cache = FINAL_CHUNKS_CACHE
        import ingest.stage3_embed as s3
        s3.FINAL_CHUNKS_CACHE = temp_cache

        create_embeddings_for_file(qdrant_client, all_final_chunks)


        temp_cache.unlink(missing_ok=True)
        s3.FINAL_CHUNKS_CACHE = original_cache

    except Exception as e:
        yield f"❌ Error uploading to cloud: {e}"
        return

    yield f"🎉 Success! Knowledge base for {company_name} ({year}) built and saved to cloud."
    return ticker

if __name__ == "__main__":
    company = "jp morgan"
    year = 2024

    for status in build_knowledge_base(company, year):
        print(status)