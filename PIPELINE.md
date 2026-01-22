# 🔥 CHIMERA - Unified Security Intelligence Pipeline

The Complete Intelligence Platform:

**contractHunter (Basilisk)** → **chimera/bridge.py** → **walletHunter (Gargophias)**

```
COMPLETE WORKFLOW
│
├── Phase 1: Contract Discovery (contractHunter)
│   └── Find vulnerable smart contracts
│
├── Phase 2: Bridge Analysis (chimera/bridge.py)
│   └── Connect contracts to exposed wallets
│
└── Phase 3: Wallet Profiling (walletHunter)
    └── Generate intelligence on at-risk wallets
```

```
ENTRY POINTS
│
├── chimera/menu.py
│   └── Unified menu system (contractHunter + walletHunter + Bridge)
│
├── contractHunter/menu.py
│   └── Contract hunting & vulnerability scanning
│
├── walletHunter/whale_menu.py
│   └── Whale hunting & wallet profiling
│
└── chimera/bridge.py
    └── Direct bridge API (contract → wallets)
```

```
CONTRACT HUNTER PIPELINE
│
├── [1/5] Contract Discovery
│   ├── DeFiLlama protocol discovery
│   ├── Filter by TVL, category, audit status
│   └── Fetch contract addresses
│
├── [2/5] Source Code Fetching
│   ├── Etherscan API (verified contracts)
│   ├── Proxy detection & implementation fetching
│   └── Multi-file contract parsing
│
├── [3/5] Vulnerability Scanning
│   ├── PatternScanner (14+ pattern detectors, free)
│   ├── Slither analysis (20+ detectors, if installed)
│   └── LLM analyzers (12+ specialized analyzers)
│
├── [3.5/5] Finding Validation
│   └── FindingValidator (filters false positives)
│       ├── Validates findings against source code
│       ├── Filters false positives automatically
│       └── Returns only confirmed + needs_review findings
│
├── [4/5] Priority Scoring
│   ├── Severity assessment (Critical/High/Medium/Low)
│   ├── Priority score calculation (0-100)
│   └── Verdict generation
│
└── [5/5] Report Generation & Categorization
    ├── Save to Contracts/_all/{protocol}/
    │   ├── profile.json (with vulnerabilities + verdicts)
    │   ├── summary.txt (human-readable)
    │   ├── scan_results.json
    │   ├── report.md
    │   └── source.sol
    ├── Auto-categorize into archetypes
    │   └── ContractCategorizer (mirrors walletHunter OSINT categorization)
    │       ├── Analyzes vulnerabilities, TVL, audit status, protocol type
    │       ├── Assigns to category folders (🎯_prime_targets, ⚠️_high_vulns, etc.)
    │       └── Creates symlinks from categories to _all/
    └── Generate hunt_YYYYMMDD_HHMMSS.json
```

```
WALLET HUNTER PIPELINE
│
├── [1/9] Wallet Data Collection
│   ├── ETH balance (RPC)
│   ├── Token balances (ERC-20)
│   └── USD value calculation
│
├── [2/9] Transaction Analysis
│   ├── Normal transactions
│   ├── Internal transactions
│   ├── Token transfers
│   └── NFT transfers
│
├── [3/9] Behavioral Intelligence
│   ├── Activity patterns
│   ├── Trading style
│   ├── Sophistication level
│   └── Risk tolerance
│
├── [4/9] Funding Trace
│   ├── Multi-hop funding chain
│   ├── Exchange detection (KYC vector)
│   ├── Mixer detection (Tornado Cash)
│   └── Bridge detection
│
├── [5/9] IPFS OSINT
│   ├── NFT metadata extraction
│   ├── IPFS hash discovery
│   ├── Domain analysis
│   └── Identity pivots (usernames, emails, social)
│
├── [6/9] ENS Resolution
│   ├── Address → ENS name
│   ├── ENS text records
│   └── Social media links
│
├── [7/9] Approval Scanner
│   ├── ERC-20 approval events
│   ├── Unlimited approval detection
│   ├── Contract verification check
│   └── Risk exposure calculation
│
├── [8/9] Token Risk Scanner
│   ├── Honeypot detection
│   ├── Fake token detection
│   ├── Contract age analysis
│   └── Proxy risk assessment
│
└── [9/9] Verdicts & Categorization
    ├── OSINT verdicts (threats, vulnerabilities)
    ├── Behavioral categorization
    └── Priority scoring
```

