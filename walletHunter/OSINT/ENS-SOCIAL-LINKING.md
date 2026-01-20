# 🌐 ENS Resolution & Social Linking Module

## Overview

The ENS (Ethereum Name Service) Resolution & Social Linking module provides identity pivots by resolving ENS names to addresses, extracting social media links from ENS text records, and verifying connections between wallets and social profiles.

## Entry Points

```
┌─────────────────────────────────────────────────────────────┐
│                     ENTRY DOORS                             │
├─────────────────────────────────────────────────────────────┤
│  Wallet Address    ENS Name    Twitter/Discord    NFT PFP   │
└──────────┬──────────────┬─────────────┬─────────────┬───────┘
           │              │             │             │
           ▼              ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────┐
│                    THE PIVOT POINT                          │
│                                                             │
│                  💎 WALLET ADDRESS 💎                        │
│                                                             │
│         (This is the phone number of Web3)                  │
└─────────────────────────────────────────────────────────────┘
```

## Core Functionality

### 1. ENS Resolution

#### Address → ENS Name
- Resolves wallet address to ENS name (if registered)
- Example: `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045` → `vitalik.eth`

#### ENS Name → Address
- Resolves ENS name to wallet address
- Example: `vitalik.eth` → `0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045`

### 2. ENS Text Records

ENS supports text records that users can set publicly:
- `com.twitter` - Twitter/X username
- `com.discord` - Discord username
- `com.github` - GitHub username
- `url` - Personal website
- `email` - Email address
- `description` - Bio/description
- `avatar` - Profile picture URL

### 3. Social Media Verification

- Cross-reference usernames found in IPFS metadata with ENS records
- Verify Twitter/Discord links are legitimate
- Build identity graph: Wallet → ENS → Social Media

## Implementation Details

### Module: `src/utils/ens_resolver.py`

#### Functions

**`resolve_ens_to_address(ens_name: str, rpc_client) -> Optional[str]`**
- Resolves ENS name to Ethereum address
- Uses ENS resolver contract (0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e)
- Returns checksummed address or None

**`resolve_address_to_ens(address: str, rpc_client) -> Optional[str]`**
- Resolves address to ENS name (reverse lookup)
- Uses reverse resolver
- Returns ENS name (e.g., "vitalik.eth") or None

**`get_ens_text_record(ens_name: str, key: str, rpc_client) -> Optional[str]`**
- Retrieves specific text record from ENS
- Common keys: 'com.twitter', 'com.discord', 'com.github', 'url', 'email'
- Returns text value or None

**`get_all_ens_text_records(ens_name: str, rpc_client) -> Dict[str, str]`**
- Retrieves all text records for an ENS name
- Returns dictionary of key-value pairs

**`check_ens_social_links(ens_name: str, rpc_client) -> Dict[str, str]`**
- Convenience function to get all social links
- Returns: {twitter, discord, github, website, email}

**`scan_wallet_ens(address: str, rpc_client) -> Dict`**
- Complete ENS scan for a wallet
- Returns:
  ```python
  {
    'address': address,
    'ens_name': 'vitalik.eth' or None,
    'text_records': {
      'com.twitter': '@VitalikButerin',
      'com.discord': 'vitalik#1234',
      'url': 'https://vitalik.ca',
      ...
    },
    'social_links': {
      'twitter': 'https://twitter.com/VitalikButerin',
      'discord': 'vitalik#1234',
      'github': 'https://github.com/vitalik',
      'website': 'https://vitalik.ca'
    },
    'has_ens': bool,
    'has_social_links': bool
  }
  ```

### Integration Points

#### 1. IPFS OSINT Scan Integration
- After IPFS scan completes, check if wallet has ENS
- Extract social links from ENS text records
- Cross-reference with usernames found in IPFS metadata
- Add verified social links to report

#### 2. Report Generation
- Add "ENS & Social Identity" section to IPFS report
- Show ENS name if available
- List verified social media links
- Show cross-references between IPFS findings and ENS records

#### 3. Verdict System
- New verdict: **"SOCIAL IDENTITY LINKED"** (HIGH)
  - Triggered when ENS → Twitter/Discord link found
  - Evidence: ENS name, social platform, verified link
  - Action: "Profile target via social media for additional OSINT"

#### 4. Menu Integration
- Add option to `whale_menu.py`: "Check ENS & Social Links"
- Can be run standalone or automatically after IPFS scan

## Workflow Example

