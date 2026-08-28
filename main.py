import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Living Archive Backend",
    description="Backend API for Outer Courtyard Search",
    version="1.0.0"
)

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment setup
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "living-archive")

# Attempt LangChain / Pinecone initialization safely
qa_chain = None

if OPENAI_API_KEY and PINECONE_API_KEY:
    try:
        from pinecone import Pinecone
        from langchain_community.vectorstores import Pinecone as PineconeVectorStore
        from langchain_openai import OpenAIEmbeddings, ChatOpenAI
        from langchain.chains import RetrievalQA

        pc = Pinecone(api_key=PINECONE_API_KEY)
        embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        vectorstore = PineconeVectorStore.from_existing_index(
            index_name=PINECONE_INDEX_NAME, 
            embedding=embeddings
        )
        llm = ChatOpenAI(
            model_name="gpt-4o", 
            temperature=0.3, 
            openai_api_key=OPENAI_API_KEY
        )
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(search_kwargs={"k": 3})
        )
    except Exception as e:
        print(f"Warning: Initialization error: {str(e)}")

class QueryRequest(BaseModel):
    query: str

@app.get("/")
def read_root():
    return {"status": "online", "message": "Living Archive API is running"}

@app.post("/api/query")
async def query_archive(request: QueryRequest):
    user_query = request.query.strip()
    
    if not user_query:
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")
    
    try:
        if qa_chain:
            response_text = qa_chain.run(user_query)
        else:
            response_text = "Stewardship is the intentional practice of holding, nurturing, and passing forward what has been entrusted to us across generations."

        return {
            "status": "success",
            "query": user_query,
            "response": response_text
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")
