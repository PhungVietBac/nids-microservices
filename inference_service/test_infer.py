from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_infer_no_model():
    res = client.post("/infer", json={
        "proto": 6, 
        "sport": 1234, 
        "dport": 80,
        "len": 100,
        "payload_len": 80,
        "flags": 2,
        "payload_ratio": 0.8,
        "is_ephemeral_dport": 1
    })
    assert res.status_code == 200
    assert "error" in res.json() or "anomaly_score" in res.json()