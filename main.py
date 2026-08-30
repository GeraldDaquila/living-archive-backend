import re
from typing import Dict, Any

# =====================================================================
# INTENT CLASSIFICATION ENGINE (SITE ORIENTATION VS TOPICAL)
# =====================================================================

SITE_TOKENS_PATTERN = re.compile(
    r"\b(the\s+)?(whole\s+|own\s+)?(living\s+archive|archive|site|website|place|everything|all\s+this)(\s+itself|\s+as\s+a\s+whole|\s+on\s+this\s+site|\s+its\s+own\s+purpose)?\b",
    re.IGNORECASE
)

TOPICAL_PREPOSITION_GUARD = re.compile(
    r"\b(with|about|on|through|in|for|to)\s+(?!(the\s+)?(whole\s+|own\s+)?(living\s+archive|archive|site|website|place|everything|all\s+this)\b)\w+",
    re.IGNORECASE
)

SIGNAL_C_PATTERN = re.compile(
    r"^(what\s+is\s+(the\s+living\s+archive|this\s+archive|this\s+site|this\s+place)(\s+about)?|"
    r"where\s+(should|do)\s+i\s+(start|begin)|"
    r"how\s+(do|can)\s+i\s+navigate\s+(this\s+site|the\s+archive))$",
    re.IGNORECASE
)

SIGNAL_A_TOKENS = {"start", "begin", "entry", "first", "overwhelmed", "lost", "confused", "navigate", "explore", "find my way"}
SIGNAL_B_TOKENS = {"this site", "the site", "website", "this archive", "the archive", "living archive", "everything here", "all this", "how much is on"}

# UPDATE THIS SLUG/ID to match your actual Pinecone vector ID for the Living Archive Root Node
ROOT_NODE_ID = "canonical_root_living_archive" 

def classify_intent(query_str: str) -> str:
    clean_query = query_str.strip()

    # 1. Prepositional Guard (Topical Override)
    if TOPICAL_PREPOSITION_GUARD.search(clean_query):
        return "TOPICAL_INQUIRY"

    # 2. Explicit Identity Check
    if SIGNAL_C_PATTERN.search(clean_query):
        return "WHOLE_SITE_ORIENTATION"

    # 3. Site-Referential Prepositional Check
    if SITE_TOKENS_PATTERN.search(clean_query) and any(w in clean_query.lower() for w in SIGNAL_A_TOKENS):
        return "WHOLE_SITE_ORIENTATION"

    # 4. Compound Signal Check
    query_lower = clean_query.lower()
    has_signal_a = any(token in query_lower for token in SIGNAL_A_TOKENS)
    has_signal_b = any(token in query_lower for token in SIGNAL_B_TOKENS)

    if has_signal_a and has_signal_b:
        return "WHOLE_SITE_ORIENTATION"

    return "TOPICAL_INQUIRY"

# =====================================================================
# UPDATED RETRIEVAL LOGIC
# Replace your existing fetch_canonical_context function with this one
# =====================================================================

def fetch_canonical_context(user_query: str) -> Dict[str, Any]:
    intent = classify_intent(user_query)
    retrieved_docs = []

    if intent == "WHOLE_SITE_ORIENTATION":
        # Slot 1: Fetch Canonical Root Node
        try:
            root_doc = index.fetch(ids=[ROOT_NODE_ID])
            if ROOT_NODE_ID in root_doc.get("vectors", {}):
                retrieved_docs.append(root_doc["vectors"][ROOT_NODE_ID]["metadata"])
        except Exception as e:
            # Fallback gracefully if fetch fails
            pass

        # Slots 2–3: Semantic Backfill (K=2)
        query_vector = generate_local_embedding(user_query)
        res = index.query(vector=query_vector, top_k=2, include_metadata=True)
        for match in res.get("matches", []):
            if match["id"] != ROOT_NODE_ID:
                retrieved_docs.append(match["metadata"])
    else:
        # Standard Topical Retrieval (K=3)
        query_vector = generate_local_embedding(user_query)
        res = index.query(vector=query_vector, top_k=3, include_metadata=True)
        for match in res.get("matches", []):
            retrieved_docs.append(match["metadata"])

    retrieved_docs = retrieved_docs[:3]

    return {
        "intent": intent,
        "context_blocks": format_context_blocks(retrieved_docs)
    }
