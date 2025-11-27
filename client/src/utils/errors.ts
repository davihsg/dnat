/**
 * Extract user-friendly error message from transaction errors
 */
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    // Check for common MetaMask/user rejection
    if (error.message.includes("user rejected") || error.message.includes("User denied")) {
      return "Transaction was rejected by user";
    }
    
    // Check for insufficient funds
    if (error.message.includes("insufficient funds") || error.message.includes("insufficient balance")) {
      return "Insufficient funds for this transaction";
    }
    
    // Check for revert reasons
    const revertMatch = error.message.match(/revert\s+(.+)/i);
    if (revertMatch) {
      return revertMatch[1];
    }
    
    // Return the error message if it's reasonable
    if (error.message.length < 200) {
      return error.message;
    }
  }
  
  return "An unknown error occurred";
}

/**
 * Check if error is a user rejection
 */
export function isUserRejection(error: unknown): boolean {
  if (error instanceof Error) {
    return error.message.includes("user rejected") || error.message.includes("User denied");
  }
  return false;
}

