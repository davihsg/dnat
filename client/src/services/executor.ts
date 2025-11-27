/**
 * Executor Service - Communicates with the SGX executor API
 * 
 * The Executor API orchestrates the following flow:
 * 1. Fetch asset info from blockchain (IPFS URIs)
 * 2. Verify user has access rights
 * 3. Fetch encrypted assets from IPFS
 * 4. Send to SGX enclave for decryption and execution
 * 5. Return results to client
 */

export interface ExecutionRequest {
  datasetId: string;
  applicationId: string;
  userAddress: string;
  params?: Record<string, any>;
}

export interface ExecutionResult {
  success: boolean;
  output?: string;
  error?: string;
  executionTime?: number;
  timestamp: string;
}

// Executor API endpoint - configure based on your deployment
const EXECUTOR_API_URL = process.env.NEXT_PUBLIC_EXECUTOR_URL || "http://localhost:8080";

/**
 * Request execution of an application over a dataset in the SGX enclave
 */
export async function requestExecution(request: ExecutionRequest): Promise<ExecutionResult> {
  const startTime = Date.now();
  
  try {
    const response = await fetch(`${EXECUTOR_API_URL}/execute`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    const result = await response.json();
    const executionTime = Date.now() - startTime;
    
    if (!response.ok) {
      return {
        success: false,
        error: result.error || `Executor error: ${response.status}`,
        executionTime,
        timestamp: new Date().toISOString(),
      };
    }

    return {
      success: result.success,
      output: result.output,
      error: result.error,
      executionTime: result.executionTime || executionTime,
      timestamp: new Date().toISOString(),
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Failed to connect to executor",
      executionTime: Date.now() - startTime,
      timestamp: new Date().toISOString(),
    };
  }
}

/**
 * Check executor health status
 */
export async function checkExecutorHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${EXECUTOR_API_URL}/health`, {
      method: "GET",
    });
    return response.ok;
  } catch {
    return false;
  }
}

