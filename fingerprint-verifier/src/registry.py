from typing import Dict

# Simple in-memory registry of known fingerprints -> model metadata
REGISTRY: Dict[str, Dict] = {
    # example: 'fingerprint': {'model': 'gpt-test', 'version': '0.1'}
}

def register(fingerprint: str, meta: Dict):
    REGISTRY[fingerprint] = meta

def lookup(fingerprint: str):
    return REGISTRY.get(fingerprint)
