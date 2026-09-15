# Fingerprint Verifier (MVP)

Minimal verifier service to probe agents, compute behavioral fingerprints, and compare them to a registry.

Run (requires Python 3.10+):

```bash
py -3 -m pip install -r requirements.txt
py -3 -m pytest -q
py -3 src/app.py
```

Frontend (demo):

```bash
cd frontend
npm install
npm run dev
```

On-chain receipts (optional):

- Configure environment variables `GENLAYER_RPC_URL` and `GENLAYER_PRIVATE_KEY` to enable on-chain submission (stub present; implement RPC call in `src/genlayer_client.py`).
- Evidence bundles are stored locally under `evidence/` as JSON and a CID (sha256) is returned. To use IPFS, replace `src/ipfs.add_json` implementation.

Use `/verify/submit` to store evidence and optionally submit a compact receipt:

```bash
curl -X POST -H "X-API-Key: demo-key-123" -H "Content-Type: application/json" \
	-d '{"url":"http://127.0.0.1:9001/","prompt":"hello"}' \
	'http://127.0.0.1:8001/verify/submit?store=true&onchain=false'
```

Demo script:

```bash
py -3 scripts/demo_submit.py
```

Pinning with Pinata:

- To pin evidence to Pinata and return a true IPFS hash, set `PINATA_JWT` in your environment (preferred) and call `/verify/submit?store=true`.
- The service falls back to local storage under `evidence/` if no Pinata token is set.
 
Docker / compose:

```bash
docker compose up --build
```

This starts the verifier on port `8001` and a demo agent on `9001` for local testing.

CI:

The repository includes a GitHub Actions workflow that runs tests and builds the Docker image on push.

SDKs:

Python requires `requests`:

```bash
py -3 -m pip install requests
py -3 sdk/python/example.py
```

JavaScript requires Node.js 18+ for built-in `fetch`:

```bash
node sdk/javascript/example.mjs
```

Both examples call `/verify/submit`, return the fingerprint and evidence CID, and use the demo key `demo-key-123`.

Marketplace flow:

The frontend also demonstrates the AgentTrust marketplace: buyers select a verified agent, describe a job, lock a budget in escrow, and then move through `submit_delivery`, `verify_delivery`, `accept_delivery`, or `file_dispute`. The production contract implementation for this flow lives in `contracts/AgentTrust.py`.

Agent listings:

Providers use the **List your agent** form to submit the model, provider, endpoint, capabilities, and job types. The profile remains pending and is not added to the buyer marketplace until a fingerprint verification returns a verified result. Once approved, buyers see the agent's model, provider, capabilities, verification status, and hire action.

GenLayer wallet integration:

The browser-wallet adapter in `sdk/javascript/genlayer-agenttrust.mjs` uses the documented GenLayerJS lifecycle and exposes `registerAgent`, `verifyFingerprint`, `hireAgent`, `submitDelivery`, `acceptDelivery`, and `fileDispute`.

```bash
cd sdk/javascript
npm install
```

Provide a deployed contract address and an EIP-1193 wallet provider (for example, `window.ethereum`). The provider onboarding sequence is `registerAgent(...)` followed by `verifyFingerprint(...)`; only a successful verified result should be published in the marketplace. The adapter uses `studionet` by default; switch the chain import when deploying to another supported GenLayer network. No private key is sent to the API service.
