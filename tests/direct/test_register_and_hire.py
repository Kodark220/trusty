"""Direct-mode tests (genlayer-test). Leader path only — see write-contract / direct-tests skills."""

import json

FP = json.dumps(json.dumps(
    {
        "score": 96,
        "verdict": "verified",
        "explanation": "Samples match the claimed model.",
    }
))

DELIVERY = json.dumps(json.dumps(
    {
        "meets_terms": True,
        "quality_score": 94,
        "sla_met": True,
        "worker_share_pct": 100,
        "explanation": "JSONL and manifest present.",
    }
))


def set_sender(vm, sender):
    vm.sender = sender
    try:
        import genlayer as gl
        gl.message.sender_address = sender
    except Exception:
        pass


def test_register_hire_verify(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy("contracts/AgentTrust.py", direct_alice)

    set_sender(direct_vm, direct_bob)
    registered = contract.register_agent(
        "Ledger",
        "GPT-5.6",
        "OpenAI",
        "5.6",
        "document analysis, JSONL",
        "https://agents.ledger.dev/v1",
        "",
    )
    worker = registered["owner"]

    direct_vm.mock_llm(r".*model-fingerprinting examiner.*", FP)
    contract.verify_fingerprint("structured JSON refusals and citations " * 3, "summarize this 10k corpus")
    agent = contract.get_agent(worker)
    assert agent["fingerprint_status"] == "verified"
    assert agent["metrics"]["model_authenticity"] == 96

    set_sender(direct_vm, direct_alice)
    contract.deposit("200")
    hired = contract.hire_agent(
        worker,
        "10k document analysis",
        "Analyze 10,000 documents",
        "JSONL {id, summary, risk}. 4h SLA.",
        "200",
    )
    assert hired["status"] == "escrowed"

    set_sender(direct_vm, direct_bob)
    contract.submit_delivery(str(hired["job_id"]), "manifest sha256 + 10000 rows", True)

    set_sender(direct_vm, direct_alice)
    direct_vm.mock_llm(r".*settlement judge.*", DELIVERY)
    settled = contract.verify_delivery(str(hired["job_id"]))
    assert settled["status"] == "settled"
    assert settled["worker_payout"] == 200

    after = contract.get_agent(worker)
    assert after["jobs_completed"] == 1
    assert after["metrics"]["overall_trust"] > 0


def test_unverified_authenticity_is_zero(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy("contracts/AgentTrust.py", direct_alice)
    direct_vm.sender = direct_bob
    registered = contract.register_agent("Nimbus", "Mixtral", "Self-hosted", "ft", "ocr", "", "")
    agent = contract.get_agent(registered["owner"])
    assert agent["metrics"]["model_authenticity"] == 0
    assert agent["fingerprint_status"] == "unverified"


def test_cannot_hire_self(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/AgentTrust.py", direct_alice)
    direct_vm.sender = direct_alice
    registered = contract.register_agent("Solo", "GPT-5.6", "OpenAI", "5.6", "docs", "", "")
    contract.deposit("50")
    with direct_vm.expect_revert("Cannot hire yourself"):
        contract.hire_agent(registered["owner"], "x", "x", "x", "50")
