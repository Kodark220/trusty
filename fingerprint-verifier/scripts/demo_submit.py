"""Demo: call the local verifier and submit evidence (store only).

Run after starting the FastAPI app (py -3 src/app.py)
"""
import requests
import json

URL = 'http://127.0.0.1:8001/verify/submit?store=true&onchain=false'
KEY = 'demo-key-123'

def main():
    payload = {'url':'http://127.0.0.1:9001/','prompt':'hello demo'}
    headers = {'X-API-Key': KEY, 'Content-Type': 'application/json'}
    r = requests.post(URL, headers=headers, data=json.dumps(payload))
    print('status', r.status_code)
    try:
        print(json.dumps(r.json(), indent=2))
    except Exception:
        print(r.text)

if __name__ == '__main__':
    main()