```
CHIMERA BRIDGE PIPELINE
│
├── Input: Hunt Results (hunt_*.json from contractHunter)
│   ├── Filter by vulnerability severity
│   ├── Process vulnerabilities + verdicts
│   └── Handle multiple protocol name fields
│
├── Step 1: Query Contract Interactions
│   ├── Etherscan transaction history
│   ├── Extract unique wallet addresses
│   ├── Filter known exchanges (Binance, Coinbase, etc.)
│   └── Filter null/burn addresses
│
├── Step 2: Estimate Exposure
│   └── Placeholder (returns 0.0, can be enhanced)
│
├── Step 3: Profile Exposed Wallets (optional)
│   ├── Limit to first 5 wallets per contract
│   ├── 30 second timeout per wallet
│   └── UnifiedProfiler.generate_full_profile()
│
└── Output: Bridge Report
    ├── bridge_YYYYMMDD_HHMMSS.json
    ├── bridge_YYYYMMDD_HHMMSS.md
    ├── Total wallets found
    ├── High-value wallets (>$100k)
    └── Top 20 wallets per contract
```

```
COMPLETE CHIMERA WORKFLOW
│
├── chimera/menu.py [1] Contract Hunter
│   │
│   ├── [1] Hunt Contracts (Full Scan)
│   │   └── scripts/hunt.py --preset full_scan --scan
│   │       │
│   │       ├── DeFiLlama discovery
│   │       ├── Contract address fetching
│   │       ├── Source code retrieval
│   │       ├── PatternScanner + Slither scanning
│   │       └── Save to Contracts/hunt_*.json
│   │
│   ├── [2] Custom Hunt
│   │   └── Configure filters (TVL, category, chain, audit)
│   │
│   ├── [3] View Hunt Results
│   │   └── Browse previous scans
│   │
│   └── [4] Browse Contract Reports
│       └── View vulnerability reports
│
├── chimera/menu.py [2] Wallet Hunter
│   │
│   ├── [1] Hunt Whales
│   │   └── unified_profiler.hunt_whales_unified()
│   │       │
│   │       ├── Discover high-value wallets
│   │       ├── Generate full profiles (9-step pipeline)
│   │       ├── IPFS OSINT (optional)
│   │       └── Auto-categorization
│   │
│   ├── [2] Analyze Address
│   │   └── UnifiedProfiler.generate_full_profile()
│   │
│   ├── [3] Target Search
│   │   └── Filter profiles by criteria
│   │
│   ├── [4] View Profiles
│   │   └── Browse wallet profiles
│   │
│   └── [5] IPFS OSINT Scan
│       └── NFT metadata analysis
│
└── chimera/menu.py [3] Chimera Bridge
    │
    ├── [1] Bridge Hunt Results
    │   └── ChimeraBridge.bridge_from_hunt_results()
    │       │
    │       ├── Load hunt_*.json from contractHunter
    │       ├── Filter by severity (default: HIGH+)
    │       ├── Process vulnerabilities + verdicts
    │       ├── For each contract (default: max 10):
    │       │   ├── Query exposed wallets (default: max 20)
    │       │   ├── Estimate exposure
    │       │   └── Optionally profile wallets (default: disabled)
    │       └── Generate bridge reports (JSON + Markdown)
    │
    └── [2] View Bridge Reports
        └── Browse chimera/reports/bridge_*.json
```

