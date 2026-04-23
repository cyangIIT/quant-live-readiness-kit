# Repository topics

GitHub repository topics improve discoverability, populate
[github.com/topics/…](https://github.com/topics) listings, and help
people find the project through search.

## Recommended topics

Set these on the repo:

```
quantitative-finance
systematic-trading
paper-trading
trading-infrastructure
risk-management
monitoring
kill-switch
reconciliation
live-readiness
python
cli
template
```

Rationale:

| Topic | Why |
| --- | --- |
| `quantitative-finance` | primary domain |
| `systematic-trading` | primary audience |
| `paper-trading` | the main workflow this kit supports |
| `trading-infrastructure` | accurate category — this is ops, not alpha |
| `risk-management` | kill switch + promotion gate are risk controls |
| `monitoring` | core capability |
| `kill-switch` | distinctive capability |
| `reconciliation` | distinctive capability |
| `live-readiness` | mirrors the package name and thesis |
| `python` | language |
| `cli` | how users run it |
| `template` | signals this repo is safe to fork |

(GitHub allows up to 20 topics — the list above is conservative at 12.)

## How to apply

### Option A — GitHub web UI

1. Open the repository on github.com.
2. Click the gear icon next to **About** (top-right of the overview).
3. In the **Topics** field, paste the comma-separated list:

   ```
   quantitative-finance, systematic-trading, paper-trading, trading-infrastructure, risk-management, monitoring, kill-switch, reconciliation, live-readiness, python, cli, template
   ```

4. Click **Save changes**.

### Option B — `gh` CLI

Once the remote repository exists and you are authenticated with
`gh auth login`:

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

### Option C — `gh api`

```bash
gh api -X PUT repos/cyangIIT/quant-live-readiness-kit/topics \
  -H "Accept: application/vnd.github+json" \
  -f 'names[]=quantitative-finance' \
  -f 'names[]=systematic-trading' \
  -f 'names[]=paper-trading' \
  -f 'names[]=trading-infrastructure' \
  -f 'names[]=risk-management' \
  -f 'names[]=monitoring' \
  -f 'names[]=kill-switch' \
  -f 'names[]=reconciliation' \
  -f 'names[]=live-readiness' \
  -f 'names[]=python' \
  -f 'names[]=cli' \
  -f 'names[]=template'
```
