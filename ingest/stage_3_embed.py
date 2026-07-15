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


FINAL_CHUNKS_CACHE = Path(__file__).parent.parent / "stage_2_json" / "final_rag_chunks.json"


JINA_API_KEY = os.getenv("jina")
JINA_MODEL = "jina-embeddings-v4"
JINA_BATCH_SIZE = 100  # How many texts to send to Jina at once (100 is fast and safe)
QDRANT_UPLOAD_BATCH = 20  # How many vectors to upload to Qdrant at once (prevents timeout)



def sanitize_collection_name(filename: str) -> str:
    name = Path(filename).stem
    name = re.sub(r'[^a-zA-Z0-9]', '_', name)
    name = re.sub(r'_+', '_', name)
    if name[0].isdigit():
        name = "doc_" + name
    return name.lower()



def create_embeddings_for_file(qdrant_client: QdrantClient, chunks: list[dict]):
    source_file = chunks[0]["metadata"]["source"]
    collection_name = sanitize_collection_name(source_file)


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


    points = []
    for idx, chunk in enumerate(chunks):
        payload = {
            "text": chunk["original_text"],
            "headline": chunk.get("headline", ""),
            "summary": chunk.get("summary", ""),
            "source": chunk["metadata"]["source"],
            "type": chunk["metadata"]["type"],
            "broad_topic": chunk["metadata"].get("broad_topic", "")
        }
        points.append(PointStruct(id=idx, vector=vectors[idx], payload=payload))


    for i in range(0, len(points), QDRANT_UPLOAD_BATCH):
        batch = points[i:i + QDRANT_UPLOAD_BATCH]
        qdrant_client.upsert(collection_name=collection_name, points=batch)

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

    qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL"), api_key=os.getenv("QDRANT_API_KEY"))

    print(f"Found {len(file_groups)} distinct documents to process.\n")

    for source_file, chunks in file_groups.items():
        print(f"Processing: {Path(source_file).name}")
        create_embeddings_for_file(qdrant_client, chunks)
        print("-" * 40)

    print("\nIngestion complete! Data is now on Qdrant Cloud.")