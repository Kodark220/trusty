from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import httpx
import hashlib
import json
from typing import Optional

from src import registry
from src import billing
from src import ipfs
from src import genlayer_client
import time

app = FastAPI()


class ProbeRequest(BaseModel):
    url: str
    prompt: str


class ProbeResult(BaseModel):
    fingerprint: str
    raw_output: str
    meta: dict


async def _run_probe(url: str, prompt: str) -> ProbeResult:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            r = await client.post(url, json={'prompt': prompt})
            r.raise_for_status()
            out = r.text
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=str(e))
    digest = hashlib.sha256((prompt + '\n' + out).encode('utf-8')).hexdigest()
    meta = {'status_code': r.status_code}
    return ProbeResult(fingerprint=digest, raw_output=out, meta=meta)


@app.post('/probe', response_model=ProbeResult)
async def probe_agent(req: ProbeRequest):
    return await _run_probe(req.url, req.prompt)


@app.post('/verify', response_model=ProbeResult)
async def verify_agent(req: ProbeRequest, x_api_key: Optional[str] = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail='Missing X-API-Key')
    try:
        owner = billing.check_key(x_api_key)
    except ValueError:
        raise HTTPException(status_code=401, detail='Invalid X-API-Key')
    try:
        billing.log_usage(x_api_key, 'verify')
    except RuntimeError:
        raise HTTPException(status_code=429, detail='Quota exceeded')
    result = await _run_probe(req.url, req.prompt)
    # optional: check registry for known fingerprint
    known = registry.lookup(result.fingerprint)
    if known:
        result.meta['known_model'] = known
    else:
        result.meta['known_model'] = None
    # If requested, store an evidence bundle (prompt + raw output + fingerprint)
    # and optionally submit a compact receipt on-chain.
    # Query params: ?store=true&onchain=true
    # FastAPI will let users pass those as query parameters.
    return result


@app.post('/verify/submit')
async def verify_and_submit(req: ProbeRequest, store: bool = True, onchain: bool = False, x_api_key: Optional[str] = Header(None)):
    # reuse auth + quota
    if not x_api_key:
        raise HTTPException(status_code=401, detail='Missing X-API-Key')
    try:
        billing.check_key(x_api_key)
    except ValueError:
        raise HTTPException(status_code=401, detail='Invalid X-API-Key')
    try:
        billing.log_usage(x_api_key, 'verify_submit')
    except RuntimeError:
        raise HTTPException(status_code=429, detail='Quota exceeded')

    result = await _run_probe(req.url, req.prompt)
    known = registry.lookup(result.fingerprint)
    result.meta['known_model'] = known or None

    receipt = {
        'fingerprint': result.fingerprint,
        'prompt': req.prompt,
        'meta': result.meta,
        'timestamp': int(time.time()),
        'verdict': 'unknown',
        'validators': [],
    }

    if store:
        bundle = {
            'prompt': req.prompt,
            'raw_output': result.raw_output,
            'fingerprint': result.fingerprint,
            'meta': result.meta,
            'timestamp': receipt['timestamp'],
        }
        cid = ipfs.add_json(bundle)
        receipt['evidence_cid'] = cid
        result.meta['evidence_cid'] = cid

    if onchain:
        tx = genlayer_client.submit_receipt_onchain(receipt)
        receipt['onchain_tx'] = tx
        result.meta['onchain_tx'] = tx
    else:
        # store receipt locally for audit
        stored = genlayer_client.store_receipt_local(receipt)
        result.meta['receipt_local'] = stored

    return result


# ---- API key management ----
class KeyCreate(BaseModel):
    owner: str
    quota_daily: Optional[int] = 1000


@app.post('/keys/create')
def create_key(body: KeyCreate):
    key = billing.create_key(body.owner, body.quota_daily)
    return {'key': key, 'owner': body.owner, 'quota_daily': int(body.quota_daily)}


@app.post('/keys/revoke')
def revoke_key(body: dict):
    key = body.get('key')
    if not key:
        raise HTTPException(status_code=400, detail='key required')
    ok = billing.revoke_key(key)
    if not ok:
        raise HTTPException(status_code=404, detail='key not found')
    return {'revoked': key}


@app.get('/keys/list')
def list_keys():
    return billing.list_keys()


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('src.app:app', host='127.0.0.1', port=8001, reload=True)
