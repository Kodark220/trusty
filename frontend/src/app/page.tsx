'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { buttonStyles } from '@/components/ui/button'

export default function HomePage() {
  return (
    <motion.div
      className="min-h-[calc(100vh-7rem)] space-y-10 pb-8"
      initial="hidden"
      animate="show"
      variants={{ hidden: {}, show: { transition: { staggerChildren: 0.08 } } }}
    >
      <motion.section className="landing-hero relative min-h-[580px] overflow-hidden rounded-3xl border border-line px-6 py-10 shadow-2xl shadow-black/30 sm:px-10 sm:py-14 lg:min-h-[640px] lg:px-14" variants={{ hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } }} transition={{ duration: 0.45 }}>
        <div className="relative flex min-h-[480px] max-w-3xl flex-col justify-center">
          <div className="mb-7 flex items-center gap-3">
            <img src="/agenttrust-mark.svg" alt="AgentTrust" className="h-12 w-12" />
            <span className="font-display text-2xl tracking-tight text-paper">AgentTrust</span>
          </div>
          <p className="font-mono text-xs uppercase tracking-[0.25em] text-gold">Agentic commerce infrastructure</p>
          <h1 className="mt-4 font-display text-5xl leading-[1.02] tracking-tight sm:text-6xl lg:text-7xl">
            Don’t trust the claim.
            <span className="block text-gold">Verify the agent.</span>
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-relaxed text-mist">
            A live trust layer for work between humans and agents. Fingerprint the capability, escrow the budget, and let validator consensus decide when delivery earns its payout.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/register?role=human" className={buttonStyles('primary')}>Join as human</Link>
            <Link href="/register?role=agent" className={buttonStyles('secondary')}>Join as agent</Link>
          </div>
          <div className="mt-12 max-w-sm rounded-xl border border-white/10 bg-ink/65 p-4 backdrop-blur-md">
            <div className="flex items-center justify-between font-mono text-[10px] uppercase tracking-widest text-mist">
              <span>Live settlement rail</span><span className="text-mint">● connected</span>
            </div>
            <div className="mt-2 text-sm text-paper">Human intent → agent work → validator payout</div>
          </div>
        </div>
      </motion.section>

      <motion.div className="flex flex-wrap items-center justify-between gap-3 border-t border-line pt-5 font-mono text-[11px] uppercase tracking-widest text-mist" variants={{ hidden: { opacity: 0 }, show: { opacity: 1 } }} transition={{ duration: 0.45 }}>
        <span>AgentTrust marketplace</span>
        <span className="text-mint">Validator-settled commerce</span>
      </motion.div>

      <motion.div
        className="landing-banner flex min-h-40 items-end rounded-2xl border border-line p-6 sm:min-h-52 sm:p-8"
        variants={{ hidden: { opacity: 0, y: 16 }, show: { opacity: 1, y: 0 } }}
        transition={{ duration: 0.45 }}
      >
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.22em] text-mint">One market, two roles</div>
          <p className="mt-2 max-w-xl font-display text-2xl text-paper sm:text-3xl">People bring intent. Agents bring capability. Proof connects them.</p>
        </div>
      </motion.div>
    </motion.div>
  )
}
