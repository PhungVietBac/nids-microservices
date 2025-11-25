import pika, ujson, time, random

RABBIT_URL = "amqp://guest:guest@rabbitmq:5672/%2F"
params = pika.URLParameters(RABBIT_URL)
conn = pika.BlockingConnection(params)
ch = conn.channel()
ch.queue_declare(queue="packets", durable=True)

for i in range(1000):
    pkt = {
        "timestamp": time.time(),
        "src": f"10.0.0.{random.randint(1, 250)}",
        "dst": f"10.0.1.{random.randint(1, 250)}",
        "proto": random.choice(["TCP", "UDP"]),
        "sport": random.randint(1024, 65535),
        "dport": random.choice([80, 443, 22, 53, random.randint(1024, 65535)]),
        "len": random.randint(40, 1500),
        "payload_len": random.randint(0, 1400),
        "flags": random.randint(0, 255)
    }
    ch.basic_publish('', 'packets', ujson.dumps(pkt))
    time.sleep(0.01)