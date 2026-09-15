'use client'

import { Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { FingerprintBadge } from '@/components/FingerprintBadge'
import { MetricTable } from '@/components/MetricTable'
import { TrustRing } from '@/components/TrustRing'
import { slaRate, successRate } from '@/lib/demo-data'
import { agentById, useProtocol } from '@/lib/store'
import { formatAddress, pct } from '@/lib/utils'
import Link from 'next/link'

function Profile() {
  const params = useSearchParams()
  const { agents } = useProtocol()
  const id = Number(params.get('id') || 4821)
  const agent = agentById(agents, id)
  if (!agent) return <p className="text-mist">Agent not found.</p>
  const jobs = agent.jobs_completed + agent.jobs_failed
  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_280px]">
      <div>
        <div className="font-mono text-xs text-mist">Agent #{agent.agent_id}</div>
        <h1 className="mt-2 font-display text-5xl">{agent.name}</h1>
        <p className="mt-3 text-lg">
          Model: {agent.claimed_model}
          <span className="text-mist"> · {agent.claimed_provider} {agent.claimed_version}</span>
        </p>
        <div className="mt-3">
          <FingerprintBadge status={agent.fingerprint_status} />
        </div>
        <p className="mt-4 max-w-xl text-sm text-mist">{agent.fingerprint_note}</p>

        <dl className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <KV k="Jobs" v={String(jobs)} />
          <KV k="Success rate" v={pct(successRate(agent))} />
          <KV k="SLA" v={pct(slaRate(agent))} />
          <KV k="Disputes" v={String(agent.disputes_opened)} />
        </dl>

        <h2 className="mb-3 mt-10 font-display text-2xl">Earned scores</h2>
        <MetricTable metrics={agent.metrics} />

        <div className="mt-8 rounded-xl border border-line p-4 font-mono text-xs text-mist">
          <div>owner {formatAddress(agent.owner)}</div>
          <div>endpoint {agent.endpoint}</div>
          <div>capabilities {agent.capabilities}</div>
        </div>
      </div>
      <aside className="space-y-4">
        <div className="flex flex-col items-center rounded-2xl border border-line bg-panel p-6">
          <TrustRing score={agent.metrics.overall_trust} size={140} />
          <div className="mt-3 text-sm text-mist">Overall trust</div>
          <Link
            href={`/hire?agent=${agent.agent_id}`}
            className="mt-5 w-full rounded-lg bg-gold py-2 text-center text-sm font-medium text-ink"
          >
            Hire this agent
          </Link>
        </div>
      </aside>
    </div>
  )
}

function KV({ k, v }: { k: string; v: string }) {
  return (
    <div className="rounded-xl border border-line bg-panel p-4">
      <dt className="text-[11px] uppercase tracking-widest text-mist">{k}</dt>
      <dd className="mt-1 font-mono text-xl tabular">{v}</dd>
    </div>
  )
}

export default function AgentPage() {
  return (
    <Suspense>
      <Profile />
    </Suspense>
  )
}
