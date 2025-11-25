import os
import joblib
import torch
import numpy as np

MODEL_DIR = os.getenv("MODEL_DIR", "/models")

class AutoencoderWrapper:
    def __init__(self, model_path=None, device='cpu'):
        self.device = device
        self.model = None
        self.mu = None
        self.scale = None
        if model_path:
            self.load(model_path)
    
    def load(self, model_path):
        blob = joblib.load(model_path)
        self.scaler = blob.get('scaler', None)
        self.torch_state = blob.get('torch_state', None)
        self.model = self._build_model(blob.get('arch', {}))
        if self.torch_state is not None:
            self.model.load_state_dict(self.torch_state)
        self.model.eval()
    
    def _build_model(self, arch):
        import torch.nn as nn
        input_dim = arch.get('input_dim', 10)
        hidden = arch.get('hidden', 4)
        return nn.Sequential(
            nn.Linear(input_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, input_dim)
        )
    
    def predict_score(self, X_dict):
        keys = ['proto', 'sport', 'dport', 'len', 'payload_len', 'flags', 'payload_ratio', 'is_ephemeral_dport']
        x = np.array([X_dict.get(k, 0.0) for k in keys], dtype=float).reshape(1, -1)
        if self.scaler:
            x = self.scaler.transform(x)
        xt = torch.from_numpy(x.astype('float32'))
        with torch.no_grad():
            recon = self.model(xt).numpy()
        score = float(((x - recon) ** 2).mean())
        return score
    
_GLOBAL_MODEL = None

def load_global(model_path):
    global _GLOBAL_MODEL
    _GLOBAL_MODEL = AutoencoderWrapper(model_path=model_path)

def get_global():
    return _GLOBAL_MODEL