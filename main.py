import os
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

app = FastAPI(
    title="Living Archive Dual Intelligence Layer - USE Engine",
    version="2.0.0",
    description="Universal Search Engine (USE) - Orientation, Sensemaking, and Guided Movement"
)

# ---------------------------------------------------------
# FROZEN SECTION: CORS & Middlewares (Working)
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# FROZEN SECTION: Client Initialization & Base Routes (Working)
# ---------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None


class QueryRequest(BaseModel):
    query: str


@app.get("/")
def read_root():
    """Base keepalive route for external cron pinging. Zero AI tokens consumed."""
    return {
        "status": "Living Archive Engine Online",
        "active_layer": "USE (Universal Search Engine)",
        "fsd_bridge_ready": True
    }


# ---------------------------------------------------------
# CONSTITUTIONAL PROMPT FOR USE (Universal Search Engine)
# ---------------------------------------------------------
USE_CONSTITUTIONAL_PROMPT = """
You are the Universal Search Engine (USE) for the Living Archive (Life.Understood.).
Your purpose is NOT merely to answer questions or dump search results. Your purpose is to understand human questions deeply enough to help visitors find their way toward greater clarity, coherence, and orientation.

CORE PRINCIPLES:
1. DOMAIN & AUDIENCE: You serve general visitors, reflective practitioners, and leaders (T1-T3 resources).
2. TRANSLATION LAYER: Speak in universal, accessible, emotionally intelligent, human language. Do NOT require the user to understand Living Archive terminology (e.g., avoid ungrounded uses of 'resonance', 'frequency', 'fractal', 'sovereignty', 'overflow') unless you translate them naturally into human experience.
3. ORIENTATION OVER INFORMATION: Your objective is to create a meaningful shift in orientation between entry and exit.

REQUIRED RESPONSE STRUCTURE:
You must structure your response clearly using the following markdown sections:

### Mirror & Interpretation
(Acknowledge the explicit question, reflect the likely human tension or state beneath it, and offer a sensemaking mirror without being clinical or preachy.)

### Orientation Pathways

1. **Immediate Movement (Now):**
   - What perspective, question, or conceptual frame can help the visitor work with this state right now?
   - Recommends general concepts, essays, or cornerstones.

2. **Medium-Term Movement (Deeper Understanding):**
   - What deeper concepts or frameworks can help them develop their understanding over time?
   - Connects to Reference Maps, Knowledge Hubs, or Guided Pathways.

3. **Developmental Movement (Underlying Pattern):**
   - What deeper exploration addresses the underlying pattern or root systemic dynamic?
   - Points toward foundational Cornerstones or long-term reflective work.
"""


# ---------------------------------------------------------
# REVISED SECTION: USE Search & Navigation Endpoint
# ---------------------------------------------------------
@app.post("/api/query")
async def query_archive(payload: QueryRequest):
    """
    USE Operational Endpoint:
    Processes queries through the USE Constitutional Logic (Sensemaking + 3-Tier Orientation).
    """
    if not payload.query or not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")

    if not client:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY is missing from environment variables."
        )

    start_time = time.time()

    try:
        # Executing via active Groq model (openai/gpt-oss-20b)
        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {
                    "role": "system",
                    "content": USE_CONSTITUTIONAL_PROMPT
                },
                {
                    "role": "user",
                    "content": payload.query
                }
            ],
            temperature=0.4,
            max_tokens=1200,
        )

        execution_latency_ms = round((time.time() - start_time) * 1000, 2)
        response_text = completion.choices[0].message.content

        return {
            "response": response_text,
            "meta": {
                "engine": "USE-v2",
                "layer": "T1-T3 Orientation",
                "model_used": "openai/gpt-oss-20b",
                "latency_ms": execution_latency_ms,
                "status": "healthy"
            }
        }

    except Exception as e:
        error_msg = str(e)
        print(f"USE Execution Error: {error_msg}")

        if "429" in error_msg or "rate_limit" in error_msg.lower():
            return {
                "response": "The search engine is currently experiencing high demand. Please pause a moment and try again.",
                "meta": {"engine": "USE-v2", "status": "rate_limited"}
            }

        return {
            "response": "An error occurred while connecting to the Living Archive engine.",
            "meta": {"engine": "USE-v2", "status": "error"}
        }
