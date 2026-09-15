# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *


class AgentEscrowBradburyV2(gl.Contract):
    """Minimal Bradbury escrow ledger with one active demo job."""

    buyer: str
    worker: str
    title: str
    brief: str
    terms: str
    evidence: str
    balance: u256
    escrowed: u256
    worker_payout: u256
    buyer_payout: u256
    status: str

    def __init__(self):
        self.buyer = ""
        self.worker = ""
        self.title = ""
        self.brief = ""
        self.terms = ""
        self.evidence = ""
        self.balance = u256(0)
        self.escrowed = u256(0)
        self.worker_payout = u256(0)
        self.buyer_payout = u256(0)
        self.status = "empty"

    def _fail(self, message: str) -> None:
        raise gl.vm.UserError(f"[EXPECTED] {message}")

    @gl.public.write
    def deposit(self, amount: str) -> dict:
        value = int(amount)
        if value <= 0:
            self._fail("Deposit must be positive")
        sender = str(gl.message.sender_address)
        if self.buyer and sender != self.buyer:
            self._fail("Only the active buyer can deposit")
        self.buyer = sender
        self.balance = u256(int(self.balance) + value)
        return {"buyer": self.buyer, "balance": int(self.balance)}

    @gl.public.write
    def hire(self, worker: str, title: str, brief: str, terms: str, budget: str) -> dict:
        amount = int(budget)
        if amount <= 0:
            self._fail("Budget must be positive")
        if not self.buyer:
            self.buyer = str(gl.message.sender_address)
        if str(gl.message.sender_address) != self.buyer:
            self._fail("Only the buyer can hire")
        if int(self.balance) < amount:
            self._fail("Insufficient balance")
        self.worker = str(worker)
        self.title = title.strip()
        self.brief = brief.strip()
        self.terms = terms.strip()
        self.escrowed = u256(amount)
        self.balance = u256(int(self.balance) - amount)
        self.status = "escrowed"
        return {"status": self.status, "worker": self.worker, "budget": amount}

    @gl.public.write
    def submit_delivery(self, evidence: str) -> dict:
        if str(gl.message.sender_address) != self.worker:
            self._fail("Only the worker can submit delivery")
        if self.status != "escrowed":
            self._fail("Job is not awaiting delivery")
        if len(evidence.strip()) < 10:
            self._fail("Evidence is too short")
        self.evidence = evidence.strip()
        self.status = "delivered"
        return {"status": self.status}

    @gl.public.write
    def settle(self, worker_share_pct: str, note: str) -> dict:
        if str(gl.message.sender_address) != self.buyer:
            self._fail("Only the buyer can settle")
        if self.status != "delivered":
            self._fail("Job is not ready for settlement")
        share = int(worker_share_pct)
        if share < 0 or share > 100:
            self._fail("Worker share must be 0-100")
        worker_payout = int(self.escrowed) * share // 100
        buyer_payout = int(self.escrowed) - worker_payout
        self.worker_payout = u256(worker_payout)
        self.buyer_payout = u256(buyer_payout)
        self.balance = u256(int(self.balance) + buyer_payout)
        self.escrowed = u256(0)
        self.status = "settled"
        return {"status": self.status, "worker_payout": worker_payout, "buyer_payout": buyer_payout, "note": note[:400]}

    @gl.public.view
    def get_state(self) -> dict:
        return {"buyer": self.buyer, "worker": self.worker, "title": self.title, "brief": self.brief, "terms": self.terms, "evidence": self.evidence, "balance": int(self.balance), "escrowed": int(self.escrowed), "worker_payout": int(self.worker_payout), "buyer_payout": int(self.buyer_payout), "status": self.status}
