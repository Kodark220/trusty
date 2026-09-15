import os
import time
import json
from typing import Dict

RECEIPTS_FILE = 'receipts.json'


def _load_receipts():
    try:
        with open(RECEIPTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def _save_receipts(data):
    with open(RECEIPTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def store_receipt_local(receipt: Dict) -> Dict:
    receipts = _load_receipts()
    receipts.append(receipt)
    _save_receipts(receipts)
    return {'status': 'stored', 'local_id': len(receipts)-1}


def submit_receipt_onchain(receipt: Dict) -> Dict:
    """Stub: submit a compact receipt to GenLayer.

    This function currently stores the receipt locally and returns a fake tx hash.
    To enable real submission, set `GENLAYER_RPC_URL` and `GENLAYER_PRIVATE_KEY`
    environment variables and implement the RPC call here.
    """
    rpc = os.getenv('GENLAYER_RPC_URL')
    key = os.getenv('GENLAYER_PRIVATE_KEY')
    # local fallback: always store
    info = store_receipt_local(receipt)
    tx = {'tx_hash': f"local_tx_{int(time.time())}", 'stored': info}
    # If RPC details present, attempt a simple HTTP POST as a stubbed submission
    if rpc and key:
        try:
            import httpx

            headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
            with httpx.Client(timeout=15.0) as client:
                r = client.post(rpc, headers=headers, json=receipt)
                r.raise_for_status()
                # try to parse response
                try:
                    resp = r.json()
                except Exception:
                    resp = {'status_code': r.status_code, 'text': r.text}
                tx['rpc_response'] = resp
                tx['tx_hash'] = resp.get('tx_hash', tx['tx_hash'])
        except Exception as e:
            tx['rpc_error'] = str(e)
    return tx
