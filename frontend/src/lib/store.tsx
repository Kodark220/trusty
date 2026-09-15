'use client'

import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import { AGENT_A, seedAgents, seedJobs, YOU } from './demo-data'
import { recompute } from './reputation'
import type { Agent, Dispute, Job } from './types'
import { connectBradbury, escrowWrite, registryWrite } from './live'

type Protocol = {
  you: string
  agents: Agent[]
  jobs: Job[]
  disputes: Dispute[]
  balances: Record<string, number>
  register: (input: Omit<Agent, 'agent_id' | 'metrics' | 'fingerprint_status' | 'fingerprint_score' | 'fingerprint_note' | 'jobs_completed' | 'jobs_failed' | 'sla_hits' | 'sla_misses' | 'tx_success' | 'tx_fail' | 'disputes_opened' | 'disputes_lost' | 'active'>) => Agent
  verifyFingerprint: (owner: string, note: string, score: number, status: Agent['fingerprint_status']) => Agent
  find: (query: string, budget: number) => Agent[]
  hire: (worker: string, title: string, brief: string, terms: string, budget: number) => Job
  deliver: (jobId: number, evidence: string, onTime: boolean) => Job
  verify: (jobId: number, ok: boolean, sla: boolean, quality: number, share: number, note: string) => Job
  fileDispute: (jobId: number, claim: string, evidence: string) => Dispute
  resolveDispute: (disputeId: number, verdict: 'buyer' | 'worker' | 'split', buyerShare: number, note: string) => Job
  reset: () => void
  mode: 'demo' | 'live'
  walletAddress: string | null
  walletSigned: boolean
  connectWallet: () => Promise<void>
  signWallet: () => Promise<void>
  disconnectWallet: () => void
  liveDeposit: (amount: number) => Promise<string>
  liveHire: (worker: string, title: string, brief: string, terms: string, budget: number) => Promise<string>
  liveWithdraw: (amount: number) => Promise<string>
  liveSubmitDelivery: (jobId: number, evidence: string) => Promise<string>
  liveRegister: (name: string, model: string, provider: string, version: string, capabilities: string, endpoint: string) => Promise<string>
  liveVerifyFingerprint: (sample: string, challenge: string) => Promise<string>
}

const KEY = 'agenttrust.v1'
const ProtocolContext = createContext<Protocol | null>(null)

function persist(data: { agents: Agent[]; jobs: Job[]; disputes: Dispute[]; balances: Record<string, number> }) {
  if (typeof window === 'undefined') return
  localStorage.setItem(KEY, JSON.stringify(data))
}

