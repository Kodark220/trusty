# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import json


class AgentDeliveryVerifierBradbury(gl.Contract):
    """Small Bradbury verifier kept separate from escrow state and payouts."""

    def __init__(self):
        pass

    def _clamp(self, value: int) -> int:
        return max(0, min(100, value))

    @gl.public.write
    def judge(self, title: str, terms: str, evidence: str) -> dict:
        if len(terms.strip()) < 5 or len(evidence.strip()) < 10:
            raise gl.vm.UserError("[EXPECTED] Terms and evidence are required")

        def evaluate() -> str:
            prompt = f"""Evaluate an agent delivery against machine-readable terms.
TITLE: {title[:500]}
TERMS: {terms[:1800]}
EVIDENCE: {evidence[:2500]}
Return JSON only with worker_share_pct from 0 to 100 and explanation."""
            return gl.nondet.exec_prompt(prompt, response_format="json")

        raw = gl.eq_principle.prompt_comparative(
            evaluate,
            "worker_share_pct must be within 10 points and verdict category must agree.",
        )
        try:
            result = raw if isinstance(raw, dict) else json.loads(str(raw))
        except Exception:
            result = {"worker_share_pct": 50, "explanation": "Inconclusive; split escrow."}
        share = self._clamp(int(result.get("worker_share_pct", 50)))
        return {
            "worker_share_pct": share,
            "buyer_share_pct": 100 - share,
            "explanation": str(result.get("explanation", ""))[:400],
        }
