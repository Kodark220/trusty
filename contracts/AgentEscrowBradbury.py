# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from dataclasses import dataclass
from genlayer import *


@allow_storage
@dataclass
class Negotiation:
    negotiation_id: str
    requester: str
    provider: str
    title: str
    brief: str
    terms: str
    proposed_value: str
    status: str
    evidence: str
    outcome_note: str


@allow_storage
@dataclass
class Reputation:
    completed: u256
    successful: u256
    disputed: u256


class AgentMarketplace(gl.Contract):
    """No-custody ledger for agent negotiations and portable reputation."""

    storage_version: u256
    negotiation_keys: DynArray[str]
    negotiations: TreeMap[str, Negotiation]
    reputations: TreeMap[str, Reputation]

    def __init__(self):
        self.storage_version = u256(1)

    def _fail(self, message: str) -> None:
        raise gl.vm.UserError(f"[EXPECTED] {message}")

    def _address(self, value) -> str:
        address = str(value).lower()
        return address[2:] if address.startswith("0x") else address

    def _require_participant(self, negotiation: Negotiation) -> str:
        sender = self._address(gl.message.sender_address)
        if sender != negotiation.requester and sender != negotiation.provider:
            self._fail("Only a participating agent can update this negotiation")
        return sender

    def _reputation(self, address: str) -> Reputation:
        key = self._address(address)
        if key not in self.reputations:
            self.reputations[key] = Reputation(u256(0), u256(0), u256(0))
        return self.reputations[key]

    def _exists(self, negotiation_id: str) -> bool:
        for key in self.negotiation_keys:
            if key == negotiation_id:
                return True
        return False

    def _key(self, negotiation_id: str) -> str:
        digest = 0
        for char in negotiation_id:
            digest = (digest * 131 + ord(char)) % 18446744073709551616
        return str(digest)

    @gl.public.write
    def create_negotiation(
        self, negotiation_id: str, provider: str, title: str, brief: str, terms: str, proposed_value: str
    ) -> dict:
        requester = self._address(gl.message.sender_address)
        provider = self._address(provider)
        negotiation_id = negotiation_id.strip()
        if not negotiation_id or self._exists(negotiation_id):
            self._fail("Negotiation reference is invalid or already exists")
        if requester == provider:
            self._fail("An agent cannot negotiate with itself")
        if not provider or not title.strip() or not brief.strip():
            self._fail("Provider, title, and brief are required")
        negotiation = Negotiation(
            negotiation_id=negotiation_id,
            requester=requester,
            provider=provider,
            title=title.strip(),
            brief=brief.strip(),
            terms=terms.strip(),
            proposed_value=proposed_value.strip(),
            status="requested",
            evidence="",
            outcome_note="",
        )
        self.negotiations[self._key(negotiation_id)] = negotiation
        self.negotiation_keys.append(negotiation_id)
        return self.get_negotiation(negotiation_id)

    @gl.public.write
    def propose(self, negotiation_id: str, terms: str, proposed_value: str) -> dict:
        negotiation = self._get(negotiation_id)
        if self._address(gl.message.sender_address) != negotiation.provider:
            self._fail("Only the provider agent can propose terms")
        if negotiation.status != "requested":
            self._fail("Negotiation is not awaiting a proposal")
        if not terms.strip():
            self._fail("Terms are required")
        negotiation.terms = terms.strip()
        negotiation.proposed_value = proposed_value.strip()
        negotiation.status = "proposed"
        self.negotiations[self._key(str(negotiation_id))] = negotiation
        return self.get_negotiation(str(negotiation_id))

    @gl.public.write
    def accept(self, negotiation_id: str) -> dict:
        negotiation = self._get(negotiation_id)
        if self._address(gl.message.sender_address) != negotiation.requester:
            self._fail("Only the requesting agent can accept terms")
        if negotiation.status != "proposed":
            self._fail("Negotiation is not awaiting acceptance")
        negotiation.status = "agreed"
        self.negotiations[self._key(str(negotiation_id))] = negotiation
        return self.get_negotiation(str(negotiation_id))

    @gl.public.write
    def submit_outcome(self, negotiation_id: str, evidence: str, note: str) -> dict:
        negotiation = self._get(negotiation_id)
        if self._address(gl.message.sender_address) != negotiation.provider:
            self._fail("Only the provider agent can submit an outcome")
        if negotiation.status != "agreed":
            self._fail("Negotiation is not active")
        if len(evidence.strip()) < 10:
            self._fail("Outcome evidence is too short")
        negotiation.evidence = evidence.strip()
        negotiation.outcome_note = note.strip()
        negotiation.status = "delivered"
        self.negotiations[self._key(str(negotiation_id))] = negotiation
        return self.get_negotiation(str(negotiation_id))

    @gl.public.write
    def confirm_outcome(self, negotiation_id: str, successful: bool, note: str) -> dict:
        negotiation = self._get(negotiation_id)
        if self._address(gl.message.sender_address) != negotiation.requester:
            self._fail("Only the requesting agent can confirm an outcome")
        if negotiation.status != "delivered":
            self._fail("Negotiation is not awaiting outcome confirmation")
        negotiation.status = "completed"
        negotiation.outcome_note = note.strip() or negotiation.outcome_note
        self.negotiations[self._key(str(negotiation_id))] = negotiation
        reputation = self._reputation(negotiation.provider)
        reputation.completed = u256(int(reputation.completed) + 1)
        if successful:
            reputation.successful = u256(int(reputation.successful) + 1)
        else:
            reputation.disputed = u256(int(reputation.disputed) + 1)
        self.reputations[negotiation.provider] = reputation
        return self.get_negotiation(str(negotiation_id))

    def _get(self, negotiation_id: str) -> Negotiation:
        key = str(negotiation_id)
        if not self._exists(key):
            self._fail("Negotiation not found")
        return self.negotiations[self._key(key)]

    @gl.public.view
    def get_negotiation(self, negotiation_id: str) -> dict:
        negotiation = self._get(negotiation_id)
        return {
            "negotiation_id": negotiation.negotiation_id,
            "requester": negotiation.requester,
            "provider": negotiation.provider,
            "title": negotiation.title,
            "brief": negotiation.brief,
            "terms": negotiation.terms,
            "proposed_value": negotiation.proposed_value,
            "status": negotiation.status,
            "evidence": negotiation.evidence,
            "outcome_note": negotiation.outcome_note,
        }

    @gl.public.view
    def get_reputation(self, agent: str) -> dict:
        agent = self._address(agent)
        reputation = self._reputation(agent)
        return {
            "agent": agent,
            "completed": int(reputation.completed),
            "successful": int(reputation.successful),
            "disputed": int(reputation.disputed),
        }