```
CONTRACT HUNTER DETAILED FLOW
│
├── scripts/hunt.py
│   │
│   ├── Step 1: Hunt Contracts (DeFiLlama)
│   │   └── ContractHunter.hunt() or hunt_preset()
│   │       │
│   │       ├── DeFiLlamaClient.find_targets()
│   │       │   ├── Fetch protocols from API
│   │       │   ├── Apply filters (TVL, category, chain, audit)
│   │       │   └── Return List[Protocol]
│   │       │
│   │       └── Address lookup
│   │           ├── Try addresses.py (hardcoded, fast)
│   │           └── Fallback to DeFiLlama detail endpoint
│   │
│   ├── Step 2: Fetch Contract Source
│   │   └── EtherscanClient.get_contract_source()
│   │       │
│   │       ├── Etherscan V2 API (chainid parameter)
│   │       ├── Parse Standard JSON format
│   │       ├── Handle multi-file contracts
│   │       ├── Detect proxy contracts
│   │       └── Fetch implementation if proxy
│   │
│   ├── Step 3: Scan for Vulnerabilities
│   │   └── PatternScanner.scan()
│   │       │
│   │       ├── Layer 1: Pattern Matching (14+ detectors)
│   │       │   ├── Reentrancy, Access Control, Delegatecall
│   │       │   ├── Selfdestruct, Integer Issues, Unchecked Returns
│   │       │   ├── tx.origin, Oracle, Flash Loan, Signature
│   │       │   └── Timestamp, Randomness, msg.value Loop, Init
│   │       │
│   │       ├── Layer 2: Slither Analysis (if installed)
│   │       │   └── 20+ Slither detectors
│   │       │
│   │       └── Return List[Finding]
│   │           ├── vulnerability_type
│   │           ├── severity (Critical/High/Medium/Low)
│   │           ├── confidence (0.0-1.0)
│   │           └── location
│   │
│   ├── Step 3.5: Validate Findings
│   │   └── FindingValidator.validate_findings()
│   │       │
│   │       ├── Checks findings against source code
│   │       ├── Filters false positives (regex/string matching)
│   │       ├── Categorizes: CONFIRMED, FALSE_POSITIVE, NEEDS_REVIEW
│   │       └── Returns only validated findings
│   │
│   ├── Step 4: Generate Verdicts & Priority
│   │   └── ContractHunter._generate_verdicts()
│   │       │
│   │       ├── Audit status verdicts
│   │       ├── Category-based verdicts
│   │       ├── TVL-based verdicts
│   │       └── Priority score calculation (0-100)
│   │           ├── TVL weight
│   │           ├── Vulnerability severity
│   │           └── Audit status
│   │
│   └── Step 5: Save Results & Categorization
│       ├── Save to Contracts/_all/{protocol}/
│       │   ├── profile.json (with vulnerabilities + verdicts)
│       │   ├── summary.txt (Enhanced Report Generator)
│       │   ├── scan_results.json
│       │   ├── report.md
│       │   └── source.sol
│       ├── Enhanced Report Generation
│       │   └── EnhancedReportGenerator.generate_enhanced_report()
│       │       ├── Extracts code context (function names, line numbers)
│       │       ├── Assesses false positive likelihood
│       │       ├── Adds recommendations and references
│       │       └── Handles known audited protocols
│       ├── Auto-categorize into archetypes
│       │   └── ContractCategorizer.categorize_from_hunt_results()
│       │       ├── Analyze vulnerabilities, TVL, audit status
│       │       ├── Assign to category folders (🎯_prime_targets, ⚠️_high_vulns, etc.)
│       │       └── Create symlinks from categories to _all/
│       └── Generate hunt_YYYYMMDD_HHMMSS.json
│
└── Output Structure
    │
    └── Contracts/ (Chimera root)
        ├── _all/ (single source of truth)
        │   └── {protocol_slug}/
        │       ├── profile.json (complete data + vulnerabilities + verdicts)
        │       ├── summary.txt (enhanced report with code context)
        │       ├── source.sol
        │       ├── scan_results.json
        │       └── report.md
        │
        ├── 🎯_prime_targets/ (symlinks - high TVL + vulns + unaudited)
        ├── 🎯_critical_vulns/ (symlinks - CRITICAL findings)
        ├── ⚠️_high_vulns/ (symlinks - HIGH findings)
        ├── 🌉_bridges/ (symlinks - bridge protocols)
        ├── 🏦_lending/ (symlinks - lending protocols)
        ├── 🔀_dex/ (symlinks - DEX protocols)
        ├── 🥩_staking/ (symlinks - staking protocols)
        ├── 💰_high_tvl_unaudited/ (symlinks - >$100M unaudited)
        ├── 🔓_access_control_issues/ (symlinks - access control vulns)
        ├── 🔄_reentrancy_risk/ (symlinks - reentrancy vulns)
        └── ... (other category folders)
        │
        └── hunt_YYYYMMDD_HHMMSS.json
```