function load() {
  if (typeof window === 'undefined') return null
  try {
    const raw = localStorage.getItem(KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch {
    return null
  }
}

function refresh(agent: Agent): Agent {
  return { ...agent, metrics: recompute(agent) }
}

export function ProtocolProvider({ children }: { children: React.ReactNode }) {
  const [agents, setAgents] = useState<Agent[]>(seedAgents)
  const [jobs, setJobs] = useState<Job[]>(seedJobs)
  const [disputes, setDisputes] = useState<Dispute[]>([])
  const [balances, setBalances] = useState<Record<string, number>>({ [YOU]: 2500 })
  const [hydrated, setHydrated] = useState(false)
  const [mode, setMode] = useState<'demo' | 'live'>('live')
  const [walletAddress, setWalletAddress] = useState<string | null>(null)
  const [wallet, setWallet] = useState<Parameters<typeof escrowWrite>[0] | null>(null)
  const [walletSignature, setWalletSignature] = useState<string | null>(null)

  useEffect(() => {
    const saved = load()
    if (saved?.agents) setAgents(saved.agents)
    if (saved?.jobs) setJobs(saved.jobs)
    if (saved?.disputes) setDisputes(saved.disputes)
    if (saved?.balances) setBalances(saved.balances)
    setHydrated(true)
  }, [])

  useEffect(() => {
    if (!hydrated) return
    persist({ agents, jobs, disputes, balances })
  }, [agents, jobs, disputes, balances, hydrated])

  const api = useMemo<Protocol>(() => {
    const find = (query: string, _budget: number) => {
      const words = query.toLowerCase().split(/\W+/).filter((w) => w.length > 3)
      return [...agents]
        .filter((a) => a.active)
        .filter((a) => {
          if (!words.length) return true
          const hay = `${a.capabilities} ${a.name} ${a.claimed_model}`.toLowerCase()
          return words.some((w) => hay.includes(w))
        })
        .sort((a, b) => b.metrics.overall_trust - a.metrics.overall_trust)
    }

    const patchAgent = (owner: string, fn: (a: Agent) => Agent) => {
      let next: Agent | null = null
      setAgents((list) =>
        list.map((a) => {
          if (a.owner !== owner) return a
          next = refresh(fn(a))
          return next
        })
      )
      return next
    }

    const settle = (
      job: Job,
      share: number,
      sla: boolean,
      quality: number,
      note: string,
      failed: boolean
    ) => {
      const workerPay = Math.floor((job.budget * share) / 100)
      const buyerPay = job.budget - workerPay
      const settled: Job = {
        ...job,
        status: 'settled',
        escrowed: 0,
        sla_met: sla,
        quality_score: quality,
        settlement_note: note,
        worker_payout: workerPay,
        buyer_payout: buyerPay,
      }
      setJobs((list) => list.map((j) => (j.job_id === job.job_id ? settled : j)))
      setBalances((b) => ({
        ...b,
        [job.worker]: (b[job.worker] || 0) + workerPay,
        [job.buyer]: (b[job.buyer] || 0) + buyerPay,
      }))
      patchAgent(job.worker, (a) => ({
        ...a,
        jobs_completed: a.jobs_completed + (failed ? 0 : 1),
        jobs_failed: a.jobs_failed + (failed ? 1 : 0),
        tx_success: a.tx_success + (failed ? 0 : 1),
        tx_fail: a.tx_fail + (failed ? 1 : 0),
        sla_hits: a.sla_hits + (sla ? 1 : 0),
        sla_misses: a.sla_misses + (sla ? 0 : 1),
      }))
      return settled
    }

    return {
      you: YOU,
      mode,
      walletAddress,
      walletSigned: Boolean(walletSignature),
      connectWallet: async () => {
        const connected = await connectBradbury()
        setWalletAddress(connected.address)
        setWallet(connected.wallet)
        setWalletSignature(null)
        setMode('live')
      },
      signWallet: async () => {
        if (!wallet || !walletAddress) throw new Error('Connect MetaMask first.')
        const signature = await wallet.request({
          method: 'personal_sign',
          params: [`Sign in to AgentTrust on GenLayer Studio Next\n\nWallet: ${walletAddress}`, walletAddress],
        })
        if (typeof signature !== 'string' || !signature) throw new Error('Wallet signature was not completed.')
        setWalletSignature(signature)
      },
      disconnectWallet: () => {
        setWalletAddress(null)
        setWallet(null)
        setWalletSignature(null)
        setMode('live')
      },
      liveDeposit: async (amount) => {
        if (!wallet || !walletAddress || !walletSignature) throw new Error('Connect and sign with MetaMask first.')
        const result = await escrowWrite(wallet, walletAddress, 'deposit', [], BigInt(amount) * BigInt(10 ** 18))
        return result.hash
      },
      liveHire: async (worker, title, brief, terms, budget) => {
        if (!wallet || !walletAddress || !walletSignature) throw new Error('Connect and sign with MetaMask first.')
        const budgetWei = BigInt(budget) * BigInt(10 ** 18)
        const result = await escrowWrite(wallet, walletAddress, 'hire', [worker, title, brief, terms, budgetWei.toString()])
        return result.hash
      },
      liveWithdraw: async (amount) => {
        if (!wallet || !walletAddress || !walletSignature) throw new Error('Connect and sign with MetaMask first.')
        const result = await escrowWrite(wallet, walletAddress, 'withdraw', [String(amount) + '000000000000000000'])
        return result.hash
      },
      liveSubmitDelivery: async (jobId, evidence) => {
        if (!wallet || !walletAddress || !walletSignature) throw new Error('Connect and sign with MetaMask first.')
        const result = await escrowWrite(wallet, walletAddress, 'submit_delivery', [String(jobId), evidence])
        return result.hash
      },
      liveRegister: async (name, model, provider, version, capabilities, endpoint) => {
        if (!wallet || !walletAddress || !walletSignature) throw new Error('Connect and sign with MetaMask first.')
        const result = await registryWrite(wallet, walletAddress, 'register', [name, model, provider, version, capabilities, endpoint, ''])
        return result.hash
      },
      liveVerifyFingerprint: async (sample, challenge) => {
        if (!wallet || !walletAddress || !walletSignature) throw new Error('Connect and sign with MetaMask first.')
        const result = await registryWrite(wallet, walletAddress, 'verify_fingerprint', [sample, challenge])
        return result.hash
      },
      agents,
      jobs,
      disputes,
      balances,
      register: (input) => {
        const agent = refresh({
          ...input,
          agent_id: 5000 + agents.length,
          fingerprint_status: 'unverified',
          fingerprint_score: 0,
          fingerprint_note: 'No fingerprint submitted',
          jobs_completed: 0,
          jobs_failed: 0,
          sla_hits: 0,
          sla_misses: 0,
          tx_success: 0,
          tx_fail: 0,
          disputes_opened: 0,
          disputes_lost: 0,
          active: true,
          metrics: {
            model_authenticity: 0,
            reliability: 70,
            sla_performance: 70,
            transaction_success: 70,
            dispute_history: 100,
            overall_trust: 0,
          },
        })
        setAgents((list) => [agent, ...list])
        return agent
      },
      verifyFingerprint: (owner, note, score, status) => {
        const updated = patchAgent(owner, (a) => ({
          ...a,
          fingerprint_status: status,
          fingerprint_score: score,
          fingerprint_note: note,
        }))
        return updated || agents.find((a) => a.owner === owner)!
      },
      find,
      hire: (worker, title, brief, terms, budget) => {
        if ((balances[YOU] || 0) < budget) throw new Error('Insufficient balance')
        const job: Job = {
          job_id: Math.max(0, ...jobs.map((j) => j.job_id)) + 1,
          buyer: YOU,
          worker,
          title,
          brief,
          terms,
          budget,
          escrowed: budget,
          status: 'escrowed',
          evidence: '',
          delivered_on_time: false,
          quality_score: 0,
          sla_met: false,
          settlement_note: '',
          buyer_payout: 0,
          worker_payout: 0,
        }
        setBalances((b) => ({ ...b, [YOU]: (b[YOU] || 0) - budget }))
        setJobs((list) => [job, ...list])
        return job
      },
      deliver: (jobId, evidence, onTime) => {
        let next: Job | null = null
        setJobs((list) =>
          list.map((j) => {
            if (j.job_id !== jobId) return j
            next = { ...j, evidence, delivered_on_time: onTime, status: 'delivered' }
            return next
          })
        )
        return next!
      },
      verify: (jobId, ok, sla, quality, share, note) => {
        const job = jobs.find((j) => j.job_id === jobId)
        if (!job) throw new Error('Job not found')
        return settle(job, ok ? share : share, sla, quality, note, share < 40)
      },
      fileDispute: (jobId, claim, evidence) => {
        const job = jobs.find((j) => j.job_id === jobId)
        if (!job) throw new Error('Job not found')
        const dispute: Dispute = {
          dispute_id: disputes.length + 1,
          job_id: jobId,
          filer: YOU,
          claim,
          evidence,
          response: '',
          status: 'open',
          verdict: '',
          buyer_share_pct: 0,
          note: '',
        }
        setJobs((list) => list.map((j) => (j.job_id === jobId ? { ...j, status: 'disputed' } : j)))
        setDisputes((list) => [dispute, ...list])
        patchAgent(job.worker, (a) => ({ ...a, disputes_opened: a.disputes_opened + 1 }))
        return dispute
      },
      resolveDispute: (disputeId, verdict, buyerShare, note) => {
        const dispute = disputes.find((d) => d.dispute_id === disputeId)
        const job = jobs.find((j) => j.job_id === dispute?.job_id)
        if (!dispute || !job) throw new Error('Dispute not found')
        setDisputes((list) =>
          list.map((d) =>
            d.dispute_id === disputeId
              ? { ...d, status: 'resolved', verdict, buyer_share_pct: buyerShare, note }
              : d
          )
        )
        if (verdict !== 'worker' && buyerShare >= 50) {
          patchAgent(job.worker, (a) => ({ ...a, disputes_lost: a.disputes_lost + 1 }))
        }
        return settle(job, 100 - buyerShare, verdict === 'worker', 100 - buyerShare, note, 100 - buyerShare < 40)
      },
      reset: () => {
        setAgents(seedAgents)
        setJobs(seedJobs)
        setDisputes([])
        setBalances({ [YOU]: 2500 })
      },
    }
  }, [agents, jobs, disputes, balances, mode, wallet, walletAddress, walletSignature])

  return <ProtocolContext.Provider value={api}>{children}</ProtocolContext.Provider>
}

export function useProtocol() {
  const ctx = useContext(ProtocolContext)
  if (!ctx) throw new Error('ProtocolProvider missing')
  return ctx
}

export function agentByOwner(agents: Agent[], owner: string) {
  return agents.find((a) => a.owner === owner)
}

export function agentById(agents: Agent[], id: number) {
  return agents.find((a) => a.agent_id === id)
}

export { AGENT_A }
