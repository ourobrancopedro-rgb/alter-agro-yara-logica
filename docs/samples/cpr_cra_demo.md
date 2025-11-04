# CPR/CRA Byte-Range Citation Demo

This sample demonstrates how to document byte-range citations for regenerative agriculture certificates.

## Sample Entry

```yaml
claim: "CRA issuance aligns with CPR carbon measurements."
sources:
  - source_id: "cpr-2024-lab"
    sha256: "c1f0..."
    byte_range: "2048-2399"
    note: "Laboratory-certified soil carbon report."
  - source_id: "cra-ledger"
    sha256: "a9d4..."
    byte_range: "512-711"
    note: "On-chain CRA allocation record."
contradictions:
  - source_id: "independent-audit"
    sha256: "b3e2..."
    byte_range: "102-189"
    label: "FACT(CONTESTED)"
```

## Validation Steps

1. Retrieve source documents from the evidence vault.
2. Compute SHA-256 and confirm they match the listed hashes.
3. Validate the byte ranges against document content.
4. Update `infra/github/hash_ledger.json` with any spec modifications.
5. Record outcomes in the relevant decision record if conflicts remain.

Replace runtime automation references with `// PRIVATE RUNTIME — NOT IN THIS REPOSITORY` when necessary.
