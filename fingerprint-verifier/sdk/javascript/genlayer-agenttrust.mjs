import { createClient, isSuccessful } from 'genlayer-js';
import { studionet } from 'genlayer-js/chains';

/**
 * Browser-wallet adapter for the AgentTrust intelligent contract.
 * The wallet signs transactions; the API service should never receive a private key.
 */
export async function createAgentTrustClient({ contractAddress, provider, account }) {
  if (!contractAddress) throw new Error('contractAddress is required');
  if (!provider) {
    throw new Error('MetaMask is not connected. Install MetaMask or open the demo in read-only mode.');
  }
  if (!account) throw new Error('Connected wallet address is required');

  const client = createClient({ chain: studionet, account, provider });
  try {
    await client.connect('studionet');
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    if (/metamask|extension not found|provider/i.test(message)) {
      throw new Error('MetaMask could not be reached. Install or unlock MetaMask, then retry.');
    }
    throw error;
  }

  async function write(functionName, args) {
    const call = { address: contractAddress, functionName, args };
    const estimate = await client.estimateTransactionFeesForWrite(call);
    const hash = await client.writeContract({
      ...call,
      fees: {
        distribution: estimate.distribution,
        feeValue: estimate.feeValue,
      },
    });
    const transaction = await client.waitForFinalization({ hash });
    if (!isSuccessful(transaction)) {
      throw new Error(`GenLayer write failed: ${transaction.statusName} / ${transaction.txExecutionResultName}`);
    }
    return { hash, transaction };
  }

  return {
    registerAgent(name, claimedModel, claimedProvider, claimedVersion, capabilities, endpoint, modelCardUrl = '') {
      return write('register_agent', [
        name,
        claimedModel,
        claimedProvider,
        claimedVersion,
        capabilities,
        endpoint,
        modelCardUrl,
      ]);
    },
    verifyFingerprint(sampleOutputs, challengePrompt) {
      return write('verify_fingerprint', [sampleOutputs, challengePrompt]);
    },
    hireAgent(worker, title, brief, terms, budget) {
      return write('hire_agent', [worker, title, brief, terms, String(budget)]);
    },
    submitDelivery(jobId, evidence, deliveredOnTime) {
      return write('submit_delivery', [String(jobId), evidence, deliveredOnTime]);
    },
    acceptDelivery(jobId) {
      return write('accept_delivery', [String(jobId)]);
    },
    fileDispute(jobId, claim, evidence) {
      return write('file_dispute', [String(jobId), claim, evidence]);
    },
  };
}
