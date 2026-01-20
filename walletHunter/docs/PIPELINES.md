# 🐋 Wallet Profiler - Process Flow

The Intelligence Pipeline:

[1/9] Wallet data
[2/9] Transaction analysis
[3/9] Behavioral intelligence
[4/9] Funding trace
[5/9] IPFS OSINT
[6/9] ENS resolution
[7/9] Approval scanner         ← Smart contract security
[8/9] Token risk scanner       ← Smart contract security (NEW)
[9/9] Verdicts

```
ENTRY POINTS
│
├── whale_menu.py
│   └── Interactive menu system
│
├── main.py
│   ├── Single address analysis
│   └── Whale hunting mode
│
├── priority_triage.py
│   └── Priority scoring & auto-triage system
│
└── target_search.py
    └── Profile search and filtering system
```

```
WHALE HUNTING FLOW
│
├── unified_profiler.py (Unified Whale Hunter)
│   │
│   └── hunt_whales_unified()
│       │
│       ├── Phase 1: Discover Whales
│       │   └── WalletProfiler.find_high_value_wallets()
│       │       └── WhaleFinder.find_high_value_wallets()
│       │           ├── RPCClient.get_balance()
│       │           ├── EtherscanClient.get_token_holders()
│       │           └── ExchangeDetector.is_likely_exchange()
│       │
│       └── Phase 2: Generate Full Profiles
│           └── UnifiedProfiler.generate_full_profile()
│               ├── [1/9] Fetch wallet data (ETH + tokens with USD values)
│               ├── [2/9] Analyze transactions
│               ├── [3/9] Build behavioral intelligence
│               ├── [4/9] Trace funding source (multi-hop funding chain)
│               ├── [5/9] Run IPFS OSINT scan (if NFT activity)
│               ├── [6/9] Resolve ENS
│               ├── [7/9] Scan token approvals (risk analysis)
│               ├── [8/9] Scan token risks (honeypots, fake tokens)
│               └── [9/9] Generate verdicts and categorize
│
└── Batch Intelligence Summary (Auto-Generated)
    │
    └── batch_summary.py
        │
        ├── generate_batch_summary()
        │   ├── Executive summary (key stats, threats detected)
        │   ├── Key findings (threats, opportunities, anomalies)
        │   ├── Top targets (ranked by actionability)
        │   ├── Threat landscape (wallets under attack, scam domains)
        │   ├── Distribution breakdown (confidence, sophistication, region, categories)
        │   └── Recommendations (actionable next steps)
        │
        └── save_batch_summary()
            ├── Create batch_intelligence/batch_YYYYMMDD_HHMMSS/
            ├── Save batch_summary.txt (human-readable report)
            └── Save batch_data.json (structured data)
```

```
SINGLE ADDRESS ANALYSIS FLOW
│
├── main.py <address>
│   │
│   └── WalletProfiler.generate_profile()
│       │
│       ├── RPCClient.get_balance()
│       │   └── ETH balance + token balances
│       │
│       ├── EtherscanClient.get_transactions()
│       │   └── Normal transactions
│       │
│       ├── EtherscanClient.get_internal_transactions()
│       │   └── Internal transactions
│       │
│       ├── EtherscanClient.get_token_transfers()
│       │   └── ERC-20 transfers
│       │
│       ├── EtherscanClient.get_nft_transfers()
│       │   └── ERC-721/1155 transfers
│       │
│       └── TransactionAnalyzer.analyze_patterns()
│           ├── Activity timeline
│           ├── Transaction frequency
│           ├── Value patterns
│           └── Time-based patterns
│
└── ReportGenerator.generate_report()
    └── Text/JSON output
```

