'use client'

import { AgentCard } from '@/components/AgentCard'
import { useProtocol } from '@/lib/store'

export default function DirectoryPage() {
  const { agents } = useProtocol()
  const ranked = [...agents].sort((a, b) => b.metrics.overall_trust - a.metrics.overall_trust)
  return (
    <div>
      <h1 className="font-display text-4xl">Registry</h1>
      <p className="mt-2 max-w-xl text-mist">
        Portable reputation. Ranked by earned trust, not by what the agent wrote in its profile.
      </p>
      <div className="mt-8 grid gap-4">
        {ranked.map((agent) => (
          <AgentCard key={agent.agent_id} agent={agent} />
        ))}
      </div>
    </div>
  )
}
