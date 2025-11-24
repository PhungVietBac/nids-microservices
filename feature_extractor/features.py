from typing import Dict

def extract_basic_features(pkt: Dict) -> Dict:
    f = {}
    f['ts'] = pkt.get('timestamp', 0.0)
    f['src_ip'] = pkt.get('src', '')
    f['dst_ip'] = pkt.get('dst', '')
    f['proto'] = 6 if pkt.get('proto') == 'TCP' else (17 if pkt.get('proto') == 'UDP' else 0)
    f['sport'] = int(pkt.get('sport') or 0)
    f['dport'] = int(pkt.get('dport') or 0)
    f['len'] = int(pkt.get('len') or 0)
    f['payload_len'] = int(pkt.get('payload_len') or 0)
    f['flags'] = int(pkt.get('flags') or 0)
    f['payload_ratio'] = (f['payload_len'] / f['len']) if f['len'] > 0 else 0.0
    f['is_ephemeral_dport'] = 1 if (1024 <= f['dport'] <= 65535) else 0
    return f
