# Recommended GitHub settings

These are the repo-level settings the maintainers recommend for a
public launch. The goal is: make it obvious this is a real,
maintained project; make it safe to accept contributions; keep the
scope narrow.

## Repository → General

| Setting | Recommendation | Why |
| --- | --- | --- |
| **Description** | *"Operational toolkit for taking a systematic trading strategy from research to auditable paper/live readiness. Freeze manifests, reconciliation, monitoring, kill switches, promotion gates."* | Matches README tagline; improves search. |
| **Website** | `https://github.com/cyangIIT/quant-live-readiness-kit` (or a docs site once deployed) | Minor SEO boost. |
| **Topics** | See `GITHUB_TOPICS.md` | Discovery. |
| **Social preview** | Upload `assets/social-preview.png` | LinkedIn/X sharing card. |

## Repository → Features

| Feature | Recommendation | Why |
| --- | --- | --- |
| **Issues** | **ON** | Standard bug/feature inbox; templates already under `.github/ISSUE_TEMPLATE/`. |
| **Discussions** | **ON** | The toolkit invites "how do I adapt this to X" questions — they are a bad fit for Issues. Create categories: *Q&A*, *Show and tell*, *Ideas*, *Announcements*. |
| **Projects** | **OFF** | Not useful at this size; turn on when there is an active roadmap board. |
| **Wiki** | **OFF** | `docs/` in the repo is already the source of truth; a wiki splits attention and can't be code-reviewed. |
| **Sponsorships** | **OFF** (for now) | Turn on only if/when there is a funding target worth declaring. |
| **Preserve this repository** | ON (default) | Inclusion in Arctic/GitHub Archive if eligible — no downside. |

## Repository → Pull Requests

| Setting | Recommendation |
| --- | --- |
| Allow merge commits | OFF |
| Allow squash merging | **ON** (default) |
| Allow rebase merging | OFF |
| Always suggest updating pull-request branches | ON |
| Allow auto-merge | ON |
| Automatically delete head branches | ON |

Squash-only keeps `main` linear and readable. Auto-delete keeps the
branch list from becoming noise.

## Branch protection → `main`

Until the repo has co-maintainers, a lightweight rule is enough:

| Rule | Value |
| --- | --- |
| Require a pull request before merging | **ON** |
| Require status checks to pass | **ON** → select `ci / test (3.10)`, `ci / test (3.11)`, `ci / test (3.12)` |
| Require branches to be up to date before merging | ON |
| Require linear history | ON (matches squash-merge policy) |
| Require conversation resolution | ON |
| Do not allow bypassing the above | ON |
| Restrict who can push to matching branches | (leave empty until co-maintainers exist) |

Applying these rules via `gh api` (replace `cyangIIT` as needed):

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

## Repository → Actions

| Setting | Recommendation |
| --- | --- |
| Allow all actions and reusable workflows | **Allow actions created by GitHub + Marketplace verified** |
| Workflow permissions | **Read repository contents and packages permissions** (default) |
| Allow GitHub Actions to create and approve pull requests | OFF |

## Tags & releases

- Use signed tags when possible (`git tag -s v0.1.0 -m "v0.1.0"`) once
  a GPG/SSH key is set up; otherwise annotated tags
  (`git tag -a v0.1.0 -m "v0.1.0"`) are fine for v0.1.0.
- Release names: `v0.1.0`, `v0.2.0`, …
- Attach `RELEASE_NOTES_v0.1.0.md` as the release body.

## Secrets and variables

No secrets are required for CI. If you add a webhook alerting adapter
that you want to test end-to-end, store the webhook URL as a GitHub
Actions secret named `QLRK_DEMO_WEBHOOK_URL` and gate the test on its
presence.
