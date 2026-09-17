"""End-to-end protocol loop against the real AgentTrust.py source."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import fake_genlayer as fg  # noqa: E402

sys.modules["genlayer"] = fg
sys.modules["genlayer.storage"] = fg.storage

# Load the contract as if `from genlayer import *` resolved to our fake.
import importlib.util

spec = importlib.util.spec_from_file_location("agenttrust_contract", ROOT / "contracts" / "AgentTrust.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
AgentTrust = mod.AgentTrust

OWNER = fg.Address("0xOWNER0000000000000000000000000000000001")
BUYER = fg.Address("0xBUYER0000000000000000000000000000000002")
WORKER = fg.Address("0xWORK00000000000000000000000000000000003")
RIVAL = fg.Address("0xRIVAL0000000000000000000000000000000004")


def as_sender(addr):
    fg.message.sender_address = addr
    fg.gl.message.sender_address = addr


def queue_llm(payload):
    text = json.dumps(payload)
    fg.nondet._llm = lambda prompt: text
    fg.gl.nondet._llm = fg.nondet._llm


def fresh():
    as_sender(OWNER)
    return fg.boot(AgentTrust, OWNER)


def test_happy_path_register_fingerprint_hire_settle():
    c = fresh()

    as_sender(WORKER)
    agent = c.register_agent(
        "Ledger",
        "GPT-5.6",
        "OpenAI",
        "5.6",
        "document analysis, JSONL, due diligence",
        "https://agents.ledger.dev/v1",
        "https://example.com/gpt-5-6",
    )
    assert agent["agent_id"] == 1
    assert agent["fingerprint_status"] == "unverified"
    assert agent["metrics"]["model_authenticity"] == 0
    unverified_trust = agent["metrics"]["overall_trust"]

    queue_llm(
        {
            "score": 98,
            "verdict": "verified",
            "explanation": "Refusal pattern and JSON discipline match GPT-5.6.",
        }
    )
    fp = c.verify_fingerprint("structured JSON refusals and citations " * 4, "extract risk from 10k filings")
    assert fp["fingerprint_status"] == "verified"
    assert fp["fingerprint_score"] == 98
    assert fp["metrics"]["model_authenticity"] == 98
    assert fp["trust_score"] > unverified_trust

    as_sender(BUYER)
    c.deposit("200")
    assert c.get_balance(str(BUYER))["balance"] == 200

    hired = c.hire_agent(
        str(WORKER),
        "10k document analysis",
        "Find me an agent capable of analyzing 10,000 documents with a budget of $200.",
        "Return JSONL {id, summary, risk}. 4 hour SLA. SHA256 manifest required.",
        "200",
    )
    assert hired["status"] == "escrowed"
    assert hired["budget"] == 200
    assert c.get_balance(str(BUYER))["balance"] == 0
    assert c.get_status()["escrowed"] == 200

    as_sender(WORKER)
    delivered = c.submit_delivery(
        str(hired["job_id"]),
        "10,000-row JSONL + sha256 manifest abcdef",
        True,
    )
    assert delivered["status"] == "delivered"

    as_sender(BUYER)
    queue_llm(
        {
            "meets_terms": True,
            "quality_score": 94,
            "sla_met": True,
            "worker_share_pct": 100,
            "explanation": "Deliverable meets machine-readable terms.",
        }
    )
    settled = c.verify_delivery(str(hired["job_id"]))
    assert settled["status"] == "settled"
    assert settled["worker_payout"] == 200
    assert settled["buyer_payout"] == 0
    assert c.get_balance(str(WORKER))["balance"] == 200
    assert c.get_status()["escrowed"] == 0

    after = c.get_agent(str(WORKER))
    assert after["jobs_completed"] == 1
    assert after["jobs_failed"] == 0
    assert after["metrics"]["overall_trust"] > 0


def test_unverified_ranks_below_verified():
    c = fresh()
    as_sender(WORKER)
    c.register_agent("Ledger", "GPT-5.6", "OpenAI", "5.6", "document analysis", "", "")
    queue_llm({"score": 98, "verdict": "verified", "explanation": "match"})
    c.verify_fingerprint("sample output that is long enough here", "challenge")
    verified = c.get_agent(str(WORKER))

    as_sender(RIVAL)
    c.register_agent("Nimbus", "Mixtral-finetune", "Self-hosted", "ft", "document analysis", "", "")
    unverified = c.get_agent(str(RIVAL))

    ranked = c.find_agents("document analysis", "200", "0")["results"]
    assert ranked[0]["owner"] == str(WORKER)
    assert verified["metrics"]["overall_trust"] > unverified["metrics"]["overall_trust"]
    assert unverified["metrics"]["model_authenticity"] == 0


def test_sla_miss_partial_refund_drops_score():
    c = fresh()
    as_sender(WORKER)
    c.register_agent("Ledger", "GPT-5.6", "OpenAI", "5.6", "docs", "", "")
    queue_llm({"score": 98, "verdict": "verified", "explanation": "ok"})
    before = c.verify_fingerprint("sample output that is long enough here", "q")

    as_sender(BUYER)
    c.deposit("500")
    job = c.hire_agent(str(WORKER), "job", "brief", "4h SLA", "500")
    as_sender(WORKER)
    c.submit_delivery(str(job["job_id"]), "late incomplete artifact xx", False)
    as_sender(BUYER)
    queue_llm(
        {
            "meets_terms": False,
            "quality_score": 40,
            "sla_met": False,
            "worker_share_pct": 60,
            "explanation": "SLA missed. Partial refund.",
        }
    )
    settled = c.verify_delivery(str(job["job_id"]))
    assert settled["worker_payout"] == 300
    assert settled["buyer_payout"] == 200
    after = c.get_agent(str(WORKER))
    assert after["sla_misses"] == 1
    assert after["metrics"]["overall_trust"] <= before["trust_score"]


def test_dispute_split_updates_dispute_history():
    c = fresh()
    as_sender(WORKER)
    c.register_agent("Ledger", "GPT-5.6", "OpenAI", "5.6", "docs", "", "")
    queue_llm({"score": 90, "verdict": "verified", "explanation": "ok"})
    c.verify_fingerprint("sample output that is long enough here", "q")

    as_sender(BUYER)
    c.deposit("100")
    job = c.hire_agent(str(WORKER), "job", "brief", "terms", "100")
    as_sender(WORKER)
    c.submit_delivery(str(job["job_id"]), "partial evidence here", True)

    as_sender(BUYER)
    d = c.file_dispute(str(job["job_id"]), "Missing required JSONL", "no manifest")
    assert d["status"] == "open"
    as_sender(WORKER)
    c.respond_to_dispute(str(d["dispute_id"]), "Rows were delivered via endpoint")
    as_sender(BUYER)
    queue_llm(
        {
            "verdict": "split",
            "buyer_share_pct": 40,
            "sla_met": False,
            "explanation": "Partial delivery. 40% refund.",
        }
    )
    out = c.resolve_dispute(str(d["dispute_id"]))
    assert out["verdict"] == "split"
    assert out["buyer_share_pct"] == 40
    assert out["buyer_payout"] == 40
    assert out["worker_payout"] == 60
    worker = c.get_agent(str(WORKER))
    assert worker["disputes_opened"] == 1
    # Worker still received 60%, so this is not a lost case.
    assert worker["disputes_lost"] == 0


def test_cannot_hire_self_or_unregistered():
    c = fresh()
    as_sender(BUYER)
    c.register_agent("Solo", "GPT-5.6", "OpenAI", "5.6", "docs", "", "")
    c.deposit("50")
    try:
        c.hire_agent(str(BUYER), "x", "x", "x", "50")
        raise AssertionError("should have failed")
    except fg.UserError as e:
        assert "Cannot hire yourself" in str(e)
    try:
        c.hire_agent("0xDEAD", "x", "x", "x", "50")
        raise AssertionError("should have failed")
    except fg.UserError as e:
        assert "not a registered agent" in str(e)


def test_lost_dispute_when_buyer_gets_majority():
    c = fresh()
    as_sender(WORKER)
    c.register_agent("Ledger", "GPT-5.6", "OpenAI", "5.6", "docs", "", "")
    queue_llm({"score": 90, "verdict": "verified", "explanation": "ok"})
    c.verify_fingerprint("sample output that is long enough here", "q")
    as_sender(BUYER)
    c.deposit("100")
    job = c.hire_agent(str(WORKER), "job", "brief", "terms", "100")
    as_sender(WORKER)
    c.submit_delivery(str(job["job_id"]), "weak evidence here", True)
    as_sender(BUYER)
    d = c.file_dispute(str(job["job_id"]), "Not delivered", "empty")
    queue_llm(
        {
            "verdict": "buyer",
            "buyer_share_pct": 100,
            "sla_met": False,
            "explanation": "Terms not met. Full refund.",
        }
    )
    out = c.resolve_dispute(str(d["dispute_id"]))
    assert out["verdict"] == "buyer"
    assert out["buyer_payout"] == 100
    worker = c.get_agent(str(WORKER))
    assert worker["disputes_lost"] == 1
    assert worker["jobs_failed"] == 1


def test_match_falls_back_when_llm_ids_invalid():
    c = fresh()
    as_sender(WORKER)
    c.register_agent("Ledger", "GPT-5.6", "OpenAI", "5.6", "document analysis JSONL", "", "")
    queue_llm({"score": 98, "verdict": "verified", "explanation": "ok"})
    c.verify_fingerprint("sample output that is long enough here", "q")
    queue_llm({"agent_ids": [9999], "explanation": "hallucinated"})
    matched = c.match_agents("analyze 10000 documents", "200")
    assert matched["mode"] == "trust_fallback"
    assert matched["results"][0]["name"] == "Ledger"


if __name__ == "__main__":
    tests = [
        test_happy_path_register_fingerprint_hire_settle,
        test_unverified_ranks_below_verified,
        test_sla_miss_partial_refund_drops_score,
        test_dispute_split_updates_dispute_history,
        test_lost_dispute_when_buyer_gets_majority,
        test_cannot_hire_self_or_unregistered,
        test_match_falls_back_when_llm_ids_invalid,
    ]
    failed = 0
    for fn in tests:
        try:
            fn()
            print("PASS", fn.__name__)
        except Exception as e:
            failed += 1
            print("FAIL", fn.__name__, type(e).__name__, e)
    if failed:
        sys.exit(1)
    print("E2E OK", len(tests), "scenarios")
