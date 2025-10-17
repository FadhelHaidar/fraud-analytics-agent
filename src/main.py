from src.agent import get_response
from src.eval import evaluate_response
from src.tools import REGISTERED_TOOLS
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
    user_query: str
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
            user_query=req.query,
            response=response.get("response"),
            chunks=response.get("chunks"),
            sql=response.get("sql"),
        )

    except Exception as e:
        print("Error in /chat:", traceback.format_exc())

        return ChatResponse(
            user_query=req.query,
            response=None,
            chunks=[],
            sql=[],
            error=str(e)
        )

@app.post("/eval")
async def eval_endpoint(req: ChatResponse):

    try:
        score = await evaluate_response(req.user_query, req.response, req.chunks, req.sql)
        return {"score": score}
    except Exception as e:
        print("Error in /eval:", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)