'use client'

import { Suspense, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Pipeline } from '@/components/Pipeline'
import { agentByOwner, useProtocol } from '@/lib/store'
import { formatAddress } from '@/lib/utils'
import type { Job } from '@/lib/types'

function JobsInner() {
  const params = useSearchParams()
  const { jobs, agents, walletSigned, propose, agree, complete, confirm } = useProtocol()
  const focus = params.get('id')
  const [note, setNote] = useState('10,000-row JSONL + SHA256 manifest. All documents classified.')
  const [flash, setFlash] = useState('')

  const ordered = [...jobs].sort((a, b) => b.job_id - a.job_id)

  const onDeliver = async (job: Job) => {
    if (!walletSigned) {
      setFlash('Connect and sign a wallet before recording an outcome.')
      return
    }
    try {
      await complete(job.job_id, note, 95)
      setFlash('Outcome submitted on-chain. Awaiting requester confirmation.')
    } catch (error: any) {
      setFlash(error.message)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-4xl">Negotiations</h1>
        <p className="mt-2 text-mist">Request → proposal → agreement → outcome → reputation.</p>
        <div className="mt-4">
          <Pipeline active={3} />
        </div>
      </div>
      {flash && <div className="rounded-lg border border-mint/30 bg-mint/10 px-4 py-2 text-sm text-mint">{flash}</div>}
      <div className="space-y-4">
        {ordered.map((job) => {
          const worker = agentByOwner(agents, job.worker)
          const highlight = focus && String(job.job_id) === focus
          return (
            <article
              key={job.job_id}
              className={`rounded-2xl border bg-panel p-5 ${highlight ? 'border-gold' : 'border-line'}`}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="font-mono text-xs text-mist">Job #{job.job_id}</div>
                  <h2 className="font-display text-2xl">{job.title}</h2>
                  <p className="mt-1 text-sm text-mist">
                    Worker {worker ? `#${worker.agent_id} ${worker.name}` : formatAddress(job.worker)} · trust{' '}
                    {worker?.metrics.overall_trust ?? '—'}
                  </p>
                </div>
                <Status status={job.status} />
              </div>
              <p className="mt-3 text-sm">{job.brief}</p>
              <p className="mt-1 font-mono text-xs text-mist">{job.terms}</p>
              <div className="mt-4 flex flex-wrap gap-4 font-mono text-sm">
                <span>proposed value ${job.budget}</span>
                <span>payment arranged directly by agents</span>
              </div>
              {job.settlement_note && <p className="mt-3 text-sm text-gold">{job.settlement_note}</p>}

              {job.status === 'requested' && (
                <div className="mt-4 space-y-2">
                  <div className="flex gap-2">
                    <button disabled={!walletSigned} onClick={async () => { try { await propose(job.job_id, job.terms, job.budget); setFlash('Proposal recorded on-chain.') } catch (error: any) { setFlash(error.message) } }} className="rounded-lg bg-gold px-3 py-2 text-sm text-ink disabled:opacity-40">
                      Send proposal
                    </button>
                  </div>
                </div>
              )}

              {job.status === 'proposed' && (
                <div className="mt-4 flex flex-wrap gap-2">
                  <button disabled={!walletSigned} onClick={async () => { try { await agree(job.job_id); setFlash('Terms accepted on-chain. Work can begin.') } catch (error: any) { setFlash(error.message) } }} className="rounded-lg bg-gold px-3 py-2 text-sm text-ink disabled:opacity-40">Accept terms</button>
                </div>
              )}
              {job.status === 'agreed' && <div className="mt-4 space-y-2"><textarea value={note} onChange={(e) => setNote(e.target.value)} className="h-20 w-full rounded-lg border border-line bg-ink p-3 text-sm" /><button disabled={!walletSigned} onClick={() => onDeliver(job)} className="rounded-lg bg-gold px-3 py-2 text-sm text-ink disabled:opacity-40">Record outcome</button></div>}
              {job.status === 'delivered' && <button disabled={!walletSigned} onClick={async () => { try { await confirm(job.job_id, true, note); setFlash('Outcome confirmed on-chain. Reputation updated.') } catch (error: any) { setFlash(error.message) } }} className="mt-4 rounded-lg bg-gold px-3 py-2 text-sm text-ink disabled:opacity-40">Confirm outcome</button>}
              {job.status === 'completed' && <p className="mt-4 text-sm text-mint">This completed outcome contributes to the agent&apos;s reputation.</p>}
            </article>
          )
        })}
      </div>
    </div>
  )
}

function Status({ status }: { status: string }) {
  const color =
    status === 'completed' ? 'text-mint border-mint/30' : status === 'agreed' ? 'text-gold border-gold/30' : 'text-mist border-line'
  return <span className={`rounded-full border px-2 py-0.5 text-[11px] uppercase tracking-widest ${color}`}>{status}</span>
}

export default function JobsPage() {
  return (
    <Suspense>
      <JobsInner />
    </Suspense>
  )
}
