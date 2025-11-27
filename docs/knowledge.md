# DNAT-Style Confidential Data Marketplace – Working Notes

This document summarizes everything we’ve designed so far for your DNAT-style system (based on Ethereum + IPFS + SCONE/CAS + SGX).  
It’s meant to be a **high-level architecture + flow description**, not an exact copy of the original paper.

---

## 1. Smart Contract: `DnatMarketplace`

**Goal:** manage **assets** (datasets + applications), **access rights**, and **payments**.

### 1.1. Concept of Asset

- An **asset** can be:
  - a **Dataset** `D` (data provider),
  - an **Application** `A` (ML code provider).
- Raw data/code **never** live on-chain – only metadata and pointers.

### 1.2. Storage Layout (Conceptual)

For each `assetId`:

- `assetType`: `Dataset` or `Application`
- `owner`: Ethereum address of provider (dataset or app)
- `encryptedUri`: string, e.g. `ipfs://<CID>` for encrypted bytes `Enc(asset, K_asset)`
- `manifestUri`: string, e.g. `ipfs://<CID_manifest>` for manifest `μ`
- `contentHash`: SHA-256 (or similar) of **plaintext** asset  
  (used off-chain by Executor for integrity checks)
- `price`: price in wei
- `bloomFilter`: bytes (for datasets only) encoding **whitelisted apps that can use this dataset for free**
- `active`: bool, whether new acquisitions are allowed

Additionally:

- `accessRights[user, datasetId, applicationId]` → `bool`  
  (implemented via `mapping(bytes32 => bool)` using `keccak256(datasetId, applicationId, user)`)

---

### 1.3. Smart Contract Functions

#### 1.3.1. Registration

`registerAsset(assetType, encryptedUri, manifestUri, contentHash, price, bloomFilter) → assetId`

- Called by **asset owner** (dataset or app provider).
- Creates a new `Asset` and stores all metadata.
- Emits `AssetRegistered` event.

#### 1.3.2. Acquisition of Access Rights

`purchaseAccess(datasetId, applicationId) payable`

- Called by **user** (the one who wants to run `A` on `D`).
- Requirements:
  - `datasetId` exists `&&` `assetType == Dataset && active == true`
  - `applicationId` exists `&&` `assetType == Application && active == true`
  - `msg.value >= price(D) + price(A)`
- Effects:
  - Marks `accessRights[user, D, A] = true`
  - Transfers `price(D)` to dataset owner, `price(A)` to app owner
  - Refunds change if any
  - Emits `AccessPurchased(D, A, user, datasetPrice, appPrice)`

> **Note:** in the DNAT paper, “free by whitelist” logic is mainly enforced **off-chain** by the Executor using manifests and Bloom filters. We kept that approach (simple on-chain logic).

#### 1.3.3. Asset Revocation / Update

- `updateAsset(assetId, newPrice, newActive)`
  - Only `owner` can call.
  - Updates `price` and `active`.
- `revokeAsset(assetId)`
  - Marks `active = false`.
  - Existing access rights remain valid (history is immutable).

#### 1.3.4. View Helpers

- `hasAccess(user, datasetId, applicationId) → bool`
  - Used by Executor or clients to check rights.
- `getAsset(assetId) → (assetType, owner, encryptedUri, manifestUri, contentHash, price, bloomFilter, active)`
  - Used off-chain by client/Executor to retrieve IPFS URIs & hashes.

---

## 2. Asset Registration Flow

**Goal:** make a dataset `D` or application `A` available in the marketplace while keeping it confidential.

### 2.1. Steps for a Dataset `D` (similar for Application `A`)

1. **Owner prepares the asset**
   - Dataset provider has plaintext dataset `D_plain`.

2. **Encrypt the asset**
   - Generate a symmetric key `K_D`.
   - Compute encrypted bytes:  
     `D_enc = Enc(D_plain, K_D)`  
     (algorithm chosen by you; AES-GCM is typical).

3. **Upload encrypted asset to IPFS**
   - Add `D_enc` to IPFS:
     - `CID_D_enc = ipfs.add(D_enc)`
   - Add dataset manifest `μ_D` to IPFS:
     - `CID_μ_D = ipfs.add(manifest-D.json)`
   - `encryptedUri = "ipfs://CID_D_enc"`
   - `manifestUri = "ipfs://CID_μ_D"`

4. **Store key in SCONE CAS (KMS)**
   - Send `K_D` to CAS, **with a policy**:
     - e.g., “only SGX enclave with MREnclave = X can retrieve this key”, possibly restricted to certain Executors.
   - CAS stores `K_D` and the policy; the owner **does not expose `K_D` to others**.

