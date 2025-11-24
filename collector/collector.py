import os
import json
import time
from scapy.all import sniff, Raw, IP, TCP, UDP
import pika
import ujson
from dotenv import load_dotenv

load_dotenv()

RABBIT_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/%2F")
QUEUE = os.getenv("COLLECTOR_QUEUE", "packets")

params = pika.URLParameters(RABBIT_URL)
conn = pika.BlockingConnection(params)
ch = conn.channel()
ch.queue_declare(queue=QUEUE, durable=True)

def pkt_to_dict(pkt):
    out = {
        "timestamp": time.time()
    }
    if IP in pkt:
        ip = pkt[IP]
        out.update({
            "src": ip.src,
            "dst": ip.dst,
            "len": len(pkt),
            "ttl": ip.ttl
        })
    if TCP in pkt:
        tcp = pkt[TCP]
        out.update({
            "proto": "TCP",
            "sport": tcp.sport,
            "dport": tcp.dport,
            "flags": int(tcp.flags)
        })
    elif UDP in pkt:
        udp = pkt[UDP]
        out.update({
            "proto": "UDP",
            "sport": udp.sport,
            "dport": udp.dport
        })
    else:
        out["proto"] = pkt.summary()
    if Raw in pkt:
        out["payload_len"] = len(pkt[Raw].load)
    else:
        out["payload_len"] = 0
    return out

def on_packet(pkt):
    d = pkt_to_dict(pkt)
    ch.basic_publish(
        exchange='',
        routing_key=QUEUE,
        body=ujson.dumps(d),
        properties=pika.BasicProperties(delivery_mode=2)
    )

def main():
    iface = os.getenv("IFACE", None)
    sniff(prn=on_packet, store=False, iface=iface)

if __name__ == "__main__":
    main()