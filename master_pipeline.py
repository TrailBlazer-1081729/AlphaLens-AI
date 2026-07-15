import sys
import json
from pathlib import Path
from ingest.parsing import parse_10k_items
from rag_orchestrator.config import QDRANT_URL, QDRANT_API_KEY
from ticker_extractor import get_ticker
from MD_Generator import download_10k


KNOWLEDGE_BASE_PATH = Path(__file__).parent / "Knowledge-base" / "finance_reports"


def build_knowledge_base(company_name: str, year: int):
    """Generator function that yields status updates to Gradio while building the KB."""


    from qdrant_client import QdrantClient
    from ingest.stage_2_worker import  process_single_part
    from ingest.stage_3_embed import create_embeddings_for_file

    yield "🔍 Step 1/5: Extracting stock ticker symbol..."
    ticker = get_ticker(company_name)
    if ticker == "UNKNOWN":
        yield f"❌ Error: Could not find a valid SEC ticker for '{company_name}'. Please check the spelling and try again."
        return

    yield f"✅ Identified Ticker: {ticker}"

    yield "🔍 Step 2/5: Checking cloud database..."



    qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=120)
    collection_name = f"{ticker.lower()}_{year}_10k"

    max_retries = 3
    for attempt in range(max_retries):
        try:
            existing = [c.name for c in qdrant_client.get_collections().collections]
            if collection_name in existing:
                count = qdrant_client.get_collection(collection_name).points_count
                yield f"✅ Data already exists in cloud! Found {count} chunks for {ticker} {year}. Ready to chat."
                return
            break
        except Exception as e:
            if attempt < max_retries - 1:
                yield f"⚠️ Database connection attempt {attempt + 1} failed. Retrying in 5 seconds..."
                import time
                time.sleep(5)
            else:
                yield f"❌ Error connecting to database after {max_retries} attempts: {e}"
                return

    yield f"📥 Step 3/5: Downloading {year} 10-K from SEC EDGAR..."
    try:
        if (KNOWLEDGE_BASE_PATH / f"{ticker}_{year}_10k.md").exists():
            yield "✅ File already exists"
        else:
            download_10k(ticker, year)
    except Exception as e:
        yield f"❌ Error downloading document: {e}. Ensure {ticker} filed a 10-K for {year}."
        return

    # ------------------------------------------------------------------
    # STEP 4: Parse Markdown + Generate Headlines/Summaries
    # ------------------------------------------------------------------

    yield "🧠 Step 4/5: Parsing document and generating headlines..."

    try:
        md_path = KNOWLEDGE_BASE_PATH / f"{ticker}_{year}_10k.md"

        with open(md_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        # ----------------------------
        # Stage 1
        # ----------------------------
        sections = parse_10k_items(raw_text)

        print("\n" + "=" * 100)
        print(f"Stage 1 Complete - Found {len(sections)} Sections")
        print("=" * 100)

        # FIX: Use the correct dictionary keys from parse_10k_items
        for section in sections:
            print(
                f"{section.get('part_number', 0):02d}. "
                f"{section.get('topic', 'Unknown Topic')}"
            )

        print("=" * 100 + "\n")

        # ----------------------------
        # Stage 2
        # ----------------------------

        all_final_chunks = []
        total_sections = len(sections)

        for i, section in enumerate(sections, start=1):
            # FIX: Yield progress updates inside the loop so Gradio doesn't look stuck!
            topic_name = section.get("topic", "Unknown Topic")
            yield f"🧠 Step 4/5: Generating headlines... (Section {i}/{total_sections}: {topic_name})"

            part = {
                "part_number": i,
                "topic": topic_name,
                "text": section.get("text", ""),
                "source": section.get("source", str(md_path)),
                "type": section.get("type", "finance_reports"),
                "metadata": section.get("metadata", {})
            }

            processed_chunks = process_single_part(part)
            all_final_chunks.extend(processed_chunks)

        print(f"\n✅ Stage 2 Complete - Generated {len(all_final_chunks)} Final Chunks\n")

        stage_2_cache = Path(__file__).parent / "stage_2_dynamic_cache.json"
        with open(stage_2_cache, "w", encoding="utf-8") as f:
            json.dump(all_final_chunks, f, ensure_ascii=False)

    except Exception as e:
        yield f"❌ Error processing document: {e}"
        return




    yield "☁️ Step 5/5: Embedding and uploading to Qdrant Cloud (this may take a minute)..."

    max_retries = 5
    for attempt in range(max_retries):
        try:

            upload_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=120)
            create_embeddings_for_file(upload_client, all_final_chunks, collection_name)
            break

        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                yield f"⚠️ Step 5 connection failed (attempt {attempt + 1}/{max_retries}). Retrying in {wait_time}s... Error: {e}"
                import time
                time.sleep(wait_time)
            else:

                yield f"❌ Error uploading to cloud after {max_retries} attempts: {e}"
                return


if __name__ == "__main__":
    company = "jp morgan"
    year = 2024

    for status in build_knowledge_base(company, year):
        print(status)