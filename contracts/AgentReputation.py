# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from dataclasses import dataclass
from genlayer import *


@allow_storage
@dataclass
class Reputation:
    agent: str
    fingerprint_score: u256
    fingerprint_status: str
    jobs_completed: u256
    jobs_failed: u256
    sla_hits: u256
    sla_misses: u256
    payment_success: u256
    payment_failure: u256
    disputes_lost: u256
    trust_score: u256
    note: str


class AgentReputation(gl.Contract):
    """Standalone earned reputation for verified marketplace agents."""

    owner: str
    reputations: TreeMap[str, Reputation]
    agent_keys: DynArray[str]

    def __init__(self):
        self.owner = str(gl.message.sender_address)

    def _fail(self, message: str) -> None:
        raise gl.vm.UserError(f"[EXPECTED] {message}")

    def _only_owner(self) -> None:
        if str(gl.message.sender_address) != self.owner:
            self._fail("Only reputation administrator")

    def _clamp(self, value: int) -> int:
        return max(0, min(100, value))

    def _bayes(self, success: int, failure: int, prior: int = 70, strength: int = 3) -> int:
        total = success + failure
        return (success * 100 + prior * strength) // (total + strength)

    def _recompute(self, reputation: Reputation) -> None:
        reliability = self._bayes(int(reputation.jobs_completed), int(reputation.jobs_failed))
        sla = self._bayes(int(reputation.sla_hits), int(reputation.sla_misses))
        payments = self._bayes(int(reputation.payment_success), int(reputation.payment_failure))
        disputes = self._clamp(100 - int(reputation.disputes_lost) * 10)
        authenticity = int(reputation.fingerprint_score) if reputation.fingerprint_status == "verified" else 0
        weighted = authenticity * 20 + reliability * 25 + sla * 20 + payments * 20 + disputes * 15
        reputation.trust_score = u256(self._clamp((weighted + 50) // 100))

    @gl.public.write
    def register_agent(self, agent: str) -> dict:
        self._only_owner()
        if agent in self.reputations:
            self._fail("Agent reputation already exists")
        self.reputations[agent] = Reputation(
            agent=agent,
            fingerprint_score=u256(0),
            fingerprint_status="unverified",
            jobs_completed=u256(0),
            jobs_failed=u256(0),
            sla_hits=u256(0),
            sla_misses=u256(0),
            payment_success=u256(0),
            payment_failure=u256(0),
            disputes_lost=u256(0),
            trust_score=u256(0),
            note="No verified work yet",
        )
        self.agent_keys.append(agent)
        return self.get_reputation(agent)

    @gl.public.write
    def record_fingerprint(self, agent: str, score: str, status: str, note: str) -> dict:
        self._only_owner()
        if agent not in self.reputations:
            self._fail("Agent reputation not registered")
        reputation = self.reputations[agent]
        normalized = status.lower()
        if normalized not in ("verified", "mismatched", "inconclusive"):
            self._fail("Invalid fingerprint status")
        reputation.fingerprint_score = u256(self._clamp(int(score)))
        reputation.fingerprint_status = normalized
        reputation.note = note[:400]
        self._recompute(reputation)
        self.reputations[agent] = reputation
        return self.get_reputation(agent)

    @gl.public.write
    def record_outcome(
        self,
        agent: str,
        completed: bool,
        sla_met: bool,
        paid: bool,
        dispute_lost: bool,
    ) -> dict:
        self._only_owner()
        if agent not in self.reputations:
            self._fail("Agent reputation not registered")
        reputation = self.reputations[agent]
        if completed:
            reputation.jobs_completed = u256(int(reputation.jobs_completed) + 1)
        else:
            reputation.jobs_failed = u256(int(reputation.jobs_failed) + 1)
        if sla_met:
            reputation.sla_hits = u256(int(reputation.sla_hits) + 1)
        else:
            reputation.sla_misses = u256(int(reputation.sla_misses) + 1)
        if paid:
            reputation.payment_success = u256(int(reputation.payment_success) + 1)
        else:
            reputation.payment_failure = u256(int(reputation.payment_failure) + 1)
        if dispute_lost:
            reputation.disputes_lost = u256(int(reputation.disputes_lost) + 1)
        self._recompute(reputation)
        self.reputations[agent] = reputation
        return self.get_reputation(agent)

    @gl.public.view
    def get_reputation(self, agent: str) -> dict:
        if agent not in self.reputations:
            self._fail("Agent reputation not found")
        reputation = self.reputations[agent]
        return {
            "agent": reputation.agent,
            "fingerprint_score": int(reputation.fingerprint_score),
            "fingerprint_status": reputation.fingerprint_status,
            "jobs_completed": int(reputation.jobs_completed),
            "jobs_failed": int(reputation.jobs_failed),
            "sla_hits": int(reputation.sla_hits),
            "sla_misses": int(reputation.sla_misses),
            "payment_success": int(reputation.payment_success),
            "payment_failure": int(reputation.payment_failure),
            "disputes_lost": int(reputation.disputes_lost),
            "trust_score": int(reputation.trust_score),
            "note": reputation.note,
        }

    @gl.public.view
    def list_reputations(self) -> dict:
        return {"reputations": [self.get_reputation(agent) for agent in self.agent_keys], "total": len(self.agent_keys)}