```
TRIAGE SYSTEM FLOW
│
├── priority_triage/
│   │
│   ├── triage.py (Priority Scoring System - PRIMARY)
│   │   │
│   │   ├── run_migration()
│   │   │   ├── find_all_profiles() (keeps most complete version)
│   │   │   ├── Score all profiles (value + vulnerability + confidence + freshness)
│   │   │   ├── Consolidate to _all/ (single source of truth)
│   │   │   ├── Create actionable symlinks (top 50, score >= 60)
│   │   │   ├── Archive low scores (20-29)
│   │   │   ├── Trash disqualified/low scores (< 20)
│   │   │   └── Clean category folders (keep structure, remove duplicates)
│   │   │
│   │   └── generate_hitlist()
│   │       └── Markdown report of actionable targets
│   │
│   ├── scoring.py
│   │   ├── PriorityScore dataclass
│   │   ├── calculate_value_score() (0-40: based on balance)
│   │   ├── calculate_vulnerability_score() (0-30: exploitability)
│   │   ├── calculate_confidence_score() (0-20: real-person confidence)
│   │   ├── calculate_freshness_score() (0-10: data recency)
│   │   ├── check_disqualifiers() (auto-trash: institutions, bots, low balance/confidence)
│   │   └── score_profile() (total: 0-100)
│   │
│   ├── file_ops.py
│   │   ├── get_profile_completeness_score() (selects best version)
│   │   ├── find_all_profiles() (keeps most complete version per address)
│   │   ├── setup_directory_structure() (creates _all/, actionable/, archive/, trash/, categories)
│   │   ├── save_profile_to_all() (saves to _all/ with score.json)
│   │   ├── create_actionable_symlinks() (top 50 to 🎯_actionable/)
│   │   ├── move_to_archive() (score 20-29)
│   │   ├── move_to_trash() (score < 20 or disqualified)
│   │   ├── cleanup_old_category_folders() (empties but keeps folders)
│   │   └── cleanup_trash() (auto-delete after 7 days)
│   │
│   ├── config.py
│   │   ├── ACTIONABLE_THRESHOLD = 60
│   │   ├── KEEP_THRESHOLD = 30
│   │   ├── ARCHIVE_THRESHOLD = 20
│   │   ├── MAX_ACTIONABLE = 50
│   │   └── Auto-disqualifiers (institutions, bots, low balance/confidence)
│   │
│   ├── legacy_triage.py (Legacy - kept for compatibility)
│   │   └── Old triage system (category-based organization)
│   │
│   └── osint_triage.py (Legacy - kept for compatibility)
│       └── OSINT-specific categorization triage
```

```
OSINT CATEGORIZATION FLOW
│
└── osint_categorizer.py
    │
    └── categorize_for_osint()
        │
        ├── EXCLUSIONS
        │   ├── 🏢_institutions (tx_count > 50000)
        │   └── 🤖_bots (tx_count > 10000, low confidence)
        │
        ├── VULNERABILITY CATEGORIES
        │   ├── 🎰_gamblers (meme exposure, high frequency)
        │   ├── 🆕_newcomers (fresh wallet, high balance)
        │   ├── 🏆_status_seekers (NFT collectors)
        │   ├── 💤_dormant_whales (high balance, low activity)
        │   └── 🌉_cross_chain_users (multiple bridges)
        │
        ├── SOPHISTICATION CATEGORIES
        │   ├── 🐟_easy_targets (novice, no DeFi)
        │   ├── 🦊_cautious_holders (low activity, conservative)
        │   └── 🧠_defi_natives (advanced DeFi users)
        │
        ├── BEHAVIORAL PATTERNS
        │   ├── 🌙_night_traders (off-hours activity)
        │   ├── 📈_momentum_chasers (pump buyers)
        │   └── 🏛️_governance_voters (DAO participation)
        │
        └── VALUE CATEGORIES
            ├── 💎_high_value (balance > $1M)
            └── 🎯_prime_targets (high value + easy target)
```

```
DATA COLLECTION LAYER
│
├── api_clients.py
│   │
│   ├── EtherscanClient
│   │   ├── get_transactions()
│   │   ├── get_token_balances()
│   │   ├── get_token_holders()
│   │   └── get_nft_transfers()
│   │
│   └── RPCClient
│       ├── get_balance()
│       ├── get_nft_metadata_uri() (ERC-721/1155)
│       └── get_current_nft_holdings()
│
├── exchange_detector.py
│   ├── is_likely_exchange()
│   └── is_institutional_wallet()
│
└── transaction_analyzer.py
    ├── analyze_patterns()
    ├── analyze_token_activity()
    └── analyze_nft_activity()
```

