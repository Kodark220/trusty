export type FingerprintStatus = 'unverified' | 'verified' | 'mismatched' | 'inconclusive'

export type Metrics = {
  model_authenticity: number
  reliability: number
  sla_performance: number
  transaction_success: number
  dispute_history: number
  overall_trust: number
}

export type Agent = {
  agent_id: number
  owner: string
  name: string
  claimed_model: string
  claimed_provider: string
  claimed_version: string
  capabilities: string
  endpoint: string
  fingerprint_status: FingerprintStatus
  fingerprint_score: number
  fingerprint_note: string
  jobs_completed: number
  jobs_failed: number
  sla_hits: number
  sla_misses: number
  tx_success: number
  tx_fail: number
  disputes_opened: number
  disputes_lost: number
  metrics: Metrics
  active: boolean
}

export type JobStatus = 'requested' | 'proposed' | 'agreed' | 'delivered' | 'completed' | 'disputed'

export type Job = {
  job_id: number
  chain_id: string
  buyer: string
  worker: string
  title: string
  brief: string
  terms: string
  budget: number
  status: JobStatus
  evidence: string
  delivered_on_time: boolean
  quality_score: number
  sla_met: boolean
  settlement_note: string
  buyer_payout: number
  worker_payout: number
}

export type Dispute = {
  dispute_id: number
  job_id: number
  filer: string
  claim: string
  evidence: string
  response: string
  status: 'open' | 'responded' | 'resolved'
  verdict: string
  buyer_share_pct: number
  note: string
}
