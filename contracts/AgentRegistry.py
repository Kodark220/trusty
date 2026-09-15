# { "Depends": "py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng" }
from dataclasses import dataclass
import genlayer as gl
from genlayer.storage import allow as allow_storage
import json


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
    score: gl.u256
    note: str
    active: bool


class AgentRegistry(gl.contract.Contract):
    """Standalone Studionet registry and GenLayer fingerprint verifier."""

    agents: gl.storage.TreeMap[str, RegistryAgent]
    agent_keys: gl.storage.DynArray[str]

    def __init__(self):
        pass

    def _fail(self, message: str) -> None:
        raise gl.vm.UserError(f"[EXPECTED] {message}")

    def _clamp(self, value: int) -> int:
        return max(0, min(100, value))

    def _parse(self, raw) -> dict:
        if isinstance(raw, dict):
            return raw
        text = str(raw).strip()
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            return {}
        try:
            value = json.loads(text[start : end + 1])
            return value if isinstance(value, dict) else {}
        except Exception:
            return {}

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
            note="Fingerprint verification required",
            active=True,
        )
        self.agents[sender] = agent
        self.agent_keys.append(sender)
        return self.get_agent(sender)

    @gl.public.write
    def verify_fingerprint(self, sample_outputs: str, challenge_prompt: str) -> dict:
        sender = str(gl.message.sender_address)
        if sender not in self.agents:
            self._fail("Agent not registered")
        if len(sample_outputs.strip()) < 20:
            self._fail("Fingerprint sample is too short")
        agent = self.agents[sender]
        memory_agent = gl.storage.copy_to_memory(agent)

        def judge() -> str:
            prompt = f"""You verify an agent model claim.
CLAIM: {memory_agent.provider} {memory_agent.claimed_model} {memory_agent.version}
CHALLENGE: {challenge_prompt[:800]}
SAMPLE: {sample_outputs[:2500]}
Return JSON only with score 0-100, verdict verified/mismatched/inconclusive, and note."""
            return gl.nondet.exec_prompt(prompt, response_format="json")

        raw = gl.eq_principle.prompt_comparative(
            judge,
            "Verdict category must match and scores must be within 10 points.",
        )
        result = self._parse(raw)
        verdict = str(result.get("verdict", "inconclusive")).lower()
        if verdict not in ("verified", "mismatched", "inconclusive"):
            verdict = "inconclusive"
        score = self._clamp(int(result.get("score", 40)))
        note = str(result.get("note", result.get("explanation", "")))[:400]
        digest = 0
        for char in challenge_prompt[:400] + "|" + sample_outputs[:400]:
            digest = (digest * 131 + ord(char)) % 18446744073709551616
        agent.fingerprint_hash = hex(digest)
        agent.status = verdict
        agent.score = gl.u256(score)
        agent.note = note
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
    def list_verified(self) -> dict:
        result = []
        for address in self.agent_keys:
            if address in self.agents and self.agents[address].status == "verified":
                result.append(self.get_agent(address))
        return {"agents": result, "total": len(result)}