```
INTELLIGENCE ANALYSIS LAYER
│
├── intel_profiler.py
│   │
│   └── build_wallet_intel()
│       │
│       ├── BehavioralProfile
│       │   ├── confidence_score
│       │   ├── sophistication
│       │   ├── risk_tolerance
│       │   ├── trading_style
│       │   ├── likely_region
│       │   ├── meme_exposure
│       │   ├── defi_protocols
│       │   ├── nft_platforms
│       │   └── bridges_used
│       │
│       └── generate_intel_report()
│           └── Formatted summary.txt
│
├── ipfs_osint.py
│   │
│   ├── scan_wallet_ipfs()
│   │   ├── get_nft_transfers()
│   │   ├── get_nft_metadata_uri()
│   │   ├── extract_ipfs_hash()
│   │   ├── extract_domain_from_url()
│   │   ├── fetch_ipfs_content() (9 gateways, 30s timeout)
│   │   ├── fetch_https_metadata()
│   │   └── analyze_ipfs_metadata()
│   │
│   ├── analyze_domain()
│   │   ├── Scam keyword detection
│   │   ├── Token/protocol impersonation
│   │   ├── Suspicious TLD detection
│   │   └── Reputation scoring
│   │
│   └── generate_ipfs_report()
│       ├── IPFS hash analysis
│       ├── Domain intelligence
│       ├── ENS & Social Identity
│       ├── Metadata sources
│       ├── Linked URLs, usernames, emails
│       └── Social media links
│
└── ens_resolver.py
    │
    ├── resolve_address_to_ens()
    │   └── Address → ENS name (reverse lookup)
    │
    ├── resolve_ens_to_address()
    │   └── ENS name → Address
    │
    ├── get_ens_text_records()
    │   └── Extract social links (Twitter, Discord, GitHub)
    │
    └── scan_wallet_ens()
        └── Complete ENS scan with social links
│
├── funding_tracer.py
    │
    ├── FundingTracer
    │   ├── trace_funding() (Multi-hop funding source tracing)
    │   ├── get_first_funding_tx() (First significant ETH inflow)
    │   ├── identify_address() (Exchange, mixer, bridge, distributor detection)
    │   └── generate_verdict() (Funding source verdicts)
    │
    ├── Funding Chain Analysis
    │   ├── Traces back 2-3 hops from target wallet
    │   ├── Identifies known exchanges (KYC vector)
    │   ├── Detects mixers (Tornado Cash - CRITICAL)
    │   ├── Detects bridges (cross-chain funding)
    │   └── Detects distributors (airdrops, vesting)
    │
    ├── Verdict Generation
    │   ├── CRITICAL: Funded via mixer (Tornado Cash)
    │   ├── HIGH: Funding traced to exchange (KYC identity exists)
    │   ├── MEDIUM: Funding via bridge (cross-chain)
    │   ├── LOW: Airdrop/distributor funding
    │   └── INFO: Partial trace (origin not identified)
    │
    └── trace_funding_for_profile()
        └── Returns funding trace data for profile integration
│
├── approval_scanner.py
    │
    ├── ApprovalScanner
    │   ├── get_approval_events() (ERC20 Approval events via Etherscan logs)
    │   ├── analyze_spender() (Contract verification, age, risk analysis)
    │   ├── get_token_info() (Token symbol, decimals, price)
    │   └── scan_wallet() (Complete approval risk scan)
    │
    ├── Risk Detection
    │   ├── Unlimited approvals (type(uint256).max)
    │   ├── Unverified contracts
    │   ├── New contracts (< 7 days = suspicious, < 30 days = new)
    │   ├── Known malicious contracts
    │   └── Total exposure calculation (USD)
    │
    └── scan_approvals_for_profile()
        └── Returns approval data for profile integration
│
├── token_risk_scanner.py
    │
    ├── TokenRiskScanner
    │   ├── scan_wallet() (Scan wallet token holdings for risks)
    │   ├── get_token_holdings() (Fetch all ERC20 tokens)
    │   ├── analyze_token_contract() (Contract verification, age, proxy)
    │   ├── check_honeypot_indicators() (Blacklist, trading restrictions, hidden fees)
    │   └── check_impersonation() (Fake token detection)
    │
    ├── Risk Detection
    │   ├── Honeypot detection (unsellable tokens)
    │   ├── Fake token detection (impersonators)
    │   ├── Unverified contracts
    │   ├── Very new contracts (< 7 days)
    │   └── Proxy contracts (upgradeable risk)
    │
    ├── Verdict Generation
    │   ├── CRITICAL: Holding honeypot token
    │   ├── CRITICAL: Holding fake token (impersonator)
    │   ├── HIGH: Risky token with multiple red flags
    │   ├── MEDIUM: Token with some concerns
    │   └── LOW: Minor token concerns
    │
    └── scan_token_risks_for_profile()
        └── Returns token risk data for profile integration
│
└── osint_verdicts.py
    │
    ├── analyze_domain_for_verdicts()
    │   ├── SCAM NFT AIRDROP DETECTED (CRITICAL)
    │   ├── SUSPICIOUS NFT AIRDROP (HIGH)
    │   └── POTENTIAL IMPERSONATION (MEDIUM)
    │
    ├── analyze_wallet_for_verdicts()
    │   ├── ACTIVE PHISHING TARGET (HIGH)
    │   ├── NEWCOMER WITH SIGNIFICANT FUNDS (HIGH)
    │   ├── HIGH-RISK TRADER PROFILE (MEDIUM)
    │   ├── NO EXCHANGE TRAIL (MEDIUM)
    │   ├── LOW SOPHISTICATION TARGET (MEDIUM)
    │   └── CONFIRMED INDIVIDUAL (INFO)
    │
    ├── analyze_ipfs_for_verdicts()
    │   ├── EMAIL ADDRESS LEAKED (HIGH)
    │   ├── USERNAME DISCOVERED (MEDIUM)
    │   ├── SOCIAL MEDIA LINKED (HIGH)
    │   └── NFT CREATOR IDENTIFIED (LOW)
    │
    ├── analyze_ens_for_verdicts()
    │   ├── SOCIAL IDENTITY LINKED (HIGH)
    │   ├── EMAIL IN ENS RECORD (MEDIUM)
    │   └── PERSONAL WEBSITE LINKED (LOW)
    │
    ├── analyze_approvals_for_verdicts()
    │   ├── APPROVAL TO KNOWN MALICIOUS CONTRACT (CRITICAL)
    │   ├── UNLIMITED APPROVAL TO UNVERIFIED CONTRACT (CRITICAL)
    │   ├── APPROVAL TO VERY NEW CONTRACT (CRITICAL/HIGH)
    │   ├── UNLIMITED APPROVAL TO UNKNOWN CONTRACT (HIGH)
    │   └── UNLIMITED APPROVAL TO KNOWN PROTOCOL (MEDIUM)
    │
    ├── analyze_funding_for_verdicts()
    │   ├── FUNDED VIA MIXER (CRITICAL) - Tornado Cash detected
    │   ├── FUNDING TRACED TO EXCHANGE (HIGH) - KYC identity exists
    │   ├── FUNDED VIA BRIDGE (MEDIUM) - Cross-chain funding
    │   └── FUNDED VIA AIRDROP (LOW) - Protocol distribution
    │
    ├── analyze_token_risks_for_verdicts()
    │   ├── HOLDING HONEYPOT TOKEN (CRITICAL) - Cannot sell
    │   ├── HOLDING FAKE TOKEN (CRITICAL) - Impersonator contract
    │   ├── RISKY TOKEN HOLDING (HIGH) - Multiple red flags
    │   └── TOKEN WITH CONCERNS (MEDIUM) - Some risk indicators
    │
    └── generate_all_verdicts()
        └── format_verdicts_for_report()
```

