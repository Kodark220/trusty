import json
import time
from typing import Dict

API_KEYS: Dict[str, Dict] = {
    # sample key for testing
    'demo-key-123': {'owner': 'demo', 'tier': 'free', 'quota_daily': 100}
}

USAGE_FILE = 'usage.json'


def _load_usage():
    try:
        with open(USAGE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _save_usage(data):
    with open(USAGE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def create_key(owner: str, quota_daily: int = 1000) -> str:
    import secrets

    key = secrets.token_hex(16)
    API_KEYS[key] = {'owner': owner, 'tier': 'custom', 'quota_daily': int(quota_daily)}
    return key


def revoke_key(key: str) -> bool:
    if key in API_KEYS:
        del API_KEYS[key]
        return True
    return False


def list_keys() -> Dict[str, Dict]:
    return API_KEYS.copy()


def _count_recent_calls(records, window_seconds: int = 86400) -> int:
    now = int(time.time())
    cutoff = now - window_seconds
    return sum(1 for r in records if r.get('timestamp', 0) >= cutoff)


def check_key(key: str) -> str:
    if key in API_KEYS:
        return API_KEYS[key]['owner']
    raise ValueError('Invalid API key')


def check_quota(key: str) -> None:
    # raise ValueError('Invalid API key') for invalid, RuntimeError for quota exceeded
    if key not in API_KEYS:
        raise ValueError('Invalid API key')
    quota = int(API_KEYS[key].get('quota_daily', 0))
    data = _load_usage()
    records = data.get(key, [])
    used = _count_recent_calls(records)
    if quota >= 0 and used >= quota:
        raise RuntimeError('Quota exceeded')


def log_usage(key: str, endpoint: str):
    # check and then log (atomicity not guaranteed for concurrent writes)
    check_quota(key)
    data = _load_usage()
    now = int(time.time())
    rec = {'timestamp': now, 'endpoint': endpoint}
    data.setdefault(key, []).append(rec)
    _save_usage(data)
