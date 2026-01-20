# 🐋 Wallet Profiler - User Flow Documentation

This document describes all user interaction flows within the Wallet Profiler system. Each flow is currently distinct, though some may be combined in future iterations.

---

## Entry Point

**Main Menu** (`whale_menu.py`)
- Interactive menu system launched via `python3 whale_menu.py`
- Displays total profile count
- Provides access to all major features

---

## Flow 1: 🔍 Hunt Whales

**Purpose:** Discover high-value wallets automatically from token holders

**User Journey:**
1. User selects `[1] 🔍 Hunt Whales` from main menu
2. System prompts for:
   - Minimum balance (USD, default: 100000)
   - Limit (number of wallets, default: 10)
3. System executes whale discovery:
   - Queries top token holders via Moralis API (or RPC fallback)
   - Checks balances via direct RPC calls
   - Filters out exchanges, contracts, and mixers
   - Calculates total portfolio value (ETH + all tokens)
4. For each discovered wallet:
   - Generates behavioral intelligence profile
   - Categorizes into OSINT behavioral categories
   - Saves to appropriate category folder (e.g., `🎰_gamblers/`, `🆕_newcomers/`)
5. System displays results and saves profiles
6. User returns to main menu

**Output:**
- Profile JSON files in category folders
- Each profile includes: balance, transaction analysis, behavioral flags, OSINT categories

**Current State:** Standalone flow - does not trigger IPFS scanning or other analysis

**Future Integration:** Could automatically trigger IPFS OSINT scan for wallets with NFT activity

---

## Flow 2: 📋 Profile Management

**Purpose:** Organize, score, and maintain discovered profiles

**User Journey:**
1. User selects `[2] 📋 Profile Management` from main menu
2. System displays sub-menu:
   - `[1] Run Priority Triage`
   - `[2] Dry Run (Preview Changes)`
   - `[3] Cleanup Trash`
   - `[b] Back`

### Sub-Flow 2.1: Run Priority Triage

**User Journey:**
1. User selects `[1] Run Priority Triage`
2. System executes priority scoring system:
   - Scans all profiles across category folders
   - Keeps most complete version per address
   - Scores each profile (0-100):
     - Value score (0-40): Based on balance
     - Vulnerability score (0-30): Exploitability
     - Confidence score (0-20): Real-person confidence
     - Freshness score (0-10): Data recency
   - Checks disqualifiers (institutions, bots, low balance/confidence)
3. System organizes profiles:
   - **Actionable** (score >= 60): Creates symlinks in `🎯_actionable/` (top 50)
   - **Keep** (score 30-59): Remains in `_all/`
   - **Archive** (score 20-29): Moves to `📦_archive/`
   - **Trash** (score < 20 or disqualified): Moves to `🗑️_trash/`
4. System consolidates to `_all/` directory (single source of truth)
5. System cleans up category folders (removes duplicates, keeps structure)
6. System displays summary statistics
7. User returns to Profile Management menu

**Output:**
- Consolidated profiles in `profiles/_all/{address}/`
- Score JSON files with detailed breakdown
- Symlinks in `🎯_actionable/` for top targets
- Organized archive and trash folders

### Sub-Flow 2.2: Dry Run (Preview Changes)

**User Journey:**
1. User selects `[2] Dry Run (Preview Changes)`
2. System performs same scoring and organization logic
3. System displays what would happen (no files moved)
4. Shows:
   - How many profiles would be actionable/archived/trashed
   - Top 10 actionable targets
   - Sample trash reasons
5. User reviews preview
6. User returns to Profile Management menu

**Output:**
- Console output showing proposed changes
- No file system modifications

### Sub-Flow 2.3: Cleanup Trash

**User Journey:**
1. User selects `[3] Cleanup Trash`
2. System scans `🗑️_trash/` folder
3. System deletes profiles older than 7 days
4. System displays cleanup summary
5. User returns to Profile Management menu

**Output:**
- Deleted old trash profiles
- Cleanup summary

---

## Flow 3: 🔎 Analyze Address

**Purpose:** Generate comprehensive profile for a single wallet address

**User Journey:**
1. User selects `[3] 🔎 Analyze Address` from main menu
2. System prompts for Ethereum address
3. User enters address (must be valid 0x format)
4. System performs analysis:
   - Fetches ETH balance + token balances
   - Retrieves transaction history (normal, internal, token transfers, NFT transfers)
   - Analyzes transaction patterns (timeline, frequency, value)
   - Identifies contract interactions
   - Generates behavioral profile
5. System displays report (text format)
6. User returns to main menu

**Output:**
- Console output with formatted report
- Includes: balance, transaction counts, patterns, behavioral analysis

