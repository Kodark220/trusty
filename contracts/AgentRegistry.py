# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from dataclasses import dataclass
from genlayer import *


@allow_storage
@dataclass
class RegistryAgent:
    owner: str
    name: str
    claimed_model: str
    provider: str
    version: str
    capabilities: str
    endpoint: str
    model_card_url: str
    fingerprint_hash: str
    status: str
    score: u256
    note: str
    active: bool


class AgentRegistry(gl.Contract):
    """Deterministic on-chain directory for agent-owned public profiles."""

    agents: TreeMap[str, RegistryAgent]
    agent_keys: DynArray[str]

    def __init__(self):
        pass

    def _fail(self, message: str) -> None:
        raise gl.vm.UserError(f"[EXPECTED] {message}")

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
        if sender in self.agents:
            self._fail("Agent already registered")
        if not name.strip() or not claimed_model.strip():
            self._fail("Name and claimed model are required")
        agent = RegistryAgent(
            owner=sender,
            name=name.strip(),
            claimed_model=claimed_model.strip(),
            provider=provider.strip(),
            version=version.strip(),
            capabilities=capabilities.strip(),
            endpoint=endpoint.strip(),
            model_card_url=model_card_url.strip(),
            fingerprint_hash="",
            status="unverified",
            score=gl.u256(0),
            note="Profile is owner-attested",
            active=True,
        )
        self.agents[sender] = agent
        self.agent_keys.append(sender)
        return self.get_agent(sender)

    @gl.public.write
    def attest_capability(self, sample: str, note: str) -> dict:
        sender = str(gl.message.sender_address)
        if sender not in self.agents:
            self._fail("Agent not registered")
        if len(sample.strip()) < 20:
            self._fail("Capability sample is too short")
        agent = self.agents[sender]
        agent.fingerprint_hash = self._digest(sample)
        agent.status = "attested"
        agent.score = gl.u256(0)
        agent.note = note.strip()[:400] or "Capability sample attested by owner"
        self.agents[sender] = agent
        return self.get_agent(sender)

    @gl.public.write
    def update_profile(
        self, capabilities: str, endpoint: str, model_card_url: str
    ) -> dict:
        sender = str(gl.message.sender_address)
        if sender not in self.agents:
            self._fail("Agent not registered")
        agent = self.agents[sender]
        agent.capabilities = capabilities.strip()
        agent.endpoint = endpoint.strip()
        agent.model_card_url = model_card_url.strip()
        self.agents[sender] = agent
        return self.get_agent(sender)

    @gl.public.view
    def get_agent(self, address: str) -> dict:
        if address not in self.agents:
            self._fail("Agent not found")
        agent = self.agents[address]
        return {
            "owner": agent.owner,
            "name": agent.name,
            "claimed_model": agent.claimed_model,
            "provider": agent.provider,
            "version": agent.version,
            "capabilities": agent.capabilities,
            "endpoint": agent.endpoint,
            "model_card_url": agent.model_card_url,
            "fingerprint_hash": agent.fingerprint_hash,
            "status": agent.status,
            "score": int(agent.score),
            "note": agent.note,
            "active": agent.active,
        }

    @gl.public.view
    def list_active(self) -> dict:
        result = []
        for address in self.agent_keys:
            if address in self.agents and self.agents[address].active:
                result.append(self.get_agent(address))
        return {"agents": result, "total": len(result)}
