#!/usr/bin/env python3
"""Walk the AgentTrust loop with the same numbers as the pitch."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.test_reputation import authenticity_from_fingerprint, bayes, dispute_score, overall


def card(agent_id, model, fp, jobs, success, sla, disputes, metrics):
    print(f"\nAgent #{agent_id}")
    print(f"Model: {model} — fingerprint {fp}")
    print(f"Jobs: {jobs}")
    print(f"Success rate: {success}")
    print(f"SLA: {sla}")
    print(f"Disputes: {disputes}")
    print(f"Reputation: {metrics['overall']}/100")
    print("  authenticity {a}  reliability {r}  sla {s}  tx {t}  disputes {d}".format(
        a=metrics["auth"], r=metrics["rel"], s=metrics["sla"], t=metrics["tx"], d=metrics["disp"]
    ))


def metrics(fp_status, fp_score, completed, failed, sla_hits, sla_misses, tx_ok, tx_bad, lost, opened):
    auth = authenticity_from_fingerprint(fp_status, fp_score)
    rel = bayes(completed, failed)
    sla = bayes(sla_hits, sla_misses)
    tx = bayes(tx_ok, tx_bad)
    disp = dispute_score(lost, opened)
    return {
        "auth": auth,
        "rel": rel,
        "sla": sla,
        "tx": tx,
        "disp": disp,
        "overall": overall(auth, rel, sla, tx, disp),
    }


def main():
    print("QUERY")
    print('  "Find me an agent capable of analyzing 10,000 documents with a budget of $200."')

    a = metrics("verified", 98, 180, 4, 178, 2, 180, 4, 0, 3)
    b = metrics("verified", 91, 62, 6, 60, 5, 61, 7, 1, 4)
    c = metrics("unverified", 0, 21, 8, 18, 9, 20, 9, 2, 5)

    print("\nSHORTLIST (trust desc)")
    card(4821, "GPT-5.6", "verified", 184, "97.8%", "99.2%", 3, a)
    card(1904, "Claude 4.1", "verified", 68, "91.2%", "92.3%", 4, b)
    card(773, "Mixtral-finetune", "unverified", 29, "72.4%", "66.7%", 5, c)

    print("\nHIRE Agent #4821")
    print("  $200 escrowed")
    print("  terms: 10k documents, structured JSON, 4h SLA")

    print("\nDELIVER + VERIFY")
    print("  evidence: 10,000-row JSONL + SHA256 manifest")
    print("  validators: meets_terms=true, sla_met=true, quality=94")
    print("  $200 released to worker")

    after = metrics("verified", 98, 181, 4, 179, 2, 181, 4, 0, 3)
    print("\nREPUTATION UPDATE")
    print(f"  {a['overall']} → {after['overall']}")

    print("\nCOUNTERFACTUAL: missed SLA, 40% refund")
    miss = metrics("verified", 98, 180, 5, 178, 3, 180, 5, 0, 3)
    print(f"  trust would fall {a['overall']} → {miss['overall']}")


if __name__ == "__main__":
    main()
