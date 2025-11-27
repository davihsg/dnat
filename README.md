# dnat


# Structure

```
dnat/
├─ README.md
├─ docs/
│  └─ artigo.pdf               # the paper, design notes, etc.
├─ smart-contract/             # everything Ethereum / Solidity
│  ├─ contracts/
│  │  └─ DnatMarketplace.sol   # smart contract
│  ├─ scripts/
│  │  └─ deploy.js             # deploy script (Hardhat example)
│  ├─ test/
│  │  └─ DnatMarketplace.t.js  # tests for the contract
│  ├─ hardhat.config.js        # or foundry.toml if you use Foundry
│  ├─ package.json
│  └─ node_modules/            # (gitignored)
├─ executor/                   # SGX / SCONE executor code
│  ├─ Dockerfile
│  ├─ src/
│  └─ ...
└─ client/                     # web client that calls contract + executor
   ├─ src/
   └─ ...
```