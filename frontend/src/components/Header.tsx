'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useProtocol } from '@/lib/store'
import { cn } from '@/lib/utils'
import { Button } from './ui/button'

const links = [
  { href: '/', label: 'Home' },
  { href: '/directory', label: 'Directory' },
  { href: '/hire', label: 'Find agents' },
  { href: '/jobs', label: 'Negotiations' },
  { href: '/register', label: 'List an agent' },
]

export function Header() {
  const path = usePathname()
  const { mode, walletAddress, walletSigned, connectWallet, signWallet, disconnectWallet } = useProtocol()
  return (
    <header className="sticky top-0 z-40 border-b border-line/80 bg-[#07080b]/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-5 py-3">
        <Link href="/" className="flex items-center gap-2.5">
          <img src="/agenttrust-mark.svg" alt="" className="h-7 w-7" />
          <span className="font-display text-lg tracking-tight">AgentTrust</span>
        </Link>
        <nav className="order-3 flex w-full items-center gap-1 overflow-x-auto border-t border-line/70 pt-2 md:order-none md:w-auto md:border-0 md:pt-0">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={cn(
                'rounded-md px-3 py-1.5 text-sm text-mist transition hover:text-paper',
                path === l.href && 'bg-white/5 text-paper'
              )}
            >
              {l.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-3 text-xs">
          {mode === 'live' && walletAddress ? (
            walletSigned ? (
              <Button onClick={disconnectWallet} variant="ghost" className="border border-mint/30 px-2 py-1 text-xs text-mint">
                Signed {walletAddress.slice(0, 6)}…
              </Button>
            ) : (
              <Button onClick={() => signWallet().catch((error) => window.alert(error.message))} variant="secondary" className="px-2 py-1 text-xs">
                Sign in
              </Button>
            )
          ) : (
            <Button onClick={() => connectWallet().catch((error) => window.alert(error.message))} variant="secondary" className="px-2 py-1 text-xs">
              Connect wallet
            </Button>
          )}
          <span className="hidden items-center gap-1.5 font-mono text-[11px] text-mint sm:flex">
            <span className="h-1.5 w-1.5 rounded-full bg-mint shadow-[0_0_10px_rgba(61,220,151,0.9)]" />
            Identity ready
          </span>
        </div>
      </div>
    </header>
  )
}
