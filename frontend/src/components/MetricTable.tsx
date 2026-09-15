import type { Metrics } from '@/lib/types'

const rows: { key: keyof Metrics; label: string }[] = [
  { key: 'model_authenticity', label: 'Model authenticity' },
  { key: 'reliability', label: 'Reliability' },
  { key: 'sla_performance', label: 'SLA performance' },
  { key: 'transaction_success', label: 'Transaction success' },
  { key: 'dispute_history', label: 'Dispute history' },
  { key: 'overall_trust', label: 'Overall Trust Score' },
]

export function MetricTable({ metrics }: { metrics: Metrics }) {
  return (
    <div className="overflow-hidden rounded-xl border border-line bg-panel">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-[11px] uppercase tracking-widest text-mist">
            <th className="px-4 py-3 font-medium">Metric</th>
            <th className="px-4 py-3 font-medium">Score</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const value = metrics[row.key]
            const overall = row.key === 'overall_trust'
            return (
              <tr key={row.key} className={overall ? 'bg-white/[0.03]' : ''}>
                <td className={`px-4 py-2.5 ${overall ? 'font-medium' : 'text-mist'}`}>{row.label}</td>
                <td className="px-4 py-2.5">
                  <div className="flex items-center gap-3">
                    <div className="h-1.5 w-28 overflow-hidden rounded-full bg-line">
                      <div
                        className={`h-full ${overall ? 'bg-gold' : 'bg-mint/80'}`}
                        style={{ width: `${value}%` }}
                      />
                    </div>
                    <span className={`font-mono tabular ${overall ? 'text-gold' : ''}`}>
                      {value}{overall ? '/100' : '%'}
                    </span>
                  </div>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
