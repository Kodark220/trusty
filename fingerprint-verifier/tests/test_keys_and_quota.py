import asyncio
import time
import os
from httpx import ASGITransport, AsyncClient
from src.app import app
import src.billing as billing

import pytest

@pytest.mark.asyncio
async def test_key_create_and_quota(tmp_path, monkeypatch):
    # ensure clean usage file
    usage_file = os.path.join(os.getcwd(), 'usage.json')
    try:
        os.remove(usage_file)
    except FileNotFoundError:
        pass

    # create key
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
        resp = await ac.post('/keys/create', json={'owner':'tester','quota_daily':3})
        assert resp.status_code == 200
        key = resp.json()['key']
        # call verify endpoint 3 times (quota)
        # run a mock agent server first
        from fastapi import FastAPI, Request
        mock = FastAPI()
        @mock.post('/')
        async def root(req: Request):
            data = await req.json()
            prompt = data.get('prompt','')
            return {'response': prompt[::-1]}
        import uvicorn
        server = uvicorn.Config(mock, host='127.0.0.1', port=9010, log_level='warning')
        s = uvicorn.Server(server)
        import threading
        thread = threading.Thread(target=lambda: asyncio.run(s.serve()), daemon=True)
        thread.start()
        await asyncio.sleep(0.3)

        for i in range(3):
            r = await ac.post('/verify', json={'url':'http://127.0.0.1:9010/','prompt':'hello'}, headers={'X-API-Key':key})
            assert r.status_code == 200
        # fourth should be 429
        r = await ac.post('/verify', json={'url':'http://127.0.0.1:9010/','prompt':'hello'}, headers={'X-API-Key':key})
        assert r.status_code == 429
