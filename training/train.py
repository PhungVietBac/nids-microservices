import os
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import torch
import torch.nn as nn
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_SYNC_URL", "postgresql://postgres:postgres@postgres:5432/nids")
MODEL_OUT = os.getenv("MODEL_OUT", "/models/autoencoder.joblib")

engine = create_engine(DATABASE_URL)

def fetch_features(limit=100000):
    sql = text("SELECT proto, sport, dport, len, payload_len, flags, payload_ratio, is_ephemeral_dport FROM features ORDER BY id DESC LIMIT :limit")
    df = pd.read_sql(sql, engine, params={"limit": limit})
    return df

class AE(nn.Module):
    def __init__(self, in_dim, hidden=4):
        super().__init__()
        self.enc = nn.Sequential(nn.Linear(in_dim, hidden), nn.ReLU())
        self.dec = nn.Sequential(nn.Linear(hidden, in_dim))

    def forward(self, x):
        z = self.enc(x)
        return self.dec(z)
    
def train_autoencoder(X, epochs=30, lr=1e-3):
    in_dim = X.shape[1]
    model = AE(in_dim, hidden=min(8, in_dim // 2))
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()
    Xt = torch.tensor(X.astype('float32'))
    for e in range(epochs):
        model.train()
        opt.zero_grad()
        out = model(Xt)
        loss = loss_fn(out, Xt)
        loss.backward()
        opt.step()
        if e % 5 == 0:
            print(f"Epoch {e} loss {loss.item():.6f}")
    return model

def main():
    df = fetch_features(limit=20000)
    if df.empty:
        print("No data to train on")
        return
    cols = df.columns.to_list()
    X = df.values.astype(float)
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    model = train_autoencoder(Xs, epochs=40)
    blob = {
        "scaler": scaler,
        "torch_state": model.state_dict(),
        "arch": {"input_dim": Xs.shape[1], "hidden_dim": min(8, Xs.shape[1] // 2)}
    }
    os.makedirs(os.path.dirname(MODEL_OUT), exist_ok=True)
    joblib.dump(blob, MODEL_OUT)
    print("Saved model to", MODEL_OUT)

if __name__ == "__main__":
    main()