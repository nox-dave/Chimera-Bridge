# IPFS OSINT Integration

## How It Works

The IPFS OSINT module follows the Web3 OSINT hierarchy:

```
Wallet Address (Entry Point)
    ↓
NFT Transfers Detected
    ↓
Extract IPFS Hashes from Metadata URIs
    ↓
Query IPFS Gateways
    ↓
Analyze Metadata Content
    ↓
Extract Identity Pivots:
    • Usernames/Handles
    • Email addresses
    • Social media links
    • Creator wallet addresses
    • Timestamps
    • Linked URLs
```

## Integration Points

**Automatic Scanning:**
- Runs during whale hunting when NFT activity is detected
- Scans up to 10 NFT contracts, 3 tokens per contract
- Saves findings to `ipfs_osint.json` in profile folder
- Appends IPFS report to `summary.txt`

**Manual Scanning:**
- Menu option: `[4] IPFS OSINT Scan`
- Can scan any address with NFT transfers
- Standalone script: `python3 -m src.utils.ipfs_scanner --address 0x...`

## What It Finds

**From NFT Metadata:**
- IPFS hashes (image, external_url, attributes)
- Collection names
- Creator addresses
- Upload timestamps
- Linked websites/social media

**Extracted Patterns:**
- Email addresses in metadata
- Twitter/Discord usernames
- Social media links
- External URLs
- Creator wallet addresses (for further analysis)

## Use Cases

**Status Seekers (NFT Collectors):**
- Their NFT PFPs are on IPFS
- Metadata often contains social links
- Creator addresses can reveal connections

**Identity Pivots:**
- IPFS hash → Metadata → Username → Social profile
- IPFS hash → Creator wallet → Analyze creator
- Metadata timestamp → Activity timeline

**Deep Dives:**
- When you need to go beyond on-chain analysis
- Finding social media connections
- Identifying creator networks
- Extracting leaked information

## Example Flow

1. Profile shows `🏆_status_seekers` category
2. System detects NFT activity
3. IPFS scanner extracts hashes from NFT metadata
4. Fetches metadata from IPFS gateways
5. Finds Twitter handle in metadata
6. You now have: Wallet → NFT → IPFS → Twitter → Real identity

## Technical Details

**IPFS Gateways Used:**
- ipfs.io
- gateway.pinata.cloud
- cloudflare-ipfs.com
- dweb.link
- gateway.ipfs.io

**Hash Patterns Detected:**
- CIDv0: `Qm...` (44 chars)
- CIDv1: `baf...` (56+ chars)

**Limits:**
- 10 NFT contracts per wallet
- 3 tokens per contract
- 20 total metadata files analyzed
- Prevents rate limiting and timeouts

