# MCP Shell Manager Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a local shell-managed command surface for starting and stopping the GSC and Ads MCP servers via `mcp <service> <action>`.

**Architecture:** Keep runtime logic in a dedicated sourced shell file under `~/.config/mcp-manager/`, and keep `~/.zshrc` as a thin loader. Use fixed service-to-session mappings and tmux as the only background process manager.

**Tech Stack:** zsh, tmux, Homebrew-installed tmux, local project paths for Google Search Console MCP and Google Ads MCP

### Task 1: Create manager config directory and shell entrypoint

**Files:**
- Create: `/Users/celeste/.config/mcp-manager/CLAUDE.md`
- Create: `/Users/celeste/.config/mcp-manager/mcp.sh`

**Step 1: Write the failing verification**

Run:

```bash
test -f /Users/celeste/.config/mcp-manager/mcp.sh
```

Expected: FAIL because the file does not exist yet.

**Step 2: Write minimal implementation**

Create:
- `CLAUDE.md` for the config directory
- `mcp.sh` with service maps, tmux helper functions, and the `mcp` shell function

**Step 3: Verify**

Run:

```bash
zsh -lc 'source /Users/celeste/.config/mcp-manager/mcp.sh && whence -w mcp'
```

Expected: output shows `mcp: function`

**Step 4: Commit**

This task modifies home-directory config outside the repo; no git commit applies.

### Task 2: Wire zsh startup to load the manager

**Files:**
- Modify: `/Users/celeste/.zshrc`

**Step 1: Write the failing verification**

Run:

```bash
zsh -lc 'whence -w mcp'
```

Expected: FAIL or `mcp: none`

**Step 2: Write minimal implementation**

Append a guarded source stanza in `~/.zshrc`:

```bash
[ -f "$HOME/.config/mcp-manager/mcp.sh" ] && source "$HOME/.config/mcp-manager/mcp.sh"
```

**Step 3: Verify**

Run:

```bash
zsh -lc 'whence -w mcp'
```

Expected: `mcp: function`

**Step 4: Commit**

This task modifies home-directory config outside the repo; no git commit applies.

### Task 3: Validate service lifecycle commands

**Files:**
- Modify: `/Users/celeste/.config/mcp-manager/mcp.sh`

**Step 1: Write the failing verification**

Run:

```bash
zsh -lc 'source ~/.config/mcp-manager/mcp.sh && mcp gsc status'
```

Expected: outputs a stable “stopped” status before any service is started.

**Step 2: Write minimal implementation**

Ensure:
- `mcp gsc start`
- `mcp gsc stop`
- `mcp gsc restart`
- `mcp gsc status`
- `mcp gsc logs`
- same surface for `ads`

**Step 3: Verify**

Run:

```bash
zsh -lc 'source ~/.config/mcp-manager/mcp.sh && mcp gsc start'
zsh -lc 'source ~/.config/mcp-manager/mcp.sh && mcp gsc status'
zsh -lc 'tmux ls | grep mcp-gsc'
zsh -lc 'source ~/.config/mcp-manager/mcp.sh && mcp gsc stop'
```

Expected:
- start succeeds
- status reports running
- tmux session exists
- stop removes the session

Repeat for:

```bash
zsh -lc 'source ~/.config/mcp-manager/mcp.sh && mcp ads start'
zsh -lc 'source ~/.config/mcp-manager/mcp.sh && mcp ads stop'
```

### Task 4: Sync design maps

**Files:**
- Modify: `docs/plans/CLAUDE.md`

**Step 1: Verify**

Run:

```bash
sed -n '1,200p' /Users/celeste/Documents/GitHub/google-search-console-mcp/docs/plans/CLAUDE.md
```

Expected: the new design and plan files are listed.

**Step 2: Commit**

```bash
git add docs/plans/CLAUDE.md docs/plans/2026-04-12-mcp-shell-manager-design.md docs/plans/2026-04-12-mcp-shell-manager.md
git commit -m "docs: add mcp shell manager design and plan"
```
