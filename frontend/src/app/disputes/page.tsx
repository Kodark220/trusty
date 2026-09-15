'use client'

import { useProtocol } from '@/lib/store'

export default function DisputesPage() {
  const { disputes } = useProtocol()
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
              <p className="mt-4 text-sm text-mint">Consensus review is pending. Participants cannot set the verdict.</p>
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
