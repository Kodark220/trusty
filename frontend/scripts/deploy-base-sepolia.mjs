import { readFile } from 'node:fs/promises'
import { privateKeyToAccount } from 'viem/accounts'
import { createPublicClient, createWalletClient, http } from 'viem'

const privateKey = process.env.BASE_SEPOLIA_DEPLOYER_PRIVATE_KEY
if (!privateKey || !/^0x[0-9a-fA-F]{64}$/.test(privateKey)) {
  throw new Error('Set BASE_SEPOLIA_DEPLOYER_PRIVATE_KEY to a 32-byte private key before deploying.')
}

const rpcUrl = process.env.BASE_SEPOLIA_RPC_URL || 'https://sepolia.base.org'
const account = privateKeyToAccount(privateKey)
const bytecode = `0x${(await readFile('../artifacts/base-registry/contracts_base_AgentRegistry_sol_AgentRegistry.bin', 'utf8')).trim()}`
const chain = {
  id: 84532,
  name: 'Base Sepolia',
  nativeCurrency: { name: 'Ether', symbol: 'ETH', decimals: 18 },
  rpcUrls: { default: { http: [rpcUrl] } },
}
const transport = http(rpcUrl)
const publicClient = createPublicClient({ chain, transport })
const walletClient = createWalletClient({ account, chain, transport })

console.log(`Deploying AgentRegistry from ${account.address} to Base Sepolia...`)
const hash = await walletClient.deployContract({ abi: [], bytecode })
console.log(`Submitted: https://sepolia.basescan.org/tx/${hash}`)
const receipt = await publicClient.waitForTransactionReceipt({ hash })
if (receipt.status !== 'success' || !receipt.contractAddress) {
  throw new Error(`Deployment failed: ${hash}`)
}

console.log(`Registry deployed: ${receipt.contractAddress}`)
console.log(`NEXT_PUBLIC_AGENTTRUST_BASE_REGISTRY_ADDRESS=${receipt.contractAddress}`)