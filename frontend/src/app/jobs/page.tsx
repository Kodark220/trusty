'use client'

import { Suspense, useState } from 'react'
import { useSearchParams } from 'next/navigation'
import { Pipeline } from '@/components/Pipeline'
import { agentByOwner, useProtocol } from '@/lib/store'
import { formatAddress } from '@/lib/utils'
import type { Job } from '@/lib/types'

function JobsInner() {
  const params = useSearchParams()
  const { jobs, agents, walletAddress, walletSigned, liveWithdraw, liveSubmitDelivery } = useProtocol()
  const focus = params.get('id')
  const [note, setNote] = useState('10,000-row JSONL + SHA256 manifest. All documents classified.')
  const [flash, setFlash] = useState('')
  const [withdrawAmount, setWithdrawAmount] = useState(0)

  const ordered = [...jobs].sort((a, b) => b.job_id - a.job_id)

  const onDeliver = async (job: Job) => {
    if (!walletSigned) {
      setFlash('Connect and sign with an EVM wallet before submitting delivery.')
      return
    }
    try {
      const hash = await liveSubmitDelivery(job.job_id, note)
      setFlash(`Submitted. Validators are settling automatically: ${hash.slice(0, 12)}...`)
    } catch (error: any) {
      setFlash(error.message)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-4xl">Jobs</h1>
        <p className="mt-2 text-mist">Escrow → work → verification → settlement → reputation.</p>
        <div className="mt-4">
          <Pipeline active={3} />
        </div>
      </div>
      {flash && <div className="rounded-lg border border-mint/30 bg-mint/10 px-4 py-2 text-sm text-mint">{flash}</div>}
      <section className="rounded-2xl border border-line bg-panel p-5">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
          <div>
            <div className="font-mono text-xs uppercase tracking-widest text-gold">Wallet balance</div>
            <p className="mt-1 text-sm text-mist">Withdraw settled GEN to the connected Studionet wallet.</p>
          </div>
          <div className="flex gap-2">
            <input type="number" min="0" value={withdrawAmount} onChange={(e) => setWithdrawAmount(Number(e.target.value))} className="w-28 rounded-lg border border-line bg-ink px-3 py-2 font-mono text-sm" />
            <button disabled={!walletSigned || withdrawAmount <= 0} onClick={async () => { try { const hash = await liveWithdraw(withdrawAmount); setFlash(`Withdrawal submitted: ${hash.slice(0, 12)}...`) } catch (error: any) { setFlash(error.message) } }} className="rounded-lg bg-gold px-3 py-2 text-sm font-medium text-ink disabled:opacity-40">Withdraw GEN</button>
          </div>
        </div>
      </section>
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
                <span>budget ${job.budget}</span>
                <span>escrow ${job.escrowed}</span>
                {job.status === 'settled' && (
                  <span className="text-mint">
                    paid ${job.worker_payout} / refund ${job.buyer_payout}
                  </span>
                )}
              </div>
              {job.settlement_note && <p className="mt-3 text-sm text-gold">{job.settlement_note}</p>}

              {job.status === 'escrowed' && (
                <div className="mt-4 space-y-2">
                  <textarea
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    className="h-20 w-full rounded-lg border border-line bg-ink p-3 text-sm"
                  />
                  <div className="flex gap-2">
                    <button disabled={!walletSigned} onClick={() => onDeliver(job)} className="rounded-lg bg-gold px-3 py-2 text-sm text-ink disabled:opacity-40">
                      Submit delivery
                    </button>
                  </div>
                </div>
              )}

              {job.status === 'delivered' && (
                <div className="mt-4 flex flex-wrap gap-2">
                  <p className="w-full text-sm text-mint">Automatic validator settlement is pending. No buyer approval is required.</p>
                </div>
              )}
            </article>
          )
        })}
      </div>
    </div>
  )
}

function Status({ status }: { status: string }) {
  const color =
    status === 'settled' ? 'text-mint border-mint/30' : status === 'disputed' ? 'text-red-300 border-red-400/30' : 'text-gold border-gold/30'
  return <span className={`rounded-full border px-2 py-0.5 text-[11px] uppercase tracking-widest ${color}`}>{status}</span>
}

export default function JobsPage() {
  return (
    <Suspense>
      <JobsInner />
    </Suspense>
  )
}
