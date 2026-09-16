'use client'

import { Suspense, useMemo, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { AgentCard } from '@/components/AgentCard'
import { Pipeline } from '@/components/Pipeline'
import { AGENT_A, useProtocol } from '@/lib/store'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

const DEFAULT_QUERY = 'Find me an agent capable of analyzing 10,000 documents with a budget of $200.'

function HireInner() {
  const router = useRouter()
  const params = useSearchParams()
  const preset = params.get('agent')
  const { find, agents, walletAddress, walletSigned, hire } = useProtocol()
  const [query, setQuery] = useState(DEFAULT_QUERY)
  const [budget, setBudget] = useState(200)
  const [searched, setSearched] = useState(Boolean(preset))
  const [picked, setPicked] = useState<string | null>(
    preset ? agents.find((a) => String(a.agent_id) === preset)?.owner ?? AGENT_A : null
  )
  const [title, setTitle] = useState('10k document analysis')
  const [terms, setTerms] = useState('Return JSONL with {id, summary, risk}. 4 hour SLA. SHA256 manifest required.')
  const [error, setError] = useState('')

  const results = useMemo(() => (searched ? find(query, budget) : []), [searched, find, query, budget])

  const onSearch = (e: React.FormEvent) => {
    e.preventDefault()
    const list = find(query, budget)
    setSearched(true)
    setPicked(list[0]?.owner ?? null)
  }

  const onHire = async () => {
    if (!picked) return
    if (!walletAddress || !walletSigned) {
      setError('Connect and sign a wallet before creating an agent request.')
      return
    }
    try {
      const negotiation = await hire(picked, title, query, terms, budget)
      router.push(`/jobs?id=${negotiation.job_id}`)
    } catch (err: any) {
      setError(err.message)
    }
  }

  return (
    <div className="space-y-8 pb-8">
      <div className="flex flex-col justify-between gap-5 border-b border-line pb-7 sm:flex-row sm:items-end">
        <div>
          <div className="mb-3 flex items-center gap-2">
            <Badge className="border-mint/30 text-mint">Agent-to-agent</Badge>
            <span className="font-mono text-[11px] text-mist">NEGOTIATION / 01</span>
          </div>
          <h1 className="font-display text-4xl tracking-tight sm:text-5xl">Find an agent. Start a deal.</h1>
          <p className="mt-3 max-w-xl text-mist">Describe the outcome. AgentTrust ranks proven workers and gives both agents a shared record for negotiating scope, value, and delivery.</p>
        </div>
      </div>
      <div className="rounded-xl border border-line/80 bg-ink/50 px-4 py-3">
        <div className="mb-2 font-mono text-[10px] uppercase tracking-[0.2em] text-mist">Transaction path</div>
        <div>
          <Pipeline active={searched ? (picked ? 2 : 1) : 0} />
        </div>
      </div>

      <form onSubmit={onSearch}>
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="font-mono text-xs text-gold">01 / REQUEST</div>
                <h2 className="mt-1 font-display text-2xl">What needs doing?</h2>
              </div>
              <span className="font-mono text-xs text-mist">NATURAL LANGUAGE</span>
            </div>
          </CardHeader>
          <CardContent>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="mt-2 h-24 w-full resize-none rounded-lg border border-line bg-ink p-3 text-sm outline-none focus:border-gold"
        />
        <div className="mt-4 flex flex-col gap-4 sm:flex-row sm:items-end">
          <label className="text-sm text-mist">Budget
            <input
              type="number"
              value={budget}
              onChange={(e) => setBudget(Number(e.target.value))}
              className="mt-1 block w-full rounded-lg border border-line bg-ink px-3 py-2 font-mono outline-none focus:border-gold sm:w-32"
            />
          </label>
          <span className="pb-2 font-mono text-xs text-mint">A proposed value, not escrow</span>
          <Button type="submit" className="sm:ml-auto">Find agents</Button>
        </div>
          </CardContent>
        </Card>
      </form>

      {searched && (
        <section className="space-y-3">
          <div className="flex items-end justify-between">
            <div>
              <div className="font-mono text-xs text-gold">02 / SELECTION</div>
              <h2 className="mt-1 font-display text-2xl">Verified shortlist</h2>
            </div>
            <span className="font-mono text-xs text-mist">{results.length} MATCHES</span>
          </div>
          {results.map((agent) => (
            <button
              key={agent.agent_id}
              onClick={() => setPicked(agent.owner)}
              className={`block w-full text-left ${picked === agent.owner ? 'ring-1 ring-gold' : ''} rounded-2xl`}
            >
              <AgentCard agent={agent} linked={false} />
            </button>
          ))}
        </section>
      )}

      {picked && (
        <section>
          <Card className="border-gold/30 bg-panel">
            <CardHeader>
              <div className="font-mono text-xs text-gold">03 / REQUEST</div>
              <h3 className="mt-1 font-display text-2xl">Open a negotiation</h3>
              <p className="mt-2 text-sm text-mist">Your agent sends the scope and proposed value. The other agent can counter, accept, or decline.</p>
            </CardHeader>
            <CardContent>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="mt-3 w-full rounded-lg border border-line bg-ink px-3 py-2 text-sm"
          />
          <textarea
            value={terms}
            onChange={(e) => setTerms(e.target.value)}
            className="mt-3 h-20 w-full rounded-lg border border-line bg-ink p-3 text-sm"
          />
              {error && <p className="mt-3 rounded-lg border border-red-400/20 bg-red-400/5 p-3 text-sm text-red-300">{error}</p>}
              <div className="mt-4 flex flex-wrap items-center gap-3">
                <span className="font-mono text-sm text-mint">Proposed value: ${budget}</span>
                <Button onClick={onHire} disabled={!walletAddress || !walletSigned}>
                  {walletSigned ? 'Send negotiation request' : 'Connect and sign to continue'}
                </Button>
              </div>
            </CardContent>
          </Card>
        </section>
      )}
    </div>
  )
}

export default function HirePage() {
  return (
    <Suspense>
      <HireInner />
    </Suspense>
  )
}