```
1. User scans wallet: 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
   │
   ├── IPFS Scan finds:
   │   ├── Username: "@vitalik"
   │   ├── Social link: "twitter.com/vitalikbuterin"
   │   └── Email: "vitalik@example.com"
   │
   └── ENS Resolution:
       ├── Resolve address → ENS: "vitalik.eth"
       ├── Get text records:
       │   ├── com.twitter: "VitalikButerin"
       │   ├── url: "https://vitalik.ca"
       │   └── description: "Ethereum co-founder"
       │
       └── Cross-reference:
           ├── ✅ Twitter matches: @vitalik ↔ VitalikButerin
           └── ✅ Website found: https://vitalik.ca

2. Generate Report:
   └── ENS & Social Identity:
       ├── ENS Name: vitalik.eth
       ├── Verified Social Links:
       │   ├── Twitter: @VitalikButerin (verified via ENS)
       │   └── Website: https://vitalik.ca
       └── Cross-References:
           └── IPFS metadata username matches ENS Twitter

3. Generate Verdict:
   └── ⚠️ [HIGH] SOCIAL IDENTITY LINKED
       Description: Wallet has ENS name with verified social media links
       Evidence:
         • ENS: vitalik.eth
         • Twitter: @VitalikButerin (verified)
         • Website: https://vitalik.ca
       → Action: Profile target via social media for additional OSINT
```

## Technical Implementation

### ENS Resolver Contract
- Main ENS Registry: `0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e`
- Public Resolver: `0x4976fb03C32e5B8cfe2b6cCB31c09Ba78EBaBa41`
- Reverse Resolver: Uses `addr.reverse` subdomain

### Web3 Integration
- Uses existing `RPCClient` from `api_clients.py`
- Requires Web3.py with ENS support
- Handles both mainnet and testnet (if needed)

### Error Handling
- Graceful fallback if ENS resolution fails
- Timeout handling for RPC calls
- Cache results to avoid repeated lookups

## Security Considerations

1. **Public Data Only**: All ENS text records are public on-chain
2. **No Authentication**: We're reading public records, not modifying anything
3. **Rate Limiting**: Respect RPC provider rate limits
4. **Privacy**: Users who set ENS records are making this information public

## Future Enhancements

1. **ENS Subdomain Resolution**: Check for subdomains (e.g., `wallet.vitalik.eth`)
2. **Multi-chain ENS**: Support ENS on other chains (Polygon, etc.)
3. **Historical ENS Records**: Track ENS name changes over time
4. **ENS Avatar Resolution**: Extract and analyze profile pictures
5. **Social Media API Integration**: Verify Twitter/Discord accounts are active
6. **Cross-platform Username Search**: Search for username across multiple platforms

## Integration with Existing Systems

### IPFS OSINT Module
- Enhances findings with verified social links
- Cross-references usernames found in NFT metadata
- Provides additional identity pivots

### Verdict System
- Adds new verdict type for social identity linking
- Provides actionable intelligence for OSINT operations

### Report Generation
- Adds new section to summary.txt
- Integrates seamlessly with existing IPFS report format

## Usage Examples

### Standalone ENS Check
```python
from src.core.api_clients import RPCClient
from src.utils.ens_resolver import scan_wallet_ens

rpc = RPCClient()
result = scan_wallet_ens("0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045", rpc)
print(result['ens_name'])  # "vitalik.eth"
print(result['social_links']['twitter'])  # Twitter link if available
```

### Integrated with IPFS Scan
```python
# Automatically runs after IPFS scan
ipfs_data = scan_wallet_ipfs(address, nft_transfers, rpc)
ens_data = scan_wallet_ens(address, rpc)
# Combine findings in report
```

## Success Metrics

- **ENS Resolution Rate**: % of wallets with ENS names
- **Social Link Discovery**: % of ENS names with social links
- **Cross-Reference Accuracy**: % of IPFS usernames matching ENS records
- **Verdict Generation**: Number of "SOCIAL IDENTITY LINKED" verdicts

## Dependencies

- `web3` - Already in use for RPC calls
- `ens` - ENS utilities (may need to install)
- Existing `RPCClient` from `api_clients.py`

## Testing

Test cases:
1. Resolve known ENS name (e.g., vitalik.eth)
2. Resolve address that has ENS
3. Resolve address without ENS (should return None)
4. Get text records for ENS with social links
5. Get text records for ENS without social links
6. Cross-reference IPFS findings with ENS records

