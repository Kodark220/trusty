import asyncio
from httpx import ASGITransport, AsyncClient
from src.app import app

async def mock_agent_server():
    from fastapi import FastAPI
    from fastapi import Request
    mock = FastAPI()

    @mock.post('/')
    async def root(req: Request):
        data = await req.json()
        prompt = data.get('prompt','')
        return {'response': prompt[::-1]}

    import uvicorn
    config = uvicorn.Config(mock, host='127.0.0.1', port=9001, log_level='warning')
    server = uvicorn.Server(config)
    await server.serve()

import pytest
import threading

@pytest.mark.asyncio
async def test_probe_and_fingerprint():
    # run mock agent in background thread
    thread = threading.Thread(target=lambda: asyncio.run(mock_agent_server()), daemon=True)
    thread.start()
    await asyncio.sleep(0.5)

    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as ac:
        resp = await ac.post('/probe', json={'url':'http://127.0.0.1:9001/','prompt':'hello'})
        assert resp.status_code == 200
        data = resp.json()
        assert 'fingerprint' in data
        assert data['raw_output']
