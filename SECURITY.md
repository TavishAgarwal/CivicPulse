# 🔒 SECURITY.md — CivicPulse Security Policy

---

## Reporting a Vulnerability

**Do NOT open a public GitHub Issue for security vulnerabilities.**

Report security issues privately to: **security@civicpulse.org**

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if known)

We will acknowledge receipt within 48 hours and provide a resolution timeline within 7 days.

---

## Security Standards

### Encryption
- All data at rest: AES-256
- All data in transit: TLS 1.3 minimum
- Database connections: SSL enforced
- Secrets: Never in code or logs — use environment variables or AWS Secrets Manager

### Authentication
- API: JWT Bearer tokens, 8-hour expiry
- Admin dashboard: MFA required
- Service-to-service: mTLS in production

### Data Privacy
- No PII stored anywhere in the pipeline (see `docs/privacy-framework.md`)
- k-anonymity (k≥5) applied to all location data
- Data residency: Indian city data stays in AWS ap-south-1
- Right to erasure: automated data deletion on MOU termination

### Dependencies
- `pip-audit` and `npm audit` run on every PR
- Dependabot enabled for automatic security patches
- Critical CVEs must be patched within 72 hours

---

## Supported Versions

| Version | Supported |
|---|---|
| 1.x (latest) | ✅ Full support |
| 0.x (beta) | ⚠️ Security patches only |

---

## Responsible Disclosure

We follow coordinated disclosure practices. Reporters who follow this policy responsibly will be:
- Acknowledged in our release notes (with permission)
- Notified when the fix is deployed
- Considered for our future bug bounty program (planned for v1.0)
