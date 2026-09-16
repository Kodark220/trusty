# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from dataclasses import dataclass
from genlayer import *
import json


@gl.evm.contract_interface
class _Recipient:
    class View:
        pass

    class Write:
        pass


@allow_storage
@dataclass
class Job:
    job_id: u256
    buyer: str
    worker: str
    title: str
    brief: str
    terms: str
    budget: u256
    escrowed: u256
    status: str
    evidence: str
    worker_payout: u256
    buyer_payout: u256
    note: str


class AgentEscrow(gl.Contract):
    """Studionet escrow: hire, evidence submission, and settlement."""

    next_job_id: u256
    job_keys: DynArray[str]
    jobs: TreeMap[str, Job]
    balances: TreeMap[str, u256]

    def __init__(self):
        self.next_job_id = u256(1)

    def _fail(self, message: str) -> None:
        raise gl.vm.UserError(f"[EXPECTED] {message}")

    def _number(self, value: str) -> int:
        text = str(value)
        if text.startswith("int:") or text.startswith("str:"):
            text = text[4:]
        return int(text)

    def _credit(self, address: str, amount: int) -> None:
        current = int(self.balances[address]) if address in self.balances else 0
        self.balances[address] = u256(current + amount)

    def _debit(self, address: str, amount: int) -> None:
        current = int(self.balances[address]) if address in self.balances else 0
        if current < amount:
            self._fail("Insufficient balance")
        self.balances[address] = u256(current - amount)

    def _judge_delivery(self, job: Job) -> tuple[int, str]:
        def evaluate() -> str:
            prompt = f"""Evaluate this agent delivery against the agreed terms.
TITLE: {job.title[:500]}
TERMS: {job.terms[:1800]}
EVIDENCE: {job.evidence[:2500]}
Return JSON only with worker_share_pct from 0 to 100 and explanation."""
            return gl.nondet.exec_prompt(prompt, response_format="json")

        raw = gl.eq_principle.prompt_comparative(
            evaluate,
            "worker_share_pct must be within 10 points and the result must be consistent.",
        )
        try:
            result = raw if isinstance(raw, dict) else json.loads(str(raw))
        except Exception:
            result = {"worker_share_pct": 50, "explanation": "Inconclusive; split escrow."}
        share = max(0, min(100, int(result.get("worker_share_pct", 50))))
        return share, str(result.get("explanation", ""))[:400]

    @gl.public.write.payable
    def deposit(self) -> dict:
        value = int(gl.message.value)
        if value <= 0:
            self._fail("Deposit must be positive")
        sender = str(gl.message.sender_address)
        self._credit(sender, value)
        return {"address": sender, "balance": int(self.balances[sender])}

    @gl.public.write
    def withdraw(self, amount: str) -> dict:
        sender = str(gl.message.sender_address)
        value = self._number(amount)
        if value <= 0:
            self._fail("Withdrawal must be positive")
        self._debit(sender, value)
        _Recipient(Address(sender)).emit_transfer(value=u256(value))
        return {"address": sender, "withdrawn": value, "balance": int(self.balances[sender])}

    @gl.public.write
    def hire(self, worker: str, title: str, brief: str, terms: str, budget: str) -> dict:
        buyer = str(gl.message.sender_address)
        worker = str(worker)
        if buyer == worker:
            self._fail("Cannot hire yourself")
        amount = self._number(budget)
        if amount <= 0:
            self._fail("Budget must be positive")
        self._debit(buyer, amount)
        job_id = int(self.next_job_id)
        self.jobs[str(job_id)] = Job(
            job_id=u256(job_id), buyer=buyer, worker=worker,
            title=title.strip(), brief=brief.strip(), terms=terms.strip(),
            budget=u256(amount), escrowed=u256(amount), status="escrowed",
            evidence="", worker_payout=u256(0), buyer_payout=u256(0), note="",
        )
        self.job_keys.append(str(job_id))
        self.next_job_id = u256(job_id + 1)
        return {"job_id": job_id, "status": "escrowed", "budget": amount}

    @gl.public.write
    def submit_delivery(self, job_id: str, evidence: str) -> dict:
        key = str(job_id)
        if key not in self.jobs:
            self._fail("Job not found")
        job = self.jobs[key]
        if str(gl.message.sender_address) != job.worker:
            self._fail("Only the worker can submit delivery")
        if job.status != "escrowed":
            self._fail("Job is not awaiting delivery")
        if len(evidence.strip()) < 10:
            self._fail("Evidence is too short")
        job.evidence = evidence.strip()
        job.status = "verifying"
        memory_job = gl.storage.copy_to_memory(job)
        share, explanation = self._judge_delivery(memory_job)
        worker_payout = int(job.escrowed) * share // 100
        buyer_payout = int(job.escrowed) - worker_payout
        self._credit(job.worker, worker_payout)
        self._credit(job.buyer, buyer_payout)
        job.status = "settled"
        job.escrowed = u256(0)
        job.worker_payout = u256(worker_payout)
        job.buyer_payout = u256(buyer_payout)
        job.note = explanation or "Automatic validator settlement"
        self.jobs[key] = job
        return {"job_id": int(job.job_id), "status": "settled", "worker_payout": worker_payout, "buyer_payout": buyer_payout, "note": job.note}

    @gl.public.write
    def settle(self, job_id: str, worker_share_pct: str, note: str) -> dict:
        key = str(job_id)
        if key not in self.jobs:
            self._fail("Job not found")
        job = self.jobs[key]
        if str(gl.message.sender_address) != job.buyer:
            self._fail("Only the buyer can settle")
        if job.status != "delivered":
            self._fail("Job is not ready for settlement")
        share = self._number(worker_share_pct)
        if share < 0 or share > 100:
            self._fail("Worker share must be 0-100")
        worker_payout = int(job.escrowed) * share // 100
        buyer_payout = int(job.escrowed) - worker_payout
        self._credit(job.worker, worker_payout)
        self._credit(job.buyer, buyer_payout)
        job.status = "settled"
        job.escrowed = u256(0)
        job.worker_payout = u256(worker_payout)
        job.buyer_payout = u256(buyer_payout)
        job.note = note.strip() or "Buyer settlement"
        self.jobs[key] = job
        return {"job_id": int(job.job_id), "status": "settled", "worker_payout": worker_payout, "buyer_payout": buyer_payout, "note": job.note}

    @gl.public.view
    def get_job(self, job_id: str) -> dict:
        key = str(job_id)
        if key not in self.jobs:
            self._fail("Job not found")
        job = self.jobs[key]
        return {"job_id": int(job.job_id), "buyer": job.buyer, "worker": job.worker, "title": job.title, "brief": job.brief, "terms": job.terms, "budget": int(job.budget), "escrowed": int(job.escrowed), "status": job.status, "evidence": job.evidence, "worker_payout": int(job.worker_payout), "buyer_payout": int(job.buyer_payout), "note": job.note}