5. **Register asset on Ethereum**
   - Compute `contentHash_D = SHA256(D_plain)`.
   - Call `registerAsset` on `DnatMarketplace`:
     - `assetType = Dataset`
     - `encryptedUri = ipfs://CID_D_enc`
     - `manifestUri = ipfs://CID_μ_D`
     - `contentHash = contentHash_D`
     - `price = datasetPrice`
     - `bloomFilter = BF_D` (Bloom filter encodes whitelisted apps for free usage)
   - The contract stores metadata and emits `AssetRegistered`.

At the end of registration:

- **Blockchain** knows:
  - pointer to encrypted dataset (`encryptedUri`),
  - pointer to manifest (`manifestUri`),
  - owner, price, Bloom filter, content hash.
- **IPFS** stores encrypted bytes and manifest.
- **CAS** stores `K_D` with SGX attestation policy.

---

## 3. Acquiring Assets’ Access Rights

**Goal:** let a user pay for the right to run an application `A` over a dataset `D`.

### 3.1. Assets Involved

- At least one **dataset** `D`.
- At least one **application** `A`.

### 3.2. Normal Paid Access

1. **User chooses** `D` and `A`.
2. **User calls** `purchaseAccess(D_id, A_id)` on the smart contract:
   - Sends ETH: `msg.value >= price(D) + price(A)`.
3. **Smart contract checks**:
   - `D` is a dataset and active.
   - `A` is an application and active.
4. **Payments:**
   - `price(D)` → dataset owner address.
   - `price(A)` → application owner address.
5. **Access recording:**
   - `accessRights[user, D, A] = true`.
   - Emits `AccessPurchased(D, A, user, ...)`.

### 3.3. Whitelisted Free Access

- The **dataset manifest** and **Bloom filter** define which applications `A` can access `D` for **free**.
- DNAT’s design:
  - The **Executor** uses the Bloom filter + manifest to verify free-access conditions.
  - The smart contract still records access (so we have traceability), but *payment amount can be zero* for the whitelisted combination.
- Implementation detail (your system):
  - You can either:
    - handle free/paid logic entirely off-chain (just record the fact of access on-chain), or
    - extend `purchaseAccess` to accept a “free flag” validated by the Executor or client.

---

## 4. Application Execution Flow

**Goal:** securely run `A` over `D` so that **only the SGX enclave** sees plaintext, while we:

- enforce on-chain rights,
- use IPFS for storage,
- use CAS for key release.

### 4.1. External Components

- **Client**: front-end / CLI used by the user.
- **Executor**: SGX-enabled service, conceptually split into:
  - **Untrusted part** (outside enclave):
    - receives execution requests,
    - fetches encrypted assets from IPFS,
    - starts enclaves and passes data.
  - **Trusted part** (inside enclave):
    - talks to CAS (KMS),
    - fetches keys,
    - decrypts and runs code,
    - checks blockchain rights.
- **IPFS node/gateway**: stores `Enc(D, K_D)`, `Enc(A, K_A)`, and manifests.
- **SCONE CAS**: holds `K_D`, `K_A` and enforces SGX attestation policies.
- **Ethereum node / Provider**: lets the enclave read contract state and event logs.

---

### 4.2. High-Level Step-By-Step Execution

Assume user already has `accessRights[user, D, A] = true` on chain.

#### 1. User requests execution

- User uses the **Client** to request:
  - “Run application `A` on dataset `D` with parameters P”.
- Client sends an execution request to the **Executor**:
  - includes `datasetId`, `applicationId`, `userAddress`, and possibly P.

#### 2. Untrusted Executor fetches encrypted assets from IPFS

- Untrusted Executor calls contract `getAsset(D_id)` and `getAsset(A_id)` to get:
  - `encryptedUri_D`, `manifestUri_D`
  - `encryptedUri_A`, `manifestUri_A`
- From `encryptedUri` it derives the IPFS CID.
- It fetches:
  - `Enc(D_plain, K_D)` and `Enc(A_plain, K_A)` from IPFS.

#### 3. First enclave: (re-)encryption under a common key `K_AD`

To ensure both app and dataset can be processed securely in a separate execution enclave:

