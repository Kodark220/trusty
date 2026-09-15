# { "Depends": "py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng" }
"""
AgentTrust — verifiable trust layer for autonomous agents.

GenLayer owns: fingerprint judgment, delivery verification, dispute jury,
escrow split, and the reputation write after those judgments.

Frontend owns: UI, ranking previews, demo playback, indexing.

External sources own: model cards and deliverable evidence. Validators re-read
them; they are not trusted until consensus.

Verify what an agent claims to be (model fingerprint).
Measure how it actually behaves (jobs, SLA, disputes, settlement).
Let that reputation follow it everywhere.
"""
from dataclasses import dataclass
import genlayer as gl
from genlayer.storage import allow as allow_storage
import json

Address = gl.Address
u256 = gl.u256
TreeMap = gl.storage.TreeMap
DynArray = gl.storage.DynArray

ERROR_EXPECTED = "[EXPECTED]"
ERROR_EXTERNAL = "[EXTERNAL]"
ERROR_TRANSIENT = "[TRANSIENT]"
ERROR_LLM = "[LLM_ERROR]"


@allow_storage
@dataclass
class Agent:
    agent_id: u256
    owner: str
    name: str
    claimed_model: str
    claimed_provider: str
    claimed_version: str
    capabilities: str
    endpoint: str
    model_card_url: str
    fingerprint_hash: str
    fingerprint_status: str
    fingerprint_score: u256
    fingerprint_note: str
    jobs_completed: u256
    jobs_failed: u256
    sla_hits: u256
    sla_misses: u256
    tx_success: u256
    tx_fail: u256
    disputes_opened: u256
    disputes_lost: u256
    authenticity: u256
    reliability: u256
    sla_score: u256
    tx_score: u256
    dispute_score: u256
    trust_score: u256
    active: bool


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
    delivered_on_time: bool
    quality_score: u256
    sla_met: bool
    settlement_note: str
    buyer_payout: u256
    worker_payout: u256


@allow_storage
@dataclass
class Dispute:
    dispute_id: u256
    job_id: u256
    filer: str
    claim: str
    evidence: str
    response: str
    status: str
    verdict: str
    buyer_share_pct: u256
    note: str


