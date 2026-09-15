import type { ButtonHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'

export function buttonStyles(variant: ButtonVariant = 'primary') {
  return cn(
    'inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold/70 disabled:pointer-events-none disabled:opacity-50',
    variant === 'primary' && 'bg-gold text-ink hover:bg-gold/90',
    variant === 'secondary' && 'border border-line bg-panel text-paper hover:border-gold/50 hover:bg-white/[0.04]',
    variant === 'ghost' && 'text-mist hover:bg-white/[0.04] hover:text-paper',
    variant === 'danger' && 'border border-red-400/30 text-red-300 hover:bg-red-400/10',
  )
}

export function Button({
  className,
  variant = 'primary',
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }) {
  return <button className={cn(buttonStyles(variant), className)} {...props} />
}