/**
 * Generate a random encryption key (32 bytes for AES-256)
 */
export async function generateEncryptionKey(): Promise<CryptoKey> {
  return await crypto.subtle.generateKey(
    {
      name: "AES-GCM",
      length: 256,
    },
    true, // extractable
    ["encrypt", "decrypt"]
  );
}

/**
 * Export key to raw bytes (for storage/transmission)
 */
export async function exportKey(key: CryptoKey): Promise<Uint8Array> {
  return new Uint8Array(await crypto.subtle.exportKey("raw", key));
}

/**
 * Import key from raw bytes
 */
export async function importKey(keyBytes: Uint8Array): Promise<CryptoKey> {
  return await crypto.subtle.importKey(
    "raw",
    keyBytes,
    {
      name: "AES-GCM",
      length: 256,
    },
    true,
    ["encrypt", "decrypt"]
  );
}

/**
 * Encrypt data using AES-GCM
 */
export async function encryptData(
  data: ArrayBuffer,
  key: CryptoKey
): Promise<{ encrypted: ArrayBuffer; iv: Uint8Array }> {
  // Generate random IV (12 bytes for GCM)
  const iv = crypto.getRandomValues(new Uint8Array(12));

  const encrypted = await crypto.subtle.encrypt(
    {
      name: "AES-GCM",
      iv: iv,
    },
    key,
    data
  );

  return { encrypted, iv };
}

/**
 * Decrypt data using AES-GCM
 */
export async function decryptData(
  encryptedData: ArrayBuffer,
  key: CryptoKey,
  iv: Uint8Array
): Promise<ArrayBuffer> {
  return await crypto.subtle.decrypt(
    {
      name: "AES-GCM",
      iv: iv,
    },
    key,
    encryptedData
  );
}

/**
 * Encrypt file and return encrypted blob
 * 
 * Format: iv (12 bytes) + ciphertext + tag (16 bytes)
 * This matches what the SGX enclave expects for decryption.
 */
export async function encryptFile(
  file: File,
  key: CryptoKey
): Promise<{ encryptedBlob: Blob; iv: Uint8Array }> {
  const fileBuffer = await file.arrayBuffer();
  const { encrypted, iv } = await encryptData(fileBuffer, key);
  
  // Prepend IV to encrypted data: iv (12 bytes) + ciphertext + tag (16 bytes)
  const encryptedWithIV = new Uint8Array(iv.length + encrypted.byteLength);
  encryptedWithIV.set(iv, 0);
  encryptedWithIV.set(new Uint8Array(encrypted), iv.length);
  
  return { encryptedBlob: new Blob([encryptedWithIV]), iv };
}

