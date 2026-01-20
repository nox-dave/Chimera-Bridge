# 🐋 Unified Whale Profiler

The unified profiler combines whale discovery, behavioral analysis, IPFS OSINT, ENS resolution, and verdict generation into a single integrated flow.

## What It Does

**Old Flow (Fragmented):**
1. Hunt Whales → Basic profile saved
2. Manual IPFS Scan → Separate step
3. Manual ENS lookup → Separate step
4. Verdicts → Generated separately

**New Flow (Unified):**
1. Hunt Whales → Complete profile with:
   - Behavioral intelligence
   - IPFS OSINT (if NFT activity detected)
   - ENS resolution
   - OSINT verdicts
   - Automatic categorization
   - Full summary report

## Usage

### Command Line

**Hunt whales with full profiling:**
```bash
python unified_profiler.py --hunt --min-balance 100000 --limit 10
```

**Profile single address:**
```bash
python unified_profiler.py --address 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb
```

**Fast mode (skip IPFS + ENS):**
```bash
python unified_profiler.py --hunt --fast
```

**Skip IPFS only:**
```bash
python unified_profiler.py --hunt --no-ipfs
```

### Python API

```python
from unified_profiler import UnifiedProfiler, ProfileConfig

config = ProfileConfig(
    include_ipfs=True,
    include_ens=True,
    include_verdicts=True,
    save_to_disk=True,
    verbose=True
)

profiler = UnifiedProfiler(config)
profile = profiler.generate_full_profile("0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb")
```

## Configuration

### ProfileConfig Options

- `include_ipfs` (bool): Run IPFS OSINT scan (default: True)
- `include_ens` (bool): Resolve ENS names (default: True)
- `include_verdicts` (bool): Generate OSINT verdicts (default: True)
- `save_to_disk` (bool): Save profile to filesystem (default: True)
- `verbose` (bool): Print progress messages (default: True)

### Global Settings

In `unified_profiler.py`:
- `ENABLE_IPFS_BY_DEFAULT = True`: Enable IPFS by default
- `IPFS_ONLY_IF_NFT_ACTIVITY = True`: Only scan IPFS if NFT activity detected

## Output

Profiles are saved to:
- `profiles/_all/{address}/` - Single source of truth
- `profiles/{category}/{address}/` - Category folders for browsing

Each profile includes:
- `profile.json` - Complete profile data
- `summary.txt` - Formatted intelligence report
- `ipfs_osint.json` - IPFS findings (if available)

## Integration with Existing System

The unified profiler:
- Uses existing `WalletProfiler` for transaction analysis
- Uses existing `IPFS OSINT` scanner
- Uses existing `ENS resolver`
- Uses existing `OSINT categorizer`
- Uses existing `verdict generator`
- Saves in same format as `ProfileSaver`

**Compatible with:**
- Priority triage system (`priority_triage.py`)
- Target search (`target_search.py`)
- Menu system (can be integrated)

## Performance

- **Basic profiling**: ~5-10 seconds per wallet
- **With IPFS**: ~15-30 seconds per wallet (if NFT activity)
- **With ENS**: +1-2 seconds per wallet

IPFS scanning is automatically skipped if:
- `IPFS_ONLY_IF_NFT_ACTIVITY = True` and no NFT activity detected
- `--no-ipfs` flag used
- `--fast` mode enabled

## Future Integration

To integrate into `whale_menu.py`:

```python
def menu_hunt_whales_unified():
    clear_screen()
    print_header("🔍 Hunt Whales (Unified)")
    
    min_balance = get_input("Minimum balance (USD, default 100000): ")
    min_balance = float(min_balance) if min_balance else 100000
    
    limit = get_input("Limit (default 10): ")
    limit = int(limit) if limit else 10
    
    include_ipfs = get_input("Include IPFS OSINT? (y/n, default y): ")
    include_ipfs = include_ipfs != 'n'
    
    from unified_profiler import hunt_whales_unified
    hunt_whales_unified(min_balance=min_balance, limit=limit, include_ipfs=include_ipfs)
    input("\nPress Enter to continue...")
```

## Benefits

1. **Single Pass**: Complete intelligence in one operation
2. **Automatic**: No manual steps required
3. **Comprehensive**: All OSINT data collected together
4. **Consistent**: Same format as existing profiles
5. **Efficient**: Only runs expensive scans when needed
