import { AgentTrustClient } from './agenttrust-client.mjs';

const client = new AgentTrustClient({ apiKey: 'demo-key-123' });
const result = await client.verifyAndSubmit(
  'http://127.0.0.1:9001/',
  'Summarize the latest task',
);
console.log(JSON.stringify(result, null, 2));