1. Untrusted Executor starts an **enclave session 1**.
2. Inside enclave 1:
   - It performs SGX attestation with CAS.
   - CAS checks that this is a trusted Executor code (MREnclave matches).
   - CAS releases `K_D` and `K_A` (and may cooperate to derive a new `K_AD`).
   - Enclave 1 decrypts:
     - `D_plain = Dec(Enc(D_plain, K_D), K_D)`
     - `A_plain = Dec(Enc(A_plain, K_A), K_A)`
   - It generates a fresh execution-specific key `K_AD`.
   - It re-encrypts:
     - `Enc_D_AD = Enc(D_plain, K_AD)`
     - `Enc_A_AD = Enc(A_plain, K_AD)`
   - Optionally: computes integrity hashes with `K_AD`:
     - `H_D_AD = H(D_plain, K_AD)`
     - `H_A_AD = H(A_plain, K_AD)`

3. Enclave 1 passes `Enc_D_AD` and `Enc_A_AD` (and/or hashes) back to the untrusted Executor.

> This step can be implemented as one or multiple enclaves; the key idea is:  
> **“Only enclaves see plaintext; everything passed outside is (re)encrypted.”**

#### 4. Second enclave: final execution

1. Untrusted Executor starts **enclave session 2** for the actual computation.
2. Inside enclave 2:
   - Performs SGX attestation with CAS again.
   - CAS releases `K_AD` (or all `K_D`, `K_A`, `K_AD` as per your design).
   - Enclave 2:
     - Decrypts `Enc_D_AD` and `Enc_A_AD` using `K_AD`.
     - Optionally verifies that:
       - `contentHash` from the smart contract matches `SHA256(D_plain)` / `SHA256(A_plain)`.
       - If “free by whitelist”, reads manifests from IPFS and verifies `A` is indeed in `D`’s whitelist.
   - Checks on-chain rights:
     - Calls `hasAccess(user, D, A)` on the contract, or
     - Reads `AccessPurchased` events via Ethereum Provider and verifies tuple `<D, A, user>` exists.
   - If all checks pass:
     - Executes application `A` (ML training/inference) on dataset `D`.
     - Produces result `R` (e.g., model parameters, metrics, predictions).

3. Enclave 2 returns `R` to the untrusted Executor.

#### 5. Logging and returning results

- Optionally, the Executor or client can log **usage events** on the blockchain:
  - e.g., another “execution log” event if you want auditability.
- Untrusted Executor sends the final result `R` back to the Client.
- Client delivers `R` to the user.

---

## 5. Overall Architecture Summary

Putting everything together:

1. **Smart Contract layer (Ethereum)**
   - Stores **asset metadata** and **access rights**.
   - Handles **payments** to dataset and app owners.
   - Exposes `getAsset`, `hasAccess`, and emits events for off-chain components.

2. **Storage layer (IPFS)**
   - Stores encrypted datasets and applications (`Enc(asset, K_asset)`).
   - Stores manifests (`μ`) that describe assets, pricing, whitelists, etc.
   - Access via local IPFS node or remote pinning providers.

3. **Key Management layer (SCONE CAS)**
   - Holds encryption keys `K_D`, `K_A`, etc.
   - Enforces that only **attested SGX enclaves** (trusted Executors) can retrieve keys.
   - Supports generating per-execution keys `K_AD`.

4. **Execution layer (SGX Executor)**
   - Untrusted part:
     - Receives execution requests.
     - Fetches encrypted data/code from IPFS.
     - Orchestrates enclaves.
   - Trusted part (enclave):
     - Retrieves keys from CAS after attestation.
     - Decrypts and re-encrypts data securely.
     - Checks blockchain for rights/metadata.
     - Executes `A` on `D` and returns results.

5. **Client layer**
   - Registers assets (calls smart contract, uploads to IPFS, sends keys to CAS).
   - Lets users acquire rights (pay for D+A).
   - Triggers executions and presents results.

---

## 6. Current Implementation Status (What You’ve Defined)

- **Smart Contract**
  - Asset registration (`registerAsset`)
  - Access acquisition (`purchaseAccess`)
  - Asset revocation/update (`revokeAsset`, `updateAsset`)
  - Helpers: `getAsset`, `hasAccess`

- **Off-chain Flows (Design)**
  - Asset registration:
    - Encrypt → IPFS → CAS → contract call.
  - Access acquisition:
    - User pays → contract pays providers & records rights.
  - Execution:
    - Client → Executor → SGX enclaves → CAS → IPFS → blockchain checks → result to user.

This `.md` file is a **living design doc**; as we refine/implement details (e.g., exact manifest schema, Bloom filter bits, escrowed payments), you can add new sections or change behaviors accordingly.
