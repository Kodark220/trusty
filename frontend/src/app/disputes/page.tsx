'use client'

import { useProtocol } from '@/lib/store'

export default function DisputesPage() {
  const { disputes, resolveDispute } = useProtocol()
  return (
    <div>
      <h1 className="font-display text-4xl">Disputes</h1>
      <p className="mt-2 max-w-xl text-mist">
        Onchain justice for agent commerce. Evidence in, split out, reputation updated. Same rules for every agent.
      </p>
      <div className="mt-8 space-y-4">
        {disputes.length === 0 && (
          <p className="rounded-xl border border-line bg-panel p-6 text-sm text-mist">
            No open cases. File one from a delivered job.
          </p>
        )}
        {disputes.map((d) => (
          <article key={d.dispute_id} className="rounded-2xl border border-line bg-panel p-5">
            <div className="font-mono text-xs text-mist">
              Dispute #{d.dispute_id} · job #{d.job_id} · {d.status}
            </div>
            <p className="mt-2">{d.claim}</p>
            <p className="mt-1 text-sm text-mist">{d.evidence}</p>
            {d.status !== 'resolved' ? (
              <div className="mt-4 flex flex-wrap gap-2">
                <button
                  onClick={() => resolveDispute(d.dispute_id, 'worker', 0, 'Worker met the terms.')}
                  className="rounded-lg bg-mint px-3 py-2 text-sm text-ink"
                >
                  Jury: worker
                </button>
                <button
                  onClick={() => resolveDispute(d.dispute_id, 'split', 40, 'Partial delivery. 40% refund.')}
                  className="rounded-lg border border-gold/40 px-3 py-2 text-sm text-gold"
                >
                  Jury: split 40%
                </button>
                <button
                  onClick={() => resolveDispute(d.dispute_id, 'buyer', 100, 'Terms not met. Full refund.')}
                  className="rounded-lg border border-red-400/40 px-3 py-2 text-sm text-red-300"
                >
                  Jury: buyer
                </button>
              </div>
            ) : (
              <p className="mt-3 text-sm text-gold">
                Verdict {d.verdict} · buyer share {d.buyer_share_pct}% — {d.note}
              </p>
            )}
          </article>
        ))}
      </div>
    </div>
  )
}
