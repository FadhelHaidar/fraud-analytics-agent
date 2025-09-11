from app.agent import get_response
from app.tools import REGISTERED_TOOLS
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import traceback

app = FastAPI(title="LangGraph Agent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str
    chat_history: list

class ChatResponse(BaseModel):
    response: str | None = None
    chunks: list | None = None
    sql: list | None = None
    error: str | None = None  

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    try:
        response = get_response(
            query=req.query,
            chat_history=req.chat_history,
            tools=REGISTERED_TOOLS,
        )

        return ChatResponse(
            response=response.get("response"),
            chunks=response.get("chunks"),
            sql=response.get("sql"),
        )

    except Exception as e:
        print("Error in /chat:", traceback.format_exc())

        return ChatResponse(
            response=None,
            chunks=[],
            sql=[],
            error=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)