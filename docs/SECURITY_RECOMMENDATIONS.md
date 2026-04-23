# Security recommendations for this repo

A Python library this small doesn't need enterprise security tooling,
but a handful of free GitHub features are worth turning on before the
repo goes public.

## 1. Dependency graph + Dependabot alerts

**Enable both.** Free for public repos, no configuration required.

Settings → Security & analysis:

- [x] Dependency graph → **Enable**
- [x] Dependabot alerts → **Enable**
- [x] Dependabot security updates → **Enable**
- [x] Dependabot version updates → **Enable** (uses
      `.github/dependabot.yml`, see below)

Add a minimal `dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: pip
    directory: /
    schedule:
      interval: weekly
    open-pull-requests-limit: 5
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
```

## 2. Secret scanning

**Enable both scanning and push protection.**

Settings → Security & analysis:

- [x] Secret scanning → **Enable**
- [x] Push protection → **Enable**

Even though the codebase doesn't touch real broker credentials, push
protection is a cheap safety net against accidentally committing an
API key someone has locally in their `.env`.

## 3. Code scanning (CodeQL)

**Enable default setup.** Free for public repos.

Settings → Security & analysis → Code scanning → **Set up** →
**Default**. CodeQL will add a scheduled workflow, which is fine.

There isn't much attack surface in this package (no network handlers,
no template engines, no process execution on untrusted input), but
CodeQL's Python query pack is cheap insurance.

## 4. Security policy

Already present — [`SECURITY.md`](../SECURITY.md). GitHub's private
"Report a vulnerability" button on the **Security** tab will point to
that file automatically.

Confirm:

- Settings → Security → Security advisories → Private vulnerability
  reporting → **Enable**.

## 5. Branch protection

Covered in [`GITHUB_SETTINGS.md`](GITHUB_SETTINGS.md#branch-protection-main).
The key point: require CI to pass on `main`, require PR reviews,
disallow force-push.

## 6. Actions security

- Workflow permissions: **Read-only token** (default). The CI workflow
  only runs tests; it does not need write access.
- Do not grant `pull-requests: write` or `contents: write` to any
  workflow unless a specific feature requires it (e.g., a release-drafter
  action, which isn't currently set up).

## 7. What's out of scope

- Trading losses from using the toolkit — the MIT license disclaims
  all warranties and the README says so again.
- Vulnerabilities in third-party broker SDKs — this repo has none.
- Social-engineering risks unrelated to the code.

## 8. Reporting a vulnerability

See [`SECURITY.md`](../SECURITY.md). Summary:

> Use GitHub's private "Report a vulnerability" feature on the Security
> tab. Expect acknowledgement within 72 hours; fix or mitigation within
> 30 days for confirmed issues.