```
CONTRACT CATEGORIZER
│
├── Automatic Categorization (runs after each hunt)
│   └── ContractCategorizer.categorize_from_hunt_results()
│       │
│       ├── Analyzes each contract:
│       │   ├── Vulnerability severity (CRITICAL/HIGH/MEDIUM)
│       │   ├── Vulnerability type (reentrancy, access control, etc.)
│       │   ├── Protocol category (bridge, lending, DEX, staking)
│       │   ├── TVL and audit status
│       │   └── Priority score
│       │
│       ├── Assigns to category folders:
│       │   ├── 🎯_prime_targets (>$500M TVL + vulns + unaudited)
│       │   ├── ⚠️_high_vulns (HIGH severity findings)
│       │   ├── 🎯_critical_vulns (CRITICAL findings)
│       │   ├── 🌉_bridges (bridge protocols)
│       │   ├── 🏦_lending (lending protocols)
│       │   ├── 🔀_dex (DEX protocols)
│       │   ├── 🥩_staking (staking protocols)
│       │   ├── 💰_high_tvl_unaudited (>$100M unaudited)
│       │   ├── 🔓_access_control_issues (access control vulns)
│       │   ├── 🔄_reentrancy_risk (reentrancy vulns)
│       │   └── ... (15+ categories)
│       │
│       └── Creates symlinks from categories to _all/
│           └── Single source of truth pattern (mirrors walletHunter)
│
├── Address Database Enhancement
│   ├── Auto-discovers missing addresses from DeFiLlama
│   ├── Tries multiple chains if primary chain fails
│   └── Caches discovered addresses during hunt
│
└── Manual Categorization
    └── scripts/categorize.py
        ├── --hunt-results (categorize from JSON)
        ├── --recategorize (re-categorize all in _all/)
        └── --report (print category summary)
```

```
WALLET HUNTER DETAILED FLOW
│
├── unified_profiler.py
│   │
│   ├── hunt_whales_unified()
│   │   │
│   │   ├── Phase 1: Discover Whales
│   │   │   └── WhaleFinder.find_high_value_wallets()
│   │   │       │
│   │   │       ├── Query top token holders (Moralis API)
│   │   │       ├── RPC balance scanning
│   │   │       ├── Filter exchanges (ExchangeDetector)
│   │   │       ├── Filter contracts
│   │   │       └── Filter mixers
│   │   │
│   │   └── Phase 2: Generate Full Profiles
│   │       └── UnifiedProfiler.generate_full_profile()
│   │           │
│   │           ├── [1/9] Fetch wallet data
│   │           │   ├── RPCClient.get_balance() (ETH)
│   │           │   ├── EtherscanClient.get_token_balances()
│   │           │   └── USD value calculation
│   │           │
│   │           ├── [2/9] Analyze transactions
│   │           │   ├── TransactionAnalyzer.analyze_patterns()
│   │           │   ├── Activity timeline
│   │           │   ├── Frequency analysis
│   │           │   └── Value patterns
│   │           │
│   │           ├── [3/9] Build behavioral intelligence
│   │           │   └── IntelProfiler.build_wallet_intel()
│   │           │       ├── Confidence score
│   │           │       ├── Sophistication level
│   │           │       ├── Trading style
│   │           │       ├── Likely region/timezone
│   │           │       └── Risk tolerance
│   │           │
│   │           ├── [4/9] Trace funding source
│   │           │   └── FundingTracer.trace_funding()
│   │           │       ├── Multi-hop tracing (2-3 hops)
│   │           │       ├── Exchange detection (KYC vector)
│   │           │       ├── Mixer detection (Tornado Cash)
│   │           │       ├── Bridge detection
│   │           │       └── Distributor detection
│   │           │
│   │           ├── [5/9] IPFS OSINT scan
│   │           │   └── IPFSOsint.scan_wallet_ipfs()
│   │           │       ├── Get NFT transfers
│   │           │       ├── Extract IPFS hashes
│   │           │       ├── Fetch metadata (9 gateways)
│   │           │       ├── Analyze domains
│   │           │       └── Extract identity pivots
│   │           │
│   │           ├── [6/9] Resolve ENS
│   │           │   └── ENSResolver.scan_wallet_ens()
│   │           │       ├── Address → ENS name
│   │           │       ├── ENS text records
│   │           │       └── Social media links
│   │           │
│   │           ├── [7/9] Scan token approvals
│   │           │   └── ApprovalScanner.scan_approvals_for_profile()
│   │           │       ├── Get approval events
│   │           │       ├── Analyze spender contracts
│   │           │       ├── Detect unlimited approvals
│   │           │       └── Calculate exposure
│   │           │
│   │           ├── [8/9] Scan token risks
│   │           │   └── TokenRiskScanner.scan_token_risks_for_profile()
│   │           │       ├── Get token holdings
│   │           │       ├── Analyze contract verification
│   │       │       ├── Check honeypot indicators
│   │       │       └── Check impersonation
│   │       │
│   │       └── [9/9] Generate verdicts
│   │           └── OSINTVerdicts.generate_all_verdicts()
│   │               ├── Domain verdicts
│   │               ├── Wallet behavior verdicts
│   │               ├── IPFS verdicts
│   │               ├── ENS verdicts
│   │               ├── Approval risk verdicts
│   │               ├── Funding verdicts
│   │               └── Token risk verdicts
│   │
│   └── Auto-categorization
│       └── OSINTCategorizer.categorize_for_osint()
│           ├── Exclusions (institutions, bots)
│           ├── Vulnerability categories
│           ├── Sophistication categories
│           ├── Behavioral patterns
│           └── Value categories
│
└── Output Structure
    │
    └── profiles/
        ├── _all/ (single source of truth)
        │   └── {address}/
        │       ├── profile.json
        │       ├── score.json
        │       ├── summary.txt
        │       └── ipfs_osint.json (if available)
        │
        ├── 🎯_actionable/ (symlinks, top 50)
        ├── 📦_archive/ (score 20-29)
        ├── 🗑️_trash/ (score < 20, auto-deleted after 7 days)
        │
        └── OSINT Categories
            ├── 🎯_prime_targets/
            ├── 🎰_gamblers/
            ├── 🆕_newcomers/
            ├── 💤_dormant_whales/
            ├── 🐟_easy_targets/
            └── ... (14 total categories)
```