class AgentTrust(gl.contract.Contract):
    """Identity + fingerprint + escrow + earned reputation for agents."""

    owner: Address
    is_paused: bool
    next_agent_id: u256
    next_job_id: u256
    next_dispute_id: u256
    total_agents: u256
    total_jobs: u256
    total_settled: u256
    total_disputes: u256
    total_escrowed: u256

    agents: TreeMap[str, Agent]
    agents_by_id: TreeMap[str, str]
    agent_keys: DynArray[str]
    jobs: TreeMap[str, Job]
    job_keys: DynArray[str]
    disputes: TreeMap[str, Dispute]
    dispute_keys: DynArray[str]
    balances: TreeMap[str, u256]

    def __init__(self, owner: Address):
        self.owner = Address(owner)
        self.is_paused = False
        self.next_agent_id = u256(1)
        self.next_job_id = u256(1)
        self.next_dispute_id = u256(1)
        self.total_agents = u256(0)
        self.total_jobs = u256(0)
        self.total_settled = u256(0)
        self.total_disputes = u256(0)
        self.total_escrowed = u256(0)

    # ── internals ──────────────────────────────────────────

    def _sender(self) -> str:
        return str(gl.message.sender_address)

    def _fail(self, msg: str) -> None:
        raise gl.vm.UserError(f"{ERROR_EXPECTED} {msg}")

    def _require_active(self) -> None:
        if self.is_paused:
            self._fail("Protocol is paused")

    def _parse_llm_json(self, raw, fallback: dict) -> dict:
        if isinstance(raw, dict):
            parsed = raw
        else:
            text = str(raw).strip()
            if text.startswith("```"):
                lines = text.split("\n")
                lines = lines[1:]
                if lines and lines[-1].strip().startswith("```"):
                    lines = lines[:-1]
                text = "\n".join(lines).strip()
            start = text.find("{")
            end = text.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return fallback
            try:
                parsed = json.loads(text[start : end + 1])
            except Exception:
                return fallback
            if not isinstance(parsed, dict):
                return fallback
        for key, aliases in (
            ("score", ("rating", "points", "value", "fingerprint_score", "quality_score")),
            ("verdict", ("decision", "label", "status")),
            ("explanation", ("reason", "note", "summary")),
            ("worker_share_pct", ("worker_share", "payout_pct")),
            ("buyer_share_pct", ("buyer_share", "refund_pct")),
            ("agent_ids", ("ids", "ranked")),
        ):
            if key not in parsed or parsed[key] is None:
                for alt in aliases:
                    if alt in parsed and parsed[alt] is not None:
                        parsed[key] = parsed[alt]
                        break
        return parsed

    def _clamp(self, value: int) -> int:
        if value < 0:
            return 0
        if value > 100:
            return 100
        return value

    def _as_bool(self, value, default: bool = False) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, u256)):
            return int(value) != 0
        text = str(value).strip().lower()
        if text in ("true", "yes", "1", "y"):
            return True
        if text in ("false", "no", "0", "n", ""):
            return False
        return default

    def _bayes(self, success: int, fail: int, prior: int = 70, strength: int = 3) -> int:
        total = success + fail
        return (success * 100 + prior * strength) // (total + strength)

    def _overall(
        self,
        authenticity: int,
        reliability: int,
        sla_score: int,
        tx_score: int,
        dispute_score: int,
    ) -> int:
        weighted = (
            authenticity * 20
            + reliability * 25
            + sla_score * 20
            + tx_score * 20
            + dispute_score * 15
        )
        return self._clamp((weighted + 50) // 100)

    def _recompute(self, agent: Agent) -> Agent:
        completed = int(agent.jobs_completed)
        failed = int(agent.jobs_failed)
        sla_hits = int(agent.sla_hits)
        sla_misses = int(agent.sla_misses)
        tx_ok = int(agent.tx_success)
        tx_bad = int(agent.tx_fail)
        lost = int(agent.disputes_lost)
        opened = int(agent.disputes_opened)

        if agent.fingerprint_status == "verified":
            authenticity = int(agent.fingerprint_score)
        elif agent.fingerprint_status == "mismatched":
            authenticity = self._clamp(int(agent.fingerprint_score) // 2)
        elif agent.fingerprint_status == "inconclusive":
            authenticity = 40
        else:
            authenticity = 0

        reliability = self._bayes(completed, failed)
        sla_score = self._bayes(sla_hits, sla_misses)
        tx_score = self._bayes(tx_ok, tx_bad)
        dispute_score = self._clamp(100 - lost * 8 - opened * 2)

        agent.authenticity = u256(authenticity)
        agent.reliability = u256(reliability)
        agent.sla_score = u256(sla_score)
        agent.tx_score = u256(tx_score)
        agent.dispute_score = u256(dispute_score)
        agent.trust_score = u256(
            self._overall(authenticity, reliability, sla_score, tx_score, dispute_score)
        )
        return agent

    def _agent_public(self, agent: Agent) -> dict:
        completed = int(agent.jobs_completed)
        failed = int(agent.jobs_failed)
        total = completed + failed
        sla_hits = int(agent.sla_hits)
        sla_misses = int(agent.sla_misses)
        sla_total = sla_hits + sla_misses
        tx_ok = int(agent.tx_success)
        tx_bad = int(agent.tx_fail)
        tx_total = tx_ok + tx_bad
        success_rate = 0 if total == 0 else (completed * 1000 // total)
        sla_rate = 0 if sla_total == 0 else (sla_hits * 1000 // sla_total)
        tx_rate = 0 if tx_total == 0 else (tx_ok * 1000 // tx_total)
        return {
            "agent_id": int(agent.agent_id),
            "owner": agent.owner,
            "name": agent.name,
            "claimed_model": agent.claimed_model,
            "claimed_provider": agent.claimed_provider,
            "claimed_version": agent.claimed_version,
            "capabilities": agent.capabilities,
            "endpoint": agent.endpoint,
            "fingerprint_status": agent.fingerprint_status,
            "fingerprint_score": int(agent.fingerprint_score),
            "fingerprint_note": agent.fingerprint_note,
            "jobs_completed": completed,
            "jobs_failed": failed,
            "jobs_total": total,
            "success_rate_x10": success_rate,
            "sla_hits": sla_hits,
            "sla_misses": sla_misses,
            "sla_rate_x10": sla_rate,
            "tx_success": tx_ok,
            "tx_fail": tx_bad,
            "tx_rate_x10": tx_rate,
            "disputes_opened": int(agent.disputes_opened),
            "disputes_lost": int(agent.disputes_lost),
            "metrics": {
                "model_authenticity": int(agent.authenticity),
                "reliability": int(agent.reliability),
                "sla_performance": int(agent.sla_score),
                "transaction_success": int(agent.tx_score),
                "dispute_history": int(agent.dispute_score),
                "overall_trust": int(agent.trust_score),
            },
            "active": agent.active,
        }

    def _credit(self, who: str, amount: int) -> None:
        if amount <= 0:
            return
        current = int(self.balances[who]) if who in self.balances else 0
        self.balances[who] = u256(current + amount)

    def _debit(self, who: str, amount: int) -> None:
        current = int(self.balances[who]) if who in self.balances else 0
        if current < amount:
            self._fail("Insufficient balance")
        self.balances[who] = u256(current - amount)

    def _capability_hit(self, capabilities: str, query: str) -> bool:
        hay_tokens = [t for t in capabilities.lower().replace(",", " ").split() if len(t) > 2]
        words = [w for w in query.lower().replace(",", " ").split() if len(w) > 3]
        if not words:
            return True
        for word in words:
            for token in hay_tokens:
                if word in token or token in word:
                    return True
        return False

    # ── identity ───────────────────────────────────────────

    @gl.public.write
    def register_agent(
        self,
        name: str,
        claimed_model: str,
        claimed_provider: str,
        claimed_version: str,
        capabilities: str,
        endpoint: str,
        model_card_url: str,
    ) -> dict:
        self._require_active()
        sender = self._sender()
        if sender in self.agents:
            self._fail("Agent already registered")
        if len(name.strip()) == 0 or len(claimed_model.strip()) == 0:
            self._fail("Name and claimed model are required")

        agent_id = int(self.next_agent_id)
        agent = Agent(
            agent_id=u256(agent_id),
            owner=sender,
            name=name.strip(),
            claimed_model=claimed_model.strip(),
            claimed_provider=claimed_provider.strip(),
            claimed_version=claimed_version.strip(),
            capabilities=capabilities.strip(),
            endpoint=endpoint.strip(),
            model_card_url=model_card_url.strip(),
            fingerprint_hash="",
            fingerprint_status="unverified",
            fingerprint_score=u256(0),
            fingerprint_note="No fingerprint submitted",
            jobs_completed=u256(0),
            jobs_failed=u256(0),
            sla_hits=u256(0),
            sla_misses=u256(0),
            tx_success=u256(0),
            tx_fail=u256(0),
            disputes_opened=u256(0),
            disputes_lost=u256(0),
            authenticity=u256(0),
            reliability=u256(70),
            sla_score=u256(70),
            tx_score=u256(70),
            dispute_score=u256(100),
            trust_score=u256(0),
            active=True,
        )
        agent = self._recompute(agent)
        self.agents[sender] = agent
        self.agents_by_id[str(agent_id)] = sender
        self.agent_keys.append(sender)
        self.next_agent_id = u256(agent_id + 1)
        self.total_agents = u256(int(self.total_agents) + 1)
        return self._agent_public(agent)

    @gl.public.write
    def update_agent(self, capabilities: str, endpoint: str, model_card_url: str) -> dict:
        self._require_active()
        sender = self._sender()
        if sender not in self.agents:
            self._fail("Agent not registered")
        agent = self.agents[sender]
        agent.capabilities = capabilities.strip()
        agent.endpoint = endpoint.strip()
        agent.model_card_url = model_card_url.strip()
        self.agents[sender] = agent
        return self._agent_public(agent)

    @gl.public.write
    def verify_fingerprint(self, sample_outputs: str, challenge_prompt: str) -> dict:
        """Prove the agent runs the model it claims. Validators agree on score ±10."""
        self._require_active()
        sender = self._sender()
        if sender not in self.agents:
            self._fail("Agent not registered")
        agent = self.agents[sender]
        if len(sample_outputs.strip()) < 20:
            self._fail("Fingerprint sample is too short")

        def analyze() -> str:
            model_card = ""
            if agent.model_card_url:
                try:
                    fetched = gl.nondet.web.render(agent.model_card_url, mode="text")
                    if fetched:
                        model_card = str(fetched)[:1200]
                except Exception:
                    model_card = ""
            prompt = f"""You are a model-fingerprinting examiner for autonomous agents.

CLAIMED IDENTITY:
- Provider: {agent.claimed_provider}
- Model: {agent.claimed_model}
- Version: {agent.claimed_version}

CHALLENGE PROMPT:
{challenge_prompt[:800]}

AGENT SAMPLE OUTPUTS:
{sample_outputs[:2500]}

PUBLIC MODEL CARD (may be empty):
{model_card}

Decide whether the sample is consistent with the claimed model (reasoning style, tool use, refusal pattern, knowledge cutoff cues, formatting). This is not cryptographic proof of weights; it is behavioral fingerprint evidence.

Return ONLY JSON:
{{
  "score": <0-100>,
  "verdict": "<verified|mismatched|inconclusive>",
  "explanation": "<one or two sentences>"
}}
"""
            return gl.nondet.exec_prompt(prompt, response_format="json")

        raw = gl.eq_principle.prompt_comparative(
            analyze,
            "Fingerprint scores should be within 10 points. Verdict must be the same category: verified, mismatched, or inconclusive.",
        )
        fallback = {
            "score": 40,
            "verdict": "inconclusive",
            "explanation": "Validators could not agree on a fingerprint match.",
        }
        result = self._parse_llm_json(raw, fallback)
        score = self._clamp(int(result.get("score", 40)))
        verdict = str(result.get("verdict", "inconclusive")).strip().lower()
        if verdict not in ("verified", "mismatched", "inconclusive"):
            verdict = "inconclusive"
        note = str(result.get("explanation", ""))[:400]

        digest_src = challenge_prompt + "|" + sample_outputs[:400]
        acc = 0
        for ch in digest_src:
            acc = (acc * 131 + ord(ch)) % 18446744073709551616
        fingerprint_hash = hex(acc)

        agent.fingerprint_status = verdict
        agent.fingerprint_score = u256(score)
        agent.fingerprint_note = note
        agent.fingerprint_hash = fingerprint_hash
        agent = self._recompute(agent)
        self.agents[sender] = agent
        return {
            "agent_id": int(agent.agent_id),
            "fingerprint_status": verdict,
            "fingerprint_score": score,
            "fingerprint_hash": fingerprint_hash,
            "explanation": note,
            "trust_score": int(agent.trust_score),
            "metrics": self._agent_public(agent)["metrics"],
        }

    # ── balances / escrow ──────────────────────────────────

    @gl.public.write
    def deposit(self, amount: str) -> dict:
        """Credit internal escrow balance (demo units, e.g. USD)."""
        self._require_active()
        value = int(amount)
        if value <= 0:
            self._fail("Deposit must be positive")
        sender = self._sender()
        self._credit(sender, value)
        return {"balance": int(self.balances[sender]), "credited": value}

    @gl.public.view
    def get_balance(self, address: str) -> dict:
        key = address if address else self._sender()
        bal = int(self.balances[key]) if key in self.balances else 0
        return {"address": key, "balance": bal}

    # ── hiring ─────────────────────────────────────────────

    @gl.public.write
    def hire_agent(self, worker: str, title: str, brief: str, terms: str, budget: str) -> dict:
        """Lock budget in escrow. Reputation → selection → escrow."""
        self._require_active()
        buyer = self._sender()
        if buyer == worker:
            self._fail("Cannot hire yourself")
        if worker not in self.agents:
            self._fail("Worker is not a registered agent")
        worker_agent = self.agents[worker]
        if not worker_agent.active:
            self._fail("Worker is inactive")
        if worker_agent.fingerprint_status != "verified":
            self._fail("Worker fingerprint must be verified before hiring")
        amount = int(budget)
        if amount <= 0:
            self._fail("Budget must be positive")
        self._debit(buyer, amount)

        job_id = int(self.next_job_id)
        job = Job(
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
            delivered_on_time=False,
            quality_score=u256(0),
            sla_met=False,
            settlement_note="",
            buyer_payout=u256(0),
            worker_payout=u256(0),
        )
        self.jobs[str(job_id)] = job
        self.job_keys.append(str(job_id))
        self.next_job_id = u256(job_id + 1)
        self.total_jobs = u256(int(self.total_jobs) + 1)
        self.total_escrowed = u256(int(self.total_escrowed) + amount)
        return {
            "job_id": job_id,
            "status": "escrowed",
            "buyer": buyer,
            "worker": worker,
            "worker_agent_id": int(worker_agent.agent_id),
            "budget": amount,
            "worker_trust": int(worker_agent.trust_score),
        }

    @gl.public.write
    def submit_delivery(self, job_id: str, evidence: str, delivered_on_time: bool) -> dict:
        self._require_active()
        if job_id not in self.jobs:
            self._fail("Job not found")
        job = self.jobs[job_id]
        sender = self._sender()
        if sender != job.worker:
            self._fail("Only the hired agent can deliver")
        if job.status not in ("escrowed", "delivered"):
            self._fail("Job is not awaiting delivery")
        if len(evidence.strip()) < 10:
            self._fail("Evidence is too short")
        job.evidence = evidence.strip()
        job.delivered_on_time = delivered_on_time
        job.status = "delivered"
        self.jobs[job_id] = job
        return {"job_id": int(job.job_id), "status": "delivered"}

    @gl.public.write
    def accept_delivery(self, job_id: str) -> dict:
        """Buyer accepts without a dispute. Releases escrow and updates reputation."""
        self._require_active()
        if job_id not in self.jobs:
            self._fail("Job not found")
        job = self.jobs[job_id]
        if self._sender() != job.buyer:
            self._fail("Only the buyer can accept")
        if job.status != "delivered":
            self._fail("Nothing to accept")
        quality = 90 if job.delivered_on_time else 70
        return self._settle(
            job,
            worker_share=100,
            sla_met=job.delivered_on_time,
            quality=quality,
            note="Buyer accepted delivery",
            worker_failed=False,
        )

    @gl.public.write
    def verify_delivery(self, job_id: str) -> dict:
        """GenLayer validators judge evidence against the job's machine-readable terms."""
        self._require_active()
        if job_id not in self.jobs:
            self._fail("Job not found")
        job = self.jobs[job_id]
        if job.status != "delivered":
            self._fail("Job has no delivery to verify")
        worker = self.agents[job.worker]

        def analyze() -> str:
            prompt = f"""You are the settlement judge for an agent-to-agent job.

JOB TITLE: {job.title}
BRIEF: {job.brief}
MACHINE-READABLE TERMS: {job.terms}
BUDGET: {int(job.budget)}
DELIVERED ON TIME: {job.delivered_on_time}

WORKER CLAIMED MODEL: {worker.claimed_model} ({worker.fingerprint_status})

EVIDENCE / DELIVERABLE:
{job.evidence[:2500]}

Decide if the deliverable satisfies the terms. Be strict about missing artifacts and SLA.

Return ONLY JSON:
{{
  "meets_terms": <true|false>,
  "quality_score": <0-100>,
  "sla_met": <true|false>,
  "worker_share_pct": <0-100>,
  "explanation": "<one or two sentences>"
}}
"""
            return gl.nondet.exec_prompt(prompt, response_format="json")

        raw = gl.eq_principle.prompt_comparative(
            analyze,
            "quality_score and worker_share_pct should be within 10 points. meets_terms and sla_met must match.",
        )
        fallback = {
            "meets_terms": False,
            "quality_score": 50,
            "sla_met": job.delivered_on_time,
            "worker_share_pct": 50,
            "explanation": "Verification was inconclusive; escrow split.",
        }
        result = self._parse_llm_json(raw, fallback)
        quality = self._clamp(int(result.get("quality_score", 50)))
        sla_met = self._as_bool(result.get("sla_met", job.delivered_on_time), job.delivered_on_time)
        meets = self._as_bool(result.get("meets_terms", False), False)
        share = self._clamp(int(result.get("worker_share_pct", 50)))
        if meets and share < 70:
            share = 100
        if not meets and share > 70:
            share = 50
        note = str(result.get("explanation", ""))[:400]
        return self._settle(
            job,
            worker_share=share,
            sla_met=sla_met,
            quality=quality,
            note=note,
            worker_failed=share == 0,
        )

    def _settle(
        self,
        job: Job,
        worker_share: int,
        sla_met: bool,
        quality: int,
        note: str,
        worker_failed: bool,
    ) -> dict:
        if job.status in ("settled", "refunded"):
            self._fail("Job already settled")
        escrow = int(job.escrowed)
        share = self._clamp(worker_share)
        worker_payout = escrow * share // 100
        buyer_payout = escrow - worker_payout
        self._credit(job.worker, worker_payout)
        self._credit(job.buyer, buyer_payout)

        job.status = "settled"
        job.sla_met = sla_met
        job.quality_score = u256(quality)
        job.settlement_note = note
        job.worker_payout = u256(worker_payout)
        job.buyer_payout = u256(buyer_payout)
        job.escrowed = u256(0)
        self.jobs[str(int(job.job_id))] = job
        self.total_settled = u256(int(self.total_settled) + 1)
        current_escrow = int(self.total_escrowed)
        self.total_escrowed = u256(current_escrow - escrow if current_escrow >= escrow else 0)

        if job.worker in self.agents:
            agent = self.agents[job.worker]
            if worker_failed or share < 40:
                agent.jobs_failed = u256(int(agent.jobs_failed) + 1)
                agent.tx_fail = u256(int(agent.tx_fail) + 1)
            else:
                agent.jobs_completed = u256(int(agent.jobs_completed) + 1)
                agent.tx_success = u256(int(agent.tx_success) + 1)
            if sla_met:
                agent.sla_hits = u256(int(agent.sla_hits) + 1)
            else:
                agent.sla_misses = u256(int(agent.sla_misses) + 1)
            agent = self._recompute(agent)
            self.agents[job.worker] = agent
            trust = int(agent.trust_score)
            metrics = self._agent_public(agent)["metrics"]
        else:
            trust = 0
            metrics = {}

        return {
            "job_id": int(job.job_id),
            "status": "settled",
            "worker_payout": worker_payout,
            "buyer_payout": buyer_payout,
            "sla_met": sla_met,
            "quality_score": quality,
            "explanation": note,
            "worker_trust": trust,
            "metrics": metrics,
        }

    # ── disputes ───────────────────────────────────────────

    @gl.public.write
    def file_dispute(self, job_id: str, claim: str, evidence: str) -> dict:
        self._require_active()
        if job_id not in self.jobs:
            self._fail("Job not found")
        job = self.jobs[job_id]
        sender = self._sender()
        if sender not in (job.buyer, job.worker):
            self._fail("Only job parties can dispute")
        if job.status not in ("escrowed", "delivered"):
            self._fail("Job cannot be disputed")
        dispute_id = int(self.next_dispute_id)
        dispute = Dispute(
            dispute_id=u256(dispute_id),
            job_id=job.job_id,
            filer=sender,
            claim=claim.strip(),
            evidence=evidence.strip(),
            response="",
            status="open",
            verdict="",
            buyer_share_pct=u256(0),
            note="",
        )
        job.status = "disputed"
        self.jobs[job_id] = job
        self.disputes[str(dispute_id)] = dispute
        self.dispute_keys.append(str(dispute_id))
        self.next_dispute_id = u256(dispute_id + 1)
        self.total_disputes = u256(int(self.total_disputes) + 1)
        if job.worker in self.agents:
            agent = self.agents[job.worker]
            agent.disputes_opened = u256(int(agent.disputes_opened) + 1)
            agent = self._recompute(agent)
            self.agents[job.worker] = agent
        return {"dispute_id": dispute_id, "job_id": int(job.job_id), "status": "open"}

    @gl.public.write
    def respond_to_dispute(self, dispute_id: str, response: str) -> dict:
        self._require_active()
        if dispute_id not in self.disputes:
            self._fail("Dispute not found")
        dispute = self.disputes[dispute_id]
        job = self.jobs[str(int(dispute.job_id))]
        sender = self._sender()
        if sender not in (job.buyer, job.worker) or sender == dispute.filer:
            self._fail("Only the other party can respond")
        dispute.response = response.strip()
        dispute.status = "responded"
        self.disputes[dispute_id] = dispute
        return {"dispute_id": int(dispute.dispute_id), "status": "responded"}

    @gl.public.write
    def resolve_dispute(self, dispute_id: str) -> dict:
        """LLM jury. Evidence in, split out, reputation updated."""
        self._require_active()
        if dispute_id not in self.disputes:
            self._fail("Dispute not found")
        dispute = self.disputes[dispute_id]
        if dispute.status not in ("open", "responded"):
            self._fail("Dispute already resolved")
        job = self.jobs[str(int(dispute.job_id))]

        def analyze() -> str:
            prompt = f"""You are an on-chain jury for an agent-to-agent commerce dispute.

JOB: {job.title}
TERMS: {job.terms}
BRIEF: {job.brief}
BUDGET: {int(job.budget)}
DELIVERY EVIDENCE: {job.evidence[:1800]}
DELIVERED ON TIME: {job.delivered_on_time}

FILER: {dispute.filer}
CLAIM: {dispute.claim}
FILER EVIDENCE: {dispute.evidence[:1200]}
RESPONSE: {dispute.response[:1200]}

Verdict must be buyer, worker, or split.
buyer_share_pct is the percent of escrow returned to the buyer (0-100).

Return ONLY JSON:
{{
  "verdict": "<buyer|worker|split>",
  "buyer_share_pct": <0-100>,
  "sla_met": <true|false>,
  "explanation": "<one or two sentences>"
}}
"""
            return gl.nondet.exec_prompt(prompt, response_format="json")

        raw = gl.eq_principle.prompt_comparative(
            analyze,
            "buyer_share_pct within 10 points. verdict category must match: buyer, worker, or split.",
        )
        fallback = {
            "verdict": "split",
            "buyer_share_pct": 50,
            "sla_met": False,
            "explanation": "Dispute unresolved with high confidence; escrow split.",
        }
        result = self._parse_llm_json(raw, fallback)
        verdict = str(result.get("verdict", "split")).strip().lower()
        if verdict not in ("buyer", "worker", "split"):
            verdict = "split"
        buyer_share = self._clamp(int(result.get("buyer_share_pct", 50)))
        if verdict == "buyer":
            buyer_share = 100
        elif verdict == "worker":
            buyer_share = 0
        sla_met = self._as_bool(result.get("sla_met", False), False)
        note = str(result.get("explanation", ""))[:400]
        worker_share = 100 - buyer_share

        dispute.status = "resolved"
        dispute.verdict = verdict
        dispute.buyer_share_pct = u256(buyer_share)
        dispute.note = note
        self.disputes[dispute_id] = dispute

        worker_failed = worker_share < 40
        if job.worker in self.agents and verdict in ("buyer", "split") and buyer_share >= 50:
            agent = self.agents[job.worker]
            agent.disputes_lost = u256(int(agent.disputes_lost) + 1)
            self.agents[job.worker] = agent

        settled = self._settle(
            job,
            worker_share=worker_share,
            sla_met=sla_met,
            quality=self._clamp(worker_share),
            note=note,
            worker_failed=worker_failed,
        )
        settled["dispute_id"] = int(dispute.dispute_id)
        settled["verdict"] = verdict
        settled["buyer_share_pct"] = buyer_share
        return settled

    # ── matching ───────────────────────────────────────────

    @gl.public.view
    def find_agents(self, query: str, budget: str, min_trust: str) -> dict:
        """Deterministic shortlist: capability keywords + budget + trust rank."""
        max_budget = int(budget) if budget else 10**18
        floor = int(min_trust) if min_trust else 0
        ranked = []
        for key in self.agent_keys:
            if key not in self.agents:
                continue
            agent = self.agents[key]
            if not agent.active:
                continue
            if agent.fingerprint_status != "verified":
                continue
            if int(agent.trust_score) < floor:
                continue
            if query and not self._capability_hit(agent.capabilities + " " + agent.name, query):
                continue
            ranked.append(self._agent_public(agent))
        ranked.sort(key=lambda a: a["metrics"]["overall_trust"], reverse=True)
        return {
            "query": query,
            "budget": max_budget,
            "results": ranked[:12],
            "total": len(ranked),
        }

    @gl.public.view
    def match_agents(self, query: str, budget: str) -> dict:
        """LLM ranks registered agents for a natural-language hire request."""
        budget_i = int(budget) if budget else 0
        catalog = []
        for key in self.agent_keys:
            if key not in self.agents:
                continue
            agent = self.agents[key]
            if not agent.active:
                continue
            if agent.fingerprint_status != "verified":
                continue
            catalog.append(
                {
                    "agent_id": int(agent.agent_id),
                    "owner": agent.owner,
                    "name": agent.name,
                    "model": agent.claimed_model,
                    "fingerprint": agent.fingerprint_status,
                    "capabilities": agent.capabilities,
                    "trust": int(agent.trust_score),
                    "authenticity": int(agent.authenticity),
                    "reliability": int(agent.reliability),
                    "sla": int(agent.sla_score),
                }
            )
        if not catalog:
            return {"query": query, "results": [], "explanation": "No agents registered"}

        def analyze() -> str:
            prompt = f"""You match autonomous agents to a hire request.

REQUEST: {query}
BUDGET: {budget_i}

CANDIDATES:
{json.dumps(catalog)[:3500]}

Pick up to 3 agent_ids, best first. Prefer fingerprint-verified agents with higher trust when capabilities match. Do not invent ids.

Return ONLY JSON:
{{
  "agent_ids": [<int>, ...],
  "explanation": "<one sentence>"
}}
"""
            return gl.nondet.exec_prompt(prompt, response_format="json")

        raw = gl.eq_principle.prompt_comparative(
            analyze,
            "Selected agent_ids should substantially overlap. Prefer the same top agent.",
        )
        parsed = self._parse_llm_json(raw, {"agent_ids": [], "explanation": ""})
        ids = parsed.get("agent_ids") or []
        picked = []
        seen = {}
        for item in ids:
            sid = str(int(item))
            if sid in seen:
                continue
            if sid not in self.agents_by_id:
                continue
            addr = self.agents_by_id[sid]
            picked.append(self._agent_public(self.agents[addr]))
            seen[sid] = True
        if not picked:
            fallback = self.find_agents(query, budget, "0")
            return {
                "query": query,
                "budget": budget_i,
                "results": fallback["results"][:3],
                "explanation": parsed.get("explanation") or "Ranked by on-chain trust score",
                "mode": "trust_fallback",
            }
        return {
            "query": query,
            "budget": budget_i,
            "results": picked,
            "explanation": str(parsed.get("explanation", ""))[:400],
            "mode": "llm",
        }

    # ── views ──────────────────────────────────────────────

    @gl.public.view
    def get_agent(self, address: str) -> dict:
        if address not in self.agents:
            self._fail("Agent not found")
        return self._agent_public(self.agents[address])

    @gl.public.view
    def get_agent_by_id(self, agent_id: str) -> dict:
        if agent_id not in self.agents_by_id:
            self._fail("Agent not found")
        return self._agent_public(self.agents[self.agents_by_id[agent_id]])

    @gl.public.view
    def list_agents(self) -> dict:
        out = []
        for key in self.agent_keys:
            if key in self.agents and self.agents[key].fingerprint_status == "verified":
                out.append(self._agent_public(self.agents[key]))
        out.sort(key=lambda a: a["metrics"]["overall_trust"], reverse=True)
        return {"agents": out, "total": len(out)}

    @gl.public.view
    def get_job(self, job_id: str) -> dict:
        if job_id not in self.jobs:
            self._fail("Job not found")
        job = self.jobs[job_id]
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
            "delivered_on_time": job.delivered_on_time,
            "quality_score": int(job.quality_score),
            "sla_met": job.sla_met,
            "settlement_note": job.settlement_note,
            "buyer_payout": int(job.buyer_payout),
            "worker_payout": int(job.worker_payout),
        }

    @gl.public.view
    def list_jobs(self) -> dict:
        out = []
        for key in self.job_keys:
            if key in self.jobs:
                out.append(self.get_job(key))
        return {"jobs": out, "total": len(out)}

    @gl.public.view
    def get_dispute(self, dispute_id: str) -> dict:
        if dispute_id not in self.disputes:
            self._fail("Dispute not found")
        d = self.disputes[dispute_id]
        return {
            "dispute_id": int(d.dispute_id),
            "job_id": int(d.job_id),
            "filer": d.filer,
            "claim": d.claim,
            "evidence": d.evidence,
            "response": d.response,
            "status": d.status,
            "verdict": d.verdict,
            "buyer_share_pct": int(d.buyer_share_pct),
            "note": d.note,
        }

    @gl.public.view
    def list_disputes(self) -> dict:
        out = []
        for key in self.dispute_keys:
            if key in self.disputes:
                out.append(self.get_dispute(key))
        return {"disputes": out, "total": len(out)}

    @gl.public.view
    def get_status(self) -> dict:
        return {
            "paused": self.is_paused,
            "owner": str(self.owner),
            "agents": int(self.total_agents),
            "jobs": int(self.total_jobs),
            "settled": int(self.total_settled),
            "disputes": int(self.total_disputes),
            "escrowed": int(self.total_escrowed),
        }

    @gl.public.write
    def pause(self, reason: str) -> dict:
        if gl.message.sender_address != self.owner:
            self._fail("Only owner")
        self.is_paused = True
        return {"paused": True, "reason": reason}

    @gl.public.write
    def resume(self, justification: str) -> dict:
        if gl.message.sender_address != self.owner:
            self._fail("Only owner")
        self.is_paused = False
        return {"paused": False, "justification": justification}
