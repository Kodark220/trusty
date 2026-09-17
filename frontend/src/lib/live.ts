import { createClient, isSuccessful } from 'genlayer-js'
import { studioDevnet } from 'genlayer-js/chains'
import { encodeFunctionData } from 'viem'

export const STUDIONET_RPC = process.env.NEXT_PUBLIC_GENLAYER_RPC_URL || 'https://studio-next.genlayer.com/api'
export const STUDIONET_CHAIN_ID = 61997
export const STUDIONET_CHAIN_ID_HEX = '0xF22D'
export const AGENTTRUST_MARKETPLACE = process.env.NEXT_PUBLIC_AGENTTRUST_MARKETPLACE_ADDRESS || '0xbE6505366A839E31C16eCd7BD0f4E71C95FA616e'
const legacyRegistry = '0x209D7C1afBfD0c0915c064AE0BD3b22283b07805'
const configuredRegistry = process.env.NEXT_PUBLIC_AGENTTRUST_REGISTRY_ADDRESS
export const AGENTTRUST_REGISTRY = configuredRegistry && configuredRegistry.toLowerCase() !== legacyRegistry.toLowerCase()
  ? configuredRegistry
  : '0x3eAf1a624749Db29bE82B144cb687e94897255b8'
export const BASE_SEPOLIA_CHAIN_ID_HEX = '0x14A34'
export const BASE_SEPOLIA_RPC = process.env.NEXT_PUBLIC_BASE_SEPOLIA_RPC_URL || 'https://sepolia.base.org'
export const BASE_REGISTRY = process.env.NEXT_PUBLIC_AGENTTRUST_BASE_REGISTRY_ADDRESS || ''
export const LIVE_WORKER = process.env.NEXT_PUBLIC_AGENTTRUST_WORKER_ADDRESS || ''

const studioNetwork = studioDevnet
const studionetChain = {
  chainId: STUDIONET_CHAIN_ID_HEX,
  chainName: 'GenLayer Studio Next',
  nativeCurrency: { name: 'GEN', symbol: 'GEN', decimals: 18 },
  rpcUrls: [STUDIONET_RPC],
  blockExplorerUrls: ['https://explorer-studio-dev.genlayer.com'],
}
const baseSepoliaChain = {
  chainId: BASE_SEPOLIA_CHAIN_ID_HEX,
  chainName: 'Base Sepolia',
  nativeCurrency: { name: 'Ether', symbol: 'ETH', decimals: 18 },
  rpcUrls: [BASE_SEPOLIA_RPC],
  blockExplorerUrls: ['https://sepolia.basescan.org'],
}
const baseRegistryAbi = [{
  type: 'function',
  name: 'register',
  stateMutability: 'nonpayable',
  inputs: [{
    name: 'input',
    type: 'tuple',
    components: [
      { name: 'name', type: 'string' },
      { name: 'claimedModel', type: 'string' },
      { name: 'provider', type: 'string' },
      { name: 'version', type: 'string' },
      { name: 'capabilities', type: 'string' },
      { name: 'endpoint', type: 'string' },
      { name: 'modelCardUrl', type: 'string' },
    ],
  }],
  outputs: [],
}] as const

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

async function ensureStudionet(wallet: EthereumProvider) {
  const chainId = await wallet.request({ method: 'eth_chainId' })
  if (typeof chainId === 'string' && chainId.toLowerCase() === STUDIONET_CHAIN_ID_HEX.toLowerCase()) return
  try {
    await wallet.request({ method: 'wallet_switchEthereumChain', params: [{ chainId: STUDIONET_CHAIN_ID_HEX }] })
  } catch (error) {
    const details = error as { code?: number; message?: string }
    if (details.code !== 4902) {
      throw new Error(details.message || 'Switch your wallet to GenLayer Studio Next, then try again.')
    }
    try {
      await wallet.request({ method: 'wallet_addEthereumChain', params: [studionetChain] })
    } catch (addError) {
      const addDetails = addError as { message?: string }
      throw new Error(addDetails.message || 'Add GenLayer Studio Next to your wallet, then try again.')
    }
  }
}

async function ensureBaseSepolia(wallet: EthereumProvider) {
  const chainId = await wallet.request({ method: 'eth_chainId' })
  if (typeof chainId === 'string' && chainId.toLowerCase() === BASE_SEPOLIA_CHAIN_ID_HEX.toLowerCase()) return
  try {
    await wallet.request({ method: 'wallet_switchEthereumChain', params: [{ chainId: BASE_SEPOLIA_CHAIN_ID_HEX }] })
  } catch (error) {
    const details = error as { code?: number; message?: string }
    if (details.code !== 4902) throw new Error(details.message || 'Switch your wallet to Base Sepolia, then try again.')
    await wallet.request({ method: 'wallet_addEthereumChain', params: [baseSepoliaChain] })
  }
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
  wallet: EthereumProvider,
  address: string,
  functionName: string,
  args: unknown[],
  value: bigint,
) {
  await ensureStudionet(wallet)
  const call = {
    address: address as `0x${string}`,
    functionName,
    args,
    value,
    leaderOnly: true,
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
    wallet,
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
    wallet,
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

export async function baseRegistryWrite(
  wallet: EthereumProvider,
  account: string,
  input: { name: string; claimedModel: string; provider: string; version: string; capabilities: string; endpoint: string; modelCardUrl: string },
): Promise<{ hash: string }> {
  if (!BASE_REGISTRY) throw new Error('Base registry is not configured. Deploy contracts/base/AgentRegistry.sol to Base Sepolia, then set NEXT_PUBLIC_AGENTTRUST_BASE_REGISTRY_ADDRESS.')
  await ensureBaseSepolia(wallet)
  const data = encodeFunctionData({ abi: baseRegistryAbi, functionName: 'register', args: [input] })
  const hash = await wallet.request({
    method: 'eth_sendTransaction',
    params: [{ from: account, to: BASE_REGISTRY, data, value: '0x0' }],
  })
  if (typeof hash !== 'string') throw new Error('Your wallet did not return a Base Sepolia transaction hash.')
  for (let attempt = 0; attempt < 60; attempt += 1) {
    const receipt = await wallet.request({ method: 'eth_getTransactionReceipt', params: [hash] }) as { status?: string } | null
    if (receipt) {
      if (receipt.status !== '0x1') throw new Error('Base Sepolia registration transaction reverted.')
      return { hash }
    }
    await new Promise((resolve) => setTimeout(resolve, 1000))
  }
  throw new Error(`Base Sepolia transaction is pending: ${hash}`)
}