# Security Policy

Thank you for helping keep Celesto secure.

## Important Legal Note

Celesto is licensed under the **Apache License 2.0**. See [LICENSE](LICENSE).

This security policy is provided on a **best-effort** basis and is for process clarity only.
It does **not** create any contractual, legal, or other binding obligation on maintainers.
In particular, this policy does **not** create:

- any duty to respond within a specific time,
- any duty to fix, backport, or disclose on a specific schedule,
- any warranty, guarantee, SLA, or support commitment,
- any entitlement to payment, bug bounty, or other compensation.

All software and updates remain provided **"AS IS"**, without warranties, as described in Apache-2.0.

## Supported Versions

Celesto is currently pre-1.0. Security fixes are prioritized for:

| Version / Branch | Supported |
| --- | --- |
| Latest release tag | ✅ |
| `main` branch | ✅ (best effort) |
| Older release tags | ❌ |

If you are on an older version, please upgrade before reporting behavior that may already be fixed.

## Reporting a Vulnerability

Please **do not open public GitHub issues** for suspected vulnerabilities.

Use GitHub's private vulnerability reporting flow:

- **Private report:** https://github.com/CelestoAI/Celesto/security/advisories/new

If that link is unavailable, open a minimal issue asking maintainers for a private contact channel (without sensitive details).

## What to Include in a Report

Please include as much of the following as possible:

- A clear description of the vulnerability and impact
- Affected version/commit and host environment (OS, architecture)
- Reproduction steps or proof-of-concept
- Expected vs. actual behavior
- Any suggested mitigation

## Response Expectations (Best Effort)

As a small team, we handle reports as capacity allows.
Our non-binding target process is:

1. Acknowledge report within **3 business days**
2. Triage and severity assessment within **7 business days**
3. Provide periodic updates when possible

Timelines may vary depending on complexity and maintainer availability.

## Disclosure Policy

We follow coordinated disclosure where possible:

- Please allow reasonable time for a fix before public disclosure
- We may publish security advisories for confirmed issues
- We are happy to credit reporters (unless anonymous credit is requested)

## Scope Notes

This policy covers vulnerabilities in this repository's code and release artifacts.

Out-of-scope (unless caused by Celesto code):

- Vulnerabilities in third-party dependencies/upstream projects
- Host misconfiguration outside documented Celesto setup
- Security findings without a realistic exploit path or impact

## Current SSH Trust Model (Important)

Celesto verifies SSH server identity before sending credentials and rejects unknown
or changed keys. Updated managed Linux images publish their public host key through
the local boot console; the network connection cannot supply that identity.

### Impact

- Custom, Windows, and older images need a known-hosts entry obtained through a
  trusted console or image-building process before SSH can connect.
- Your machine, its local inventory, and the image-building process remain part
  of the trust boundary.

### Recommended Operational Guidance

- Prefer local-only usage on developer machines or trusted CI runners.
- Avoid exposing guest SSH endpoints to public or untrusted networks.
- Set `CELESTO_SSH_KNOWN_HOSTS` to a trusted key file when the image cannot publish
  its identity through the local console. Do not use an unverified network scan
  to create that file. See [secure local access](docs/security.md#verify-ssh-identity).
