Billing model (MVP)

- API key based metered billing.
- `X-API-Key` header required for `/verify` endpoint.
- Usage recorded in `usage.json` for later billing/aggregation.
- Suggested next steps: integrate a payment gateway, implement quota enforcement, and add subscription tiers.

Example curl:

```bash
curl -H "X-API-Key: demo-key-123" -H "Content-Type: application/json" \
  -d '{"url":"http://127.0.0.1:9001/","prompt":"hello"}' \
  http://127.0.0.1:8001/verify
```
