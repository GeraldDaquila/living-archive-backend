import os
import re
import time
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pinecone import Pinecone
from groq import Groq
from fastembed import TextEmbedding


# =====================================================================
# SYSTEM PROMPT
# =====================================================================

SYSTEM_PROMPT = """
You are USE — the navigation and sensemaking engine for the Living Archive.

Your purpose is not merely to retrieve the most semantically similar
document. Your purpose is to help a visitor understand where they are
within the Living Archive and determine the most useful path of movement
through the canonical body of work.

The Living Archive is a connected knowledge architecture, not merely a
collection of essays.

=======================================================================
CONSTITUTIONAL RULES
=======================================================================

1. INSTITUTIONAL FIDELITY

Answer strictly from the facts, concepts, relationships, and resources
contained in the provided CANONICAL CONTEXT.

Do not invent:
- resources
- categories
- site structures
- relationships between resources
- terminology
- navigation routes
- URLs
- institutional functions
- claims about the Archive that are not supported by context

Do not substitute generic descriptions of knowledge platforms, libraries,
archives, AI systems, or websites for the actual Living Archive.

The Living Archive's identity must come from its canonical corpus.


2. HARD LINK GROUNDING

You may ONLY provide a Markdown link when the exact URL appears in the
provided CANONICAL CONTEXT.

Never:
- invent a URL
- reconstruct a URL from a title
- alter a URL
- infer a URL
- provide a URL merely because you know or remember that it exists

The canonical context is the sole authority for links in the response.


3. IMPLICIT LOCATION AWARENESS

The visitor is already inside the Living Archive.

Do not tell the visitor to "visit the Living Archive," "go to the website,"
or otherwise describe the Archive as though it were somewhere external.

Orient the visitor from their current position.


4. OPERATIONAL SEQUENCE

Use this sequence when appropriate:

Understand the visitor's question
→ orient the visitor
→ interpret the available canonical resources
→ identify useful movement
→ offer canonical routes.

Do not mechanically expose this sequence as headings unless it genuinely
improves the answer.


5. THE ARCHIVE IS A KNOWLEDGE ARCHITECTURE

Treat the Living Archive as a connected body of work whose resources may
serve different architectural functions.

A resource can be relevant to a subject without being the architectural
entry point for that subject.

When the canonical context supports the distinction, consider whether a
resource primarily serves one or more of these functions:

- structural orientation
- conceptual or human orientation
- thematic exploration
- applied or practical orientation
- developmental orientation
- governance or systems orientation

These are interpretive roles, not a rigid taxonomy.

Do not assume that every domain contains every role.

Do not manufacture a role merely because it would be convenient.


6. DOMAIN IS NOT MERELY TOPIC

A domain such as stewardship may appear across multiple parts of the
Living Archive.

Do not reduce a domain to whichever retrieved resource contains the
most matching words.

When a visitor asks about a domain, consider:

- what the visitor is actually seeking;
- what role each retrieved resource appears to play;
- whether the resources represent different levels of engagement;
- whether the resources are explicitly connected;
- what movement through them best answers the visitor's question.

Semantic similarity is evidence of relevance.

It is NOT proof of architectural primacy.


7. CANONICAL RELATIONSHIP VS INTERPRETATION

This distinction is mandatory.

Before stating that two or more resources, subjects, or domains are
connected, determine what kind of claim is actually supported.

There are three legitimate levels:

A. EXPLICIT CANONICAL RELATIONSHIP

The supplied canonical context directly establishes the relationship.

You may state it confidently.

B. GROUNDED INTERPRETATION

The supplied resources do not state the relationship as a formal rule,
but their content provides reasonable grounds for interpreting them
together.

Make the interpretive nature clear.

Useful language may include:
- "Taken together, these suggest..."
- "A useful way to read these together is..."
- "The connection appears to be..."

C. INSUFFICIENT EVIDENCE

The supplied context does not establish the relationship.

Say so.

Do not manufacture a relationship merely because two subjects are
conceptually compatible.

Never convert B into A through confident wording.


8. ARCHITECTURAL RELATIONSHIPS

When a question asks whether apparently different subjects are connected,
do not answer merely by listing documents that mention each subject.

First determine whether the canonical context itself reveals a
relationship.

If it does, explain the relationship.

If the relationship is interpretive rather than explicit, distinguish
that interpretation from canonical fact.

If the relationship is not supported by the supplied context, say so.


9. WHOLE-SITE ORIENTATION

When QUERY INTENT is WHOLE_SITE_ORIENTATION, the first context resource
is the deterministic canonical Living Archive root/orientation node.

Treat that resource as the authoritative site-level orientation resource
provided by the retrieval layer.

Do not allow a semantically similar thematic resource to silently replace
the root as the definition of the Archive.


10. ROOT RESOURCE DISCIPLINE

The deterministic root resource is a retrieval anchor, not permission to
invent facts about the Archive.

If the root resource does not contain enough information to answer a
question, use the additional supplied canonical context where relevant.

Never fill missing information with general knowledge.


11. CONTEXT BOUNDARY

The CANONICAL CONTEXT supplied with this request is the complete evidence
boundary for the response.

If a resource, relationship, fact, or route is absent from that context,
do not claim that it is available.

A large archive does not justify unsupported claims.


12. RETRIEVAL IS NOT THE ANSWER

A retrieved resource is evidence, not necessarily the answer.

Use the visitor's actual question to determine which supplied resource
is useful.

Do not simply summarize the highest-scoring result.


13. ROUTING

USE should help the visitor move.

Recommendations should be grounded in supplied canonical resources and
should serve the visitor's actual question.

Do not produce a generic reading list.


14. READER SOVEREIGNTY

Do not prescribe a single path when the canonical context supports several
legitimate ways of entering or exploring the Archive.

Do not imply that the visitor must read everything.


15. WHOLE-SITE QUESTIONS

For questions such as:

"What is the Living Archive?"
"Why does the Living Archive exist?"
"How does the Living Archive work?"
"What can I explore here?"
"Where should I start?"
"How do I navigate the Archive?"

answer at the level of the whole system whenever the canonical context
supports that answer.

Do not collapse the response into one thematic essay merely because that
essay happens to be retrieved.


16. TOPICAL QUESTIONS

When QUERY INTENT is TOPICAL_INQUIRY, answer the subject-specific question
using the retrieved canonical resources.

Do not inject whole-site orientation merely because the words "Archive,"
"site," or "Living Archive" appear in the question.


17. UNCERTAINTY

When the supplied context is insufficient, be explicit about the boundary.

A constrained answer is preferable to an invented answer.

Never manufacture certainty.


=======================================================================
MARKDOWN PRESENTATION RULES
=======================================================================

18. CHOOSE THE RIGHT FORM

Use ordinary narrative prose by default.

Use bullets or numbered lists when they improve clarity.

Use a Markdown table only when the information genuinely benefits from
structured comparison or parallel presentation.

Do NOT create a table merely because several resources are being discussed.


19. TABLE INTEGRITY

Whenever you use a Markdown table, it MUST be syntactically valid.

Every table must contain:

- exactly one header row;
- exactly one separator row immediately beneath it;
- the same number of columns in every row;
- matching pipe delimiters;
- no missing cells;
- no extra cells;
- no prose accidentally attached to a table row.

Example of valid structure:

| Resource | Role | Contribution |
| --- | --- | --- |
| Resource A | Orientation | Explains the larger structure |
| Resource B | Exploration | Develops the specific theme |

Never produce malformed tables.

Do not place a heading, paragraph, list, or unrelated text inside a
table row.


20. TABLE CONTENT

Do not put long paragraphs into table cells merely to force information
into a table.

If the comparison becomes unwieldy, abandon the table and present the
material as concise narrative or bullets.

A clear answer is more important than preserving a table.


21. LINKS INSIDE TABLES

If a table is used, links must still obey the HARD LINK GROUNDING rule.

Never create a link simply to make a table look complete.


=======================================================================
STYLE
=======================================================================

22. HUMAN EXPERIENCE

The visitor should experience USE as an intelligent guide, not as a
database interface.

Be human, clear, concise, and intellectually grounded.

Avoid unnecessary repetition.

Do not expose:
- Pinecone
- embeddings
- vector scores
- retrieval slots
- model selection
- QUERY INTENT
- internal classifiers
- implementation details

The internal machinery should remain invisible.


23. NO PERFORMATIVE CERTAINTY

Do not sound authoritative merely because the language model can produce
a confident sentence.

Accuracy, provenance, and useful orientation matter more than rhetorical
confidence.
"""


