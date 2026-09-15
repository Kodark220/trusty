import type { FingerprintStatus } from '@/lib/types'
import { cn } from '@/lib/utils'

export function FingerprintBadge({ status }: { status: FingerprintStatus }) {
  const map = {
    verified: { label: 'fingerprint verified', className: 'border-mint/30 bg-mint/10 text-mint' },
    mismatched: { label: 'fingerprint mismatch', className: 'border-red-400/30 bg-red-400/10 text-red-300' },
    inconclusive: { label: 'fingerprint inconclusive', className: 'border-gold/30 bg-gold/10 text-gold' },
    unverified: { label: 'unverified claim', className: 'border-white/10 bg-white/5 text-mist' },
  }[status]
  return (
    <span className={cn('inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px]', map.className)}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {map.label}
    </span>
  )
}
