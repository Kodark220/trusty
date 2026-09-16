const steps = [
  'Discover',
  'Request',
  'Proposal',
  'Agreement',
  'Outcome',
  'Reputation',
]

export function Pipeline({ active = -1 }: { active?: number }) {
  return (
    <ol className="flex flex-wrap gap-1 text-[11px] uppercase tracking-widest text-mist">
      {steps.map((step, i) => (
        <li key={`${step}-${i}`} className="flex items-center gap-1">
          <span className={i === active ? 'text-gold' : i < active ? 'text-mint' : ''}>{step}</span>
          {i < steps.length - 1 && <span className="text-line">→</span>}
        </li>
      ))}
    </ol>
  )
}
