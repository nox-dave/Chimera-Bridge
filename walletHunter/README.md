# Wallet intelligence (walletHunter)

![Logo](docs/screenshots/image.png)

Ethereum address intelligence for **financial crime and security casework**: traces public on-chain activity, enriches addresses with OSINT where appropriate, and organizes outputs for **investigative triage** (not for unauthorized surveillance).

## Features

**Core Analysis**
- Balance analysis (ETH + all tokens)
- Transaction pattern analysis (timeline, frequency, value)
- Behavioral profiling (active hours, timezone detection, trading style)
- Token activity tracking (ERC-20 interactions)
- NFT activity detection
- Contract interaction mapping
- Address relationship analysis (top senders/recipients)

**High-balance discovery**
- Batch discovery from token holder lists (Moralis) or RPC-assisted scans
- RPC-based balance checks (no API limits on RPC path)
- Exchange and bot filtering where configured
- Portfolio notional estimation for triage

**OSINT categorization**
Profiles can be grouped into behavioral categories (folder names on disk are historical):
- 🎯 Priority review (high balance + low sophistication indicators)
- 🎰 High-velocity speculative activity
- 🆕 Emerging or recently funded accounts
- 🏆 NFT-heavy profiles
- 💤 Inactive large holders
- 🐟 Simplified triage queue indicators
- 🦊 Security-conscious patterns
- 🧠 Advanced DeFi usage patterns
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

**Optional (recommended for holder-assisted discovery):**
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
- Bulk address discovery (high-balance screening)
- Profile management (triage, organize, cleanup)
- Analyze address (single-address intelligence)
- IPFS-linked artifact review (NFT metadata, where applicable)
- View reports (browse categorized profiles)
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

### Bulk discovery workflow

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
- Categorized by behavioral patterns (speculative activity, newcomers, etc.)
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
- Actionable profiles in `🎯_actionable/` (symlinks)
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
- Focused on behavioral classification for triage

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
- Risk and follow-up suggestions
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