**Current State:** Standalone flow - does not save profile or trigger IPFS scanning

**Future Integration:** Could automatically save profile and trigger IPFS scan if NFT activity detected

---

## Flow 4: 🌐 IPFS OSINT Scan

**Purpose:** Extract intelligence from NFT metadata stored on IPFS

**User Journey:**
1. User selects `[4] 🌐 IPFS OSINT Scan` from main menu
2. System prompts for Ethereum address
3. User enters address (must be valid 0x format)
4. System fetches NFT transfers for address (last 50)
5. If NFT transfers found:
   - For each NFT contract:
     - Gets current NFT holdings
     - For each token:
       - Retrieves metadata URI
       - Extracts IPFS hash or HTTPS URL
       - Analyzes domain (if HTTPS)
       - Fetches metadata from IPFS gateways (9 gateways, 30s timeout each)
       - Analyzes metadata content
6. System extracts intelligence:
   - IPFS hashes
   - Linked URLs and domains
   - Usernames/handles
   - Email addresses
   - Social media links
   - Creator wallet addresses
   - Timestamps
   - Collection information
7. System performs ENS resolution:
   - Resolves address to ENS name
   - Fetches ENS text records (Twitter, Discord, GitHub)
8. System generates OSINT verdicts:
   - Domain verdicts (scam detection, impersonation)
   - Wallet behavior verdicts (phishing targets, newcomers)
   - IPFS intelligence verdicts (email leaks, social links)
   - ENS verdicts (social identity linked)
9. System generates formatted report
10. System checks if profile exists:
    - If found: Updates `ipfs_osint.json` and appends to `summary.txt`
    - If not found: Prompts user to save to `ipfs_scans/` folder
11. System displays report
12. User returns to main menu

**Output:**
- IPFS OSINT report (formatted text)
- `ipfs_osint.json` file (if profile exists or user saves)
- Updated `summary.txt` (if profile exists)
- OSINT verdicts with severity levels

**Current State:** Standalone flow - requires manual address entry, separate from whale hunting

**Future Integration:** Could be automatically triggered during whale hunting for wallets with NFT activity

---

## Flow 5: 🎯 Target Search

**Purpose:** Search and filter existing profiles by various criteria

**User Journey:**
1. User selects `[5] 🎯 Target Search` from main menu
2. System displays search options:
   - `[1] Interactive Search`
   - `[2] Rich & Dumb (Prime Targets)`
   - `[3] Rich (>$1M)`
   - `[4] Newcomers`
   - `[5] Gamblers`
   - `[6] Easy Targets`
   - `[7] European Whales`
   - `[8] Asia-Pacific Whales`
   - `[9] Scam Victims`
   - `[0] Custom Search`
   - `[b] Back`

### Sub-Flow 5.1: Interactive Search

**User Journey:**
1. User selects `[1] Interactive Search`
2. System launches interactive query interface
3. User can enter queries like:
   - "rich" → High balance targets
   - "dumb" → Low sophistication
   - "newcomer" → Fresh wallets
   - "balance >500k" → Custom balance filter
   - "conf >70" → High confidence
   - "cat gamblers" → Category filter
4. System applies filters and displays results
5. User can:
   - View results in table or verbose format
   - Export address list
   - Clear filters and search again
6. User exits to Target Search menu

### Sub-Flow 5.2-5.9: Preset Searches

**User Journey:**
1. User selects preset search option (2-9)
2. System executes predefined filter:
   - **Rich & Dumb**: High balance + Low sophistication
   - **Rich**: Balance > $1M
   - **Newcomers**: Fresh wallets with funds
   - **Gamblers**: Meme coin traders
   - **Easy Targets**: Novice users
   - **European Whales**: High-value + European timezone
   - **Asia-Pacific Whales**: High-value + Asia-Pacific timezone
   - **Scam Victims**: Wallets with scam NFT airdrops
3. System displays results (verbose format)
4. User returns to Target Search menu

### Sub-Flow 5.0: Custom Search

**User Journey:**
1. User selects `[0] Custom Search`
2. System prompts for custom filters
3. User enters filter string (e.g., `--balance '>500k' --newcomer --confidence '>70'`)
4. System parses and applies filters
5. System displays results
6. User returns to Target Search menu

**Output:**
- Filtered list of matching profiles
- Address, balance, confidence, categories displayed
- Option to export address list

---

## Flow 6: 📊 View Reports

**Purpose:** Browse and view organized profile reports

**User Journey:**
1. User selects `[6] 📊 View Reports` from main menu
2. System displays available folders:
   - Priority folders (high_priority, medium_priority, low_priority, filtered)
   - Category folders (all OSINT categories)
