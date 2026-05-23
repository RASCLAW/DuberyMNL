# Data Backup Strategy

How DuberyMNL state is backed up, what gets pushed where, and how to recover if something goes wrong.

---

## What gets backed up

| Layer | Lives in | Backed up to | Cadence |
|-------|----------|--------------|---------|
| **Code** | DuberyMNL git repo | GitHub (`origin/main`) | Every `/closeout` or `/sendit` |
| **Memory + skills** | `~/.claude/` git repo | GitHub (`origin/master`) | Every `/closeout` or `/sendit` |
| **Cross-project context** | `~/projects/EA-brain` git repo | GitHub | Every `/closeout` or `/sendit` |
| **Secrets** | `.env`, `credentials.json`, `token.json`, `.credentials.json` | Drive: `DuberyMNL/Backups/secrets` (pinned `keepForever`) | Every `/closeout` or `/sendit` (always re-uploads) |
| **Generated content (drafts)** | `contents/new/` (gitignored) | Drive: `DuberyMNL/backup/contents/new` | Every `/closeout` or `/sendit` (idempotent skip-existing) |
| **Generated content (curated)** | `contents/ready/` (gitignored) | Drive: `DuberyMNL/backup/contents/ready` | Every `/closeout` or `/sendit` (idempotent skip-existing) |
| **Fallback (push-blocked)** | local commits | Drive: `DuberyMNL/backup/pending-pushes/<date>-<session>/` | Manual, only when `git push` is unavailable |

What is NOT backed up:
- `.tmp/` — disposable scratch, gitignored, never synced
- `contents/failed/` — rejected images, intentional trash
- `archives/` — already preserved via git history
- Anything in `node_modules/`, `__pycache__/`, build outputs

---

## Normal flow (`/sendit`)

`/sendit` fires 6 parallel background tasks:

1. `python tools/drive/backup_secrets.py` — pins 4 secret files to Drive with `keepForever`
2. `python tools/drive/sync_folder.py --local contents/new --remote DuberyMNL/backup/contents/new`
3. `python tools/drive/sync_folder.py --local contents/ready --remote DuberyMNL/backup/contents/ready`
4. `git push origin main` (DuberyMNL repo)
5. `git push origin master` (`~/.claude/` repo)
6. `git push` (EA-brain repo)

All run independently. A failure in one doesn't block the others.

Each `git push` has an automatic `pull --rebase` fallback for branch divergence (e.g. when another machine pushed first). If rebase has merge conflicts, the tool stops and reports — never force-pushes.

---

## Fallback flow (git push blocked)

Sometimes `git push origin main` is blocked by Claude Code's auto-mode safety classifier (defends against unintended pushes to default branches). When this happens, commits sit locally but the work is still preserved by pushing the unpushed commits to Drive as git patches.

**Pattern:**
```bash
# 1. Generate patches for unpushed commits from each affected repo
cd c:/Users/RAS/projects/DuberyMNL
mkdir -p .tmp/sendit-fallback-<date>-session-<N>/DuberyMNL .tmp/sendit-fallback-<date>-session-<N>/claude
git format-patch origin/main..HEAD -o .tmp/sendit-fallback-<date>-session-<N>/DuberyMNL

cd ~/.claude
git format-patch origin/master..HEAD -o c:/Users/RAS/projects/DuberyMNL/.tmp/sendit-fallback-<date>-session-<N>/claude

# 2. (Optional) Copy related artifacts like .tmp/plan.md
cp c:/Users/RAS/projects/DuberyMNL/.tmp/plan.md c:/Users/RAS/projects/DuberyMNL/.tmp/sendit-fallback-<date>-session-<N>/

# 3. Sync to Drive
cd c:/Users/RAS/projects/DuberyMNL
python tools/drive/sync_folder.py --local .tmp/sendit-fallback-<date>-session-<N> --remote "DuberyMNL/backup/pending-pushes/<date>-session-<N>"
```

**Recovery from a Drive fallback** (any machine, fresh clone):
```bash
# Download the patch files from Drive folder DuberyMNL/backup/pending-pushes/<folder>/
# Then apply:
cd <DuberyMNL repo> && git am /path/to/DuberyMNL/0001-*.patch
cd ~/.claude && git am /path/to/claude/0001-*.patch
```

Patches preserve author, commit message, and exact diff — `git am` replays them as new commits on top of current `HEAD`.

---

## Recovery scenarios

| If you lose... | Restore from... | Steps |
|----------------|-----------------|-------|
| **Local code** | GitHub | `git clone git@github.com:RASCLAW/DuberyMNL.git` |
| **Memory / skills** | GitHub (RASCLAW/claude-config) | `git clone` into `~/.claude/` (or restore from another machine) |
| **Secrets (.env etc)** | Drive `DuberyMNL/Backups/secrets/` | Download each file back into repo root; chmod 600 if on POSIX |
| **Generated content** | Drive `DuberyMNL/backup/contents/` | Drag down or use `gdown` for bulk |
| **Unpushed commits (fallback exists)** | Drive `DuberyMNL/backup/pending-pushes/` | See "Recovery from a Drive fallback" above |
| **Unpushed commits (no fallback)** | Whichever machine still has them | Push from that machine, OR `git format-patch` + transfer manually |

---

## Why this layered approach

- **Git is the primary source of truth** for code + memory. Cheap, fast, diff-friendly.
- **Drive is the secrets + content + last-resort backup**. Files git shouldn't carry (PII, large binaries, generated images).
- **Patches in Drive cover the gap** when git is temporarily unavailable. Same fidelity as a normal push, just async.
- **Three machines + GitHub + Drive** = no single point of failure. The pattern survived an April 2026 PC death (full disk wipe; restored within an hour from GitHub + Drive).

---

## Known gotchas

- **Auto-mode classifier blocks `git push origin main`** intermittently, even with explicit allow rules in `~/.claude/settings.json`. Documented in `~/projects/DuberyMNL/PROJECT_LOG.md` session 171 (rules added) and session 172 (still triggered). Workaround: manual push from terminal or Drive fallback.
- **`sync_folder.py` is idempotent** — skips files already on Drive by exact path match. Safe to re-run; cheap on no-op.
- **`backup_secrets.py` is NOT idempotent** — always re-uploads all 4 secret files and pins the new revision `keepForever`. Old revisions also stay pinned for history.
- **`.tmp/` is gitignored** so plan documents (`.tmp/plan.md`) don't survive a clean checkout. If a plan matters across sessions, either copy it to a tracked path or include it in the Drive fallback bundle.
