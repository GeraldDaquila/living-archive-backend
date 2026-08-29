def fetch_archive_context(query: str, top_k: int = 4) -> str:
    """
    Uses Pinecone's native inference API to generate embeddings 
    and retrieve metadata (titles, URLs, text chunks).
    """
    if not index or not pc:
        return ""

    try:
        # Embed query natively via Pinecone (uses default embedding model assigned to index)
        embeddings = pc.inference.embed(
            model="multilingual-e5-large", # or "llama-text-embed-v2" depending on index setup
            inputs=[query],
            parameters={"input_type": "query"}
        )
        
        query_vector = embeddings[0].values

        query_response = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True
        )

        context_blocks = []
        for match in query_response.get("matches", []):
            meta = match.get("metadata", {})
            title = meta.get("title", "Archive Reference")
            url = meta.get("url", "")
            text = meta.get("text", meta.get("chunk_text", ""))

            if url:
                context_blocks.append(f"ARTICLE TITLE: {title}\nURL: {url}\nEXCERPT: {text}\n")

        return "\n---\n".join(context_blocks)
    except Exception as e:
        print(f"Pinecone retrieval notice: {e}")
        return ""
