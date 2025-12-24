from pydantic import BaseModel
from fastapi import FastAPI
from api.schemas import ChatRequest, ChatResponse
from api.advisor_service import get_advice
import numpy as np
import pandas as pd

app = FastAPI(title="Academic Advisor Chat API")

def convert_numpy(obj):
    # 1️⃣ Handle pandas DataFrame
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")

    # 2️⃣ Handle pandas Series
    if isinstance(obj, pd.Series):
        return obj.to_dict()

    # 3️⃣ Handle numpy scalars
    if isinstance(obj, np.generic):
        return obj.item()

    # 4️⃣ Handle dict
    if isinstance(obj, dict):
        return {k: convert_numpy(v) for k, v in obj.items()}

    # 5️⃣ Handle list / tuple
    if isinstance(obj, (list, tuple)):
        return [convert_numpy(v) for v in obj]

    # 6️⃣ Handle NaN safely
    if obj is None:
        return None

    try:
        if pd.isna(obj):
            return None
    except Exception:
        pass

    # 7️⃣ Normal python value
    return obj


@app.get("/")
def root():
    return {"status": "API is running"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    student_id = request.student_id
    message = request.message

    reply = get_advice(student_id, message)
    reply = convert_numpy(reply)
    return {"reply": reply}