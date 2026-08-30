def get_candidate_models() -> list[str]:
    candidates = []
    if PREFERRED_MODEL:
        candidates.append(PREFERRED_MODEL)

    default_chat_models = [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768"
    ]

    if groq_client:
        try:
            models_page = groq_client.models.list()
            available = [m.id for m in models_page.data if getattr(m, 'active', True)]
            
            # Added "compound" to the excluded keyword filters
            excluded_keywords = ["guard", "whisper", "orpheus", "vision", "safetensors", "compound"]
            
            for m_id in available:
                m_lower = m_id.lower()
                if not any(ex in m_lower for ex in excluded_keywords):
                    if m_id not in candidates:
                        candidates.append(m_id)
        except Exception as e:
            print(f"Model Fetch Notice: {e}")

    for fb in default_chat_models:
        if fb not in candidates:
            candidates.append(fb)

    return candidates
