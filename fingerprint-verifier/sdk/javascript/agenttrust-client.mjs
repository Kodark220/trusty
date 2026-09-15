export class AgentTrustClient {
  constructor({ baseUrl = 'http://127.0.0.1:8001', apiKey } = {}) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.apiKey = apiKey;
  }

  headers() {
    const headers = { 'content-type': 'application/json' };
    if (this.apiKey) headers['x-api-key'] = this.apiKey;
    return headers;
  }

  async verify(agentUrl, prompt) {
    return this.request('/verify', { url: agentUrl, prompt });
  }

  async verifyAndSubmit(agentUrl, prompt, { store = true, onchain = false } = {}) {
    const query = new URLSearchParams({ store: String(store), onchain: String(onchain) });
    return this.request(`/verify/submit?${query}`, { url: agentUrl, prompt });
  }

  async request(path, body) {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: this.headers(),
      body: JSON.stringify(body),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(`${response.status}: ${data.detail || 'request failed'}`);
    }
    return data;
  }
}