```
CHIMERA BRIDGE DETAILED FLOW
│
├── chimera/bridge.py
│   │
│   ├── ChimeraBridge (ContractWalletBridge alias for compatibility)
│   │   │
│   │   ├── API Key Loading
│   │   │   ├── Constructor parameter
│   │   │   ├── ETHERSCAN_API_KEY env var
│   │   │   ├── ETHERSCAN_KEY env var
│   │   │   └── .env file search (current dir, parent, contractHunter, walletHunter, home)
│   │   │
│   │   ├── ChimeraBridge.bridge_from_hunt_results()
│   │   │   │
│   │   │   ├── Load hunt_*.json from contractHunter
│   │   │   ├── Filter contracts by severity threshold
│   │   │   ├── Process vulnerabilities + verdicts arrays
│   │   │   ├── Handle protocol/protocol_name fields
│   │   │   ├── Skip contracts with empty addresses
│   │   │   │
│   │   │   ├── For each vulnerable contract:
│   │   │   │   ├── Query wallet interactions (Etherscan)
│   │   │   │   ├── Filter exchanges & known contracts
│   │   │   │   ├── Estimate exposure (default: 0.0)
│   │   │   │   └── Optionally profile wallets (walletHunter)
│   │   │   │
│   │   │   └── Generate bridge report (JSON + Markdown)
│   │   │
│   │   ├── analyze_contract()
│   │   │   │
│   │   │   ├── Query contract interactions
│   │   │   │   └── get_contract_interactions()
│   │   │   │       ├── Etherscan API: txlist
│   │   │   │       ├── Extract unique wallet addresses
│   │   │   │       ├── Filter known exchanges (Binance, Coinbase, etc.)
│   │   │   │       └── Filter null/burn addresses
│   │   │   │
│   │   │   ├── Process wallets (default: max 20 per contract)
│   │   │   │   └── Optional profiling (default: disabled)
│   │   │   │       ├── Limit to first 5 wallets
│   │   │   │       ├── 30 second timeout per wallet
│   │   │   │       └── Run in executor (async-safe)
│   │   │   │
│   │   │   └── Return ContractExposure
│   │   │
│   │   └── generate_exposure_summary()
│   │       │
│   │       ├── Text summary format
│   │       ├── Overview stats
│   │       ├── Per-contract breakdown
│   │       └── Top exposed wallets
│   │
│   └── Output Structure
│       │
│       └── chimera/reports/
│           ├── bridge_YYYYMMDD_HHMMSS.json
│           │   ├── contracts_analyzed
│           │   ├── total_wallets_found
│           │   ├── total_exposure_usd
│           │   └── exposures[] (top 20 wallets per contract)
│           │
│           └── bridge_YYYYMMDD_HHMMSS.md
│               ├── Overview table
│               ├── Exposure by contract table
│               └── Contract details with top wallets
```

```
DATA FLOW DIAGRAM
│
└── contractHunter
    │
    ├── DeFiLlama API
    │   └── Protocol discovery
    │
    ├── Etherscan API
    │   └── Contract source fetching
    │
    ├── PatternScanner
    │   └── Vulnerability detection
    │
    └── Output: Contracts/hunt_*.json
        │
        └── chimera/bridge.py
            │
            ├── Etherscan API
            │   └── Transaction queries
            │
            ├── RPC (Web3)
            │   └── Balance queries
            │
            └── walletHunter
                │
                ├── Etherscan API
                │   ├── Transaction history
                │   ├── Token transfers
                │   └── NFT transfers
                │
                ├── RPC (Web3)
                │   ├── Balance queries
                │   └── Contract calls
                │
                ├── IPFS Gateways
                │   └── Metadata fetching
                │
                └── Output: profiles/_all/{address}/
                    │
                    └── chimera/reports/exposure_*.json
```