3. User can:
   - Select folder by number/letter to browse profiles
   - View triage report (`[t]`)
   - Open profiles folder in file manager (`[o]`)
   - Go back (`[b]`)

### Sub-Flow 6.1: Browse Profiles

**User Journey:**
1. User selects a folder (priority or category)
2. System displays paginated list of profiles (10 per page)
3. For each profile shows:
   - Address
   - Balance (USD)
   - Confidence score
4. User can:
   - Navigate pages (`n` next, `p` previous)
   - Select profile by number to view details
   - Go back (`b`)

### Sub-Flow 6.2: View Profile Details

**User Journey:**
1. User selects profile from list
2. System displays profile summary:
   - Balance, ETH, Confidence, Category, Priority
   - Indicates if summary.txt exists
3. User can:
   - Open Etherscan (`[e]`)
   - Open Debank (`[d]`)
   - View Summary (`[v]`) - displays full summary.txt
   - Go back (`[b]`)

**Output:**
- Profile browsing interface
- Access to profile files and external links

---

## Flow 7: ⚙️ Settings

**Purpose:** Manage API keys and configuration

**User Journey:**
1. User selects `[7] ⚙️ Settings` from main menu
2. System displays settings menu:
   - `[1] View API Keys`
   - `[2] Set Etherscan API Key`
   - `[3] View Configuration`
   - `[b] Back`

### Sub-Flow 7.1: View API Keys

**User Journey:**
1. User selects `[1] View API Keys`
2. System displays masked API keys (first 10 characters)
3. User returns to Settings menu

### Sub-Flow 7.2: Set Etherscan API Key

**User Journey:**
1. User selects `[2] Set Etherscan API Key`
2. System prompts for API key
3. User enters API key
4. System saves to `.env` file
5. User returns to Settings menu

### Sub-Flow 7.3: View Configuration

**User Journey:**
1. User selects `[3] View Configuration`
2. System displays:
   - Profiles root directory
   - Main script paths
   - Triage script paths
3. User returns to Settings menu

---

## Command Line Flows

Users can also interact with the system via command line (bypassing menu):

### CLI Flow 1: Single Address Analysis
```bash
python main.py 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
python main.py 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb --json
python main.py 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb --output profile.txt
```

### CLI Flow 2: Whale Hunting
```bash
python main.py --find-whale --min-balance 500000 --limit 20
```

### CLI Flow 3: Priority Triage
```bash
python priority_triage.py
python priority_triage.py --dry-run
python priority_triage.py --cleanup-only
```

### CLI Flow 4: Target Search
```bash
python target_search.py -i
python target_search.py --rich-dumb -v
python target_search.py --balance '>500k' --newcomer -v
```

---

## Current Flow Separation

**Currently Distinct Flows:**
- **Hunt Whales** (Flow 1) - Discovery only, saves basic profiles
- **IPFS OSINT Scan** (Flow 4) - Intelligence extraction only, requires manual address entry
- **Analyze Address** (Flow 3) - Analysis only, does not save or trigger IPFS

**Why They're Separate:**
- Whale hunting focuses on discovery and basic profiling
- IPFS scanning is resource-intensive and only relevant for NFT collectors
- Address analysis is quick lookup without persistence

**Future Integration Opportunities:**
1. **Auto-IPFS on Whale Discovery**: Automatically trigger IPFS scan for discovered whales with NFT activity
2. **Auto-Save on Address Analysis**: Save profile when analyzing address, then trigger IPFS if applicable
3. **Unified Profile Generation**: Combine discovery → analysis → IPFS → save in single flow
4. **Batch IPFS Scanning**: Scan IPFS for multiple addresses from search results

---

## Data Flow Summary

```
User Input
    ↓
Main Menu
    ↓
┌─────────────────────────────────────────┐
│  Flow Selection                        │
└─────────────────────────────────────────┘
    ↓
┌──────────┬──────────┬──────────┬──────────┐
│ Hunt     │ Analyze  │ IPFS     │ Search   │
│ Whales   │ Address  │ Scan     │ Targets  │
└──────────┴──────────┴──────────┴──────────┘
    ↓           ↓          ↓          ↓
Profile      Analysis   Intelligence  Filter
Generation   Report     Extraction   Results
    ↓           ↓          ↓          ↓
Save to      Display    Save to     Display
Categories   Only       Profile     Only
    ↓
Profile Management (Triage)
    ↓
Scoring & Organization
    ↓
Actionable/Archive/Trash
```

---

## Notes

- All flows return to main menu after completion
- Profile data persists in `profiles/` directory
- IPFS scanning is optional and separate from basic profiling
- Triage system consolidates all profiles into `_all/` directory
- Search operates on existing profiles only
- CLI access provides programmatic control for automation
