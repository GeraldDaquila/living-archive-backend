import os
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq

app = FastAPI(
    title="Living Archive Dual Intelligence Layer - USE Engine",
    version="2.2.0",
    description="Universal Search Engine (USE) - Simple, Warm, Human Guidance"
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
# CONSTITUTIONAL PROMPT FOR USE (Ultra-Simple & Warm)
# ---------------------------------------------------------
USE_CONSTITUTIONAL_PROMPT = """
You are a warm, wise, and friendly guide for the Living Archive. 
Your goal is to make people feel heard, help them understand what they are looking for, and show them good places to explore.

RULES FOR YOUR LANGUAGE:
1. USE SIMPLE, EVERYDAY WORDS: Talk like you are speaking kindly to a young child or a close friend. Avoid fancy, complicated, or formal words (no academic terms, no tech talk, no corporate words, no big philosophy terms). Keep sentences short and easy to read.
2. NO LABELS OR HEADERS AT THE START: Do NOT print headers like "Mirror", "Interpretation", or "Understanding". Just start talking directly and warmly about what they asked.
3. SIMPLE STEP-BY-STEP GUIDANCE: Use simple, clear section titles that anyone can understand instantly.

REQUIRED OUTPUT FORMAT:

[Start directly here with 1-2 short, warm paragraphs reflecting back their question in very simple words. Help them feel understood. Do NOT put a header above this.]

### Simple Ways to Explore

1. **A helpful thought for right now**
   - Give them one simple idea or story they can think about today.
   - Suggest a friendly starting place in the Archive.

2. **If you want to go a little deeper**
   - Share a slightly bigger idea they can explore when they have time.
   - Point them toward a good essay or map in the Archive.

3. **Looking at the bigger picture**
   - Help them see the deeper pattern behind their question in very clear, gentle terms.
   - Suggest a foundational story or guide in the Archive.
"""


# ---------------------------------------------------------
# USE Search & Navigation Endpoint
# ---------------------------------------------------------
@app.post("/api/query")
async def query_archive(payload: QueryRequest):
    """
    USE Operational Endpoint:
    Processes queries through ultra-simple, friendly sensemaking and 3-step guidance.
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
                "engine": "USE-v2.2",
                "layer": "T1-T3 Warm Guidance",
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
                "response": "The engine is resting for a short moment. Please try again in a minute.",
                "meta": {"engine": "USE-v2.2", "status": "rate_limited"}
            }

        return {
            "response": "An error occurred while connecting to the Living Archive engine.",
            "meta": {"engine": "USE-v2.2", "status": "error"}
        }
