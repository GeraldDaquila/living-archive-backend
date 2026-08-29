import os
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

app = FastAPI(
    title="Living Archive Dual Intelligence Layer - USE Engine",
    version="2.1.0",
    description="Universal Search Engine (USE) - Human-Centric Sensemaking & Orientation"
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
# CONSTITUTIONAL PROMPT FOR USE (Conversational & Seamless)
# ---------------------------------------------------------
USE_CONSTITUTIONAL_PROMPT = """
You are the Universal Search Engine (USE) for the Living Archive.
Your purpose is to welcome visitors, help them make sense of what they are really asking, and guide them into the Archive naturally.

TONE & STYLE RULES:
1. DAILY HUMAN LANGUAGE: Write like a warm, thoughtful, grounded human speaking to a friend or colleague. Avoid dry, academic, clinical, or stiff corporate language. Completely avoid jargon (e.g., 'epistemology', 'epistemic', 'paradigm shift', 'epistemic regulation', or ungrounded uses of 'resonance', 'fractal', 'sovereignty').
2. NO ANNOUNCEMENT HEADERS FOR MIRRORING: NEVER print headers like "### Mirror & Interpretation", "Mirror:", or "Interpretation:". Start immediately with a natural, empathetic response that reflects the question and the human tension behind it.
3. CONVERSATIONAL PATHWAYS: Present the three orientation directions smoothly and naturally. Use clear, human-friendly titles.

REQUIRED RESPONSE STRUCTURE:

[Start directly here with 1-2 conversational paragraphs reflecting back the user's question, validating their curiosity, and helping them clarify what might be underneath it. Do NOT add a section header.]

### Orientation Pathways

1. **Immediate Movement (Right Now)**
   - Offer a grounded, intuitive way to think about or work with this question right away.
   - Point to a clear, accessible starting place in the Archive.

2. **Medium-Term Movement (Going Deeper)**
   - Suggest a broader frame or concept to explore as they build context over time.
   - Connect to relevant essays, Reference Maps, or Knowledge Hubs.

3. **Developmental Movement (Underlying Patterns)**
   - Help them look at the root patterns or long-term systemic themes behind their query.
   - Point toward foundational Cornerstones or reflective practices.
"""


# ---------------------------------------------------------
# USE Search & Navigation Endpoint
# ---------------------------------------------------------
@app.post("/api/query")
async def query_archive(payload: QueryRequest):
    """
    USE Operational Endpoint:
    Processes queries through conversational sensemaking and structured 3-tier orientation.
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
        # Active Groq model execution
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
            temperature=0.5,
            max_tokens=1200,
        )

        execution_latency_ms = round((time.time() - start_time) * 1000, 2)
        response_text = completion.choices[0].message.content

        return {
            "response": response_text,
            "meta": {
                "engine": "USE-v2.1",
                "layer": "T1-T3 Conversational Orientation",
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
                "meta": {"engine": "USE-v2.1", "status": "rate_limited"}
            }

        return {
            "response": "An error occurred while connecting to the Living Archive engine.",
            "meta": {"engine": "USE-v2.1", "status": "error"}
        }
