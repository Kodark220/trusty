import { createClient, isSuccessful } from 'genlayer-js'
import { studionet } from 'genlayer-js/chains'

export const STUDIONET_RPC = process.env.NEXT_PUBLIC_GENLAYER_RPC_URL || 'https://studio.genlayer.com/api'
export const STUDIONET_CHAIN_ID = 61999
export const STUDIONET_CHAIN_ID_HEX = '0xF22F'
export const AGENTTRUST_MARKETPLACE = process.env.NEXT_PUBLIC_AGENTTRUST_MARKETPLACE_ADDRESS || ''
export const AGENTTRUST_REGISTRY = process.env.NEXT_PUBLIC_AGENTTRUST_REGISTRY_ADDRESS || ''
export const LIVE_WORKER = process.env.NEXT_PUBLIC_AGENTTRUST_WORKER_ADDRESS || ''

const studioNetwork = studionet

export type EthereumProvider = {
  request(args: { method: string; params?: unknown[] }): Promise<unknown>
  isMetaMask?: boolean
  isOkxWallet?: boolean
  isRabby?: boolean
  isCoinbaseWallet?: boolean
  providers?: EthereumProvider[]
}

async function errorMessage(error: unknown, fallback: string) {
  if (error instanceof Error && error.message) return error.message
  if (error && typeof error === 'object') {
    const details = error as { message?: unknown; data?: { message?: unknown }; code?: unknown }
    const message = typeof details.message === 'string'
      ? details.message
      : typeof details.data?.message === 'string'
        ? details.data.message
        : ''
    if (message) return message
    if (details.code === 4001) return 'Transaction was rejected in your wallet.'
  }
  return fallback
}

async function provider(): Promise<EthereumProvider> {
  const injected = window as Window & {
    ethereum?: EthereumProvider
    okxwallet?: EthereumProvider
    coinbaseWalletExtension?: EthereumProvider
  }
  const candidates = [
    injected.okxwallet,
    injected.coinbaseWalletExtension,
    ...(injected.ethereum?.providers ?? []),
    injected.ethereum,
  ].filter((wallet): wallet is EthereumProvider => Boolean(wallet?.request))
  const evmWallets: EthereumProvider[] = []
  for (const wallet of candidates) {
    try {
      const chainId = await wallet.request({ method: 'eth_chainId' })
      if (typeof chainId === 'string' && chainId.startsWith('0x')) evmWallets.push(wallet)
    } catch {
      // Ignore non-EVM injected extensions.
    }
  }
  const value = evmWallets.find((wallet) => wallet.isMetaMask && !wallet.isOkxWallet) ?? evmWallets[0]
  if (!value) throw new Error('Open an EVM wallet extension, then reconnect.')
  return value
}

export async function connectEvmWallet() {
  const wallet = await provider()
  let accounts: string[]
  try {
    accounts = await wallet.request({ method: 'eth_requestAccounts' }) as string[]
  } catch (error) {
    const details = error as { code?: number; message?: string }
    if (details.code === -32002) throw new Error('A wallet connection request is already open. Approve it in your wallet extension.')
    throw new Error(details.message || 'Your wallet did not approve the connection request.')
  }
  if (!accounts[0]) throw new Error('No wallet account was selected.')
  return { address: accounts[0], wallet }
}

function requireContractAddress(address: string, contractName: string) {
  if (!address) throw new Error(`${contractName} is not configured. Deploy it to Studionet, then set its address in frontend/.env.local.`)
  return address
}

async function writeWithEstimatedFees(
  client: ReturnType<typeof createClient>,
  address: string,
  functionName: string,
  args: unknown[],
  value: bigint,
) {
  const call = {
    address: address as `0x${string}`,
    functionName,
    args,
    value,
    leaderOnly: functionName === 'deposit',
  }
  return client.writeContract(call as never)
}

export async function marketplaceWrite(
  wallet: EthereumProvider,
  account: string,
  functionName: string,
  args: unknown[],
  value = BigInt(0),
): Promise<{ hash: string }> {
  const client = createClient({
    chain: studioNetwork,
    account: account as `0x${string}`,
    provider: wallet,
  })
  const hash = await writeWithEstimatedFees(
    client,
    requireContractAddress(AGENTTRUST_MARKETPLACE, 'AgentTrust marketplace'),
    functionName,
    args,
    value,
  ).catch(async (error) => {
    throw new Error(await errorMessage(error, 'Your wallet could not submit the Studionet transaction.'))
  })
  const transaction = await client.waitForFinalization({ hash })
  if (!isSuccessful(transaction)) {
    throw new Error(`Studionet transaction failed: ${transaction.statusName ?? transaction.status ?? 'unknown status'}`)
  }
  return { hash: String(hash) }
}

export async function registryWrite(
  wallet: EthereumProvider,
  account: string,
  functionName: string,
  args: unknown[],
): Promise<{ hash: string }> {
  const client = createClient({
    chain: studioNetwork,
    account: account as `0x${string}`,
    provider: wallet,
  })
  const hash = await writeWithEstimatedFees(
    client,
    requireContractAddress(AGENTTRUST_REGISTRY, 'AgentTrust registry'),
    functionName,
    args,
    BigInt(0),
  ).catch(async (error) => {
    throw new Error(await errorMessage(error, 'Your wallet could not submit the Studionet transaction.'))
  })
  const transaction = await client.waitForFinalization({ hash })
  if (!isSuccessful(transaction)) {
    throw new Error(`Studionet registry transaction failed: ${transaction.statusName ?? transaction.status ?? 'unknown status'}`)
  }
  return { hash: String(hash) }
}