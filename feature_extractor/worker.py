import os
import ujson
import pika
from dotenv import load_dotenv
from features import extract_basic_features
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import Table, Column, Integer, Float, String, MetaData
import requests

load_dotenv()
RABBIT_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/%2F")
QUEUE = os.getenv("COLLECTOR_QUEUE", "packets")
INFER_URL = os.getenv("INFERENCE_URL", "http://inference:9000/infer")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@postgres:5432/nids")

metadata = MetaData()
features_table = Table(
    "features", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("ts", Float),
    Column("src_ip", String(64)),
    Column("dst_ip", String(64)),
    Column("proto", Integer),
    Column("sport", Integer),
    Column("dport", Integer),
    Column("len", Integer),
    Column("payload_len", Integer),
    Column("flags", Integer),
    Column("payload_ratio", Float),
    Column("is_ephemeral_dport", Integer),
    Column("anomaly_score", Float, nullable=True),
    Column("label", String(64), nullable=True)
)

engine = create_async_engine(DATABASE_URL, echo=False, future=True)

def forward_to_inference(features):
    r = requests.post(INFER_URL, json=features, timeout=2.0)
    return r.json()

def process_message(body):
    pkt = ujson.loads(body)
    f = extract_basic_features(pkt)
    return f

def consume():
    params = pika.URLParameters(RABBIT_URL)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    ch.queue_declare(queue=QUEUE, durable=True)

    def callback(ch, method, properties, body):
        try:
            features = process_message(body)
            resp = forward_to_inference(features)
            features['anomaly_score'] = resp.get('anomaly_score')
            requests.post("http://localhost:8000/store", json=features, timeout=2.0)
        except Exception as e:
            print("processing error:", e)
        finally:
            ch.basic_ack(delivery_tag=method.delivery_tag)
    
    ch.basic_qos(prefetch_count=10)
    ch.basic_consume(queue=QUEUE, on_message_callback=callback)
    ch.start_consuming()

if __name__ == "__main__":
    consume()