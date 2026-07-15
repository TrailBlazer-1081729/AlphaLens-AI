from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from litellm import completion
from tqdm import tqdm
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
)
import json
import time

sys_prompt = """You are a deterministic document segmentation engine for a Retrieval-Augmented Generation (RAG) pipeline.
Your job is NOT to rewrite, edit, summarize, improve, clean, or interpret the document.
Your job is to partition one input document into coherent semantic chunks while preserving every character of the original text.
You must follow these rules exactly.
------------------------
PRIMARY OBJECTIVE
------------------------

Partition the input into between 5 and 8 semantically coherent chunks.
Each chunk must represent one logical topic or closely related set of topics.
The chunks together must cover the ENTIRE input exactly once.
------------------------
CRITICAL RULES
------------------------

1. NEVER hallucinate.
2. NEVER invent text.
3. NEVER omit text.
4. NEVER duplicate text.
5. NEVER rewrite the original text.
6. NEVER fix grammar.
7. NEVER remove markdown.
8. NEVER change spacing, punctuation, tables, headings, or formatting.
9. original_text MUST be copied verbatim from the input.
10. Every character of the input must appear in exactly one chunk.
11. The concatenation of every original_text field must reconstruct the complete original input without losing any information.
12. Do not split a paragraph in the middle unless absolutely necessary.
13. Prefer splitting at natural semantic boundaries such as:
   - section headings
   - subsection headings
   - topic changes
   - major paragraph transitions
14. Keep related paragraphs together.
15. If one topic is extremely large, divide it into logical consecutive sections while preserving meaning.
------------------------
HEADLINE
------------------------

The headline must:
- be concise
- describe only the current chunk
- not mention information outside the chunk
- not invent titles
------------------------
SUMMARY
------------------------
The summary must:
- be 1–2 sentences
- describe only the information contained inside original_text
- not add external knowledge
- not speculate
- not infer facts not explicitly stated
------------------------
OUTPUT
------------------------
Return ONLY valid JSON.
Return no explanations.
Return no markdown.
Return no commentary.
The JSON must exactly follow the supplied schema."""

load_dotenv(override=True)
MODEL = "gemini/gemini-3.1-flash-lite"

SLICED_CACHE = Path(__file__).parent.parent / "stage_1_json" / "sliced_parts_cache.json"
FINAL_CHUNKS_CACHE = Path(__file__).parent.parent / "stage_2_json" / "final_rag_chunks.json"

TARGET_WORDS_PER_CHUNK = 25000
OVERLAP_WORDS = 1000


class WorkerChunk(BaseModel):
    headline: str = Field(description="A brief, specific heading for this sub-chunk")
    summary: str = Field(description="A short 1-2 sentence summary of this sub-chunk")
    original_text: str = Field(
        description="THE EXACT ORIGINAL TEXT. Copied word-for-word from the markers. DO NOT alter, format, or change a single character.")


class PartChunksResponse(BaseModel):
    chunks: list[WorkerChunk]


def create_sub_chunks(text: str, target_words: int = TARGET_WORDS_PER_CHUNK, overlap_words: int = OVERLAP_WORDS) -> \
list[str]:
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]

    if not paragraphs:
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

    if not paragraphs:
        return [text]

    chunks = []
    current_chunk_paragraphs = []
    current_word_count = 0

    for para in paragraphs:
        para_word_count = len(para.split())

        if para_word_count > target_words:
            if current_chunk_paragraphs:
                chunks.append("\n\n".join(current_chunk_paragraphs))
                current_chunk_paragraphs = []
                current_word_count = 0
            chunks.append(para)
            continue

        if current_word_count + para_word_count > target_words and current_chunk_paragraphs:
            chunks.append("\n\n".join(current_chunk_paragraphs))

            overlap_paragraphs = []
            overlap_word_count = 0
            for p in reversed(current_chunk_paragraphs):
                p_wc = len(p.split())
                if overlap_word_count + p_wc <= overlap_words:
                    overlap_paragraphs.insert(0, p)
                    overlap_word_count += p_wc
                else:
                    break

            current_chunk_paragraphs = overlap_paragraphs
            current_word_count = overlap_word_count

        current_chunk_paragraphs.append(para)
        current_word_count += para_word_count

    if current_chunk_paragraphs:
        chunks.append("\n\n".join(current_chunk_paragraphs))

    return chunks


def format_worker_prompt(part_topic: str, chunk: str) -> str:
    return f"""
    You are processing one logically isolated section of a corporate SEC 10-K filing for a Retrieval-Augmented Generation (RAG) system.
    Broad Topic:
    {part_topic}
    Your task is to divide the document below into BETWEEN 5 AND 8 coherent semantic chunks.
    A semantic chunk should represent one complete topic or closely related set of topics. Keep related paragraphs together whenever possible.
    For EACH chunk generate:
    1. headline
       - A concise and specific title describing only that chunk.
    2. summary
       - A factual 1-2 sentence summary describing only the contents of that chunk.
       - Do not add external knowledge or make assumptions.
    3. original_text
       - Copy the text EXACTLY as it appears in the input.
       - Do NOT rewrite. Do NOT paraphrase. Do NOT summarize. Do NOT correct grammar. Do NOT remove markdown. Do NOT remove tables. Do NOT modify whitespace or formatting.
    IMPORTANT RULES
    • Divide the document into 5-8 chunks.
    • Keep the chunks in the original document order.
    • Every piece of the input must appear in exactly ONE chunk.
    • Do NOT omit any text. Do NOT duplicate any text. Do NOT invent any text.
    • Prefer splitting at natural topic boundaries or headings.
    Document:
    ---------------- BEGIN DOCUMENT ----------------
    {chunk}
    ---------------- END DOCUMENT ----------------
    Return ONLY valid JSON that exactly matches the provided Pydantic schema.
    """


@retry(
    wait=wait_exponential(multiplier=1, min=10, max=240),
    stop=stop_after_attempt(5),
    reraise=True,
)
def process_single_chunk(part_topic: str, sub_chunk: str) -> list[WorkerChunk]:
    prompt = format_worker_prompt(part_topic, sub_chunk)

    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": prompt}
    ]

    response = completion(
        model=MODEL,
        messages=messages,
        response_format=PartChunksResponse
    )
    time.sleep(1)
    reply = response.choices[0].message.content
    return PartChunksResponse.model_validate_json(reply).chunks


def process_single_part(part_data: dict) -> list[dict]:
    part_topic = part_data.get("topic", "General Document Content")
    raw_text = part_data["text"]

    sub_chunks = create_sub_chunks(raw_text)
    print(f"  -> Sliced into {len(sub_chunks)} sub-chunks locally.")

    final_chunks = []

    for i, sub_chunk in enumerate(sub_chunks, start=1):
        print(f"    -> Gemini Call #{i}/{len(sub_chunks)}")

        llm_chunks = process_single_chunk(part_topic, sub_chunk)

        for llm_chunk in llm_chunks:

            merged_metadata = part_data.get("metadata", {})


            merged_metadata["source"] = part_data.get("source", "unknown")
            merged_metadata["type"] = part_data.get("type", "unknown")
            merged_metadata["broad_topic"] = part_topic

            final_chunks.append({
                "headline": llm_chunk.headline,
                "summary": llm_chunk.summary,
                "original_text": llm_chunk.original_text,
                "metadata": merged_metadata  # Now contains part, item, source, type, broad_topic
            })

    return final_chunks










if __name__ == "__main__":
    if not SLICED_CACHE.exists():
        print(f"Error: Could not find {SLICED_CACHE.name}")
        exit(1)
    with open(SLICED_CACHE, "r", encoding="utf-8") as f:
        sliced_parts = json.load(f)
    print(f"Loaded {len(sliced_parts)} parts to process")
    if FINAL_CHUNKS_CACHE.exists():
        print(f"Loading cached final chunks from {FINAL_CHUNKS_CACHE.name}...")
        with open(FINAL_CHUNKS_CACHE, "r", encoding="utf-8") as f:
            all_final_chunks = json.load(f)
    else:
        all_final_chunks = []
        print("Sending parts to Worker LLM ...")
        for part in tqdm(sliced_parts, desc="Processing Parts"):
            try:
                processed_chunks = process_single_part(part)
                all_final_chunks.extend(processed_chunks)
                print(f"  -> Successfully processed and validated.")
            except Exception as e:
                print(f"  -> Failed to process part: {part.get('topic', 'Unknown')}")
                print(f"     Error: {e}")
        with open(FINAL_CHUNKS_CACHE, "w", encoding="utf-8") as f:
            json.dump(all_final_chunks, f, indent=2, ensure_ascii=False)
        print(f"\nSuccess! Saved {len(all_final_chunks)} final chunks to {FINAL_CHUNKS_CACHE.name}")