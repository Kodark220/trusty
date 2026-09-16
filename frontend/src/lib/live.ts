import { createClient } from 'genlayer-js'
import { studionet } from 'genlayer-js/chains'

export const STUDIONET_RPC = process.env.NEXT_PUBLIC_GENLAYER_RPC_URL || 'https://studio.genlayer.com/api'
export const STUDIONET_CHAIN_ID = 61999
export const STUDIONET_CHAIN_ID_HEX = '0xF22F'
export const AGENTTRUST_ESCROW = process.env.NEXT_PUBLIC_AGENTTRUST_ESCROW_ADDRESS || ''
export const AGENTTRUST_REGISTRY = process.env.NEXT_PUBLIC_AGENTTRUST_REGISTRY_ADDRESS || ''
export const LIVE_WORKER = process.env.NEXT_PUBLIC_AGENTTRUST_WORKER_ADDRESS || ''

const studioNetwork = {
  ...studionet,
  id: STUDIONET_CHAIN_ID,
  name: 'GenLayer Studionet',
  nativeCurrency: { name: 'GEN', symbol: 'GEN', decimals: 18 },
  rpcUrls: { default: { http: [STUDIONET_RPC] } },
} satisfies typeof studionet

export type EthereumProvider = {
  request(args: { method: string; params?: unknown[] }): Promise<unknown>
  isOkxWallet?: boolean
  isRabby?: boolean
  isCoinbaseWallet?: boolean
  providers?: EthereumProvider[]
}

function provider(): EthereumProvider {
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
  const preferred = candidates.find((wallet) => wallet.isOkxWallet || wallet.isRabby || wallet.isCoinbaseWallet)
  const value = preferred ?? candidates[0]
  if (!value) throw new Error('No browser EVM wallet was found. Install and unlock OKX Wallet, MetaMask, Rabby, Coinbase Wallet, or Brave Wallet, then reload this page.')
  return value
}

export async function connectEvmWallet() {
  const wallet = provider()
  let accounts: string[]
  try {
    accounts = await wallet.request({ method: 'eth_requestAccounts' }) as string[]
  } catch (error) {
    const details = error as { code?: number; message?: string }
    if (details.code === -32002) throw new Error('A wallet connection request is already open. Approve it in your wallet extension.')
    throw new Error(details.message || 'Your wallet did not approve the connection request.')
  }
  if (!accounts[0]) throw new Error('No wallet account was selected.')
  try {
    await wallet.request({ method: 'wallet_switchEthereumChain', params: [{ chainId: STUDIONET_CHAIN_ID_HEX }] })
  } catch (error) {
    if ((error as { code?: number }).code !== 4902) throw error
    await wallet.request({
      method: 'wallet_addEthereumChain',
      params: [{
        chainId: STUDIONET_CHAIN_ID_HEX,
        chainName: 'GenLayer Studionet',
        nativeCurrency: { name: 'GEN', symbol: 'GEN', decimals: 18 },
        rpcUrls: [STUDIONET_RPC],
        blockExplorerUrls: ['https://explorer-studio.genlayer.com/'],
      }],
    })
    await wallet.request({ method: 'wallet_switchEthereumChain', params: [{ chainId: STUDIONET_CHAIN_ID_HEX }] })
  }
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
  const call = { address: address as `0x${string}`, functionName, args, value }
  const estimate = await client.estimateTransactionFeesForWrite(call as never)
  return client.writeContract({
    ...call,
    fees: { distribution: estimate.distribution, feeValue: estimate.feeValue },
  } as never)
}

export async function escrowWrite(
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
    requireContractAddress(AGENTTRUST_ESCROW, 'AgentTrust escrow'),
    functionName,
    args,
    value,
  )
  const transaction = await client.waitForTransactionReceipt({ hash })
  if (transaction.txExecutionResultName !== 'FINISHED_WITH_RETURN') {
    throw new Error(`Studionet transaction failed: ${transaction.txExecutionResultName ?? 'unknown result'}`)
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
  )
  const transaction = await client.waitForTransactionReceipt({ hash })
  if (transaction.txExecutionResultName !== 'FINISHED_WITH_RETURN') {
    throw new Error(`Studionet registry transaction failed: ${transaction.txExecutionResultName ?? 'unknown result'}`)
  }
  return { hash: String(hash) }
}