```
OUTPUT ORGANIZATION
│
├── profiles/
│   │
│   ├── _all/ (SINGLE SOURCE OF TRUTH)
│   │   └── {address}/
│   │       ├── profile.json (with priority_score)
│   │       ├── score.json (detailed scoring breakdown)
│   │       ├── summary.txt (most complete version)
│   │       └── ipfs_osint.json (if available)
│   │
│   ├── 🎯_actionable/ (SYMLINKS - Top 50 targets)
│   │   └── {score:02d}_{address[:12]} → symlink to _all/{address}
│   │
│   ├── 📦_archive/ (Score 20-29)
│   │   └── Low priority profiles
│   │
│   ├── 🗑️_trash/ (Score < 20 or disqualified)
│   │   └── Auto-deleted after 7 days
│   │
│   └── OSINT Categories (Preserved for whale hunter)
│       ├── 🎯_prime_targets/
│       ├── 🎰_gamblers/
│       ├── 🆕_newcomers/
│       ├── 💤_dormant_whales/
│       ├── 🐟_easy_targets/
│       ├── 🦊_cautious_holders/
│       ├── 🧠_defi_natives/
│       └── ... (14 total categories)
│       └── Folders kept but cleaned (duplicates removed)
│
└── batch_intelligence/
    │
    └── batch_YYYYMMDD_HHMMSS/
        ├── batch_summary.txt (human-readable intelligence report)
        └── batch_data.json (structured batch data)
```

