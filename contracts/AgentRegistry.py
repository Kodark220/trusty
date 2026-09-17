# v0.3.0
# { "Depends": "py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng" }
import json

import genlayer as gl


class AgentRegistry(gl.contract.Contract):
    """Deterministic on-chain directory for agent-owned public profiles."""

    agents: gl.storage.TreeMap[str, str]
    agent_keys: str

    def __init__(self):
        self.agents = gl.storage.TreeMap()
        self.agent_keys = "[]"

    def _fail(self, message: str) -> None:
        raise gl.vm.UserError(f"[EXPECTED] {message}")

    def _keys(self) -> list:
        try:
            keys = json.loads(self.agent_keys)
            return keys if isinstance(keys, list) else []
        except Exception:
            return []

    def _agent(self, owner: str) -> dict:
        try:
            return json.loads(self.agents[owner])
        except Exception:
            self._fail("Agent not found")
            return {}

    def _digest(self, content: str) -> str:
        digest = 0
        for char in content[:1600]:
            digest = (digest * 131 + ord(char)) % 18446744073709551616
        return hex(digest)

    @gl.public.write
    def register(
        self,
        name: str,
        claimed_model: str,
        provider: str,
        version: str,
        capabilities: str,
        endpoint: str,
        model_card_url: str,
    ) -> dict:
        sender = str(gl.message.sender_address)
        if sender in self._keys():
            self._fail("Agent already registered")
        if not name.strip() or not claimed_model.strip():
            self._fail("Name and claimed model are required")
        agent = {
            "owner": sender, "name": name.strip(), "claimed_model": claimed_model.strip(),
            "provider": provider.strip(), "version": version.strip(),
            "capabilities": capabilities.strip(), "endpoint": endpoint.strip(),
            "model_card_url": model_card_url.strip(), "fingerprint_hash": "",
            "status": "unverified", "score": 0, "note": "Profile is owner-attested", "active": True,
        }
        self.agents[sender] = json.dumps(agent)
        keys = self._keys()
        keys.append(sender)
        self.agent_keys = json.dumps(keys)
        return agent

    @gl.public.write
    def attest_capability(self, sample: str, note: str) -> dict:
        sender = str(gl.message.sender_address)
        if sender not in self._keys():
            self._fail("Agent not registered")
        if len(sample.strip()) < 20:
            self._fail("Capability sample is too short")
        agent = self._agent(sender)
        agent["fingerprint_hash"] = self._digest(sample)
        agent["status"] = "attested"
        agent["score"] = 0
        agent["note"] = note.strip()[:400] or "Capability sample attested by owner"
        self.agents[sender] = json.dumps(agent)
        return agent

    @gl.public.write
    def update_profile(
        self, capabilities: str, endpoint: str, model_card_url: str
    ) -> dict:
        sender = str(gl.message.sender_address)
        if sender not in self._keys():
            self._fail("Agent not registered")
        agent = self._agent(sender)
        agent["capabilities"] = capabilities.strip()
        agent["endpoint"] = endpoint.strip()
        agent["model_card_url"] = model_card_url.strip()
        self.agents[sender] = json.dumps(agent)
        return agent

    @gl.public.view
    def get_agent(self, address: str) -> dict:
        if address not in self._keys():
            self._fail("Agent not found")
        return self._agent(address)

    @gl.public.view
    def list_active(self) -> dict:
        result = []
        for address in self._keys():
            agent = self._agent(address)
            if agent.get("active"):
                result.append(agent)
        return {"agents": result, "total": len(result)}
