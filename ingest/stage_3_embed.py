from pathlib import Path
from dotenv import load_dotenv
from chromadb import PersistentClient
from openai import OpenAI
from tqdm import tqdm
import json
import re
import os

load_dotenv(override=True)


FINAL_CHUNKS_CACHE = Path(__file__).parent.parent/"stage_2_json"/ "final_rag_chunks.json"
DB_NAME = str(Path(__file__).parent.parent / "finance_db")


JINA_API_KEY = os.getenv("jina")
JINA_MODEL = "jina-embeddings-v4"
BATCH_SIZE = 100



def sanitize_collection_name(filename: str) -> str:
    """
    ChromaDB requires collection names to be 3-63 characters,
    alphanumeric with underscores, and starting with a letter/underscore.
    """

    name = Path(filename).stem
    name = re.sub(r'[^a-zA-Z0-9]', '_', name)
    name = re.sub(r'_+', '_', name)
    if name[0].isdigit():
        name = "doc_" + name
    return name.lower()




def create_embeddings_for_file(chroma_client: OpenAI, chunks: list[dict]):
    """Processes a single file's chunks: checks DB, calls Jina, and inserts into Chroma."""

    source_file = chunks[0]["metadata"]["source"]
    collection_name = sanitize_collection_name(source_file)

    existing_collections = [c.name for c in chroma_client.list_collections()]
    if collection_name in existing_collections:
        collection = chroma_client.get_collection(collection_name)
        if collection.count() > 0:
            print(
                f"  -> Collection '{collection_name}' already has {collection.count()} chunks. Skipping to save API costs.")
            return

    print(f"  -> Creating new collection: '{collection_name}' and calling Jina API...")
    collection = chroma_client.get_or_create_collection(collection_name)



    texts_to_embed = [f"{chunk.get('headline', '')}\n\n{chunk['original_text']}" for chunk in chunks]
    ids = [str(i) for i in range(len(chunks))]



    metas = []
    for chunk in chunks:
        metas.append({
            "headline": chunk.get("headline", ""),
            "summary": chunk.get("summary", ""),
            "source": chunk["metadata"]["source"],
            "type": chunk["metadata"]["type"],
            "broad_topic": chunk["metadata"].get("broad_topic", "")
        })


    jina_client = OpenAI(api_key=JINA_API_KEY, base_url="https://api.jina.ai/v1")
    vectors = []

    for i in tqdm(range(0, len(texts_to_embed), BATCH_SIZE), desc=f"Embedding {collection_name}"):
        batch = texts_to_embed[i:i + BATCH_SIZE]
        response = jina_client.embeddings.create(model=JINA_MODEL, input=batch)
        vectors.extend([x.embedding for x in response.data])


    collection.add(
        ids=ids,
        embeddings=vectors,
        documents=texts_to_embed,
        metadatas=metas
    )
    print(f"  -> Successfully inserted {len(chunks)} chunks into '{collection_name}'.")


if __name__ == "__main__":
    if not FINAL_CHUNKS_CACHE.exists():
        print(f"Error: {FINAL_CHUNKS_CACHE.name} not found")
        exit(1)

    with open(FINAL_CHUNKS_CACHE, "r", encoding="utf-8") as f:
        all_chunks = json.load(f)

    print(f"Loaded {len(all_chunks)} chunks from cache.")

    file_groups = {}
    for chunk in all_chunks:
        source = chunk["metadata"]["source"]
        if source not in file_groups:
            file_groups[source] = []
        file_groups[source].append(chunk)


    chroma_client = PersistentClient(path=DB_NAME)

    print(f"Found {len(file_groups)} distinct documents to process.\n")


    for source_file, chunks in file_groups.items():
        print(f"Processing: {Path(source_file).name}")
        create_embeddings_for_file(chroma_client, chunks)
        print("-" * 40)

    print("\nIngestion complete! Your vector database is ready.")