```
VULNERABILITY DETECTION MATRIX
│
├── contractHunter (PatternScanner)
│   │
│   ├── Pattern-Based Detection (14+ detectors)
│   │   ├── Reentrancy
│   │   ├── Access Control
│   │   ├── Delegatecall
│   │   ├── Selfdestruct
│   │   ├── Integer Overflow
│   │   ├── Unchecked Returns
│   │   ├── tx.origin
│   │   ├── Oracle Manipulation
│   │   ├── Flash Loan
│   │   ├── Signature Replay
│   │   ├── Timestamp Dependence
│   │   ├── Randomness Issues
│   │   ├── msg.value Loop
│   │   └── Initialization Issues
│   │
│   ├── Slither Analysis (20+ detectors, if installed)
│   │
│   └── FindingValidator (False Positive Filter)
│       ├── Validates findings against source code
│       ├── Filters false positives automatically
│       └── Zero LLM required (pure code analysis)
│
└── walletHunter (Security Scanners)
    │
    ├── Approval Scanner
    │   ├── Unlimited approvals
    │   ├── Unverified contracts
    │   ├── New contracts (< 7 days)
    │   └── Known malicious contracts
    │
    └── Token Risk Scanner
        ├── Honeypot detection
        ├── Fake token detection
        ├── Unverified contracts
        └── Proxy risks
```

```
INTELLIGENCE OUTPUTS
│
├── contractHunter Outputs
│   │
│   ├── Contracts/_all/{protocol}/ (Chimera root)
│   │   ├── profile.json (complete data: metadata + vulnerabilities + verdicts)
│   │   ├── summary.txt (human-readable summary)
│   │   ├── source.sol (contract source)
│   │   ├── scan_results.json (vulnerability findings)
│   │   └── report.md (detailed markdown report)
│   │
│   ├── Contracts/{category_folders}/ (symlinks to _all/)
│   │   ├── 🎯_prime_targets/ (high TVL + vulns + unaudited)
│   │   ├── ⚠️_high_vulns/ (HIGH severity findings)
│   │   ├── 🌉_bridges/ (bridge protocols)
│   │   ├── 🏦_lending/ (lending protocols)
│   │   └── ... (15+ category folders)
│   │
│   └── Contracts/hunt_YYYYMMDD_HHMMSS.json
│       ├── timestamp
│       ├── targets[] (protocols analyzed)
│       │   ├── protocol_name
│       │   ├── address
│       │   ├── chain
│       │   ├── tvl
│       │   ├── vulnerabilities[]
│       │   └── priority_score
│       └── summary stats
│
├── walletHunter Outputs
│   │
│   ├── profiles/_all/{address}/
│   │   ├── profile.json (complete wallet data)
│   │   ├── score.json (priority scoring breakdown)
│   │   ├── summary.txt (intelligence report)
│   │   └── ipfs_osint.json (if NFT activity)
│   │
│   └── batch_intelligence/batch_YYYYMMDD_HHMMSS/
│       ├── batch_summary.txt (executive summary)
│       └── batch_data.json (structured data)
│
└── chimera Bridge Outputs
    │
    ├── chimera/reports/bridge_YYYYMMDD_HHMMSS.json
    │   ├── contracts_analyzed
    │   ├── total_wallets_found
    │   ├── total_exposure_usd
    │   └── exposures[] (per contract, top 20 wallets)
    │
    └── chimera/reports/bridge_YYYYMMDD_HHMMSS.md
        ├── Overview table
        ├── Exposure by contract table
        └── Contract details with top wallets
```

```
PRIORITY SCORING SYSTEMS
│
├── contractHunter Priority Score (0-100)
│   │
│   ├── TVL Weight (0-40)
│   │   └── Higher TVL = higher score
│   │
│   ├── Vulnerability Severity (0-40)
│   │   ├── Critical: +30
│   │   ├── High: +20
│   │   ├── Medium: +10
│   │   └── Low: +5
│   │
│   └── Audit Status (0-20)
│       ├── Unaudited: +20
│       ├── Partial audit: +10
│       └── Fully audited: +0
│
└── walletHunter Priority Score (0-100)
    │
    ├── Value Score (0-40)
    │   └── Based on total balance USD
    │
    ├── Vulnerability Score (0-30)
    │   ├── Approval risks
    │   ├── Token risks
    │   ├── Scam exposure
    │   └── Funding source risks
    │
    ├── Confidence Score (0-20)
    │   └── Real-person confidence
    │
    └── Freshness Score (0-10)
        └── Data recency
```

