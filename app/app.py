from app.tools import REGISTERED_TOOLS
from app.agent import get_response
from app.utils import context_store, sql_store
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

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
    response: str
    context: list
    sql: list

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    context_store.set([])
    sql_store.set([])

    response = get_response(
        query=req.query,
        chat_history=req.chat_history,
        tools=REGISTERED_TOOLS,
    )

    return ChatResponse(
        response=response,
        context=context_store.get(),
        sql=sql_store.get(),
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)