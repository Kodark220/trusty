"""Direct coverage for the standalone live agent registry."""

import json


FINGERPRINT = json.dumps(
    json.dumps(
        {
            "score": 96,
            "verdict": "verified",
            "note": "The sample is consistent with the claimed model.",
        }
    )
)


def test_register_and_verify_agent(direct_vm, direct_deploy, direct_bob):
    contract = direct_deploy("contracts/AgentRegistry.py")
    direct_vm.sender = direct_bob

    registered = contract.register(
        "Ledger",
        "GPT-5.6",
        "OpenAI",
        "5.6",
        "document analysis, JSONL",
        "https://agents.ledger.dev/v1",
        "",
    )
    assert registered["status"] == "unverified"

    direct_vm.mock_llm(r".*You verify an agent model claim.*", FINGERPRINT)
    verified = contract.verify_fingerprint("structured JSON refusals and citations " * 3, "summarize this 10k corpus")

    assert verified["status"] == "verified"
    assert verified["score"] == 96
    assert contract.list_verified()["total"] == 1