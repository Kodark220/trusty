#!/usr/bin/env python3
"""Recover a Bradbury deployment after the SDK's 120-second L1 timeout."""
import argparse
import json
import os
import sys
import time

from genlayer_py.chains import testnet_bradbury
from genlayer_py.client import create_client
from genlayer_py.accounts import create_account
from web3.exceptions import TransactionNotFound


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tx', required=True, help='L1 transaction hash printed by deploy.py')
    parser.add_argument('--minutes', type=int, default=30)
    args = parser.parse_args()

    private_key = os.environ.get('GENLAYER_PRIVATE_KEY')
    if not private_key:
        print('Set GENLAYER_PRIVATE_KEY in this PowerShell session first.')
        return 1

    rpc = os.environ.get('GENLAYER_RPC', 'https://rpc-bradbury.genlayer.com')
    account = create_account(account_private_key=private_key)
    client = create_client(chain=testnet_bradbury, endpoint=rpc, account=account)
    client.initialize_consensus_smart_contract()

    print(f'Checking {args.tx}')
    print(f'Polling Bradbury for up to {args.minutes} minutes...')
    deadline = time.time() + args.minutes * 60
    receipt = None
    while time.time() < deadline:
        try:
            receipt = client.w3.eth.get_transaction_receipt(args.tx)
        except TransactionNotFound:
            receipt = None
        if receipt is not None:
            break
        time.sleep(10)
        print('.', end='', flush=True)

    if receipt is None:
        print('\nStill pending. Keep the transaction hash and run this command again later.')
        return 2
    if receipt.status != 1:
        print(f'\nL1 transaction failed with status {receipt.status}.')
        return 3

    event = client.w3.eth.contract(
        abi=testnet_bradbury.consensus_main_contract['abi']
    ).get_event_by_name('NewTransaction')
    events = event.process_receipt(receipt)
    if not events:
        print('\nThe L1 transaction mined but emitted no NewTransaction event.')
        return 4

    consensus_tx = client.w3.to_hex(events[0]['args']['txId'])
    print(f'\nConsensus transaction: {consensus_tx}')
    print('Waiting for GenLayer contract finalization...')
    final = client.wait_for_transaction_receipt(
        transaction_hash=consensus_tx,
        retries=max(180, args.minutes * 6),
    )
    address = final.get('recipient')
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output = os.path.join(root, 'contracts', 'deployed.json')
    with open(output, 'w', encoding='utf-8') as handle:
        json.dump({
            'network': 'testnetBradbury',
            'rpc': rpc,
            'address': str(address),
            'deployer': str(account.address),
            'l1_tx': args.tx,
            'tx': consensus_tx,
            'status': final.get('status_name') or final.get('status'),
        }, handle, indent=2)
    print(f'Contract address: {address}')
    print(f'Wrote {output}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
