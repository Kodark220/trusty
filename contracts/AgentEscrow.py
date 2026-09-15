# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from dataclasses import dataclass
from genlayer import *
import json


@allow_storage
@dataclass
class EscrowJob:
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
    """Standalone Studionet hiring, evidence verification, and escrow contract."""

    next_job_id: u256
    jobs: TreeMap[str, EscrowJob]
    job_keys: DynArray[str]
    balances: TreeMap[str, u256]

    def __init__(self):
        self.next_job_id = u256(1)

    def _fail(self, message: str) -> None:
        raise gl.vm.UserError(f"[EXPECTED] {message}")

    def _credit(self, address: str, amount: int) -> None:
        current = int(self.balances[address]) if address in self.balances else 0
        self.balances[address] = u256(current + amount)

    def _debit(self, address: str, amount: int) -> None:
        current = int(self.balances[address]) if address in self.balances else 0
        if current < amount:
            self._fail("Insufficient balance")
        self.balances[address] = u256(current - amount)

    def _clamp(self, value: int) -> int:
        return max(0, min(100, value))

    @gl.public.write
    def deposit(self, amount: str) -> dict:
        value = int(amount)
        if value <= 0:
            self._fail("Deposit must be positive")
        sender = str(gl.message.sender_address)
        self._credit(sender, value)
        return {"address": sender, "balance": int(self.balances[sender])}

    @gl.public.write
    def hire(
        self,
        worker: str,
        title: str,
        brief: str,
        terms: str,
        budget: str,
        verified_registry: bool,
    ) -> dict:
        if not verified_registry:
            self._fail("Registry verification is required before hiring")
        buyer = str(gl.message.sender_address)
        if buyer == worker:
            self._fail("Cannot hire yourself")
        amount = int(budget)
        if amount <= 0:
            self._fail("Budget must be positive")
        self._debit(buyer, amount)
        job_id = int(self.next_job_id)
        self.jobs[str(job_id)] = EscrowJob(
            job_id=u256(job_id),
            buyer=buyer,
            worker=worker,
            title=title.strip(),
            brief=brief.strip(),
            terms=terms.strip(),
            budget=u256(amount),
            escrowed=u256(amount),
            status="escrowed",
            evidence="",
            worker_payout=u256(0),
            buyer_payout=u256(0),
            note="",
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
        job.status = "delivered"
        self.jobs[key] = job
        return {"job_id": int(job.job_id), "status": job.status}

    @gl.public.write
    def verify_delivery(self, job_id: str) -> dict:
        key = str(job_id)
        if key not in self.jobs:
            self._fail("Job not found")
        job = self.jobs[key]
        if job.status != "delivered":
            self._fail("Job has no delivery")

        def judge() -> str:
            prompt = f"""Judge this job against its terms.
TITLE: {job.title}
BRIEF: {job.brief}
TERMS: {job.terms}
EVIDENCE: {job.evidence[:2500]}
Return JSON only: worker_share_pct 0-100 and explanation."""
            return gl.nondet.exec_prompt(prompt, response_format="json")

        raw = gl.eq_principle.prompt_comparative(
            judge,
            "worker_share_pct must be within 10 points.",
        )
        try:
            result = raw if isinstance(raw, dict) else json.loads(str(raw))
        except Exception:
            result = {"worker_share_pct": 50, "explanation": "Inconclusive; split escrow."}
        share = self._clamp(int(result.get("worker_share_pct", 50)))
        worker_payout = int(job.escrowed) * share // 100
        buyer_payout = int(job.escrowed) - worker_payout
        self._credit(job.worker, worker_payout)
        self._credit(job.buyer, buyer_payout)
        job.status = "settled"
        job.worker_payout = u256(worker_payout)
        job.buyer_payout = u256(buyer_payout)
        job.escrowed = u256(0)
        job.note = str(result.get("explanation", ""))[:400]
        self.jobs[key] = job
        return {
            "job_id": int(job.job_id),
            "status": job.status,
            "worker_payout": worker_payout,
            "buyer_payout": buyer_payout,
            "note": job.note,
        }

    @gl.public.view
    def get_job(self, job_id: str) -> dict:
        key = str(job_id)
        if key not in self.jobs:
            self._fail("Job not found")
        job = self.jobs[key]
        return {
            "job_id": int(job.job_id),
            "buyer": job.buyer,
            "worker": job.worker,
            "title": job.title,
            "brief": job.brief,
            "terms": job.terms,
            "budget": int(job.budget),
            "escrowed": int(job.escrowed),
            "status": job.status,
            "evidence": job.evidence,
            "worker_payout": int(job.worker_payout),
            "buyer_payout": int(job.buyer_payout),
            "note": job.note,
        }
