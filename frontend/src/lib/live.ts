import { createClient } from 'genlayer-js'
import { studioDevnet } from 'genlayer-js/chains'

export const STUDIO_NEXT_RPC = process.env.NEXT_PUBLIC_GENLAYER_RPC_URL || 'https://studio-dev.genlayer.com/api'
export const STUDIO_NEXT_CHAIN_ID = 61997
export const STUDIO_NEXT_CHAIN_ID_HEX = '0xF22D'
export const AGENTTRUST_ESCROW = process.env.NEXT_PUBLIC_AGENTTRUST_ESCROW_ADDRESS || ''
export const AGENTTRUST_REGISTRY = process.env.NEXT_PUBLIC_AGENTTRUST_REGISTRY_ADDRESS || ''
export const LIVE_WORKER = process.env.NEXT_PUBLIC_AGENTTRUST_WORKER_ADDRESS || ''

const studioNext = {
  ...studioDevnet,
  id: STUDIO_NEXT_CHAIN_ID,
  name: 'GenLayer Studio Next',
  nativeCurrency: { name: 'GEN', symbol: 'GEN', decimals: 18 },
  rpcUrls: { default: { http: [STUDIO_NEXT_RPC] } },
} satisfies typeof studioDevnet

type EthereumProvider = {
  request(args: { method: string; params?: unknown[] }): Promise<unknown>
}

function provider(): EthereumProvider {
  const value = (window as Window & { ethereum?: EthereumProvider }).ethereum
  if (!value) throw new Error('MetaMask is required. Install and unlock MetaMask to use AgentTrust live mode.')
  return value
}

export async function connectBradbury() {
  const wallet = provider()
  const accounts = await wallet.request({ method: 'eth_requestAccounts' }) as string[]
  if (!accounts[0]) throw new Error('No MetaMask account was selected.')
  try {
    await wallet.request({ method: 'wallet_switchEthereumChain', params: [{ chainId: STUDIO_NEXT_CHAIN_ID_HEX }] })
  } catch (error) {
    if ((error as { code?: number }).code !== 4902) throw error
    await wallet.request({
      method: 'wallet_addEthereumChain',
      params: [{
        chainId: STUDIO_NEXT_CHAIN_ID_HEX,
        chainName: 'GenLayer Studio Next',
        nativeCurrency: { name: 'GEN', symbol: 'GEN', decimals: 18 },
        rpcUrls: [STUDIO_NEXT_RPC],
        blockExplorerUrls: ['https://explorer-studio-dev.genlayer.com/'],
      }],
    })
  }
  return { address: accounts[0], wallet }
}

function requireContractAddress(address: string, contractName: string) {
  if (!address) throw new Error(`${contractName} is not configured. Deploy it to Studio Next, then set its address in frontend/.env.local.`)
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
    chain: studioNext,
    account: account as `0x${string}`,
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
    throw new Error(`Studio Next transaction failed: ${transaction.txExecutionResultName ?? 'unknown result'}`)
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
    chain: studioNext,
    account: account as `0x${string}`,
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
    throw new Error(`Studio Next registry transaction failed: ${transaction.txExecutionResultName ?? 'unknown result'}`)
  }
  return { hash: String(hash) }
}