```
PROFILE STRUCTURE
│
└── _all/{address}/ (Primary location)
    │
    ├── profile.json
    │   ├── address
    │   ├── balance_usd
    │   ├── priority_score (0-100)
    │   ├── last_triage (timestamp)
    │   ├── tx_count
    │   ├── risk_score
    │   ├── osint_categories
    │   └── transaction_analysis
    │
    ├── score.json
    │   ├── total_score
    │   ├── value_score (0-40)
    │   ├── vulnerability_score (0-30)
    │   ├── confidence_score (0-20)
    │   ├── freshness_score (0-10)
    │   ├── balance_usd
    │   ├── categories
    │   ├── confidence_pct
    │   └── disqualified (bool)
    │
    ├── summary.txt (Most complete version)
    │   ├── Financial summary
    │   ├── Behavioral profile
    │   ├── Activity patterns
    │   ├── Funding Source Trace
    │   ├── IPFS & Domain OSINT Analysis
    │   ├── ENS & Social Identity
    │   └── OSINT Verdicts
    │
    ├── ipfs_osint.json (optional)
    │   ├── ipfs_hashes_found
    │   ├── metadata_analyzed
    │   ├── findings (domains, URLs, usernames, emails)
    │   └── domain_analysis
    │
    ├── funding_trace (in profile.json)
    │   ├── target (wallet address)
    │   ├── total_hops (number of hops traced)
    │   ├── origin_found (bool)
    │   ├── origin_type (exchange/mixer/bridge/distributor)
    │   ├── origin_label (e.g., "Coinbase", "Tornado Cash")
    │   ├── funding_chain (list of hops with addresses, labels, values)
    │   └── verdict (funding source verdict if applicable)
    │
    ├── token_risks (in profile.json)
    │   ├── scan_timestamp
    │   ├── tokens_analyzed
    │   ├── risky_tokens
    │   ├── honeypots_detected
    │   ├── impersonators_detected
    │   ├── has_risky_tokens (bool)
    │   └── verdicts (token risk verdicts)
    │
    └── approval_risk (in profile.json)
        ├── scan_timestamp
        ├── total_approvals
        ├── unlimited_approvals
        ├── high_risk_approvals
        ├── total_exposure_usd
        └── verdicts (approval risk verdicts)
```

```
MENU SYSTEM FLOW
│
└── whale_menu.py
    │
    ├── [1] Hunt Whales
    │   └── main.py --find-whale
    │
    ├── [2] Profile Management
    │   ├── [1] Run Priority Triage (Main action)
    │   │   └── priority_triage.py
    │   │       ├── Score all profiles
    │   │       ├── Consolidate to _all/
    │   │       ├── Create actionable symlinks
    │   │       └── Archive/trash low scores
    │   ├── [2] Dry Run (Preview changes)
    │   └── [3] Cleanup Trash
    │
    ├── [3] Analyze Address
    │   └── main.py <address>
    │
    ├── [4] IPFS OSINT Scan
    │   └── menu_ipfs_scan()
    │       ├── EtherscanClient.get_nft_transfers()
    │       ├── scan_wallet_ipfs()
    │       ├── scan_wallet_ens() (ENS resolution)
    │       ├── generate_ipfs_report()
    │       ├── generate_all_verdicts()
    │       └── Append to summary.txt
    │
    ├── [5] Target Search
    │   ├── [1] Interactive Search
    │   ├── [2] Rich & Dumb (Prime Targets)
    │   ├── [3] Rich (>$1M)
    │   ├── [4] Newcomers
    │   ├── [5] Gamblers
    │   ├── [6] Easy Targets
    │   ├── [7] European Whales
    │   ├── [8] Asia-Pacific Whales
    │   ├── [9] Scam Victims
    │   └── [0] Custom Search
    │
    ├── [6] View Reports
    │   └── Browse category folders
    │
    └── [7] Settings
        └── API key management
```

