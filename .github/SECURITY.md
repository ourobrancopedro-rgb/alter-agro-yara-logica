# Security Policy — YARA Lógica Public Specifications

This repository publishes **specifications and audit artifacts only**. Operational systems, private infrastructure, and runtime code are out of scope and maintained separately.

## 📬 Reporting a Vulnerability

Email **contatoalteragro@gmail.com** with the subject line `YARA Lógica — Security Disclosure`.

Please include:
- A clear description of the issue
- Affected files or specification sections
- Recommended mitigation or questions

We acknowledge receipt within **3 business days** and provide an evaluation within **10 business days**. Sensitive disclosures may be handled on an encrypted channel.

## 🔐 Integrity Discipline

- All commits must be **GPG-signed**.
- `infra/github/hash_ledger.json` binds tracked artifacts to their SHA-256 hashes.
- CI enforces scope, prohibited-content scanning, KPI thresholds, and hash verification.

Thank you for helping protect Alter Agro's intellectual property while maintaining transparent public specifications.
