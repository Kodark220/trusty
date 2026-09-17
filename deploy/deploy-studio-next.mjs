/**
 * Deploy AgentRegistry and AgentEscrowBradbury to GenLayer Studio Next (chain ID 61997).
 *
 * Usage:
 *   node deploy/deploy-studio-next.mjs <contract-path> [private-key]
 *
 * Examples:
 *   node deploy/deploy-studio-next.mjs contracts/AgentRegistry.py
 *   node deploy/deploy-studio-next.mjs contracts/AgentEscrowBradbury.py
 */
import { readFileSync } from 'fs'
import { resolve } from 'path'

const RPC = 'https://studio-next.genlayer.com/api'
const CHAIN_ID = 61997

async function jsonRpc(method, params = []) {
  const body = JSON.stringify({ jsonrpc: '2.0', id: Date.now(), method, params })
  const res = await fetch(RPC, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
  })
  const json = await res.json()
  if (json.error) throw new Error(`RPC ${method}: ${JSON.stringify(json.error)}`)
  return json.result
}

async function main() {
  const contractPath = process.argv[2]
  if (!contractPath) {
    console.error('Usage: node deploy/deploy-studio-next.mjs <contract-path>')
    process.exit(1)
  }

  const code = readFileSync(resolve(contractPath), 'utf-8')
  console.log(`Contract: ${contractPath}`)
  console.log(`Code length: ${code.length} bytes`)
  console.log(`RPC: ${RPC}`)
  console.log()

  // Use genlayer-js for deployment
  const { createClient } = await import('genlayer-js')
  const { studioDevnet } = await import('genlayer-js/chains')
  const { createAccount } = await import('genlayer-js/accounts')

  // Load private key from keystore or env
  let privateKey = process.argv[3] || process.env.GENLAYER_PRIVATE_KEY
  if (!privateKey) {
    // Try to extract from genlayer CLI keystore
    const { execSync } = await import('child_process')
    try {
      const output = execSync('genlayer account show --export-key 2>&1', { encoding: 'utf-8' })
      const match = output.match(/0x[0-9a-fA-F]{64}/)
      if (match) privateKey = match[0]
    } catch {
      // Fall back
    }
  }

  if (!privateKey) {
    console.error('Provide a private key as the second argument or set GENLAYER_PRIVATE_KEY env var.')
    console.error('Or export from CLI: genlayer account show --export-key')
    process.exit(1)
  }

  const account = createAccount(privateKey)
  console.log(`Deployer: ${account.address}`)

  const client = createClient({
    chain: studioDevnet,
    account,
  })

  console.log('Deploying contract...')

  try {
    const hash = await client.deployContract({
      code,
      args: [],
      leaderOnly: true,
      value: BigInt('10000000000000000'), // 0.01 GEN fee deposit
    })

    console.log(`\nTransaction hash: ${hash}`)
    console.log('Waiting for finalization...')

    const receipt = await client.waitForFinalization({ hash })
    console.log(`\nStatus: ${receipt.statusName || receipt.status}`)

    if (receipt.contractAddress) {
      console.log(`\n✅ Contract deployed!`)
      console.log(`Address: ${receipt.contractAddress}`)
      console.log(`Explorer: https://explorer-studio-dev.genlayer.com/address/${receipt.contractAddress}`)
    } else {
      console.log('\nReceipt:', JSON.stringify(receipt, null, 2))
    }
  } catch (error) {
    console.error('\n❌ Deployment failed:', error.message || error)
    
    // Try alternative approach with explicit fee structure
    console.log('\nRetrying with estimate-fees approach...')
    try {
      const fees = await client.estimateFees({
        code,
        args: [],
      })
      console.log('Estimated fees:', JSON.stringify(fees, null, 2))
      
      const hash = await client.deployContract({
        code,
        args: [],
        leaderOnly: true,
        ...fees,
      })
      console.log(`\nTransaction hash: ${hash}`)
      const receipt = await client.waitForFinalization({ hash })
      console.log(`Status: ${receipt.statusName || receipt.status}`)
      if (receipt.contractAddress) {
        console.log(`\n✅ Contract deployed!`)
        console.log(`Address: ${receipt.contractAddress}`)
        console.log(`Explorer: https://explorer-studio-dev.genlayer.com/address/${receipt.contractAddress}`)
      } else {
        console.log('\nReceipt:', JSON.stringify(receipt, null, 2))
      }
    } catch (retryError) {
      console.error('Retry also failed:', retryError.message || retryError)
    }
  }
}

main().catch(console.error)
