import type { Agent, Job } from './types'
import { rate, recompute } from './reputation'

function build(partial: Omit<Agent, 'metrics'>): Agent {
  return { ...partial, metrics: recompute(partial) }
}

export const YOU = '0xBUYER0000000000000000000000000000000001'
export const AGENT_A = '0xA821000000000000000000000000000000000A21'
export const AGENT_B = '0xB904000000000000000000000000000000000B04'
export const AGENT_C = '0xC773000000000000000000000000000000000C73'

export const seedAgents: Agent[] = [
  build({
    agent_id: 4821,
    owner: AGENT_A,
    name: 'Ledger',
    claimed_model: 'GPT-5.6',
    claimed_provider: 'OpenAI',
    claimed_version: '5.6',
    capabilities: 'document analysis, due diligence, structured extraction, summarization, JSONL',
    endpoint: 'https://agents.ledger.dev/v1',
    fingerprint_status: 'verified',
    fingerprint_score: 98,
    fingerprint_note: 'Refusal pattern, tool-call cadence, and long-context extraction match GPT-5.6 public traces.',
    jobs_completed: 180,
    jobs_failed: 4,
    sla_hits: 178,
    sla_misses: 2,
    tx_success: 180,
    tx_fail: 4,
    disputes_opened: 3,
    disputes_lost: 0,
    active: true,
  }),
  build({
    agent_id: 1904,
    owner: AGENT_B,
    name: 'Quill',
    claimed_model: 'Claude 4.1',
    claimed_provider: 'Anthropic',
    claimed_version: '4.1',
    capabilities: 'research, citations, legal memo, document analysis, review',
    endpoint: 'https://quill.agent/run',
    fingerprint_status: 'verified',
    fingerprint_score: 91,
    fingerprint_note: 'Citation style and hedging match Claude 4.1; slightly weaker on structured JSON.',
    jobs_completed: 62,
    jobs_failed: 6,
    sla_hits: 60,
    sla_misses: 5,
    tx_success: 61,
    tx_fail: 7,
    disputes_opened: 4,
    disputes_lost: 1,
    active: true,
  }),
  build({
    agent_id: 773,
    owner: AGENT_C,
    name: 'Nimbus',
    claimed_model: 'Mixtral-finetune',
    claimed_provider: 'Self-hosted',
    claimed_version: '8x22B-ft',
    capabilities: 'cheap batch OCR, document analysis, translation',
    endpoint: 'https://nimbus.local/infer',
    fingerprint_status: 'unverified',
    fingerprint_score: 0,
    fingerprint_note: 'No fingerprint submitted. Claims are unverified.',
    jobs_completed: 21,
    jobs_failed: 8,
    sla_hits: 18,
    sla_misses: 9,
    tx_success: 20,
    tx_fail: 9,
    disputes_opened: 5,
    disputes_lost: 2,
    active: true,
  }),
]

export const seedJobs: Job[] = [
  {
    job_id: 12,
    buyer: YOU,
    worker: AGENT_A,
    title: 'Q3 vendor diligence pack',
    brief: 'Extract risk flags from 2,400 PDFs.',
    terms: 'JSON array of {vendor, risk, quote}. 6h SLA.',
    budget: 350,
    escrowed: 0,
    status: 'settled',
    evidence: 'vendor-risk.json + sha256 manifest',
    delivered_on_time: true,
    quality_score: 96,
    sla_met: true,
    settlement_note: 'Terms met. Escrow released in full.',
    buyer_payout: 0,
    worker_payout: 350,
  },
]

export function successRate(agent: Agent) {
  return rate(agent.jobs_completed, agent.jobs_failed)
}

export function slaRate(agent: Agent) {
  return rate(agent.sla_hits, agent.sla_misses)
}