```
IPFS OSINT SCANNING FLOW
│
├── whale_menu.py [4] IPFS OSINT Scan
│   │
│   └── menu_ipfs_scan()
│       │
│       ├── Input: Ethereum address
│       │
│       ├── EtherscanClient.get_nft_transfers()
│       │   └── Fetch last 50 NFT transfers
│       │
│       └── scan_wallet_ipfs()
│           │
│           ├── For each NFT contract:
│           │   ├── get_current_nft_holdings()
│           │   └── For each token:
│           │       ├── get_nft_metadata_uri()
│           │       ├── extract_domain_from_url()
│           │       ├── analyze_domain()
│           │       ├── extract_ipfs_hash()
│           │       │
│           │       ├── If IPFS hash found:
│           │       │   ├── extract_gateway_from_uri()
│           │       │   └── fetch_ipfs_content()
│           │       │       ├── Try preferred gateway first
│           │       │       └── Fallback through 9 gateways
│           │       │           ├── ipfs.io
│           │       │           ├── gateway.pinata.cloud
│           │       │           ├── cloudflare-ipfs.com
│           │       │           ├── dweb.link
│           │       │           ├── w3s.link
│           │       │           ├── nftstorage.link
│           │       │           └── ... (30s timeout each)
│           │       │
│           │       └── If HTTPS URL:
│           │           └── fetch_https_metadata()
│           │
│           └── analyze_ipfs_metadata()
│               ├── Extract IPFS hashes from images/URLs
│               ├── Extract linked URLs
│               ├── Extract usernames/handles
│               ├── Extract email addresses
│               ├── Extract social media links
│               └── Extract timestamps
│
├── generate_ipfs_report()
│   │
│   ├── Statistics
│   │   ├── NFT transfers analyzed
│   │   ├── Contracts checked
│   │   ├── Tokens scanned
│   │   └── Metadata files fetched
│   │
│   ├── IPFS Hashes
│   │   └── Unique hashes found
│   │
│   ├── Domain Intelligence
│   │   ├── Domain reputation (trusted/suspicious/unknown)
│   │   ├── Scam indicators
│   │   └── Metadata URL count
│   │
│   ├── ENS & Social Identity
│   │   ├── ENS name resolution (address → ENS)
│   │   ├── ENS text records (Twitter, Discord, GitHub)
│   │   ├── Verified social links
│   │   └── Cross-reference with IPFS findings
│   │
│   ├── Metadata Sources
│   │   └── All URIs found
│   │
│   ├── Linked URLs
│   ├── Usernames/Handles
│   ├── Email Addresses
│   ├── Social Media Links
│   ├── Creator Addresses
│   ├── NFT Collections
│   └── Timestamps
│
└── generate_all_verdicts()
    │
    ├── analyze_domain_for_verdicts()
    │   ├── Scam keyword detection
    │   │   └── lucky, free, claim, airdrop, reward, etc.
    │   ├── Token impersonation
    │   │   └── usdc, usdt, eth, btc, etc.
    │   ├── Protocol impersonation
    │   │   └── uniswap, opensea, metamask, etc.
    │   └── Suspicious TLDs
    │       └── .xyz, .top, .win, .click, etc.
    │
    ├── analyze_wallet_for_verdicts()
    │   ├── Dust attack detection
    │   ├── Wallet age vs balance
    │   ├── Meme coin exposure
    │   ├── Exchange interaction patterns
    │   └── Sophistication level
    │
    ├── analyze_ipfs_for_verdicts()
    │   ├── Email leaks
    │   ├── Username discovery
    │   ├── Social media links
    │   └── Creator identification
    │
    └── format_verdicts_for_report()
        ├── Group by severity (CRITICAL → INFO)
        ├── Include evidence
        └── Action recommendations
```

