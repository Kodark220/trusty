import Link from 'next/link'
import type { Agent } from '@/lib/types'
import { FingerprintBadge } from './FingerprintBadge'
import { TrustRing } from './TrustRing'
import { slaRate, successRate } from '@/lib/demo-data'
import { pct } from '@/lib/utils'
import { Card } from './ui/card'

export function AgentCard({
  agent,
  compact,
  linked = true,
}: {
  agent: Agent
  compact?: boolean
  linked?: boolean
}) {
  const jobs = agent.jobs_completed + agent.jobs_failed
  const inner = (
    <>
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="font-mono text-xs text-mist">Agent #{agent.agent_id}</div>
          <div className="mt-1 font-display text-xl">{agent.name}</div>
          <div className="mt-1 text-sm text-paper/80">
            Model: {agent.claimed_model}
          </div>
          <div className="mt-2">
            <FingerprintBadge status={agent.fingerprint_status} />
          </div>
        </div>
        <TrustRing score={agent.metrics.overall_trust} size={compact ? 72 : 88} />
      </div>
      {!compact && (
        <dl className="mt-5 grid grid-cols-2 gap-x-6 gap-y-2 text-sm sm:grid-cols-4">
          <Stat label="Jobs" value={String(jobs)} />
          <Stat label="Success" value={pct(successRate(agent))} />
          <Stat label="SLA" value={pct(slaRate(agent))} />
          <Stat label="Disputes" value={String(agent.disputes_opened)} />
        </dl>
      )}
    </>
  )
  const cls = 'hairline block p-5 transition hover:border-gold/40 hover:shadow-[0_0_0_1px_rgba(201,162,39,0.12)]'
  if (!linked) return <Card className={cls}>{inner}</Card>
  return (
    <Card className={cls}>
      <Link href={`/agent?id=${agent.agent_id}`}>
        {inner}
      </Link>
    </Card>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-[11px] uppercase tracking-widest text-mist">{label}</dt>
      <dd className="font-mono tabular">{value}</dd>
    </div>
  )
}
