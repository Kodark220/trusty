"""Direct coverage for the live escrow's automatic settlement workflow."""

import json


DELIVERY = json.dumps(
    json.dumps(
        {
            "worker_share_pct": 100,
            "explanation": "The evidence satisfies the agreed deliverable.",
        }
    )
)


def test_delivery_settles_without_buyer_verification(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = direct_deploy("contracts/AgentEscrowBradbury.py")

    direct_vm.sender = direct_alice
    direct_vm.value = 200
    buyer = contract.deposit()["address"]
    direct_vm.value = 0

    direct_vm.sender = direct_bob
    direct_vm.value = 1
    worker = contract.deposit()["address"]
    direct_vm.value = 0

    direct_vm.sender = direct_alice
    hired = contract.hire(worker, "Document analysis", "Analyze the corpus", "Return a JSONL report.", "200")
    assert hired["status"] == "escrowed"

    direct_vm.sender = direct_bob
    direct_vm.mock_llm(r".*Evaluate this agent delivery.*", DELIVERY)
    settled = contract.submit_delivery(str(hired["job_id"]), "manifest sha256 and complete JSONL report")

    assert settled["status"] == "settled"
    assert settled["worker_payout"] == 200
    assert settled["buyer_payout"] == 0
    assert contract.get_job(str(hired["job_id"]))["status"] == "settled"
    assert buyer != worker