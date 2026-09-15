import type { Metadata } from 'next'
import './globals.css'
import { AppShell } from '@/components/AppShell'
import { ProtocolProvider } from '@/lib/store'

export const metadata: Metadata = {
  title: 'AgentTrust — verifiable trust for autonomous agents',
  description:
    'Verify what an agent is, measure how it behaves, and let its reputation follow it everywhere.',
  icons: { icon: '/favicon.svg' },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&family=Syne:wght@600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>
        <ProtocolProvider>
          <AppShell>{children}</AppShell>
        </ProtocolProvider>
      </body>
    </html>
  )
}