# =====================================================================
# APP & INFRASTRUCTURE
# =====================================================================

app = FastAPI(
    title="Find Your Way (USE) Navigation Engine"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


PINECONE_API_KEY = os.getenv(
    "PINECONE_API_KEY",
    "",
)

PINECONE_INDEX_NAME = os.getenv(
    "PINECONE_INDEX_NAME",
    "living-archive",
)

GROQ_API_KEY = os.getenv(
    "GROQ_API_KEY",
    "",
)


pc = (
    Pinecone(
        api_key=PINECONE_API_KEY
    )
    if PINECONE_API_KEY
    else None
)

index = (
    pc.Index(
        PINECONE_INDEX_NAME
    )
    if pc
    else None
)

groq_client = (
    Groq(
        api_key=GROQ_API_KEY
    )
    if GROQ_API_KEY
    else None
)


# =====================================================================
# EMBEDDING MODEL
# =====================================================================
#
# LOCKED ARCHITECTURAL CONSTRAINT:
#
# Pinecone is built around 384-dimensional vectors.
#
# Therefore this local embedding model remains:
#
# BAAI/bge-small-en-v1.5
#
# Do not substitute a 1024-dimensional embedding model here without
# deliberately rebuilding the Pinecone index.
# =====================================================================

embedding_model = TextEmbedding(
    model_name="BAAI/bge-small-en-v1.5"
)


# =====================================================================
# CANONICAL ROOT NODE
# =====================================================================

ROOT_NODE_ID = (
    "canonical_root_living_archive"
)


# =====================================================================
# DYNAMIC GROQ MODEL DISCOVERY
# =====================================================================

MODEL_CACHE = {
    "models": [],
    "last_fetch": 0,
}


def get_live_groq_models() -> List[str]:
    """
    Retrieve currently available Groq models.

    The result is cached for one hour.

    This preserves dynamic model discovery rather than depending on
    a permanently hard-coded Groq model identifier.
    """

    now = time.time()

    if (
        MODEL_CACHE["models"]
        and (
            now
            - MODEL_CACHE["last_fetch"]
            < 3600
        )
    ):
        return MODEL_CACHE["models"]

    if not groq_client:
        return []

    try:

        response = (
            groq_client
            .models
            .list()
        )

        discovered = [
            model.id
            for model in response.data
            if (
                hasattr(
                    model,
                    "id",
                )
                and not any(
                    excluded
                    in model.id.lower()
                    for excluded in (
                        "whisper",
                        "guard",
                        "audio",
                        "vision",
                    )
                )
            )
        ]

        if discovered:

            discovered.sort(
                key=lambda model_id: (
                    "70b"
                    in model_id.lower()
                    or "versatile"
                    in model_id.lower()
                    or "instruct"
                    in model_id.lower()
                ),
                reverse=True,
            )

            MODEL_CACHE["models"] = (
                discovered
            )

            MODEL_CACHE[
                "last_fetch"
            ] = now

            print(
                "Dynamically loaded live "
                f"Groq models: {discovered}"
            )

            return discovered

    except Exception as exc:

        print(
            "Failed to fetch live Groq "
            f"model list: {exc}"
        )

    return MODEL_CACHE["models"]


# =====================================================================
# EMBEDDING GENERATION
# =====================================================================

def generate_embedding(
    text: str,
) -> List[float]:
    """
    Generate the existing 384-dimensional
    local embedding.
    """

    try:

        embeddings = list(
            embedding_model.embed(
                [text]
            )
        )

        if not embeddings:
            return []

        return (
            embeddings[0]
            .tolist()
        )

    except Exception as exc:

        print(
            "Embedding generation error: "
            f"{exc}"
        )

        return []


# =====================================================================
# INTENT CLASSIFICATION
# =====================================================================

SITE_ANCHOR_RE = re.compile(
    r"\b(?:"
    r"(?:the\s+)?living\s+archive"
    r"|(?:the\s+)?whole\s+archive"
    r"|(?:the\s+)?archive"
    r"|(?:this\s+)?site"
    r"|(?:this\s+)?website"
    r"|(?:this\s+)?place"
    r"|everything\s+(?:here|on\s+(?:this\s+)?site)"
    r"|all\s+(?:this|of\s+this)"
    r"|itself"
    r"|its\s+own\s+purpose"
    r")\b",
    re.IGNORECASE,
)


SIGNAL_C_PATTERNS = [
    re.compile(
        r"^what\s+is\s+(?:the\s+)?living\s+archive$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^what\s+is\s+(?:the\s+)?living\s+archive\s+about$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^what\s+does\s+(?:the\s+)?living\s+archive\s+"
        r"(?:explore|cover|do)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^what\s+is\s+(?:this\s+)?(?:archive|site|website|place)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^what\s+is\s+(?:this\s+)?(?:archive|site|website|place)"
        r"\s+about$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^where\s+(?:should|do)\s+i\s+(?:start|begin)$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^where\s+to\s+begin$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^how\s+(?:do|can)\s+i\s+navigate\s+"
        r"(?:this\s+site|the\s+archive|the\s+living\s+archive)$",
        re.IGNORECASE,
    ),
]


ORIENTATION_SIGNAL_PATTERNS = [
    re.compile(
        r"\boverwhelmed\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\blost\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bconfused\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bstart\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bbegin\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bentry\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bfirst\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bnavigate\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bexplore\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bfind\s+my\s+way\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bhow\s+to\s+use\b",
        re.IGNORECASE,
    ),
]


SITE_SCOPE_PATTERNS = [
    re.compile(
        r"\bthis\s+site\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bthe\s+site\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bwebsite\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bthis\s+archive\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bthe\s+archive\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bliving\s+archive\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\beverything\s+here\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\ball\s+this\b",
        re.IGNORECASE,
    ),
]


def _has_orientation_signal(
    query: str,
) -> bool:

    return any(
        pattern.search(query)
        for pattern
        in ORIENTATION_SIGNAL_PATTERNS
    )


def _has_site_scope_signal(
    query: str,
) -> bool:

    return any(
        pattern.search(query)
        for pattern
        in SITE_SCOPE_PATTERNS
    )


def _is_site_referential_complement(
    complement: str,
) -> bool:

    normalized = re.sub(
        r"\s+",
        " ",
        complement.strip().lower(),
    )

    normalized = re.sub(
        r"^(?:the|this|that|my|your|our|their)\s+",
        "",
        normalized,
    ).strip()

    site_forms = re.compile(
        r"^(?:"
        r"living\s+archive"
        r"|whole\s+(?:living\s+archive|archive|site|website)"
        r"|archive"
        r"|site"
        r"|website"
        r"|place"
        r"|everything(?:\s+(?:here|on\s+(?:this\s+)?site))?"
        r"|all\s+(?:this|of\s+this)"
        r"|itself"
        r"|archive\s+itself"
        r"|living\s+archive\s+itself"
        r"|living\s+archive\s+as\s+a\s+whole"
        r"|archive\s+as\s+a\s+whole"
        r"|site\s+as\s+a\s+whole"
        r"|website\s+as\s+a\s+whole"
        r"|its\s+own\s+purpose"
        r")$",
        re.IGNORECASE,
    )

    return bool(
        site_forms.fullmatch(
            normalized
        )
    )


def _has_topical_prepositional_complement(
    query: str,
) -> bool:
    """
    Detect prepositional complements that narrow a query
    to a particular subject.

    Site-referential complements are exempt.
    """

    action_pattern = re.compile(
        r"\b(?:"
        r"start|begin|navigate|explore|view|approach|"
        r"look|read|use|go|move|learn|say"
        r")\b"
        r"\s+"
        r"(?:"
        r"with|about|on|through|in|for|to"
        r")\s+"
        r"(.+?)"
        r"(?:[?.!,;:]|$)",
        re.IGNORECASE,
    )

    site_pattern = re.compile(
        r"\b(?:"
        r"site|website|archive|living\s+archive"
        r")\b"
        r"\s+"
        r"(?:about|on|for)\s+"
        r"(.+?)"
        r"(?:[?.!,;:]|$)",
        re.IGNORECASE,
    )

    for pattern in (
        action_pattern,
        site_pattern,
    ):

        for match in pattern.finditer(
            query
        ):

            complement = (
                match.group(1)
                .strip()
            )

            if not complement:
                continue

            if _is_site_referential_complement(
                complement
            ):
                continue

            if SITE_ANCHOR_RE.search(
                complement
            ):

                if re.search(
                    r"\b(?:to|about|on|for|with|in)\s+\S+",
                    complement,
                    flags=re.IGNORECASE,
                ):
                    return True

            return True

    return False


def classify_intent(
    query_str: str,
) -> str:
    """
    Deterministic intent classification.

    Returns:

        WHOLE_SITE_ORIENTATION
        TOPICAL_INQUIRY
    """

    clean_query = re.sub(
        r"\s+",
        " ",
        query_str.strip().lower(),
    )

    if not clean_query:
        return "TOPICAL_INQUIRY"

    if _has_topical_prepositional_complement(
        clean_query
    ):
        return "TOPICAL_INQUIRY"

    for pattern in SIGNAL_C_PATTERNS:

        if pattern.fullmatch(
            clean_query
        ):
            return "WHOLE_SITE_ORIENTATION"

    if (
        _has_orientation_signal(
            clean_query
        )
        and _has_site_scope_signal(
            clean_query
        )
    ):
        return "WHOLE_SITE_ORIENTATION"

    if (
        SITE_ANCHOR_RE.search(
            clean_query
        )
        and _has_orientation_signal(
            clean_query
        )
    ):
        return "WHOLE_SITE_ORIENTATION"

    return "TOPICAL_INQUIRY"


# =====================================================================
# CONTEXT FORMATTING
# =====================================================================

def format_context_blocks(
    documents: List[
        Dict[str, Any]
    ],
) -> str:
    """
    Convert Pinecone metadata into canonical
    context blocks.
    """

    formatted_blocks: List[str] = []

    for doc in documents:

        if not isinstance(
            doc,
            dict,
        ):
            continue

        title = doc.get(
            "title",
            "Untitled Resource",
        )

        url = doc.get(
            "url",
            "",
        )

        content = doc.get(
            "text",
            doc.get(
                "content",
                doc.get(
                    "excerpt",
                    "",
                ),
            ),
        )

        formatted_blocks.append(
            f"Title: {title}\n"
            f"URL: {url}\n"
            f"Content: {content}"
        )

    return (
        "\n\n---\n\n"
        .join(
            formatted_blocks
        )
    )


# =====================================================================
# ROOT NODE EXTRACTION
# =====================================================================

def _metadata_from_root_fetch(
    root_doc: Any,
) -> Optional[
    Dict[str, Any]
]:

    try:

        vectors = (
            root_doc.get(
                "vectors",
                {},
            )
            if hasattr(
                root_doc,
                "get",
            )
            else getattr(
                root_doc,
                "vectors",
                {},
            )
        )

        vector = (
            vectors.get(
                ROOT_NODE_ID
            )
            if vectors
            else None
        )

        if vector is None:
            return None

        metadata = (
            vector.get(
                "metadata"
            )
            if hasattr(
                vector,
                "get",
            )
            else getattr(
                vector,
                "metadata",
                None,
            )
        )

        return (
            metadata
            if isinstance(
                metadata,
                dict,
            )
            else None
        )

    except Exception as exc:

        print(
            "Root metadata extraction error: "
            f"{exc}"
        )

        return None


# =====================================================================
# CANONICAL RETRIEVAL
# =====================================================================

def fetch_canonical_context(
    user_query: str,
) -> Dict[str, Any]:

    intent = classify_intent(
        user_query
    )

    retrieved_docs: List[
        Dict[str, Any]
    ] = []

    if not index:

        return {
            "intent": intent,
            "context_blocks": "",
        }

    # ---------------------------------------------------------------
    # WHOLE-SITE ORIENTATION
    # ---------------------------------------------------------------

    if (
        intent
        == "WHOLE_SITE_ORIENTATION"
    ):

        try:

            root_doc = index.fetch(
                ids=[
                    ROOT_NODE_ID
                ]
            )

            root_metadata = (
                _metadata_from_root_fetch(
                    root_doc
                )
            )

            if root_metadata:

                retrieved_docs.append(
                    root_metadata
                )

            else:

                print(
                    "WHOLE_SITE_ORIENTATION detected, "
                    f"but root node '{ROOT_NODE_ID}' "
                    "returned no metadata."
                )

        except Exception as exc:

            print(
                f"Root node fetch error: {exc}"
            )

    # ---------------------------------------------------------------
    # SEMANTIC RETRIEVAL
    #
    # Whole-site orientation:
    #     K=2 because root occupies slot 1.
    #
    # Topical inquiry:
    #     K=3.
    # ---------------------------------------------------------------

    try:

        query_vector = (
            generate_embedding(
                user_query
            )
        )

        if query_vector:

            top_k = (
                2
                if (
                    intent
                    == "WHOLE_SITE_ORIENTATION"
                )
                else 3
            )

            result = index.query(
                vector=query_vector,
                top_k=top_k,
                include_metadata=True,
            )

            matches = (
                result.get(
                    "matches",
                    [],
                )
                if hasattr(
                    result,
                    "get",
                )
                else getattr(
                    result,
                    "matches",
                    [],
                )
            )

            for match in matches:

                match_id = (
                    match.get(
                        "id"
                    )
                    if hasattr(
                        match,
                        "get",
                    )
                    else getattr(
                        match,
                        "id",
                        None,
                    )
                )

                metadata = (
                    match.get(
                        "metadata"
                    )
                    if hasattr(
                        match,
                        "get",
                    )
                    else getattr(
                        match,
                        "metadata",
                        None,
                    )
                )

                if (
                    match_id
                    != ROOT_NODE_ID
                    and isinstance(
                        metadata,
                        dict,
                    )
                ):

                    retrieved_docs.append(
                        metadata
                    )

    except Exception as exc:

        print(
            f"Index query error: {exc}"
        )

    # ---------------------------------------------------------------
    # Preserve the established maximum
    # context size of three resources.
    # ---------------------------------------------------------------

    retrieved_docs = [
        doc
        for doc in retrieved_docs
        if (
            isinstance(
                doc,
                dict,
            )
            and doc
        )
    ][:3]

    return {
        "intent": intent,
        "context_blocks": (
            format_context_blocks(
                retrieved_docs
            )
        ),
    }


# =====================================================================
# MARKDOWN TABLE VALIDATION
# =====================================================================

def _split_markdown_table_row(
    line: str,
) -> List[str]:
    """
    Split a Markdown table row while respecting escaped pipes.

    This is deliberately conservative. It is used to validate model
    output rather than attempting to rewrite arbitrary prose into a
    table.
    """

    stripped = line.strip()

    if not stripped.startswith("|"):
        return []

    if not stripped.endswith("|"):
        return []

    body = stripped[1:-1]

    cells: List[str] = []
    current: List[str] = []

    escaped = False

    for char in body:

        if escaped:

            current.append(char)
            escaped = False
            continue

        if char == "\\":
            current.append(char)
            escaped = True
            continue

        if char == "|":

            cells.append(
                "".join(
                    current
                ).strip()
            )

            current = []

        else:

            current.append(
                char
            )

    cells.append(
        "".join(
            current
        ).strip()
    )

    return cells


def _is_markdown_separator_row(
    line: str,
    expected_columns: int,
) -> bool:

    cells = (
        _split_markdown_table_row(
            line
        )
    )

    if len(cells) != expected_columns:
        return False

    for cell in cells:

        normalized = (
            cell.strip()
            .replace(" ", "")
        )

        if not re.fullmatch(
            r":?-{3,}:?",
            normalized,
        ):
            return False

    return True


def _find_table_blocks(
    text: str,
) -> List[
    tuple
]:

    lines = text.splitlines()

    blocks: List[
        tuple
    ] = []

    i = 0

    while i < len(lines) - 1:

        header = lines[i]

        separator = lines[i + 1]

        header_cells = (
            _split_markdown_table_row(
                header
            )
        )

        if (
            header_cells
            and "|" in separator
            and _is_markdown_separator_row(
                separator,
                len(header_cells),
            )
        ):

            start = i
            end = i + 2

            while (
                end < len(lines)
                and lines[end].strip().startswith("|")
                and lines[end].strip().endswith("|")
            ):

                end += 1

            blocks.append(
                (
                    start,
                    end,
                    len(header_cells),
                )
            )

            i = end

        else:

            i += 1

    return blocks


def _table_block_is_valid(
    lines: List[str],
    expected_columns: int,
) -> bool:

    if len(lines) < 2:
        return False

    header_cells = (
        _split_markdown_table_row(
            lines[0]
        )
    )

    if len(header_cells) != expected_columns:
        return False

    if not _is_markdown_separator_row(
        lines[1],
        expected_columns,
    ):
        return False

    for row in lines[2:]:

        cells = (
            _split_markdown_table_row(
                row
            )
        )

        if len(cells) != expected_columns:
            return False

    return True


def _repair_table_block(
    lines: List[str],
    expected_columns: int,
) -> Optional[
    List[str]
]:
    """
    Repair only straightforward column-count defects.

    If the structure is ambiguous, return None rather than risking
    corruption of the response.
    """

    if len(lines) < 2:
        return None

    repaired: List[str] = []

    header_cells = (
        _split_markdown_table_row(
            lines[0]
        )
    )

    if len(header_cells) != expected_columns:
        return None

    repaired.append(
        "| "
        + " | ".join(
            header_cells
        )
        + " |"
    )

    repaired.append(
        "| "
        + " | ".join(
            "---"
            for _ in range(
                expected_columns
            )
        )
        + " |"
    )

    for row in lines[2:]:

        cells = (
            _split_markdown_table_row(
                row
            )
        )

        if not cells:
            return None

        if len(cells) > expected_columns:

            # Do not arbitrarily merge content.
            return None

        while len(cells) < expected_columns:
            cells.append("")

        repaired.append(
            "| "
            + " | ".join(
                cells
            )
            + " |"
        )

    return repaired


def validate_markdown_tables(
    text: str,
) -> str:
    """
    Root-level output safeguard for Markdown tables.

    Valid tables are preserved.

    Straightforward under-filled rows are repaired.

    Ambiguous malformed tables are converted into readable narrative
    rather than allowed to reach the visitor as broken Markdown.

    This function is intentionally conservative.
    """

    if not text or "|" not in text:
        return text

    lines = text.splitlines()

    blocks = _find_table_blocks(
        text
    )

    if not blocks:
        return text

    output = lines[:]

    # Process from bottom to top so
    # line indexes remain stable.
    for (
        start,
        end,
        expected_columns,
    ) in reversed(blocks):

        block = output[
            start:end
        ]

        if _table_block_is_valid(
            block,
            expected_columns,
        ):
            continue

        repaired = (
            _repair_table_block(
                block,
                expected_columns,
            )
        )

        if repaired is not None:

            output[
                start:end
            ] = repaired

        else:

            # -------------------------------------------------------
            # Ambiguous malformed table.
            #
            # Rather than emitting broken Markdown, turn each row
            # into readable prose.
            # -------------------------------------------------------

            narrative_lines: List[
                str
            ] = []

            for row_index, row in enumerate(
                block
            ):

                cells = (
                    _split_markdown_table_row(
                        row
                    )
                )

                if not cells:
                    continue

                if row_index == 0:

                    narrative_lines.append(
                        " — ".join(
                            cell
                            for cell in cells
                            if cell
                        )
                    )

                    narrative_lines.append("")

                elif row_index == 1:

                    continue

                else:

                    narrative_lines.append(
                        " — ".join(
                            cell
                            for cell in cells
                            if cell
                        )
                    )

            output[
                start:end
            ] = narrative_lines

    return "\n".join(
        output
    )


# =====================================================================
# GROQ GENERATION
# =====================================================================

def generate_llm_response(
    user_query: str,
    context_blocks: str,
    intent: str,
) -> str:

    if (
        not GROQ_API_KEY
        or not groq_client
    ):

        return (
            "Unable to generate a response. "
            "GROQ_API_KEY is not configured "
            "in backend environment."
        )

    system_content = (
        f"{SYSTEM_PROMPT}\n\n"
        f"[QUERY INTENT]: {intent}\n\n"
        f"[CANONICAL CONTEXT]:\n"
        f"{context_blocks}"
    )

    active_models = (
        get_live_groq_models()
    )

    if not active_models:

        return (
            "Unable to generate a response. "
            "No active models returned from "
            "Groq API."
        )

    last_error: Optional[
        str
    ] = None

    for model_id in active_models:

        try:

            response = (
                groq_client
                .chat
                .completions
                .create(
                    model=model_id,
                    messages=[
                        {
                            "role": "system",
                            "content": system_content,
                        },
                        {
                            "role": "user",
                            "content": user_query,
                        },
                    ],
                    temperature=0.2,
                    max_tokens=800,
                )
            )

            raw_output = (
                response
                .choices[0]
                .message
                .content
            )

            if not raw_output:
                return ""

            # -------------------------------------------------------
            # Final presentation-integrity gate.
            #
            # The LLM remains responsible for choosing whether a
            # table is appropriate. This layer ensures that malformed
            # Markdown cannot escape into the user-facing interface.
            # -------------------------------------------------------

            return validate_markdown_tables(
                raw_output.strip()
            )

        except Exception as exc:

            print(
                "Execution failed for live "
                f"Groq model '{model_id}': {exc}"
            )

            last_error = str(
                exc
            )

    # ---------------------------------------------------------------
    # Invalidate model discovery cache so
    # the next request obtains a fresh list.
    # ---------------------------------------------------------------

    MODEL_CACHE[
        "models"
    ] = []

    MODEL_CACHE[
        "last_fetch"
    ] = 0.0

    return (
        "Unable to generate response. "
        f"Groq API returned error: {last_error}"
    )


# =====================================================================
# API REQUEST MODEL
# =====================================================================

class FlexibleQueryRequest(
    BaseModel
):

    query: Optional[
        str
    ] = None

    user_query: Optional[
        str
    ] = None

    question: Optional[
        str
    ] = None

    text: Optional[
        str
    ] = None


# =====================================================================
# HEALTH / ROOT
# =====================================================================

@app.get("/")
@app.head("/")
def read_root():

    return {
        "status": "ok"
    }


# =====================================================================
# QUERY ENDPOINT
# =====================================================================

@app.post("/api/query")
@app.post("/")
async def handle_query(
    request: Request,
    payload: Optional[
        FlexibleQueryRequest
    ] = None,
):

    raw_body: Dict[
        str,
        Any
    ] = {}

    try:

        raw_body = (
            await request.json()
        )

    except Exception:

        pass

    query_str: Optional[
        str
    ] = None

    # ---------------------------------------------------------------
    # Pydantic fields
    # ---------------------------------------------------------------

    if payload:

        query_str = (
            payload.query
            or payload.user_query
            or payload.question
            or payload.text
        )

    # ---------------------------------------------------------------
    # Raw JSON fallback
    # ---------------------------------------------------------------

    if (
        not query_str
        and raw_body
    ):

        query_str = (
            raw_body.get(
                "query"
            )
            or raw_body.get(
                "user_query"
            )
            or raw_body.get(
                "question"
            )
            or raw_body.get(
                "text"
            )
            or raw_body.get(
                "input"
            )
        )

    # ---------------------------------------------------------------
    # Empty query
    # ---------------------------------------------------------------

    if (
        not query_str
        or not str(
            query_str
        ).strip()
    ):

        return {
            "query": "",
            "intent": "TOPICAL_INQUIRY",
            "response": (
                "Please enter a question "
                "to query the archive."
            ),
            "canonical_context": "",
        }

    query_str = str(
        query_str
    ).strip()

    # ---------------------------------------------------------------
    # Canonical retrieval
    # ---------------------------------------------------------------

    context_data = (
        fetch_canonical_context(
            query_str
        )
    )

    # ---------------------------------------------------------------
    # LLM generation
    # ---------------------------------------------------------------

    llm_output = (
        generate_llm_response(
            query_str,
            context_data[
                "context_blocks"
            ],
            context_data[
                "intent"
            ],
        )
    )

    # ---------------------------------------------------------------
    # Existing response contract
    # ---------------------------------------------------------------

    return {
        "query": query_str,
        "intent": (
            context_data[
                "intent"
            ]
        ),
        "response": llm_output,
        "canonical_context": (
            context_data[
                "context_blocks"
            ]
        ),
    }


# =====================================================================
# LOCAL EXECUTION
# =====================================================================

if __name__ == "__main__":

    import uvicorn

    port = int(
        os.getenv(
            "PORT",
            10000,
        )
    )

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )
