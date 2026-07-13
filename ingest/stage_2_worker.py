from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from litellm import completion
from tqdm import tqdm
from tenacity import retry, wait_exponential
import json
import re
import time

load_dotenv(override=True)
MODEL = "gemini/gemini-3.1-flash-lite"


SLICED_CACHE = Path(__file__).parent.parent/"stage_1_json"/ "sliced_parts_cache.json"
FINAL_CHUNKS_CACHE = Path(__file__).parent.parent/"stage_2_json"/ "final_rag_chunks.json"



TARGET_WORDS_PER_CHUNK = 400
OVERLAP_WORDS = 50
wait = wait_exponential(multiplier=1, min=10, max=240)




class WorkerChunk(BaseModel):
    headline: str = Field(description="A brief, specific heading for this sub-chunk")
    summary: str = Field(description="A short 1-2 sentence summary of this sub-chunk")
    original_text: str = Field(
        description="THE EXACT ORIGINAL TEXT. Copied word-for-word from the markers. DO NOT alter, format, or change a single character.")




class PartChunksResponse(BaseModel):
    chunks: list[WorkerChunk]




def create_sub_chunks(text: str, target_words: int = TARGET_WORDS_PER_CHUNK, overlap_words: int = OVERLAP_WORDS) -> \
list[str]:


    """
    Splits text into chunks based on sentences to avoid cutting mid-sentence.
    Implements a look-back overlap to ensure context isn't lost between chunks.
    """


    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]


    if not sentences:
        return [text]

    chunks = []
    current_chunk_sentences = []
    current_word_count = 0

    for sentence in sentences:
        sentence_word_count = len(sentence.split())

        if sentence_word_count > target_words:
            if current_chunk_sentences:
                chunks.append(" ".join(current_chunk_sentences))
                current_chunk_sentences = []
                current_word_count = 0
            chunks.append(sentence)
            continue


        if current_word_count + sentence_word_count > target_words and current_chunk_sentences:
            chunks.append(" ".join(current_chunk_sentences))


            overlap_sentences = []
            overlap_word_count = 0
            for s in reversed(current_chunk_sentences):
                s_wc = len(s.split())
                if overlap_word_count + s_wc <= overlap_words:
                    overlap_sentences.insert(0, s)
                    overlap_word_count += s_wc
                else:
                    break


            current_chunk_sentences = overlap_sentences
            current_word_count = overlap_word_count


        current_chunk_sentences.append(sentence)
        current_word_count += sentence_word_count


    if current_chunk_sentences:
        chunks.append(" ".join(current_chunk_sentences))

    return chunks


def format_worker_prompt(part_topic: str, sub_chunks: list[str]) -> str:
    """
    Wraps the sub-chunks in clear markers so the LLM knows exactly what text to copy.
    """
    chunk_text = ""
    for i, chunk in enumerate(sub_chunks, start=1):
        chunk_text += f"---CHUNK {i}---\n{chunk}\n---END CHUNK {i}---\n\n"

    return f"""
    You are an expert data processor for a RAG (Retrieval-Augmented Generation) system.
    You are currently processing a section of a corporate 10-K document.
    The broad topic of this entire section is: {part_topic}

    Below are {len(sub_chunks)} sub-chunks of text, separated by markers.

    YOUR TASK:
    For EACH chunk, generate a highly specific `headline` and a short 1-2 sentence `summary`.

    CRITICAL INSTRUCTION FOR `original_text`:
    You MUST copy the text EXACTLY as it appears between the markers. 
    - Do NOT fix grammar.
    - Do NOT remove markdown formatting (like ** or #).
    - Do NOT summarize or alter the text.
    - It must be a VERBATIM copy-paste of the text inside the markers.

    {chunk_text}

    Respond ONLY with a valid JSON object containing a "chunks" array, following the required schema.
    """


@retry(wait=wait)
def process_single_part(part_data: dict) -> list[dict]:
    """
    Takes one of the 12 parts, slices it, calls the LLM once, and returns the formatted chunks.
    """
    part_topic = part_data.get("topic", "General Document Content")
    raw_text = part_data["text"]


    sub_chunks = create_sub_chunks(raw_text)
    print(f"  -> Sliced into {len(sub_chunks)} sub-chunks locally.")



    prompt = format_worker_prompt(part_topic, sub_chunks)
    messages = [{"role": "user", "content": prompt}]



    response = completion(model=MODEL, messages=messages, response_format=PartChunksResponse)
    time.sleep(5)



    reply = response.choices[0].message.content
    llm_chunks = PartChunksResponse.model_validate_json(reply).chunks

    final_chunks = []
    for chunk in llm_chunks:
        final_chunks.append({
            "headline": chunk.headline,
            "summary": chunk.summary,
            "original_text": chunk.original_text,
            "metadata": {
                "source": part_data.get("source", "unknown"),
                "type": part_data.get("type", "unknown"),
                "broad_topic": part_topic
            }
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
