from fastapi import FastAPI
from api.schemas import ChatRequest, ChatResponse

app = FastAPI(title="Academic Advisor Chat API")

@app.get("/")
def root():
    return {"status": "API is running"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    reply = f"You said: {request.message}"
    return ChatResponse(reply=reply)