```
VERDICT SYSTEM
│
└── osint_verdicts.py
    │
    ├── Verdict Structure
    │   ├── title (e.g., "SCAM NFT AIRDROP DETECTED")
    │   ├── severity (CRITICAL, HIGH, MEDIUM, LOW, INFO)
    │   ├── category (THREAT, VULNERABILITY, PROFILE, INTEL)
    │   ├── description
    │   ├── evidence (list of supporting facts)
    │   └── action (recommended action)
    │
    ├── Domain Verdicts
    │   ├── 🚨 SCAM NFT AIRDROP DETECTED (CRITICAL)
    │   │   └── Scam keywords + impersonation + suspicious TLD
    │   ├── ⚠️ SUSPICIOUS NFT AIRDROP (HIGH)
    │   │   └── Scam indicators but no clear impersonation
    │   └── ⚡ POTENTIAL IMPERSONATION (MEDIUM)
    │       └── Impersonation detected but no scam keywords
    │
    ├── Wallet Behavior Verdicts (Pattern Engine)
    │   └── analyze_wallet_for_verdicts()
    │       └── PatternEngine.analyze()
    │           ├── Extract signals from profile
    │           ├── Match against pattern templates
    │           └── Generate verdicts from matched patterns
    │               ├── ⚠️ ACTIVE PHISHING TARGET (HIGH)
    │               ├── ⚠️ NEWCOMER WITH SIGNIFICANT FUNDS (HIGH)
    │               ├── ⚡ HIGH-RISK TRADER PROFILE (MEDIUM)
    │               ├── ⚡ NO EXCHANGE TRAIL (MEDIUM)
    │               ├── ⚡ LOW SOPHISTICATION TARGET (MEDIUM)
    │               └── ℹ️ CONFIRMED INDIVIDUAL (INFO)
    │
    ├── IPFS Intelligence Verdicts
    │   ├── ⚠️ EMAIL ADDRESS LEAKED (HIGH)
    │   ├── ⚡ USERNAME DISCOVERED (MEDIUM)
    │   ├── ⚠️ SOCIAL MEDIA LINKED (HIGH)
    │   └── 📌 NFT CREATOR IDENTIFIED (LOW)
    │
    ├── ENS Verdicts
    │   ├── ⚠️ SOCIAL IDENTITY LINKED (HIGH)
    │   │   └── ENS → Twitter/Discord verified
    │   ├── ⚡ EMAIL IN ENS RECORD (MEDIUM)
    │   └── 📌 PERSONAL WEBSITE LINKED (LOW)
    │
    ├── Approval Risk Verdicts
    │   ├── 🚨 APPROVAL TO KNOWN MALICIOUS CONTRACT (CRITICAL)
    │   ├── 🚨 UNLIMITED APPROVAL TO UNVERIFIED CONTRACT (CRITICAL)
    │   ├── 🚨 APPROVAL TO VERY NEW CONTRACT (CRITICAL/HIGH)
    │   ├── ⚠️ UNLIMITED APPROVAL TO UNKNOWN CONTRACT (HIGH)
    │   └── ⚡ UNLIMITED APPROVAL TO KNOWN PROTOCOL (MEDIUM)
    │
    └── Token Risk Verdicts
        ├── 🚨 HOLDING HONEYPOT TOKEN (CRITICAL) - Cannot sell
        ├── 🚨 HOLDING FAKE TOKEN (CRITICAL) - Impersonator contract
        ├── ⚠️ RISKY TOKEN HOLDING (HIGH) - Multiple red flags
        └── ⚡ TOKEN WITH CONCERNS (MEDIUM) - Some risk indicators
```

```
PATTERN ENGINE
│
└── pattern_engine.py
    │
    ├── Signal Extraction
    │   └── Extract metrics from profile data
    │       ├── tx_count, balance_usd, wallet_age_days
    │       ├── tx_frequency, unique_counterparties
    │       ├── round_number_transfers, token_diversity
    │       └── sophistication, confidence_score
    │
    ├── Pattern Templates
    │   ├── exchange_hot_wallet (filters out exchanges)
    │   ├── bot_mev (filters out bots)
    │   ├── fresh_whale_real (new wallet with funds)
    │   ├── scam_nft_victim (phishing target)
    │   ├── nft_collector (NFT-focused wallet)
    │   ├── defi_power_user (advanced DeFi user)
    │   ├── dormant_whale (old inactive wallet)
    │   ├── money_mule (suspicious flow pattern)
    │   ├── low_sophistication_target (novice + high value)
    │   ├── confirmed_individual (high confidence real person)
    │   ├── high_risk_trader (meme coin trader)
    │   └── no_exchange_trail (large holder, no CEX)
    │
    ├── Pattern Matching
    │   ├── Evaluate signals against pattern templates
    │   ├── Require multiple signals (confidence threshold)
    │   └── Match patterns based on signal combinations
    │
    └── Override System
        └── Exchange/bot patterns cancel false positives
            └── Prevents misclassifying exchanges as "NEWCOMER"
```

