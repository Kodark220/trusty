"""Small Python client for the AgentTrust verifier API."""
from typing import Any, Dict, Optional

import requests


class AgentTrustClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8001", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers

    def verify(self, agent_url: str, prompt: str) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/verify",
            headers=self._headers(),
            json={"url": agent_url, "prompt": prompt},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def verify_and_submit(
        self, agent_url: str, prompt: str, store: bool = True, onchain: bool = False
    ) -> Dict[str, Any]:
        response = requests.post(
            f"{self.base_url}/verify/submit",
            params={"store": store, "onchain": onchain},
            headers=self._headers(),
            json={"url": agent_url, "prompt": prompt},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
