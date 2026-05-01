# CHIMERA

**Security Analysis Pipeline for Smart Contract Risk Discovery**

> Discover vulnerable contracts → Analyze related wallet activity → Produce clear risk reports

---

## What Is This?

Chimera is a three-stage security research toolkit that:

1. **Finds** vulnerable smart contracts across DeFi protocols
2. **Maps** related wallet activity connected to those vulnerabilities
3. **Builds** wallet risk profiles for defensive analysis

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ CONTRACT ANALYSIS│────►│  CHIMERA BRIDGE  │────►│ WALLET ANALYSIS  │
│                  │     │                  │     │                  │
├──────────────────┤     ├──────────────────┤     ├──────────────────┤
│ • DeFiLlama API  │     │ • Transaction    │     │ • Balance check  │
│ • Etherscan      │     │   history query  │     │ • Behavior       │
│ • Pattern scan   │     │ • Wallet extract │     │   analysis       │
│ • Slither        │     │ • Exchange       │     │ • Funding trace  │
│ • Auto-validate  │     │   filtering      │     │ • OSINT modules  │
└──────────────────┘     └──────────────────┘     └──────────────────┘
```

---

## Key Features

### 🔱 Contract Analysis
- Discovers 6000+ protocols via DeFiLlama API
- Fetches verified source code from Etherscan
- Scans with 14+ vulnerability patterns + Slither
- **Auto-validates findings to filter false positives**
- Categorizes by risk archetype

### 🌉 Chimera Bridge
- Connects vulnerable contracts to relevant wallets
- Queries on-chain transaction history
- Filters out exchanges, bots, and contracts
- Estimates USD exposure per wallet
- Ranks wallets by value at risk

### 👁️ Wallet Analysis
- Full 9-stage wallet profiling pipeline
- Behavioral analysis (trading style, sophistication)
- Timezone activity pattern inference
- Funding source tracing (potential exchange funding sources)
- OSINT modules (ENS, IPFS metadata, approvals)

---

## Quick Start

```bash
# Clone and setup
cd Chimera
pip install -r requirements.txt

# Set API keys
export ETHERSCAN_API_KEY=your_key

# Run the menu
python chimera/menu.py
```

---

## Example Workflow

### Step 1: Scan Vulnerable Contracts
```
Menu → [1] `Contract Hunter` module → [1] Full Scan

Output:
  ✅ 30 protocols discovered
  ✅ 7 contracts scanned
  ✅ 30 vulnerabilities found (after validation)
  ✅ Filtered 6.2% false positives
```

### Step 2: Map Related Wallets
```
Menu → [3] Chimera Bridge → [1] Bridge Hunt Results

Output:
  ✅ 5 contracts analyzed
  ✅ 1,295 wallets found
  ✅ $646,659 total exposure
  ✅ 3 high-value wallets (>$100k)
```

### Step 3: Profile High-Risk Wallets
```
Menu → [2] `Wallet Hunter` module → [2] Analyze Address

Output:
  ✅ Portfolio: $125,632
  ✅ 75% confidence: Likely non-institutional wallet
  ✅ Activity pattern: Europe-compatible timezone window (UTC+0 to +3)
  ✅ Funded via: Binance (Potential exchange funding source)
```

---

## Sample Output

### Contract Scan Results
```
🔱 SCAN RESULTS
══════════════════════════════════════════════════

📊 Summary:
   Protocols discovered: 30
   High priority contracts: 20
   Total TVL tracked: $192,544,716,982

🔍 Validation Summary:
   Raw findings: 32
   After validation: 30
   False positives filtered: 2 (6.2%)

🎯 High Priority Contracts:
──────────────────────────────────────────────────

[1] 📊 Base Bridge
    TVL: $3,316,413,394
    Priority Score: 80/100
    Vulnerabilities: 8 (validated)
    • [High] tx.origin Authentication ✅
    • [High] Unchecked Call Return ✅
    • [High] Selfdestruct Present ✅
```

### Bridge Results
```
🌉 CHIMERA BRIDGE REPORT
══════════════════════════════════════════════════

| Contract    | Wallets | Exposure   | High-Value |
|-------------|---------|------------|------------|
| Base Bridge | 321     | $129,679   | 1          |
| Tether Gold | 232     | $508,451   | 2          |
| ether.fi    | 444     | $7,571     | 0          |

Top Wallet by Exposure:
  Address: 0x1f876d92...
  Exposure: $128,030
  Interaction: proveWithdrawalTransaction
```

### Wallet Risk Profile Report
```
╔════════════════════════════════════════════════╗
║       🐋 WALLET RISK PROFILE REPORT            ║
╚════════════════════════════════════════════════╝

Address: 0x1f876d9252596fcaf8d651a6f443ce21ead7f1e1

┌────────────────────────────────────────────────┐
│ ✅ LIKELY NON-INSTITUTIONAL WALLET (75%)       │
│  Profile: Dolphin | Long-term Holder           │
└────────────────────────────────────────────────┘

💰 Portfolio:     $125,632
⏰ Timezone:      Europe (UTC+0 to +3)
🏦 Funded via:    Binance (Potential exchange funding source)
🧠 Sophistication: Advanced
⚠️  Risk Profile:  Conservative

OSINT Verdicts:
  ⚡ NFT COLLECTOR PROFILE
  ⚡ LOWER COMPLEXITY ACTIVITY PATTERN