```
TARGET SEARCH SYSTEM
│
└── target_search.py
    │
    ├── load_all_profiles()
    │   └── Load from _all/ (or scan all if _all doesn't exist)
    │
    ├── Filter Functions
    │   ├── filter_balance() (>1M, >=500k, <100k, etc.)
    │   ├── filter_confidence() (>70, >=80, etc.)
    │   ├── filter_category() (gamblers, newcomers, easy, etc.)
    │   ├── filter_region() (europe, asia, us)
    │   ├── filter_sophistication() (novice, intermediate, advanced)
    │   ├── filter_has_scam_nfts() (scam NFT airdrops - checks verdicts + IPFS)
    │   ├── filter_dust_target() (dust attack targets)
    │   ├── filter_meme_exposure() (meme coin exposure)
    │   ├── filter_has_ens() (ENS names)
    │   └── filter_no_exchange() (no exchange trail)
    │
    ├── Preset Filters
    │   ├── filter_rich_and_dumb() (High balance + Low sophistication)
    │   ├── filter_prime_targets() (High value + Exploitable)
    │   ├── filter_phishing_victims() (Scam victims)
    │   ├── filter_eu_whales() (European high-value)
    │   └── filter_asia_whales() (Asia-Pacific high-value)
    │
    ├── Interactive Mode
    │   ├── Query-based search (rich, dumb, newcomer, etc.)
    │   ├── Advanced filters (balance >500k, conf >70, cat gamblers)
    │   ├── Export results (address list)
    │   └── Clear filters
    │
    └── Output Formatting
        ├── format_results() (table or verbose view)
        └── export_addresses() (address list only)
```

```
BATCH INTELLIGENCE SUMMARY
│
└── batch_summary.py
    │
    ├── Triggered After Whale Hunt
    │   └── Automatically runs after hunt_whales_unified() completes
    │
    ├── generate_batch_summary()
    │   │
    │   ├── Executive Summary
    │   │   ├── Total value tracked
    │   │   ├── Average wallet value
    │   │   ├── Real person confidence (avg)
    │   │   ├── Wallets under attack count
    │   │   └── Scam domains detected count
    │   │
    │   ├── Key Findings
    │   │   ├── 🚨 Active Fresh Whale Lists (wallets under attack)
    │   │   ├── 💎 High-Value Low-Sophistication Targets
    │   │   ├── 🔍 Large Holders Without Exchange Trail
    │   │   ├── 💀 Wallets with Dangerous Approvals (unlimited/high-risk approvals)
    │   │   └── 🪤 Wallets Holding Honeypot Tokens (unsellable tokens)
    │   │
    │   ├── Top Targets (Ranked by Actionability)
    │   │   ├── Address, Balance, Confidence
    │   │   └── Flags (🚨ATTACKED, 💎WHALE, 🐟NOVICE)
    │   │
    │   ├── Active Threat Landscape
    │   │   ├── Wallets under active attack (with scam NFT counts)
    │   │   └── Scam domains detected (from IPFS OSINT)
    │   │
    │   ├── Distribution Breakdown
    │   │   ├── By Confidence (High/Medium/Low)
    │   │   ├── By Sophistication (Intermediate/Novice/Unknown)
    │   │   ├── By Region (with percentages)
    │   │   └── By Category (gamblers, status, easy, etc.)
    │   │
    │   └── Recommendations
    │       ├── Urgent actions (wallets under attack)
    │       ├── High-value opportunities
    │       └── Threat intel (scam domains to report)
    │
    └── save_batch_summary()
        │
        ├── Creates batch_intelligence/batch_YYYYMMDD_HHMMSS/
        │
        ├── batch_summary.txt
        │   └── Human-readable intelligence report
        │
        └── batch_data.json
            ├── generated_at (timestamp)
            ├── batch_size
            ├── parameters (min_balance, limit, include_ipfs)
            ├── total_value_usd
            └── profiles (address, balance, confidence, sophistication, categories)
```

