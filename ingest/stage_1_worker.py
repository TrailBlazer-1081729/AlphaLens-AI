from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from litellm import completion
from tqdm import tqdm
from tenacity import retry, wait_exponential
import json
import time

load_dotenv(override=True)

MODEL = "gemini/gemini-2.0-flash"
KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "knowledge-base"

wait = wait_exponential(multiplier=1, min=10, max=240)


class PartBoundary(BaseModel):
    part_number: int = Field(description="The sequential number of this part (e.g., 1, 2, 3...)")
    topic: str = Field(description="A brief description of the distinct topic covered in this part")
    start_anchor: str = Field(
        description="The EXACT first markdown heading or EXACT first 10 words of this part. Must be copy-pasted exactly from the text.")


class DocumentBlueprint(BaseModel):
    parts: list[PartBoundary]




def fetch_documents():
    """Reads all markdown files from the knowledge base."""
    documents = []
    for folder in KNOWLEDGE_BASE_PATH.iterdir():
        doc_type = folder.name
        for file in folder.rglob("*.md"):
            with open(file, "r", encoding="utf-8") as f:
                documents.append({"type": doc_type, "source": file.as_posix(), "text": f.read()})
    print(f"Loaded {len(documents)} documents")
    return documents




def make_architect_prompt(document_text: str) -> str:
    return f"""
    You are an expert document architect. I am giving you a corporate 10-K document in Markdown format.
    Your job is to divide this document into exactly 11 to 18 distinct parts. 

    CRITICAL RULE: Each part MUST cover a completely separate topic (e.g., one part for Business Overview, one for Risk Factors, one for Legal Proceedings, one for Financial Statements, etc.). There should be little to no contextual relation between the different parts.

    To tell me where to split the document, provide the EXACT text that begins each part. This should be a markdown heading (e.g., "## Item 1A. Risk Factors") or the EXACT first 10 words of the section if there is no heading. 
    Do NOT paraphrase. Do NOT guess. It must be copy-pasted EXACTLY as it appears in the source text, including exact punctuation and spacing.

    You must provide a start_anchor for EVERY part, including Part 1 (which will likely be the very first text of the document).

    Here is the document:

    {document_text}

    Return the JSON blueprint of the parts.
    """


# @retry(wait=wait)
def get_blueprint(document: dict) -> DocumentBlueprint:

    print(f"Getting blueprint for {document['source']}...")


    messages = [{"role": "user", "content": make_architect_prompt(document["text"])}]
    response = completion(model=MODEL, messages=messages, response_format=DocumentBlueprint)

    time.sleep(2)
    reply = response.choices[0].message.content
    return DocumentBlueprint.model_validate_json(reply)


def slice_document(text: str, blueprint: DocumentBlueprint) -> list[dict]:

    sliced_parts = []
    anchors = [p.start_anchor for p in blueprint.parts]

    for i in range(len(anchors)):
        anchor = anchors[i]

        start_idx = text.find(anchor)
        if start_idx == -1:
            raise ValueError(f"Failed to find exact anchor for Part {i + 1}: '{anchor}'")

        if i + 1 < len(anchors):
            end_idx = text.find(anchors[i + 1])
            if end_idx == -1:
                raise ValueError(f"Failed to find next anchor for Part {i + 2}: '{anchors[i + 1]}'")
        else:
            end_idx = len(text)

        part_text = text[start_idx:end_idx].strip()

        sliced_parts.append({
            "part_number": blueprint.parts[i].part_number,
            "topic": blueprint.parts[i].topic,
            "text": part_text
        })

    return sliced_parts


if __name__ == "__main__":
    documents = fetch_documents()
    cache_file = Path(__file__).parent.parent/"stage_1_json"/ "sliced_parts_cache.json"

    if cache_file.exists():

        print("Loading cached sliced parts...")
        with open(cache_file, "r", encoding="utf-8") as f:
            all_sliced_data = json.load(f)

    else:
        all_sliced_data = []
        print("Running Architect LLM to map split points...")

        for doc in tqdm(documents):
            try:
                blueprint = get_blueprint(doc)

                sliced_parts = slice_document(doc["text"], blueprint)

                for part in sliced_parts:
                    part["source"] = doc["source"]
                    part["type"] = doc["type"]

                all_sliced_data.extend(sliced_parts)
                print(f"  -> Successfully split into {len(sliced_parts)} parts.")

            except Exception as e:
                print(f"  -> Error processing {doc['source']}: {e}")

        # Save for the next step
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(all_sliced_data, f, indent=2, ensure_ascii=False)
        print(f"\nSaved {len(all_sliced_data)} total sliced parts to {cache_file.name}")