```
VERDICT SYSTEMS
│
├── contractHunter Verdicts
│   │
│   ├── Audit Status
│   │   ├── "UNAUDITED PROTOCOL" (HIGH)
│   │   └── "PARTIALLY AUDITED" (MEDIUM)
│   │
│   ├── Category-Based
│   │   ├── "HIGH-RISK CATEGORY" (Lending, Bridge)
│   │   └── "GROWING PROTOCOL" (HIGH)
│   │
│   └── Vulnerability-Based
│       ├── "CRITICAL VULNERABILITIES FOUND"
│       └── "HIGH VULNERABILITIES FOUND"
│
└── walletHunter Verdicts
    │
    ├── Domain Verdicts
    │   ├── "SCAM NFT AIRDROP DETECTED" (CRITICAL)
    │   └── "SUSPICIOUS NFT AIRDROP" (HIGH)
    │
    ├── Wallet Behavior Verdicts
    │   ├── "ACTIVE PHISHING TARGET" (HIGH)
    │   ├── "NEWCOMER WITH SIGNIFICANT FUNDS" (HIGH)
    │   └── "CONFIRMED INDIVIDUAL" (INFO)
    │
    ├── IPFS Verdicts
    │   ├── "EMAIL ADDRESS LEAKED" (HIGH)
    │   └── "SOCIAL MEDIA LINKED" (HIGH)
    │
    ├── Approval Risk Verdicts
    │   ├── "APPROVAL TO KNOWN MALICIOUS CONTRACT" (CRITICAL)
    │   └── "UNLIMITED APPROVAL TO UNVERIFIED CONTRACT" (CRITICAL)
    │
    ├── Funding Verdicts
    │   ├── "FUNDED VIA MIXER" (CRITICAL)
    │   └── "FUNDING TRACED TO EXCHANGE" (HIGH)
    │
    └── Token Risk Verdicts
        ├── "HOLDING HONEYPOT TOKEN" (CRITICAL)
        └── "HOLDING FAKE TOKEN" (CRITICAL)
```

```
CONFIGURATION
│
├── Environment Variables (.env)
│   │
│   ├── ETHERSCAN_API_KEY (required)
│   │   └── Used by contractHunter, walletHunter, bridge
│   │
│   ├── OPENAI_KEY (optional)
│   │   └── For LLM analyzers in contractHunter
│   │
│   ├── MORALIS_API_KEY (optional)
│   │   └── For whale discovery in walletHunter
│   │
│   ├── ALCHEMY_API_KEY (optional)
│   │   └── For RPC in walletHunter
│   │
│   └── RPC_URL (optional)
│       └── Fallback RPC endpoint
│
├── chimera/config.py
│   │
│   ├── API Keys (centralized)
│   ├── Chain configurations
│   ├── Thresholds (MIN_EXPOSURE_USD, HIGH_VALUE_THRESHOLD)
│   └── Rate limits
│
└── Default Settings
    ├── contractHunter: PatternScanner enabled (free)
    ├── walletHunter: IPFS OSINT optional
    └── bridge: Max 20 wallets per contract, profiling disabled by default
```

```
MENU SYSTEM INTEGRATION
│
└── chimera/menu.py (Unified Menu)
    │
    ├── [1] Contract Hunter
    │   ├── [1] Hunt Contracts (Full Scan)
    │   ├── [2] Custom Hunt
    │   ├── [3] View Hunt Results
    │   └── [4] Browse Contract Reports
    │
    ├── [2] Wallet Hunter
    │   ├── [1] Hunt Whales
    │   ├── [2] Analyze Address
    │   ├── [3] Target Search
    │   ├── [4] View Profiles
    │   └── [5] IPFS OSINT Scan
    │
    ├── [3] Chimera Bridge
    │   ├── [1] Bridge Hunt Results
    │   ├── [2] Bridge Single Contract
    │   └── [3] View Exposure Reports
    │
    └── [4] Settings
        ├── View API Keys
        ├── Set Etherscan API Key
        ├── View Paths
        └── Open Chimera Folder
```

