import os
import json
import hashlib
from typing import Dict

import httpx

EVIDENCE_DIR = os.path.join(os.getcwd(), 'evidence')
os.makedirs(EVIDENCE_DIR, exist_ok=True)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _store_local(text: str) -> str:
    cid = _sha256_text(text)
    path = os.path.join(EVIDENCE_DIR, f"{cid}.json")
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
    return cid


def add_json(obj: Dict) -> str:
    """Store evidence JSON and return a CID.

    If `PINATA_JWT` is set in the environment, attempt to pin via Pinata.
    Otherwise fall back to local storage (CID = sha256 of JSON).
    """
    text = json.dumps(obj, sort_keys=True)
    jwt = os.getenv('PINATA_JWT')
    if jwt:
        try:
            url = 'https://api.pinata.cloud/pinning/pinJSONToIPFS'
            headers = {'Authorization': f'Bearer {jwt}', 'Content-Type': 'application/json'}
            with httpx.Client(timeout=30.0) as client:
                r = client.post(url, headers=headers, json=obj)
                r.raise_for_status()
                payload = r.json()
                ipfs_hash = payload.get('IpfsHash')
                if ipfs_hash:
                    return ipfs_hash
        except Exception:
            # fall back to local storage on any error
            pass
    return _store_local(text)
