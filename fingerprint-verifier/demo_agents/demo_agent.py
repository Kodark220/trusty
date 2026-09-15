from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()

@app.post('/')
async def respond(req: Request):
    data = await req.json()
    prompt = data.get('prompt','')
    # simple deterministic behavior: return reversed prompt and a model tag
    return {'response': prompt[::-1], 'model_tag': 'demo-model-v1'}

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=9001)