```
COMPLETE EXAMPLE WORKFLOW
│
├── Step 1: Hunt Vulnerable Contracts
│   └── chimera/menu.py [1] → [1] Hunt Contracts
│       │
│       └── Output: Contracts/hunt_20250120_120000.json
│           ├── 15 protocols discovered
│           ├── 8 with vulnerabilities
│           └── 3 critical findings
│
├── Step 2: Bridge to Exposed Wallets
│   └── chimera/menu.py [3] → [1] Bridge Hunt Results
│       │
│       ├── Load hunt_20250120_120000.json
│       ├── Filter to HIGH+ vulnerabilities
│       ├── Process 5 vulnerable contracts
│       ├── Query wallet interactions (Etherscan)
│       ├── Filter exchanges & contracts
│       └── Optionally profile top 5 wallets per contract
│       │
│       └── Output: chimera/reports/bridge_*.json
│           ├── Total wallets found: 200+
│           ├── Contracts analyzed: 5
│           └── High-value wallets: 12 (>$100k)
│
└── Step 3: Analyze Top Targets
    └── chimera/menu.py [2] → [2] Analyze Address
        │
        ├── Select high-exposure wallet
        ├── Generate full profile (9-step pipeline)
        ├── Review verdicts
        └── Check OSINT findings
        │
        └── Output: profiles/_all/{address}/
            ├── profile.json
            ├── summary.txt
            └── ipfs_osint.json
```

```
ENHANCED REPORT GENERATOR
│
├── contractHunter/src/reports/enhanced_report_generator.py
│   │
│   ├── Code Context Extraction
│   │   ├── Extracts function names from vulnerability descriptions
│   │   ├── Finds code snippets with line numbers
│   │   └── Highlights vulnerable lines
│   │
│   ├── False Positive Assessment
│   │   ├── Checks known audited protocols
│   │   ├── Evaluates detector confidence
│   │   └── Flags likely false positives
│   │
│   ├── Enhanced Findings
│   │   ├── Code context with highlighted lines
│   │   ├── Recommendations per vulnerability type
│   │   ├── SWC registry references
│   │   └── False positive likelihood (High/Medium/Low)
│   │
│   └── Audit Handling
│       ├── Detects known audited protocols (Arbitrum, Uniswap, etc.)
│       ├── Overrides "unaudited" verdicts with audit info
│       └── Adds audit notice warnings
│
└── Integration
    └── Automatically used in ReportGenerator.save_protocol_report()
        └── Generates enhanced summary.txt for all contract reports
```

```
KEY INTEGRATIONS
│
├── contractHunter → bridge
│   │
│   └── hunt_*.json format
│       ├── targets[] (protocols)
│       ├── vulnerabilities[] (findings)
│       └── priority_score
│
├── bridge → walletHunter
│   │
│   └── UnifiedProfiler API
│       ├── generate_full_profile(address)
│       └── Returns complete profile dict
│
└── Shared Data Types (chimera/types.py)
    │
    ├── VulnerableContract
    ├── TrackedWallet
    ├── Exposure
    └── BridgeResult
```

```
OUTPUT ORGANIZATION SUMMARY
│
├── Contracts/ (Chimera root)
│   ├── _all/ (all protocols, single source of truth)
│   ├── 🎯_prime_targets/ (symlinks)
│   ├── ⚠️_high_vulns/ (symlinks)
│   ├── 🌉_bridges/ (symlinks)
│   ├── 🏦_lending/ (symlinks)
│   └── ... (15+ category folders with symlinks)
│
├── Contracts/ (Chimera root)
│   ├── _all/ (all protocols, single source of truth)
│   ├── 🎯_prime_targets/ (symlinks - high TVL + vulns + unaudited)
│   ├── ⚠️_high_vulns/ (symlinks - HIGH severity findings)
│   ├── 🎯_critical_vulns/ (symlinks - CRITICAL findings)
│   ├── 🌉_bridges/ (symlinks - bridge protocols)
│   ├── 🏦_lending/ (symlinks - lending protocols)
│   ├── 🔀_dex/ (symlinks - DEX protocols)
│   ├── 🥩_staking/ (symlinks - staking protocols)
│   ├── 💰_high_tvl_unaudited/ (symlinks - >$100M unaudited)
│   └── ... (15+ category folders with symlinks)
│
├── walletHunter/
│   └── profiles/
│       ├── _all/ (all wallets, single source of truth)
│       ├── 🎯_actionable/ (symlinks, top 50)
│       ├── 📦_archive/ (low priority)
│       └── OSINT categories/ (14 categories)
│
└── chimera/
    └── reports/
        ├── exposure_*.json (per contract)
        └── exposure_summary_*.md (consolidated)
```
