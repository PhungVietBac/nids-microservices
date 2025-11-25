from fastapi import FastAPI
from pydantic import BaseModel
import os
from model import load_global, get_global

MODEL_PATH = os.getenv("MODEL_PATH", "/models/autoencoder.joblib")

app = FastAPI()

class InRequest(BaseModel):
    proto: int
    sport: int
    dport: int
    len: int
    payload_len: int
    flags: int
    payload_ratio: float
    is_ephemeral_dport: int

@app.on_event("startup")
def startup_event():
    if os.path.exists(MODEL_PATH):
        load_global(MODEL_PATH)
    else:
        print("WARNING: model not found at", MODEL_PATH)

@app.post("/infer")
def infer(req: InRequest):
    model = get_global()
    if model is None:
        return {"error": "Model not loaded", "anomaly_score": None}
    score = model.predict_score(req.dict())
    label = "anomaly" if score > float(os.getenv("THRESHOLD", "0.01")) else "normal"
    return {"anomaly_score": score, "label": label}