# Auto-Start Whale Menu

The whale menu can be configured to run automatically when you open the project. Choose one of the following methods:

## Method 1: Using VS Code/Cursor Workspace (Recommended)

1. Open the project using the workspace file:
   ```bash
   code whale-profiler.code-workspace
   ```
   or in Cursor:
   ```bash
   cursor whale-profiler.code-workspace
   ```

2. The menu should launch automatically when the workspace opens.

## Method 2: Using VS Code/Cursor Tasks

1. Open the project folder in VS Code/Cursor
2. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
3. Type "Tasks: Run Task"
4. Select "Launch Whale Menu"
5. The menu will open in a new terminal

## Method 3: Terminal Auto-Start (For Terminal Users)

Add this to your `~/.bashrc` or `~/.zshrc`:

```bash
# Auto-start whale menu when entering project directory
if [[ "$PWD" == *"WalletOwner-Profiler"* ]]; then
    if [ -f "whale_menu.py" ]; then
        python3 whale_menu.py
    fi
fi
```

Or create an alias:

```bash
alias whale='cd /path/to/WalletOwner-Profiler && python3 whale_menu.py'
```

## Method 4: Manual Start

Simply run:
```bash
python3 whale_menu.py
```

Or use the startup script:
```bash
./start.sh
```

## Quick Access

You can also create a desktop shortcut or add to your PATH for quick access from anywhere.

