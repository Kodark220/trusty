#!/usr/bin/env python3
"""Deploy AgentTrust to GenLayer Bradbury testnet."""
import json
import os
import sys
import argparse

from genlayer_py.accounts import create_account
from genlayer_py.chains import testnet_bradbury
from genlayer_py.client import create_client

PRIVATE_KEY = os.environ.get("GENLAYER_PRIVATE_KEY")
RPC = os.environ.get("GENLAYER_RPC", "https://rpc-bradbury.genlayer.com")


def main():
    parser = argparse.ArgumentParser(description="Deploy AgentTrust to GenLayer Bradbury")
    parser.add_argument(
        "--l1-timeout",
        type=int,
        default=1800,
        help="Seconds to wait for the Bradbury L1 receipt inside genlayer_py",
    )
    parser.add_argument(
        "--consensus-retries",
        type=int,
        default=600,
        help="Consensus receipt polling attempts after the L1 transaction is mined",
    )
    parser.add_argument(
        "--priority-fee-gwei",
        type=int,
        default=5,
        help="Priority fee used to replace a stuck Bradbury transaction",
    )
    parser.add_argument(
        "--allow-pending",
        action="store_true",
        help="Submit despite queued transactions from this deployer (use only intentionally)",
    )
    args = parser.parse_args()

    if not PRIVATE_KEY:
        print("Set GENLAYER_PRIVATE_KEY")
        sys.exit(1)

    account = create_account(account_private_key=PRIVATE_KEY)
    print(f"Deployer: {account.address}")

    client = create_client(chain=testnet_bradbury, endpoint=RPC, account=account)
    latest_nonce = client.w3.eth.get_transaction_count(account.address, "latest")
    pending_nonce = client.w3.eth.get_transaction_count(account.address, "pending")
    if pending_nonce > latest_nonce and not args.allow_pending:
        print(
            f"Queued Bradbury transaction detected (latest nonce {latest_nonce}, "
            f"pending nonce {pending_nonce}). Wait for it to finalize or clear it "
            "before deploying again. Use --allow-pending only for an intentional replacement."
        )
        sys.exit(2)

    from genlayer_py.contracts import actions as contract_actions

    # genlayer_py currently hard-codes a 2 gwei priority fee. If a previous
    # deployment is stuck at the same nonce, Bradbury rejects that fee as an
    # insufficient replacement. Keep the SDK's transaction construction, but
    # raise both fee fields for this deployment.
    original_prepare = contract_actions._prepare_transaction

    def prepare_with_fee_bump(*prepare_args, **prepare_kwargs):
        transaction = original_prepare(*prepare_args, **prepare_kwargs)
        if "maxFeePerGas" in transaction:
            priority_fee = args.priority_fee_gwei * 10**9
            current_max_fee = int(transaction["maxFeePerGas"], 16)
            transaction["maxPriorityFeePerGas"] = hex(priority_fee)
            transaction["maxFeePerGas"] = hex(max(current_max_fee * 2, priority_fee * 2))
        return transaction

    contract_actions._prepare_transaction = prepare_with_fee_bump
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "contracts", "AgentTrust.py")
    with open(path, "r", encoding="utf-8") as f:
        code = f.read()

    # genlayer_py currently calls Web3's receipt waiter without a timeout,
    # which defaults to 120 seconds. Bradbury L1 inclusion can take longer.
    original_wait = client.w3.eth.wait_for_transaction_receipt

    def wait_for_l1_receipt(transaction_hash, timeout=args.l1_timeout, poll_latency=3):
        return original_wait(
            transaction_hash,
            timeout=timeout,
            poll_latency=poll_latency,
        )

    client.w3.eth.wait_for_transaction_receipt = wait_for_l1_receipt

    print("Deploying AgentTrust...")
    tx_hash = client.deploy_contract(code=code, args=[str(account.address)])
    print(f"tx: {tx_hash}")
    receipt = client.wait_for_transaction_receipt(
        transaction_hash=tx_hash,
        retries=args.consensus_retries,
    )
    address = receipt.get("recipient")
    status = receipt.get("status_name") or receipt.get("status")
    execution = receipt.get("tx_execution_result_name") or receipt.get("tx_execution_result")
    print(f"status: {status}")
    print(f"execution: {execution}")
    if status not in (None, "FINALIZED", "ACCEPTED", "SUCCESS"):
        print("Deployment did not reach a successful GenLayer status")
        sys.exit(2)
    if execution not in (None, "SUCCESS", "SUCCEEDED"):
        print("Deployment transaction finalized with an unsuccessful execution result")
        sys.exit(3)
    print(f"address: {address}")

    out = os.path.join(root, "contracts", "deployed.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(
            {
                "network": "testnetBradbury",
                "rpc": RPC,
                "address": str(address),
                "deployer": str(account.address),
                "tx": str(tx_hash),
            },
            f,
            indent=2,
        )
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
