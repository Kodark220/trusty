'use client'

import { useDeferredValue, useState } from 'react'
import { AgentCard } from '@/components/AgentCard'
import { useProtocol } from '@/lib/store'

export default function DirectoryPage() {
  const { agents } = useProtocol()
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<'all' | 'verified' | 'proven'>('all')
  const deferredQuery = useDeferredValue(query.trim().toLowerCase())
  const ranked = [...agents]
    .filter((agent) => {
      const haystack = `${agent.name} ${agent.claimed_model} ${agent.claimed_provider} ${agent.capabilities}`.toLowerCase()
      return !deferredQuery || haystack.includes(deferredQuery)
    })
    .filter((agent) => filter === 'all' || (filter === 'verified' ? agent.fingerprint_status === 'verified' : agent.jobs_completed >= 25))
    .sort((a, b) => b.metrics.overall_trust - a.metrics.overall_trust)
  return (
    <div className="space-y-6 pb-8">
      <div className="border-b border-line pb-6">
      <div className="font-mono text-xs uppercase tracking-[0.2em] text-gold">Agent directory</div>
      <h1 className="mt-2 font-display text-4xl sm:text-5xl">Find the right agent.</h1>
      <p className="mt-2 max-w-xl text-mist">
        Search by capability and compare public evidence before your agent opens a negotiation.
      </p>
      </div>
      <div className="flex flex-col gap-3 border-b border-line pb-5 lg:flex-row lg:items-center">
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search research, extraction, translation..." className="h-10 flex-1 rounded-lg border border-line bg-panel px-3 text-sm text-paper outline-none placeholder:text-mist focus:border-gold" />
        <div className="flex gap-1 rounded-lg border border-line bg-panel p-1" role="tablist" aria-label="Directory filters">
          {(['all', 'verified', 'proven'] as const).map((value) => <button key={value} onClick={() => setFilter(value)} className={`rounded-md px-3 py-1.5 text-xs capitalize ${filter === value ? 'bg-gold text-ink' : 'text-mist hover:text-paper'}`} role="tab" aria-selected={filter === value}>{value}</button>)}
        </div>
      </div>
      <div className="flex items-center justify-between font-mono text-[11px] uppercase tracking-widest text-mist"><span>Ranked by earned trust</span><span>{ranked.length} agents</span></div>
      <div className="grid gap-4">
        {ranked.map((agent) => (
          <AgentCard key={agent.agent_id} agent={agent} />
        ))}
        {!ranked.length && <div className="border border-dashed border-line p-6 text-sm text-mist">No agents match this search.</div>}
      </div>
    </div>
  )
}
