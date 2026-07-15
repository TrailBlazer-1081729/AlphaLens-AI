from pathlib import Path
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from openai import OpenAI
from tqdm import tqdm
import json
import re
import os

load_dotenv(override=True)
from tenacity import retry, stop_after_attempt, wait_exponential
import time


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(5),
    reraise=True,
)
def upload_batch(coll_name, batch_points):
    qdrant_client.upsert(collection_name=coll_name, points=batch_points)




FINAL_CHUNKS_CACHE = Path(__file__).parent.parent/"stage_2_dynamic_cache.json"


JINA_API_KEY = os.getenv("jina")
JINA_MODEL = "jina-embeddings-v4"
JINA_BATCH_SIZE = 10  # How many texts to send to Jina at once (100 is fast and safe)
QDRANT_UPLOAD_BATCH = 20  # How many vectors to upload to Qdrant at once (prevents timeout)



def sanitize_collection_name(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r'[^a-zA-Z0-9]', '_', name)
    name = re.sub(r'_+', '_', name)
    if name[0].isdigit():
        name = "doc_" + name
    return name.lower()



def create_embeddings_for_file(qdrant_client: QdrantClient, chunks: list[dict],collection_name:str):

    existing_collections = [c.name for c in qdrant_client.get_collections().collections]
    if collection_name in existing_collections:
        collection = qdrant_client.get_collection(collection_name)
        if collection.points_count > 0:
            print(f"  -> Collection '{collection_name}' already has {collection.points_count} chunks. Skipping.")
            return


    print(f"  -> Creating new collection: '{collection_name}' and calling Jina API...")
    qdrant_client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=2048, distance=Distance.COSINE)
    )


    texts_to_embed = [f"{chunk.get('headline', '')}\n\n{chunk['original_text']}" for chunk in chunks]
    jina_client = OpenAI(api_key=JINA_API_KEY, base_url="https://api.jina.ai/v1")
    vectors = []

    for i in tqdm(range(0, len(texts_to_embed), JINA_BATCH_SIZE), desc=f"Embedding {collection_name}"):
        batch = texts_to_embed[i:i + JINA_BATCH_SIZE]
        response = jina_client.embeddings.create(model=JINA_MODEL, input=batch)
        vectors.extend([x.embedding for x in response.data])
        time.sleep(5)


    points = []
    for idx, chunk in enumerate(chunks):
        payload = {
            "text": chunk["original_text"],
            "headline": chunk.get("headline", ""),
            "summary": chunk.get("summary", ""),
            "source": chunk["metadata"]["source"],
            "type": chunk["metadata"]["type"],
            "broad_topic": chunk["metadata"].get("broad_topic", ""),
            "part": chunk["metadata"].get("part", ""),
            "item": chunk["metadata"].get("item", "")
        }
        points.append(PointStruct(id=idx, vector=vectors[idx], payload=payload))


    for i in range(0, len(points), QDRANT_UPLOAD_BATCH):
        batch = points[i:i + QDRANT_UPLOAD_BATCH]
        print(f"  -> Uploading batch {i // QDRANT_UPLOAD_BATCH + 1}...")
        try:
            upload_batch(collection_name, batch)
            time.sleep(1)
        except Exception as e:
            print(f"  -> Failed to upload batch after multiple retries: {e}")
            raise e

    print(f"  -> Successfully uploaded {len(points)} chunks to Qdrant Cloud.")


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

    qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"),timeout=120)

    print(f"Found {len(file_groups)} distinct documents to process.\n")

    for source_file, chunks in file_groups.items():
        print(f"Processing: {Path(source_file).name}")
        create_embeddings_for_file(qdrant_client, chunks,"googl_2024_10k")
        print("-" * 40)

    print("\nIngestion complete! Data is now on Qdrant Cloud.")