```

---

## Project Structure

```
Chimera/
├── chimera/
│   ├── menu.py              # Unified menu system
│   ├── bridge.py            # Contract → Wallet bridge
│   └── reports/             # Bridge output
│
├── contractHunter/
│   ├── scripts/
│   │   └── hunt.py          # CLI entry point
│   └── src/
│       ├── hunters/
│       │   └── contract_hunter.py
│       ├── scanners/
│       │   ├── pattern_scanner.py
│       │   └── finding_validator.py  # False positive filter
│       └── fetchers/
│           ├── defillama_client.py
│           └── etherscan_fetcher.py
│
├── walletHunter/
│   ├── whale_menu.py        # Wallet analysis menu
│   └── src/
│       ├── unified_profiler.py
│       ├── intel_profiler.py
│       └── osint/
│
└── Contracts/               # Output directory
    ├── _all/                # All scanned contracts
    ├── priority_review_cases/ # High-value vulnerable contracts
    └── hunt_*.json          # Hunt results
```

---

## Technical Highlights

### FindingValidator
Automatically filters false positives from scanner output:

```python
# Before: Scanner reports 9 HIGH findings
# After:  Validator confirms 8, filters 1 false positive

Elimination rate: 6-100% depending on contract type
Zero LLM required - pure regex/string matching
```

| Finding Type | Validation Method |
|--------------|-------------------|
| tx.origin | Check if `tx.origin` exists in code |
| selfdestruct | Check if `selfdestruct` exists in code |
| unchecked call | Check if `require(success)` follows `.call()` |
| access control | Check if function has modifier |

### Bridge Risk Mapping
```python
# Input: Vulnerable contract
# Output: Ranked list of related wallets by estimated exposure

Process:
1. Query Etherscan for all transactions
2. Extract unique wallet addresses
3. Filter known exchanges (Binance, Coinbase, etc.)
4. Query balances for each wallet
5. Rank by USD exposure
```

---

## Use Cases

| Scenario | Flow |
|----------|------|
| Bug bounty research | Contract analysis module → Manual review |
| Exposure assessment | Full pipeline → Bridge report |
| Wallet investigation | Wallet Analysis → OSINT profile |
| Protocol security audit | Contract analysis + validation |

---

## Requirements

- Python 3.9+
- Etherscan API key (free tier works)
- Optional: Slither (`pip install slither-analyzer`)
- Optional: Moralis API key (for whale discovery)

---

## Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Required
ETHERSCAN_API_KEY=your_etherscan_api_key_here

# Optional (for enhanced features)
OPENAI_KEY=your_openai_key_here              # For LLM analyzers
MORALIS_API_KEY=your_moralis_key_here        # For whale discovery
ALCHEMY_API_KEY=your_alchemy_key_here         # For RPC
RPC_URL=https://eth.llamarpc.com             # Fallback RPC endpoint
```

**Etherscan API Key** (Required)
- Get free key from [Etherscan](https://etherscan.io/apis)
- Free tier: 5 calls/second

**Moralis API Key** (Optional)
- Used for top token holder queries
- Free tier: 25k requests/day
- Falls back to RPC scanning if not provided

---

## Advanced Usage

### Direct CLI Access

**Contract Analysis**
```bash
cd contractHunter
python3 scripts/hunt.py --preset full_scan --scan --save
```

**Wallet Analysis**
```bash
cd walletHunter
python3 unified_profiler.py
python3 main.py 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
```

**Bridge**
```bash
cd chimera
python3 -c "
from bridge import ContractWalletBridge
import asyncio
bridge = ContractWalletBridge()
asyncio.run(bridge.bridge_from_hunt_results('contractHunter/contracts/hunt_YYYYMMDD_HHMMSS.json'))
"
```

### Custom Hunt Presets

```bash
cd contractHunter

# Emerging high-value protocols (unaudited, $500k-$50M TVL)
python3 scripts/hunt.py --preset fresh_whales --scan

# Bridge-focused protocols
python3 scripts/hunt.py --preset bridge_targets --scan

# Lending risks
python3 scripts/hunt.py --preset lending_risks --scan
```

---

## Output Organization

**Contract Analysis Outputs**
- `contracts/_all/{protocol}/` – Complete protocol analysis
- `contracts/hunt_*.json` – Scan results with vulnerabilities
- `contracts/priority_review_cases/` – Prioritized high-value vulnerable contracts

**Wallet Analysis Outputs**
- `profiles/_all/{address}/` – Complete wallet profiles
- `profiles/🎯_actionable/` – Top 50 prioritized review cases
- `profiles/{category}/` – OSINT behavioral categories

**Bridge Outputs**
- `chimera/reports/bridge_*.json` – Per-contract exposure reports
- `chimera/reports/bridge_*.md` – Human-readable summaries

---

## Limitations & Considerations

**Rate Limits**
- Etherscan: 5 calls/second (free tier)
- Moralis: 25k requests/day (free tier)
- RPC: Unlimited (public endpoints)

**Codebase Size**
- Contract Analysis: Optimized for DeFi protocols (typically <10k LOC per contract)
- Large codebases may require selective analysis

**API Costs**
- PatternScanner: Free (pattern-based detection)
- Slither: Free (if installed locally)
- LLM Analyzers: Requires OpenAI API key (optional)
- Etherscan: Free tier sufficient for development

---

## Disclaimer

This tool is for **authorized security research only**. Use responsibly and ethically within the bounds of applicable laws and authorized bug bounty programs.

---

## Author

Built by NoxDave as part of smart contract security research for Softstack internship preparation.

*January 2026*
