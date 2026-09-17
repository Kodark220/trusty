# Agent Tank submission copy

Portal: https://portal.genlayer.foundation/agent-tank/hackathon/submit?track=Agentic%20Commerce%20Infrastructure

**Track:** Agentic Commerce Infrastructure

**Project name:** AgentTrust

**One-liner:** A trust layer for the agent economy — verify what an agent is, measure how it behaves, and let its reputation follow it everywhere.

**GitHub:** https://github.com/Kodark220/trusty

**Website / demo:** frontend at http://localhost:3100 (deploy to Vercel/Fly after `npm run build`)

## Concise Copy (< 500 characters)

AgentTrust is a verifiable trust & reputation layer for the AI agent economy. GenLayer validators verify claimed agent models via challenge fingerprinting, judge job deliverables against machine-readable SLA terms, and execute escrow payouts. Overall trust is calculated deterministically across 5 metrics: Model Authenticity (20%), Reliability (25%), SLA (20%), Transaction Success (20%), and Dispute History (15%).

## Description (paste)

Agents can already find each other, invoice each other, and pay each other. They cannot carry a file that says who they actually are and how they have behaved.

AgentTrust is that file.

Every agent has two layers:

1. **Claim** — model, provider, version, capabilities, identity.
2. **Conduct** — jobs, SLA, settlements, disputes, fingerprint checks.

The fingerprint is not a bio. GenLayer validators compare challenge outputs (and an optional public model card) to the claimed model. Verified, mismatched, or inconclusive. Unverified authenticity is 0. That number is 20% of overall trust, so lying about GPT-5.6 is expensive.

Reputation is not a vibe. After every escrowed job:

- terms met → pay worker, reliability / SLA / transaction scores up
- SLA miss → partial refund, scores down
- dispute → LLM jury, lost cases cut dispute history harder than opened ones

Overall trust is a weighted average, not a black box:

Model authenticity 20 · Reliability 25 · SLA 20 · Transaction success 20 · Dispute history 15

A buyer agent can query “analyze 10,000 documents, budget $200” and hire the highest-trust match with escrow in the same protocol. Selection, work, verification, settlement, and the next reputation write are one object.

This is the model-fingerprinting verifier the track asked for, welded to SLA escrow, portable identity, and onchain justice — because fingerprinting alone does not tell you if the agent shows up.

## How to demo

1. Open the dashboard. Agent #4821 is Ledger, GPT-5.6, fingerprint verified, trust 97.
2. Hire: paste the 10k-document query, match, escrow $200 on Ledger.
3. Jobs: deliver on time → validators “terms met” → watch trust tick.
4. Reset, hire again, deliver late / fail verification → partial refund, scores drop.
5. Register a new agent: authenticity 0 until you run the fingerprint.

## Technical facts

- Intelligent Contract: `contracts/AgentTrust.py`
- Runner: `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6` (networks reject `test` / `latest`)
- Equivalence: comparative on fingerprint, delivery, dispute, match — validators rerun the task
- Errors: `gl.vm.UserError` with `[EXPECTED]` / `[LLM_ERROR]` prefixes
- Web: `gl.nondet.web.render` of the model card during fingerprinting
- Deterministic score math in `tests/test_reputation.py` (pitch example 98/96/99/97/94 → 97)
- Agent skill: `skills/agenttrust/SKILL.md`
