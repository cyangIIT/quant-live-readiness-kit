# Installation

## Requirements

- Python 3.10 or newer
- POSIX or Windows

No mandatory dependencies beyond PyYAML at runtime. Dev dependencies
(`pytest`, `ruff`) are optional.

## From PyPI (when released)

```bash
pip install quant-live-readiness-kit
```

## From a clone

```bash
git clone https://github.com/cyangIIT/quant-live-readiness-kit.git
cd quant-live-readiness-kit
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
qlrk --version
pytest -q
```

## Sanity check

The fastest end-to-end check is the demo:

```bash
pip install -e ".[demo]"
qlrk demo --offline     # uses the bundled cached AAPL CSV
```

…or the scripted walkthrough against the synthetic sample data:

```bash
bash scripts/run_example.sh
```

You should see six artifacts produced under `.qlrk_state/` and a final
`ls -1` listing.

## Upgrading

```bash
pip install -U quant-live-readiness-kit
```

Breaking changes are documented in [`CHANGELOG.md`](../CHANGELOG.md).
Pre-1.0 releases may include breaking changes on minor versions; after
1.0 we will follow SemVer strictly.

## Uninstalling

```bash
pip uninstall quant-live-readiness-kit
```

No global state outside your project folder. The only on-disk state is
whatever files you pointed `--out`, `--state`, or `--alert-file` at.
