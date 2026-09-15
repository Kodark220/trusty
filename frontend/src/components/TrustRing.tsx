export function TrustRing({ score, size = 92 }: { score: number; size?: number }) {
  const r = 34
  const c = 2 * Math.PI * r
  const offset = c - (score / 100) * c
  const color = score >= 90 ? '#3ddc97' : score >= 75 ? '#c9a227' : score >= 50 ? '#d97706' : '#f07167'
  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg viewBox="0 0 80 80" className="h-full w-full -rotate-90">
        <circle cx="40" cy="40" r={r} fill="none" stroke="#1c2030" strokeWidth="6" />
        <circle
          cx="40"
          cy="40"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="6"
          strokeDasharray={c}
          strokeDashoffset={offset}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="font-mono text-xl tabular leading-none" style={{ color }}>
          {score}
        </div>
        <div className="text-[9px] uppercase tracking-widest text-mist">trust</div>
      </div>
    </div>
  )
}
