"""Direct coverage for the deterministic agent directory."""


def test_register_and_attest_agent(direct_vm, direct_deploy, direct_bob):
    contract = direct_deploy("contracts/AgentRegistry.py")
    direct_vm.sender = direct_bob
    assert contract.list_active() == {"agents": [], "total": 0}

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

    attested = contract.attest_capability("structured JSON refusals and citations " * 3, "Owner-attested response sample")

    assert attested["status"] == "attested"
    assert attested["fingerprint_hash"]
    assert contract.list_active()["total"] == 1
    assert contract.get_agent(registered["owner"])["status"] == "attested"