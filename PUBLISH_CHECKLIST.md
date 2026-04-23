# Publish checklist — v0.1.0

This is the exact sequence to take `quant-live-readiness-kit` from
"private working copy" to "announced on LinkedIn." Items are grouped
by where the work has to happen: `[local]`, `[GitHub UI]`, or `[gh CLI]`.

Assumptions:

- You have `gh` installed (`gh --version` works) and are authenticated
  (`gh auth status`).
- The remote GitHub account/org is `cyangIIT`. Replace with your own
  if different.

---

## 0 — What this repo already has ✅

These are done and do not need repeating:

- [x] Working CLI + 54 tests, all passing on Python 3.10 / 3.11 / 3.12.
- [x] README with first-60-seconds quickstart (`qlrk demo`).
- [x] End-to-end public demo (yfinance AAPL + toy SMA crossover) with
      offline fallback and bundled cached CSV.
- [x] Community health files: `LICENSE` (MIT), `CONTRIBUTING.md`,
      `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CITATION.cff`, issue +
      PR templates.
- [x] `CHANGELOG.md` with v0.1.0 section.
- [x] `RELEASE_NOTES_v0.1.0.md` (this directory).
- [x] Social preview image in `assets/` (PNG + SVG).
- [x] Dependabot config in `.github/dependabot.yml`.
- [x] Guidance docs in `docs/`: `GITHUB_TOPICS.md`,
      `GITHUB_SETTINGS.md`, `SECURITY_RECOMMENDATIONS.md`.
- [x] `.gitignore` excludes runtime state + private data.
- [x] Safety sweep for upstream strategy leakage — clean.

## 1 — Final local smoke test `[local]`

```bash
# In the repo root:
python -m venv .venv-launch && source .venv-launch/bin/activate
pip install -e ".[dev]"
ruff check .
pytest -q
qlrk demo --offline      # must produce .qlrk_state/demo/demo_report.md
qlrk demo                # online yfinance path (skip if offline)
```

If everything is green, proceed.

## 2 — Commit the launch changes `[local]`

```bash
git status
git add -A
git commit -m "release: v0.1.0 launch prep — demo, community health, assets"
```

Do **not** tag yet — the tag should point at the commit that actually
goes to GitHub.

## 3 — Create the remote repo (if it doesn't exist) `[gh CLI]`

```bash
# From inside the repo:
gh repo create cyangIIT/quant-live-readiness-kit \
  --public \
  --source . \
  --push \
  --description "Operational toolkit for taking a systematic trading strategy from research to auditable paper/live readiness." \
  --homepage "https://github.com/cyangIIT/quant-live-readiness-kit"
```

If the repo already exists, push instead:

```bash
git remote add origin https://github.com/cyangIIT/quant-live-readiness-kit.git  # if needed
git push -u origin main
```

## 4 — Apply topics `[gh CLI]`

See `docs/GITHUB_TOPICS.md`. Quick version:

```bash
gh repo edit cyangIIT/quant-live-readiness-kit \
  --add-topic quantitative-finance \
  --add-topic systematic-trading \
  --add-topic paper-trading \
  --add-topic trading-infrastructure \
  --add-topic risk-management \
  --add-topic monitoring \
  --add-topic kill-switch \
  --add-topic reconciliation \
  --add-topic live-readiness \
  --add-topic python \
  --add-topic cli \
  --add-topic template
```

## 5 — Upload social preview image `[GitHub UI]`

> No public API exists for this — must be done in the web UI.

1. Go to **Settings → General → Social preview**.
2. Click **Edit** → **Upload an image…**.
3. Select `assets/social-preview.png` from your local clone.
4. Save.

## 6 — Enable Discussions + security features `[GitHub UI or gh CLI]`

### Via UI (easier)

Settings → General → Features:

- [x] Issues
- [x] Discussions  — then create categories:
      *Q&A*, *Show and tell*, *Ideas*, *Announcements*.
- [ ] Projects   (off)
- [ ] Wiki       (off)

Settings → Security & analysis:

- [x] Dependency graph
- [x] Dependabot alerts + security updates + version updates
- [x] Secret scanning
- [x] Push protection
- [x] Code scanning (CodeQL) → Default setup
- [x] Private vulnerability reporting

### Via gh CLI

```bash
gh api -X PATCH repos/cyangIIT/quant-live-readiness-kit \
  -f has_issues=true -f has_wiki=false -f has_projects=false \
  -f has_discussions=true \
  -f allow_squash_merge=true \
  -f allow_merge_commit=false \
  -f allow_rebase_merge=false \
  -f delete_branch_on_merge=true
```

## 7 — Branch protection on `main` `[gh CLI]`

Wait until **CI has run at least once** so the status-check names
exist (`test (3.10)`, `test (3.11)`, `test (3.12)`), then:

```bash
gh api -X PUT repos/cyangIIT/quant-live-readiness-kit/branches/main/protection \
  -H "Accept: application/vnd.github+json" \
  -F required_status_checks='{"strict":true,"contexts":["test (3.10)","test (3.11)","test (3.12)"]}' \
  -F enforce_admins=false \
  -F required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
  -F restrictions= \
  -F required_linear_history=true \
  -F allow_force_pushes=false \
  -F allow_deletions=false \
  -F required_conversation_resolution=true
```

## 8 — Cut the v0.1.0 tag and release `[local + gh CLI]`

```bash
git tag -a v0.1.0 -m "v0.1.0 — first public release"
git push origin v0.1.0

gh release create v0.1.0 \
  --title "v0.1.0 — first public release" \
  --notes-file RELEASE_NOTES_v0.1.0.md \
  --verify-tag
```

Release assets are **not required** — the wheel is optional and PyPI
publishing is out of scope for this checklist.

## 9 — (Optional) Publish to PyPI `[local]`

Only after step 8 succeeds. Requires a PyPI account + token.

```bash
pip install build twine
python -m build
# Verify the wheel contents:
python -m zipfile -l dist/quant_live_readiness_kit-0.1.0-py3-none-any.whl | head
twine check dist/*
twine upload dist/*
```

## 10 — Announce on LinkedIn `[human]`

Suggested copy (edit to taste):

> Every systematic trader eventually rebuilds the same operational
> scaffolding: freeze manifests, paper-vs-broker reconciliation, a
> kill switch, monitoring with real state-transition alerts, a
> promotion gate, and incident runbooks. I finally wrote a clean,
> open-source, strategy-agnostic version.
>
> ▸ One demo command: `qlrk demo`
> ▸ Python 3.10+, MIT, alpha-free.
> ▸ github.com/cyangIIT/quant-live-readiness-kit
>
> Feedback and PRs welcome — scope is narrow on purpose (ops only,
> no alpha).

---

## What still requires the GitHub UI (no API available)

- Uploading the social preview image (step 5).
- Creating Discussion categories after enabling Discussions.
- Approving the initial CodeQL "Set up default" prompt (if the CLI
  variant errors).

Everything else can be done via `gh` + `gh api`.

## Post-launch (next 7 days)

- [ ] Respond to any Discussion threads within 48h.
- [ ] Watch CI for Dependabot PRs; squash-merge green ones.
- [ ] Pin any particularly useful community writeup in Discussions →
      Show and tell.
- [ ] Draft a short v0.2.0 roadmap issue based on incoming asks.
