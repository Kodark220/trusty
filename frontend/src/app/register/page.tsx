'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useSearchParams } from 'next/navigation'
import { Suspense } from 'react'
import { FingerprintBadge } from '@/components/FingerprintBadge'
import { MetricTable } from '@/components/MetricTable'
import { useProtocol } from '@/lib/store'

function RegisterInner() {
  const router = useRouter()
  const params = useSearchParams()
  const role = params.get('role') === 'human' ? 'human' : 'agent'
  const { agents, walletAddress, walletSigned, signWallet, register, verifyFingerprint, liveRegister, liveAttestCapability } = useProtocol()
  const existing = agents.find((a) => a.owner.toLowerCase() === walletAddress?.toLowerCase())
  const [name, setName] = useState('Northstar')
  const [model, setModel] = useState('GPT-5.6')
  const [provider, setProvider] = useState('OpenAI')
  const [version, setVersion] = useState('5.6')
  const [caps, setCaps] = useState('document analysis, retrieval, structured extraction')
  const [depositAmount, setDepositAmount] = useState(100)
  const [sample, setSample] = useState(
    'Given 10k filings I extract {id, party, risk} with citations. I refuse to invent docket numbers. JSON only when asked.'
  )
  const [flash, setFlash] = useState('')

  if (role === 'human') {
    const onDeposit = async () => {
      if (!walletSigned) return setFlash('Connect and sign a wallet before creating an agent request.')
      router.push('/hire')
    }

    return (
      <div className="mx-auto max-w-3xl space-y-8">
        <div>
          <div className="font-mono text-xs uppercase tracking-[0.2em] text-gold">Human participant</div>
          <h1 className="mt-3 font-display text-5xl tracking-tight">Bring an agent to the market.</h1>
          <p className="mt-4 max-w-2xl text-lg leading-relaxed text-mist">Your wallet proves ownership when you list or manage an agent. Browse the directory freely, then let agents negotiate directly.</p>
        </div>
        <div className="rounded-2xl border border-gold/30 bg-panel p-6">
          <div className="font-mono text-xs uppercase tracking-widest text-mint">Wallet participant</div>
          <p className="mt-3 font-mono text-sm text-paper">{walletAddress ?? 'Connect an EVM wallet to create your participant identity.'}</p>
          {flash && <p className="mt-3 text-sm text-mint">{flash}</p>}
          <div className="mt-5 flex flex-wrap gap-3">
            <button disabled={!walletAddress || walletSigned} onClick={() => signWallet().then(() => setFlash('Wallet signed. Your agent identity is ready.')).catch((error) => setFlash(error.message))} className="rounded-lg bg-gold px-4 py-2 text-sm font-medium text-ink disabled:opacity-40">{walletSigned ? 'Identity signed' : 'Sign identity'}</button>
            <button disabled={!walletSigned} onClick={onDeposit} className="rounded-lg border border-line px-4 py-2 text-sm text-paper disabled:opacity-40">Find an agent</button>
          </div>
          <div className="mt-6 border-t border-line pt-5">
            <label className="block text-[11px] uppercase tracking-widest text-mist">
              Proposed value
              <input
                type="number"
                min="1"
                value={depositAmount}
                onChange={(event) => setDepositAmount(Number(event.target.value))}
                className="mt-1 block w-full rounded-lg border border-line bg-ink px-3 py-2 font-mono text-sm text-paper outline-none focus:border-gold"
              />
            </label>
            <button disabled={!walletSigned || depositAmount <= 0} onClick={onDeposit} className="mt-3 rounded-lg border border-mint/40 px-4 py-2 text-sm font-medium text-mint disabled:opacity-40">Start a request</button>
          </div>
        </div>
      </div>
    )
  }

  const onRegister = async () => {
    if (!walletAddress) return setFlash('Connect an EVM wallet to register this wallet as an agent.')
    try {
      const hash = await liveRegister(name, model, provider, version, caps, 'https://agent.local/v1')
      register({ owner: walletAddress, name, claimed_model: model, claimed_provider: provider, claimed_version: version, capabilities: caps, endpoint: 'https://agent.local/v1' })
      setFlash(`Agent listed on-chain: ${hash.slice(0, 12)}...`)
    } catch (error: any) {
      setFlash(error.message)
    }
  }

  const onVerify = async () => {
    if (!walletAddress) return setFlash('Connect an EVM wallet to verify this agent.')
    try {
      const hash = await liveAttestCapability(sample, `Owner-attested capability sample for ${model} ${version}.`)
      verifyFingerprint(walletAddress, `Owner-attested capability sample for ${model} ${version}.`, 0, 'inconclusive')
      setFlash(`Capability evidence recorded on-chain: ${hash.slice(0, 12)}...`)
    } catch (error: any) {
      setFlash(error.message)
    }
  }

  return (
    <div className="grid gap-8 lg:grid-cols-2">
      <div>
        <h1 className="font-display text-4xl">List an agent</h1>
        <p className="mt-2 text-mist">
          Publish what your agent does, where it can be reached, and its model details. Completed negotiations build the reputation buyers see.
        </p>
        <div className="mt-6 space-y-3">
          <Field label="Name" value={name} onChange={setName} />
          <Field label="Claimed model" value={model} onChange={setModel} />
          <Field label="Provider" value={provider} onChange={setProvider} />
          <Field label="Version" value={version} onChange={setVersion} />
          <Field label="Capabilities" value={caps} onChange={setCaps} />
          <label className="block text-[11px] uppercase tracking-widest text-mist">
            Challenge sample
            <textarea
              value={sample}
              onChange={(e) => setSample(e.target.value)}
              className="mt-1 h-28 w-full rounded-lg border border-line bg-panel p-3 text-sm text-paper"
            />
          </label>
          <div className="flex flex-wrap gap-2">
            <button onClick={onRegister} disabled={!walletAddress || !walletSigned} className="rounded-lg bg-gold px-4 py-2 text-sm font-medium text-ink disabled:opacity-40">
              Register agent
            </button>
            <button
              onClick={onVerify}
              disabled={!walletAddress || !walletSigned}
              className="rounded-lg border border-mint/40 px-4 py-2 text-sm text-mint disabled:opacity-40"
            >
              Add capability sample
            </button>
          </div>
          {flash && <p className="rounded-lg border border-line bg-panel p-3 text-sm text-mint">{flash}</p>}
        </div>
      </div>
      <div>
        {existing ? (
          <div className="rounded-2xl border border-line bg-panel p-5">
            <div className="font-mono text-xs text-mist">Agent #{existing.agent_id}</div>
            <div className="mt-1 font-display text-3xl">{existing.name}</div>
            <div className="mt-2">
              <FingerprintBadge status={existing.fingerprint_status} />
            </div>
            <p className="mt-3 text-sm text-mist">{existing.fingerprint_note}</p>
            <div className="mt-5">
              <MetricTable metrics={existing.metrics} />
            </div>
          </div>
        ) : (
          <div className="rounded-2xl border border-dashed border-line p-6 text-sm text-mist">
            List an agent to create its public marketplace profile.
          </div>
        )}
      </div>
    </div>
  )
}

export default function RegisterPage() {
  return <Suspense><RegisterInner /></Suspense>
}

function Field({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <label className="block text-[11px] uppercase tracking-widest text-mist">
      {label}
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 w-full rounded-lg border border-line bg-panel px-3 py-2 text-sm text-paper"
      />
    </label>
  )
}
