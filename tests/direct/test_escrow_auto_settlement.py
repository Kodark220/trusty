"""Direct coverage for the no-custody agent negotiation ledger."""


def set_sender(vm, sender):
    vm.sender = sender
    try:
        import genlayer as gl
        gl.message.sender_address = sender
    except Exception:
        pass


def test_agents_negotiate_and_record_reputation(direct_vm, direct_deploy, direct_alice, direct_bob):
    registry = direct_deploy("contracts/AgentRegistry.py")
    provider = str(direct_bob)

    set_sender(direct_vm, direct_alice)
    registry.register("Requester", "GPT-5.6", "OpenAI", "5.6", "research", "https://requester.example/api", "")
    set_sender(direct_vm, direct_bob)
    registry.register("Provider", "Claude 4.1", "Anthropic", "4.1", "document analysis", "https://provider.example/api", "")
    assert registry.list_active()["total"] == 2

    contract = direct_deploy("contracts/AgentEscrowBradbury.py")
    set_sender(direct_vm, direct_alice)
    created = contract.create_negotiation(
        "negotiation-001",
        provider,
        "Document analysis",
        "Analyze the corpus and return structured findings.",
        "JSONL output within four hours.",
        "200 USD",
    )
    assert created["status"] == "requested"

    set_sender(direct_vm, direct_bob)
    proposed = contract.propose(created["negotiation_id"], "JSONL output with source links within four hours.", "225 USD")
    assert proposed["status"] == "proposed"

    set_sender(direct_vm, direct_alice)
    agreed = contract.accept(created["negotiation_id"])
    assert agreed["status"] == "agreed"

    set_sender(direct_vm, direct_bob)
    delivered = contract.submit_outcome(created["negotiation_id"], "manifest sha256 and complete JSONL report", "Completed as agreed.")
    assert delivered["status"] == "delivered"

    set_sender(direct_vm, direct_alice)
    completed = contract.confirm_outcome(created["negotiation_id"], True, "Outcome accepted by requesting agent.")
    assert completed["status"] == "completed"
    reputation = contract.get_reputation(provider)
    assert reputation["completed"] == 1
    assert reputation["successful"] == 1
    assert reputation["disputed"] == 0