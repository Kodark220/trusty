export function clamp(n: number) {
  return Math.max(0, Math.min(100, Math.round(n)))
}

export function bayes(success: number, fail: number, prior = 70, strength = 3) {
  const total = success + fail
  return Math.floor((success * 100 + prior * strength) / (total + strength))
}

export function authenticityFromFingerprint(status: string, score: number) {
  if (status === 'verified') return score
  if (status === 'mismatched') return clamp(Math.floor(score / 2))
  if (status === 'inconclusive') return 40
  return 0
}

export function disputeScore(lost: number, opened: number) {
  return clamp(100 - lost * 8 - opened * 2)
}

export function overall(auth: number, rel: number, sla: number, tx: number, disp: number) {
  const weighted = auth * 20 + rel * 25 + sla * 20 + tx * 20 + disp * 15
  return clamp(Math.floor((weighted + 50) / 100))
}

export function recompute(agent: {
  fingerprint_status: string
  fingerprint_score: number
  jobs_completed: number
  jobs_failed: number
  sla_hits: number
  sla_misses: number
  tx_success: number
  tx_fail: number
  disputes_opened: number
  disputes_lost: number
}) {
  const authenticity = authenticityFromFingerprint(agent.fingerprint_status, agent.fingerprint_score)
  const reliability = bayes(agent.jobs_completed, agent.jobs_failed)
  const sla = bayes(agent.sla_hits, agent.sla_misses)
  const tx = bayes(agent.tx_success, agent.tx_fail)
  const disp = disputeScore(agent.disputes_lost, agent.disputes_opened)
  return {
    model_authenticity: authenticity,
    reliability,
    sla_performance: sla,
    transaction_success: tx,
    dispute_history: disp,
    overall_trust: overall(authenticity, reliability, sla, tx, disp),
  }
}

export function rate(success: number, fail: number) {
  const total = success + fail
  if (!total) return 0
  return Math.floor((success * 1000) / total)
}
