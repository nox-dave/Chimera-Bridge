# Task Breakdown: Exchange Wallet Filtering & Targeted Whale Discovery

## Step 1: Implement Exchange Wallet Filter
**Proof of Life**: Function `is_likely_exchange()` correctly identifies known exchange addresses and high-transaction-count addresses (>100k txs)

**Deliverables**:
- Add `KNOWN_EXCHANGE_ADDRESSES` dictionary with Binance wallets
- Implement `is_likely_exchange(address, tx_count)` function
- Integrate filter into `find_high_value_wallets()` to exclude exchange wallets
- Test: Verify Binance 14 (0x28c6c06298d514db089934071355e5743bf21d60) is filtered out

---

## Step 2: DeFi Power User Discovery
**Proof of Life**: Function `find_defi_whales()` returns list of wallets with significant Aave/Compound positions (>$100k)

**Deliverables**:
- Query Aave lending pool contracts for large depositors
- Query Compound cToken contracts for large holders
- Filter by minimum position size (configurable threshold)
- Return addresses with position values and protocols
- Test: Verify at least 5 DeFi whale addresses are discovered

---

## Step 3: NFT Whale Discovery
**Proof of Life**: Function `find_nft_whales()` returns wallets holding significant blue-chip NFT collections (BAYC, CryptoPunks, Azuki, etc.)

**Deliverables**:
- Define list of blue-chip NFT contract addresses
- Query ERC-721 balanceOf for each collection
- Identify wallets with multiple NFTs or high-value holdings
- Return addresses with collection names and NFT counts
- Test: Verify at least 3 NFT whale addresses are discovered

---

## Step 4: DAO Participant Discovery
**Proof of Life**: Function `find_dao_participants()` returns wallets that hold significant governance tokens AND have voting history

**Deliverables**:
- Define major DAO governance token contracts (UNI, AAVE, COMP, etc.)
- Query token balances for governance tokens
- Check voting history via governance contract events
- Filter by minimum token holdings AND active voting
- Return addresses with DAO names, token amounts, and vote counts
- Test: Verify at least 3 active DAO participants are discovered

---

## Step 5: DEX Trader Discovery (Non-Bot)
**Proof of Life**: Function `find_dex_traders()` returns individual wallets with high Uniswap/Curve volume, excluding bot-like patterns

**Deliverables**:
- Query Uniswap V2/V3 Swap events for high-volume traders
- Query Curve pool swap events
- Implement bot detection heuristics:
  - Time-based patterns (24/7 activity = bot)
  - Transaction frequency (too regular = bot)
  - Gas price patterns (always same = bot)
- Filter out bot-like addresses
- Return addresses with DEX names, volumes, and trade counts
- Test: Verify at least 5 individual DEX traders are discovered (not bots)

---

## Step 6: Unified Whale Discovery Pipeline
**Proof of Life**: Function `find_targeted_whales()` combines all discovery methods and returns ranked list of individual whale wallets

**Deliverables**:
- Integrate all discovery functions (DeFi, NFT, DAO, DEX)
- Apply exchange wallet filter to all results
- Deduplicate addresses across categories
- Rank by combined metrics (value, activity, uniqueness)
- Return unified list with category tags
- Test: Verify final list contains 0 exchange wallets and at least 10 individual whales

---

## Step 7: Enhanced Profiling for Individual Whales
**Proof of Life**: Profile generation includes behavioral indicators: timezone patterns, risk appetite, sophistication level, social connections

**Deliverables**:
- Extend `generate_profile()` to include:
  - Timezone inference from activity hours
  - Risk score (DeFi usage, leverage indicators, memecoin exposure)
  - Sophistication indicators (MEV usage, arbitrage patterns, governance participation)
  - Social graph (shared counterparties, DAO memberships)
- Update report generator to display behavioral profile
- Test: Generate profile for discovered whale and verify behavioral indicators are present

---

## Step 8: Integration & CLI Enhancement
**Proof of Life**: `--find-whale` command uses new targeted discovery and excludes exchange wallets by default

**Deliverables**:
- Update `main.py` to use `find_targeted_whales()` instead of `find_high_value_wallets()`
- Add CLI flags:
  - `--defi-only`: Only find DeFi whales
  - `--nft-only`: Only find NFT whales
  - `--dao-only`: Only find DAO participants
  - `--dex-only`: Only find DEX traders
  - `--include-exchanges`: Override exchange filter (default: false)
- Update help text and examples
- Test: Run `python main.py --find-whale` and verify no exchange wallets in output

