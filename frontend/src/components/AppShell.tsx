'use client'

import { usePathname } from 'next/navigation'
import { Header } from './Header'

export function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname()
  const landing = path === '/'

  return (
    <>
      {!landing && <Header />}
      <main className={landing ? 'min-h-screen px-4 pb-10 pt-4 sm:px-8 lg:px-12' : 'mx-auto max-w-6xl px-5 pb-24 pt-8'}>
        {children}
      </main>
    </>
  )
}
