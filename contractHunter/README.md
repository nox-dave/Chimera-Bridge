# 🔱 Basilisk

<div align="center">
  <img src="Basilisk.svg" alt="Basilisk" width="200"/>
</div>

> **Your personal exploit library with working PoCs.**

A learning-first exploit development environment. Study vulnerabilities, write exploits, prove they work. Companion tool to [Gargophias](https://github.com/your-repo/gargophias) (OSINT) and [TRIDENT](https://github.com/nox-dave/trident-vuln-defi) (vulnerable DeFi platform).

## What Basilisk Is

**An exploit notebook, but in code.**

Every vulnerability you learn becomes a working PoC you can run, test, and reference later.
```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   CYFRIN LESSON                    BASILISK                     │
│   ══════════════                   ════════                     │
│                                                                 │
│   "Reentrancy works like..."  →   exploits/reentrancy/*.sol    │
│                                                                 │
│   You learn it              →     You prove it works            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## What Basilisk Is NOT

| Not This | Why |
|----------|-----|
| A fuzzer | Echidna, Foundry fuzz exist |
| An auto-exploit AI | That's research, not learning |
| A vulnerability scanner | Slither, Mythril exist |

**Basilisk = Your exploit arsenal. Organized, tested, ready to deploy.**

## Quick Start
```bash
# Clone and setup
git clone https://github.com/your-repo/basilisk
cd basilisk
pip install -r requirements.txt

# Set up OpenAI key (optional, for AI-assisted generation)
echo "OPENAI_KEY=your_key_here" > .env

# Install Foundry
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Launch interactive menu
python menu.py
```

### Interactive Menu
```bash
python menu.py
```
Navigate through:
- 🔍 Analyze Contract - Detect vulnerabilities
- ⚔️ Generate Exploit - AI-assisted generation
- 🧪 Test Exploit - Verify with Foundry
- 📚 Browse Challenges - Study vulnerable contracts
- ⚔️ Browse Exploits - View your PoCs
- 📊 View Results - See findings
- 📖 Learning Log - Track progress
- ⚙️ Settings - Configuration

### The Core Loop
```bash
# 1. Study a challenge
cat challenges/reentrancy/VulnerableBank.sol

# 2. Write your exploit
# exploits/reentrancy/VulnerableBank_Exploit.t.sol

# 3. Prove it works
forge test --match-path exploits/reentrancy/

# 4. Document what you learned
# Update LEARNING_LOG.md
```

### AI-Assisted Mode (Optional)
```bash
# Analyze a contract
python scripts/analyze.py reentrancy/VulnerableBank.sol

# Generate exploit from template
python scripts/generate.py reentrancy/VulnerableBank.sol

# Test generated exploit
python scripts/test.py reentrancy/VulnerableBank_Exploit.t.sol
```

## Project Structure
```
basilisk/
│
├── challenges/                 # Vulnerable contracts to learn from
│   ├── reentrancy/
│   │   ├── VulnerableBank.sol
│   │   └── README.md          # The vulnerability explained
│   ├── flash-loan/
│   ├── access-control/
│   ├── oracle-manipulation/
│   └── ...
│
├── exploits/                   # YOUR working PoCs
│   ├── reentrancy/
│   │   └── VulnerableBank_Exploit.t.sol
│   ├── flash-loan/
│   └── ...
│
├── templates/                  # Exploit templates (AI uses these)
│   ├── reentrancy.sol
│   ├── flash_loan.sol
│   └── ...
│
├── src/                        # AI-assisted tooling (optional)
│   ├── analyzers/
│   ├── generators/
│   ├── models/
│   └── utils/
│
├── scripts/
│   ├── analyze.py
│   ├── generate.py
│   └── test.py
│
├── results/
│   └── findings.json
│
├── LEARNING_LOG.md             # Your Cyfrin → Exploit mapping
└── foundry.toml
```

## The Two Modes

### Mode 1: Manual (Recommended for Learning)
```
You study → You write → You test → You understand
```
```bash
# Write your own exploit
vim exploits/reentrancy/MyReentrancyAttack.t.sol

# Test it
forge test --match-path exploits/reentrancy/MyReentrancyAttack.t.sol -vvv
```

### Mode 2: AI-Assisted (For Speed)
```
AI analyzes → AI generates → You verify → You learn
```
```bash
python scripts/generate.py reentrancy/VulnerableBank.sol
```

**Use Mode 2 to get started, but always understand what the exploit does.**

## Learning Log

Track your progress in `LEARNING_LOG.md`:
```markdown
## Reentrancy
- **Learned**: 2026-01-16
- **Cyfrin**: Section 3, Lesson 5
- **Challenge**: challenges/reentrancy/VulnerableBank.sol
- **Exploit**: exploits/reentrancy/VulnerableBank_Exploit.t.sol
- **Pattern**: External call before state update
- **Fix**: CEI (Checks-Effects-Interactions)
- **Gargophias**: "Detect wallets in protocols without CEI"

## Flash Loans
- **Learned**: ...
```

## Working with Chimera wallet intelligence

Contract assessments produced here can be passed to the Chimera menu (`python chimera/menu.py`) for **contract–wallet correlation** and **address intelligence** in walletHunter, so investigators can relate technical findings to on-chain counterparties in a controlled workflow.

## Requirements

- Python 3.10+
- Foundry
- OpenAI API key (optional)

## Responsible Use

**Educational purposes only.**

✅ Test contracts you own  
✅ Learn from intentionally vulnerable contracts  
✅ Build your security skills  

❌ Don't attack mainnet  
❌ Don't be malicious  

## License

MIT