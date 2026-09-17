# v0.3.0
# { "Depends": "py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng" }
import json

import genlayer as gl


class AgentMarketplace(gl.contract.Contract):
    """No-custody ledger for agent negotiations and portable reputation."""

    negotiation_keys: str
    negotiations_data: str
    reputations_data: str

    def __init__(self):
        self.negotiation_keys = "[]"
        self.negotiations_data = "{}"
        self.reputations_data = "{}"

    def _fail(self, message: str) -> None:
        raise gl.vm.UserError(f"[EXPECTED] {message}")

    def _address(self, value) -> str:
        address = str(value).lower()
        return address[2:] if address.startswith("0x") else address

    def _keys(self) -> list:
        try:
            keys = json.loads(self.negotiation_keys)
            return keys if isinstance(keys, list) else []
        except Exception:
            return []

    def _key(self, negotiation_id: str) -> str:
        digest = 0
        for char in negotiation_id:
            digest = (digest * 131 + ord(char)) % 18446744073709551616
        return str(digest)

    def _exists(self, negotiation_id: str) -> bool:
        return negotiation_id in self._keys()

    def _get_store(self, attr_name: str) -> dict:
        try:
            val = getattr(self, attr_name)
            return json.loads(val) if val else {}
        except Exception:
            return {}

    def _set_store(self, attr_name: str, data: dict) -> None:
        setattr(self, attr_name, json.dumps(data))

    def _get(self, negotiation_id: str) -> dict:
        if not self._exists(negotiation_id):
            self._fail("Negotiation not found")
        store = self._get_store("negotiations_data")
        key = self._key(negotiation_id)
        if key not in store:
            self._fail("Negotiation not found")
        return json.loads(store[key])

    def _save(self, negotiation: dict) -> None:
        store = self._get_store("negotiations_data")
        store[self._key(negotiation["negotiation_id"])] = json.dumps(negotiation)
        self._set_store("negotiations_data", store)

    def _reputation(self, address: str) -> dict:
        key = self._address(address)
        store = self._get_store("reputations_data")
        if key in store:
            return json.loads(store[key])
        return {"agent": key, "completed": 0, "successful": 0, "disputed": 0}

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
        negotiation = {
            "negotiation_id": negotiation_id, "requester": requester, "provider": provider,
            "title": title.strip(), "brief": brief.strip(), "terms": terms.strip(),
            "proposed_value": proposed_value.strip(), "status": "requested", "evidence": "", "outcome_note": "",
        }
        self._save(negotiation)
        keys = self._keys()
        keys.append(negotiation_id)
        self.negotiation_keys = json.dumps(keys)
        return negotiation

    @gl.public.write
    def propose(self, negotiation_id: str, terms: str, proposed_value: str) -> dict:
        negotiation = self._get(negotiation_id)
        if self._address(gl.message.sender_address) != negotiation["provider"]:
            self._fail("Only the provider agent can propose terms")
        if negotiation["status"] != "requested" or not terms.strip():
            self._fail("Negotiation is not awaiting a proposal with terms")
        negotiation["terms"] = terms.strip()
        negotiation["proposed_value"] = proposed_value.strip()
        negotiation["status"] = "proposed"
        self._save(negotiation)
        return negotiation

    @gl.public.write
    def accept(self, negotiation_id: str) -> dict:
        negotiation = self._get(negotiation_id)
        if self._address(gl.message.sender_address) != negotiation["requester"]:
            self._fail("Only the requesting agent can accept terms")
        if negotiation["status"] != "proposed":
            self._fail("Negotiation is not awaiting acceptance")
        negotiation["status"] = "agreed"
        self._save(negotiation)
        return negotiation

    @gl.public.write
    def submit_outcome(self, negotiation_id: str, evidence: str, note: str) -> dict:
        negotiation = self._get(negotiation_id)
        if self._address(gl.message.sender_address) != negotiation["provider"]:
            self._fail("Only the provider agent can submit an outcome")
        if negotiation["status"] != "agreed" or len(evidence.strip()) < 10:
            self._fail("Negotiation is not active or outcome evidence is too short")
        negotiation["evidence"] = evidence.strip()
        negotiation["outcome_note"] = note.strip()
        negotiation["status"] = "delivered"
        self._save(negotiation)
        return negotiation

    @gl.public.write
    def confirm_outcome(self, negotiation_id: str, successful: bool, note: str) -> dict:
        negotiation = self._get(negotiation_id)
        if self._address(gl.message.sender_address) != negotiation["requester"]:
            self._fail("Only the requesting agent can confirm an outcome")
        if negotiation["status"] != "delivered":
            self._fail("Negotiation is not awaiting outcome confirmation")
        negotiation["status"] = "completed"
        negotiation["outcome_note"] = note.strip() or negotiation["outcome_note"]
        self._save(negotiation)
        reputation = self._reputation(negotiation["provider"])
        reputation["completed"] = int(reputation["completed"]) + 1
        if successful:
            reputation["successful"] = int(reputation["successful"]) + 1
        else:
            reputation["disputed"] = int(reputation["disputed"]) + 1
        rep_store = self._get_store("reputations_data")
        rep_store[negotiation["provider"]] = json.dumps(reputation)
        self._set_store("reputations_data", rep_store)
        return negotiation

    @gl.public.view
    def get_negotiation(self, negotiation_id: str) -> dict:
        return self._get(negotiation_id)

    @gl.public.view
    def get_reputation(self, agent: str) -> dict:
        return self._reputation(agent)
