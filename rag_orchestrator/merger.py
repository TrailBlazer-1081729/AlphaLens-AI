from rag_orchestrator.schema import RetrievedChunk


def merge_chunks(
        original_chunks: list[RetrievedChunk],
        rewritten_chunks: list[RetrievedChunk]
) -> list[RetrievedChunk]:
    """
    Combines chunks from the original and rewritten queries.
    Removes exact duplicates based on the text content to ensure
    the reranker doesn't process the same paragraph twice.
    """


    merged = original_chunks[:]


    existing_texts = {chunk.text for chunk in merged}

    duplicate_count = 0

    
    for chunk in rewritten_chunks:
        if chunk.text not in existing_texts:
            merged.append(chunk)
            existing_texts.add(chunk.text)
        else:
            duplicate_count += 1

    print(
        f"Merged chunks: {len(original_chunks)} + {len(rewritten_chunks)} = {len(merged)} total (Removed {duplicate_count} duplicates)")

    return merged