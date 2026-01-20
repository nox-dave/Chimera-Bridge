# CHIMERA

Unified Security Intelligence Platform for Smart Contract and Wallet Analysis

**Tests** **License:** MIT **Python** 3.10+ **Foundry**

[Overview](#overview) • [Installation](#installation) • [Configuration](#configuration) • [Quick Start](#quick-start) • [Workflow](#workflow) • [Documentation](#documentation)

## Overview

CHIMERA combines three integrated systems for comprehensive security intelligence:

- **contractHunter (Basilisk)** – Discovers and analyzes vulnerable smart contracts
- **walletHunter (Gargophias)** – Profiles and categorizes high-value wallets
- **Bridge** – Connects vulnerable contracts to exposed wallets

### Key Features

**Contract Intelligence**
- DeFiLlama protocol discovery with TVL and category filtering
- Multi-chain contract source fetching (Ethereum, Polygon, Arbitrum, Optimism, Base, BSC, Avalanche)
- Pattern-based vulnerability detection (14+ detectors, free)
- Slither integration (20+ detectors, optional)
- LLM-powered analyzers for deep code analysis
- Priority scoring and automated verdict generation

**Wallet Intelligence**
- High-value wallet discovery via token holder queries and RPC scanning
- 9-step profiling pipeline: data collection, transaction analysis, behavioral intelligence, funding trace, IPFS OSINT, ENS resolution, approval scanning, token risk analysis, verdict generation
- Multi-hop funding source tracing (exchanges, mixers, bridges)
- IPFS metadata extraction and domain analysis
- Automated OSINT categorization (14 behavioral categories)
- Priority scoring with actionable target identification

**Bridge Intelligence**
- Automatic exposure calculation for vulnerable contracts
- On-chain interaction querying to identify at-risk wallets
- Integrated wallet profiling for exposed addresses
- Consolidated exposure reports with risk assessment

**Unified Interface**
- Single menu system for all operations
- Seamless workflow from contract discovery to wallet profiling
- Automated result bridging between systems

## Installation

### Prerequisites

- Python 3.10+
- Foundry (for contract compilation and testing)
- API keys (see Configuration)

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd Chimera

# Install Python dependencies
pip install -r contractHunter/requirements.txt
pip install -r walletHunter/requirements.txt

# Install Foundry (if not already installed)
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

## Configuration

### Environment Variables

Create a `.env` file in the project root or set environment variables:

```bash
# Required
ETHERSCAN_API_KEY=your_etherscan_api_key_here

# Optional (for enhanced features)
OPENAI_KEY=your_openai_key_here              # For LLM analyzers in contractHunter
MORALIS_API_KEY=your_moralis_key_here        # For whale discovery in walletHunter
ALCHEMY_API_KEY=your_alchemy_key_here         # For RPC in walletHunter
RPC_URL=https://eth.llamarpc.com             # Fallback RPC endpoint
```

### API Keys

**Etherscan API Key** (Required)
- Get free key from [Etherscan](https://etherscan.io/apis)
- Used for contract source fetching, transaction queries, and wallet analysis
- Free tier: 5 calls/second

**OpenAI API Key** (Optional)
- Required for LLM-based vulnerability analyzers in contractHunter
- Default models: gpt-4o-mini, gpt-4o
- Can be configured in contractHunter settings

**Moralis API Key** (Optional)
- Used for top token holder queries in walletHunter
- Free tier: 25k requests/day
- Falls back to RPC scanning if not provided

**Alchemy API Key** (Optional)
- Enhanced RPC access for walletHunter
- Falls back to public RPC if not provided

## Quick Start

### Launch Unified Menu

```bash
python3 chimera/menu.py
```

The menu provides access to:
- Contract Hunter (discover and scan vulnerable contracts)
- Wallet Hunter (profile and hunt whale wallets)
- Chimera Bridge (connect contracts to exposed wallets)
- Settings (API key management)

### Basic Workflow

**1. Hunt Vulnerable Contracts**
```bash
# Via unified menu
python3 chimera/menu.py
# Select [1] Contract Hunter → [1] Hunt Contracts

# Or directly
cd contractHunter
python3 scripts/hunt.py --preset full_scan --scan --save
```

**2. Bridge to Exposed Wallets**
```bash
# Via unified menu
python3 chimera/menu.py
# Select [3] Chimera Bridge → [1] Bridge Hunt Results

# Or directly
cd chimera
python3 -c "from bridge import ContractWalletBridge; import asyncio; bridge = ContractWalletBridge(); asyncio.run(bridge.bridge_from_hunt_results('contractHunter/contracts/hunt_YYYYMMDD_HHMMSS.json'))"
```

**3. Profile Wallets**
```bash
# Via unified menu
python3 chimera/menu.py
# Select [2] Wallet Hunter → [1] Hunt Whales

# Or directly
cd walletHunter
python3 unified_profiler.py
```

## Workflow

### Complete Intelligence Pipeline

```
Step 1: Contract Discovery
├── DeFiLlama protocol discovery
├── Filter by TVL, category, audit status
├── Fetch contract addresses
└── Output: contracts/hunt_YYYYMMDD_HHMMSS.json

Step 2: Vulnerability Scanning
├── Fetch verified source from Etherscan
├── Pattern-based detection (14+ detectors)
├── Slither analysis (optional)
└── Output: contracts/_all/{protocol}/scan_results.json

Step 3: Bridge Analysis
├── Load vulnerable contracts from hunt results
├── Query on-chain interactions
├── Calculate exposure amounts
└── Output: chimera/reports/exposure_*.json

Step 4: Wallet Profiling
├── Generate full profiles for exposed wallets
├── 9-step intelligence pipeline
├── OSINT categorization
└── Output: profiles/_all/{address}/

Step 5: Intelligence Reports
├── Exposure summaries
├── Top targets identification
└── Risk assessment
```

### Contract Hunter Workflow

**Hunt Contracts**
```bash
cd contractHunter

# Full scan (recommended)
python3 scripts/hunt.py --preset full_scan --scan --scan-limit 10 --save

# Custom hunt
python3 scripts/hunt.py \
  --min-tvl 100000 \
  --category "Lending" \
  --unaudited \
  --scan \
  --save
```

**View Results**
```bash
# Browse hunt results
python3 menu.py
# Select [9] Hunt Contracts → [3] View Hunt Results

# Or view JSON directly
cat contracts/hunt_YYYYMMDD_HHMMSS.json
```

### Wallet Hunter Workflow

**Hunt Whales**
```bash
cd walletHunter

# Discover and profile high-value wallets
python3 unified_profiler.py

# Or via menu
python3 whale_menu.py
# Select [1] Hunt Whales
```

**Analyze Single Address**
```bash
# Profile specific wallet
python3 main.py 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb

# With IPFS OSINT
python3 main.py 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb --ipfs
```

**Target Search**
```bash
# Search for specific profiles
python3 target_search.py --rich-dumb -v
python3 target_search.py --newcomer --balance ">500k" -v
```

### Bridge Workflow

**Bridge Hunt Results**
```bash
cd chimera

# Process latest hunt results
python3 -c "
from bridge import ContractWalletBridge
import asyncio

bridge = ContractWalletBridge()
asyncio.run(bridge.bridge_from_hunt_results(
    '../contractHunter/contracts/hunt_YYYYMMDD_HHMMSS.json',
    max_contracts=5,
    profile_wallets=True
))
"
```

**Bridge Single Contract**
```bash
cd chimera

python3 -c "
from bridge import ContractWalletBridge
import asyncio

bridge = ContractWalletBridge()
asyncio.run(bridge.find_exposed_wallets(
    contract_address='0x35fA164735182de50811E8e2E824cFb9B6118ac2',
    chain='ethereum',
    vulnerability_info={'severity': 'CRITICAL', 'type': 'reentrancy'},
    limit=50
))
"
```

## Documentation

- **[PIPELINE.md](PIPELINE.md)** – Complete process flow documentation
- **[contractHunter/docs/pipeline.md](contractHunter/docs/pipeline.md)** – Contract Hunter detailed workflow
- **[walletHunter/docs/PIPELINES.md](walletHunter/docs/PIPELINES.md)** – Wallet Hunter detailed workflow

## Project Structure

```
Chimera/
├── contractHunter/          # Contract discovery and analysis
│   ├── scripts/             # Hunt and analysis scripts
│   ├── src/                 # Core analyzers and hunters
│   ├── contracts/           # Hunt results and reports
│   └── challenges/          # Vulnerable contract examples
│
├── walletHunter/            # Wallet profiling and intelligence
│   ├── src/                 # Core profilers and analyzers
│   ├── profiles/            # Generated wallet profiles
│   └── unified_profiler.py  # Main profiling engine
│
└── chimera/                   # Bridge and shared utilities
    ├── bridge.py            # Contract → Wallet connector
    ├── config.py            # Shared configuration
    ├── types.py             # Shared data types
    ├── menu.py              # Unified menu system
    └── reports/             # Exposure reports
```

## Output Organization

**Contract Hunter Outputs**
- `contracts/_all/{protocol}/` – Complete protocol analysis
- `contracts/hunt_*.json` – Hunt results with vulnerabilities
- `contracts/🎯_critical/` – Critical findings (symlinks)
- `contracts/🎯_high/` – High severity findings (symlinks)

**Wallet Hunter Outputs**
- `profiles/_all/{address}/` – Complete wallet profiles (single source of truth)
- `profiles/🎯_actionable/` – Top 50 actionable targets (symlinks)
- `profiles/📦_archive/` – Low priority profiles
- `profiles/{category}/` – OSINT behavioral categories

**Bridge Outputs**
- `chimera/reports/exposure_{contract}.json` – Per-contract exposure reports
- `chimera/reports/exposure_summary_*.md` – Consolidated summaries

## Advanced Usage

### Custom Hunt Presets

```bash
cd contractHunter

# Fresh whales (unaudited, $500k-$50M TVL)
python3 scripts/hunt.py --preset fresh_whales --scan

# Bridge targets
python3 scripts/hunt.py --preset bridge_targets --scan

# Lending risks
python3 scripts/hunt.py --preset lending_risks --scan
```

### Priority Triage

```bash
cd walletHunter

# Run priority scoring and triage
python3 priority_triage.py

# Dry run (preview changes)
python3 priority_triage.py --dry-run
```

### Batch Intelligence

After whale hunts, batch intelligence summaries are automatically generated:
- Executive summary with key stats
- Top targets ranked by actionability
- Threat landscape analysis
- Distribution breakdowns

Location: `batch_intelligence/batch_YYYYMMDD_HHMMSS/`

## Limitations & Considerations

**Rate Limits**
- Etherscan: 5 calls/second (free tier)
- Moralis: 25k requests/day (free tier)
- RPC: Unlimited (public endpoints)

**Codebase Size**
- Contract Hunter: Optimized for DeFi protocols (typically <10k LOC per contract)
- Wallet Hunter: Handles any wallet, limited by API rate limits
- Large codebases may require selective analysis

**API Costs**
- PatternScanner: Free (pattern-based detection)
- Slither: Free (if installed locally)
- LLM Analyzers: Requires OpenAI API key (token costs)
- Etherscan: Free tier sufficient for development

## Contributing

See individual component READMEs:
- [contractHunter/README.md](contractHunter/README.md)
- [walletHunter/README.md](walletHunter/README.md)

## License

MIT

## Responsible Use

**Educational and authorized security research purposes only.**

✅ Test contracts you own or have permission to test  
✅ Analyze publicly available on-chain data  
✅ Use for security research and education  

❌ Do not attack mainnet contracts without authorization  
❌ Do not use for malicious purposes  
❌ Do not violate terms of service of APIs used  
