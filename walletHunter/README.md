# Wallet Owner Profiler

![Logo](docs/screenshots/image.png)

OSINT tool for analyzing Ethereum wallet addresses and generating behavioral profiles. Automatically discovers high-value wallets, categorizes them by psychological and behavioral patterns, and organizes everything for analysis.

## Features

**Core Analysis**
- Balance analysis (ETH + all tokens)
- Transaction pattern analysis (timeline, frequency, value)
- Behavioral profiling (active hours, timezone detection, trading style)
- Token activity tracking (ERC-20 interactions)
- NFT activity detection
- Contract interaction mapping
- Address relationship analysis (top senders/recipients)

**Whale Discovery**
- Automatic high-value wallet discovery from top token holders
- RPC-based balance scanning (no API limits)
- Exchange and bot filtering
- Portfolio value calculation

**OSINT Categorization**
Profiles are automatically categorized into behavioral/psychological categories:
- 🎯 Prime Targets (high value + low sophistication)
- 🎰 Gamblers (meme coin traders, high risk)
- 🆕 Newcomers (fresh wallets with money)
- 🏆 Status Seekers (NFT collectors)
- 💤 Dormant Whales (inactive large holders)
- 🐟 Easy Targets (novice users)
- 🦊 Cautious Holders (security-conscious)
- 🧠 DeFi Natives (advanced users)
- And more...

**Profile Management**
- Interactive menu system for all operations
- Automatic triage and categorization
- OSINT-focused organization
- Report generation
- Trash cleanup (auto-deletes low-value profiles after 7 days)

**IPFS OSINT**
- Automatic IPFS hash extraction from NFT metadata
- Metadata analysis (usernames, emails, social links)
- Creator wallet identification
- Timestamp extraction
- Gateway scanning across multiple IPFS nodes
- Integrated into profile generation for NFT collectors

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```bash
ETHERSCAN_API_KEY=your_etherscan_api_key_here
MORALIS_API_KEY=your_moralis_api_key_here
RPC_URL=https://eth.llamarpc.com
```

**Required:**
- **Etherscan API Key**: Get free key from [Etherscan](https://etherscan.io/apis) - used for transaction history

**Optional (recommended for whale finder):**
- **Moralis API Key**: Get free key from [Moralis](https://moralis.io) - 25k requests/day, enables top token holder queries
- **RPC_URL**: Public RPC endpoint (default: llamarpc.com) - used for balance checks

Or set environment variables:
```bash
export ETHERSCAN_API_KEY=your_api_key_here
```

## Usage

### Interactive Menu (Recommended)

```bash
python3 whale_menu.py
```

The menu provides access to:
- Hunt Whales (discover high-value wallets)
- Profile Management (triage, organize, cleanup)
- Analyze Address (single wallet profiling)
- IPFS OSINT Scan (extract IPFS data from NFT metadata)
- View Reports (browse categorized profiles)
- Settings (API key management)

### Command Line

**Analyze a single address:**
```bash
python main.py 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
```

**Find high-value wallets:**
```bash
python main.py --find-whale --min-balance 500000 --limit 20
```

**JSON output:**
```bash
python main.py WALLET_ADDRESS --json
```

**Save to file:**
```bash
python main.py WALLET_ADDRESS --output profile.txt
```

## How It Works

### Whale Hunting

1. Queries top token holders via Moralis API (or scans recent large transactions via RPC)
2. Checks balances via direct RPC calls (no API limits)
3. Filters out known exchanges, contracts, and mixers
4. Calculates total portfolio value (ETH + all tokens)
5. Generates behavioral intelligence profile
6. Categorizes into OSINT behavioral categories
7. Saves to appropriate category folder

**Without Moralis API:** Falls back to RPC scanning (slower but works fine).

### Profile Organization

All discovered profiles are automatically:
- Categorized by behavioral patterns (gamblers, newcomers, etc.)
- Saved to OSINT category folders
- Tagged with vulnerability assessments
- Organized for easy browsing

### IPFS OSINT

For NFT collectors, the system automatically:
- Extracts IPFS hashes from NFT metadata URIs
- Fetches and analyzes metadata from IPFS gateways
- Identifies linked URLs, usernames, emails, social media
- Finds creator wallet addresses
- Extracts timestamps and collection information

This follows the Web3 OSINT hierarchy: Wallet → NFT → IPFS → Identity pivots (usernames, emails, social links).

IPFS scanning runs automatically during profile generation for addresses with NFT activity, or can be run manually from the menu.

**Profile Structure:**
```
profiles/
├── 🎯_prime_targets/
│   └── 0xaddress/
│       ├── profile.json
│       └── summary.txt
├── 🎰_gamblers/
├── 🆕_newcomers/
└── ...
```

### Triage System

Three triage modes available:

**Priority Triage** (`priority_triage/triage.py`) - NEW
- Priority scoring system with automatic triage
- Single source of truth in `_all/` directory
- Actionable targets in `🎯_actionable/` (symlinks)
- Automatic archival and trash cleanup

**Standard Triage** (`priority_triage/legacy_triage.py`)
- Organizes profiles into priority folders
- Creates category links
- Archives old profiles
- Cleans up trash

**OSINT Triage** (`priority_triage/osint_triage.py`)
- Categorizes by behavioral patterns only
- Saves directly to OSINT categories
- No priority folders
- Focused on attack vector classification

Run triage from the menu or directly:
```bash
python3 priority_triage.py --dry-run
python3 -m src.utils.priority_triage.osint_triage --dry-run
python3 -m src.utils.priority_triage.osint_triage
```

## Output

Each profile contains:

**profile.json:**
- Address and balance information
- Transaction counts and patterns
- Risk score and confidence
- OSINT categories assigned
- Behavioral flags
- Token holdings

**summary.txt:**
- Formatted intelligence report
- Behavioral profile
- Activity patterns
- Likely region/timezone
- Attack vector suggestions
- Confidence assessment
- IPFS OSINT findings (if NFT activity detected)

**ipfs_osint.json** (if NFT activity):
- IPFS hashes found
- Metadata analysis
- Linked URLs and social media
- Usernames and emails
- Creator addresses
- Timestamps

## Project Structure

```
WalletOwner-Profiler/
├── whale_menu.py          # Interactive menu system
├── main.py                 # CLI entry point
├── src/
│   ├── core/              # Core analysis engines
│   │   ├── wallet_profiler.py
│   │   ├── whale_finder.py
│   │   ├── transaction_analyzer.py
│   │   └── exchange_detector.py
│   └── utils/             # Utilities
│       ├── profile_saver.py
│       ├── intel_profiler.py
│       ├── osint_categorizer.py
│       └── priority_triage/    # Triage systems
│           ├── triage.py       # NEW: Priority scoring system
│           ├── scoring.py
│           ├── file_ops.py
│           ├── config.py
│           ├── cli.py
│           ├── legacy_triage.py
│           └── osint_triage.py
└── profiles/              # Generated profiles
    ├── 🎯_prime_targets/
    ├── 🎰_gamblers/
    └── ...
```

See `PROCESS_FLOW.md` for detailed architecture.

## Notes

- Uses official APIs (Etherscan, Moralis) and direct RPC calls - no scraping
- Free Etherscan API: 5 calls/second rate limit
- Moralis free tier: 25k requests/day
- RPC calls are unlimited (public endpoints)
- Analysis limited to most recent 1000 transactions per type
- All data is publicly available on-chain
- Contract addresses automatically filtered out
- Low-value profiles auto-deleted from trash after 7 days

## Auto-Start

The menu can launch automatically when opening the project. See `AUTO_START.md` for setup instructions.
