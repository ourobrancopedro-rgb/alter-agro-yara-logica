# Auditor Guide

This guide explains how independent auditors validate YARA Lógica specifications without accessing private runtime code.

## 1. Pre-Check

1. Clone the repository.
2. Ensure you have Python 3.9+ and GPG tooling available.

## 2. Hash Verification

1. Run `python infra/github/verify_hashes.py`.
2. If hashes mismatch, request the maintainer to regenerate using `--update` and supply the signed commit.
3. When authoring changes, execute `python infra/github/verify_hashes.py --update` and commit the resulting ledger update.

## 3. KPI Interpretation

1. Obtain or generate `infra/github/kpi_report.json` (private reports may be shared securely).
2. Execute `python infra/github/kpi_score.py --min-faith-premise 0.80 --min-contradiction-coverage 0.90`.
3. Review the output for:
   - `faithfulness_premise`
   - `contradiction_coverage`
   - Any additional metrics included by maintainers
4. Document KPI outcomes in the audit memo.

## 4. Byte-Range Citations

1. For each claim, note the `source_sha256` and `byte_range`.
2. Retrieve the referenced document and verify the bytes match the assertion.
3. If discrepancies exist, mark the claim as `FACT(CONTESTED)` within the LSA artifact.

## 5. Reporting Workflow

1. Summaries and findings go into `docs/AUDITOR_GUIDE.md` appendices or separate audit notes.
2. Security disclosures follow `.github/SECURITY.md` contact instructions.
3. All commits must be GPG-signed before submission.

## 6. Sample Procedure

1. Review `docs/samples/cpr_cra_demo.md` for example byte-range validation.
2. Check that updated files have ledger entries.
3. Confirm trademarks and license headers remain intact.

Maintaining these steps ensures auditors can verify integrity without exposing Alter Agro's private runtime assets.
