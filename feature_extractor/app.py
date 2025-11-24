import os
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import insert
from sqlalchemy.orm import sessionmaker
from features import extract_basic_features
from dotenv import load_dotenv
from worker import features_table, engine

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@postgres:5432/nids")

app = FastAPI()

class FeatureIn(BaseModel):
    ts: float
    src_ip: str
    dst_ip: str
    proto: int
    sport: int
    dport: int
    len: int
    payload_len: int
    flags: int
    payload_ratio: float = 0.0
    is_ephemeral_dport: int = 0
    anomaly_score: float = None
    label: str = None

async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(lambda conn: features_table.create(bind=conn.engine, checkfirst=True))

@app.post("/store")
async def store_feature(f: FeatureIn):
    async with async_session() as session:
        stmt = insert(features_table).values(**f.dict())
        await session.execute(stmt)
        await session.commit()
    return {"status": "ok"}