# Security Policy

## Supported Versions

`quant-live-readiness-kit` is pre-1.0. Only the latest `main` and the latest
tagged release receive security fixes.

## Reporting a vulnerability

Please **do not** open a public issue for security reports. Email the
maintainers listed on the repo's GitHub page, or use GitHub's private
"Report a vulnerability" feature on the Security tab.

Include:

- A description of the issue and its impact
- Steps to reproduce (minimal repro preferred)
- Your suggested severity (low / medium / high / critical)

We aim to acknowledge reports within 72 hours and publish a fix or mitigation
within 30 days for confirmed issues.

## What is in scope

- Code execution from untrusted input (config files, trade logs)
- Path traversal when reading/writing artifacts
- Unsafe YAML/JSON parsing
- Secret leakage in log output

## What is out of scope

- Trading losses from using the toolkit. This software ships **as-is** with
  no warranty. See `LICENSE`.
- Vulnerabilities in third-party broker SDKs. Report those upstream.
- Social-engineering risks unrelated to the code.

## Secure use checklist

- Never commit `.env` files, broker credentials, or API keys.
- `.gitignore` excludes `private_data/`, `real_trades/`, `*.pem`, `*.key`,
  `broker_credentials*`, `.env`, `.env.*` — keep it that way.
- Treat any config file that names live accounts or real balances as
  sensitive, even if examples in this repo do not.
- The sample data in `examples/` is synthetic. Do not replace it with real
  trade logs when opening pull requests.
