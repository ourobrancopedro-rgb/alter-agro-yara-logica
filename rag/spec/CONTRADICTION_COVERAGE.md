# Contradiction Coverage Specification

## Definition

**Contradiction Coverage** measures the thoroughness of contradiction checking in YARA Lógica reasoning artifacts.

## Calculation Method

```python
def calculate_contradiction_coverage(lsa_artifact: Dict) -> float:
    """
    Contradiction Coverage = (Claims Checked) / (Total Checkable Claims)

    Where:
    - Claims Checked = claims with explicit contradiction search performed
    - Total Checkable Claims = all inferences + conclusions making factual claims
    """

    # Count checkable claims
    inferences = lsa_artifact.get("inferences", [])
    conclusions = lsa_artifact.get("conclusions", [])
    total_checkable = len(inferences) + len(conclusions)

    if total_checkable == 0:
        return 1.0  # No claims = perfect coverage

    # Count claims that were checked
    checked_claims = set()

    # Inferences/conclusions with contradictions were checked
    for contradiction in lsa_artifact.get("contradictions", []):
        checked_claims.update(contradiction.get("targets", []))

    # Conclusions explicitly marked as "checked" (even if no contradictions found)
    for conclusion in conclusions:
        if conclusion.get("contradiction_check", {}).get("performed"):
            checked_claims.add(conclusion["id"])

    # Inferences explicitly marked as checked
    for inference in inferences:
        if inference.get("contradiction_check", {}).get("performed"):
            checked_claims.add(inference["id"])

    claims_checked = len(checked_claims)

    return claims_checked / total_checkable
```

## Schema Changes Required

### Add to Conclusions

```json
{
  "id": "conclusion-001",
  "supports": ["inference-001"],
  "contested_by": [],
  "statement": "...",
  "decision_state": "approved",

  "contradiction_check": {
    "performed": true,
    "timestamp": "2025-11-04T10:30:00Z",
    "search_queries": ["carbon gain variance", "audit discrepancy"],
    "sources_searched": 15,
    "contradictions_found": 0,
    "methodology": "RAG::tight-loop"
  }
}
```

### Add to Inferences (Optional but Recommended)

```json
{
  "id": "inference-001",
  "supports": ["premise-001"],
  "methodology": "LSA::delta-carbon",
  "confidence": 0.82,
  "statement": "...",

  "contradiction_check": {
    "performed": true,
    "timestamp": "2025-11-04T10:25:00Z",
    "search_queries": ["alternative calculations"],
    "sources_searched": 8,
    "contradictions_found": 0
  }
}
```

## Minimum Threshold

**KPI Requirement:** Contradiction Coverage ≥ 0.90

This means:
- At least 90% of checkable claims must have explicit contradiction searches
- For artifacts with 10 claims, ≥9 must be checked
- For artifacts with 100 claims, ≥90 must be checked

## Exemptions

The following claims may be exempt from contradiction checking:

1. **Definitional statements** (e.g., "LSA stands for Logic-Sorting Architecture")
2. **Mathematical truths** (e.g., "2 + 2 = 4")
3. **Direct quotes** with `methodology: "LSA::direct-citation"`

Mark exemptions explicitly:

```json
{
  "id": "inference-002",
  "statement": "LSA uses a four-step PICC process",
  "contradiction_check": {
    "performed": false,
    "exempt": true,
    "exempt_reason": "definitional"
  }
}
```

## Validation

```python
def validate_contradiction_coverage(lsa_artifact: Dict, threshold: float = 0.90) -> bool:
    """
    Validate that artifact meets contradiction coverage threshold
    """
    coverage = calculate_contradiction_coverage(lsa_artifact)

    if coverage < threshold:
        print(f"❌ Contradiction coverage {coverage:.2%} below threshold {threshold:.2%}")
        return False

    print(f"✅ Contradiction coverage {coverage:.2%} meets threshold")
    return True
```

## Example: Full Coverage

```json
{
  "inferences": [
    {
      "id": "inference-001",
      "statement": "Carbon sequestration increased by 10%",
      "contradiction_check": {
        "performed": true,
        "timestamp": "2025-11-04T10:00:00Z",
        "search_queries": ["carbon sequestration decrease", "carbon loss"],
        "sources_searched": 12,
        "contradictions_found": 0
      }
    }
  ],
  "conclusions": [
    {
      "id": "conclusion-001",
      "statement": "Project shows positive carbon impact",
      "contradiction_check": {
        "performed": true,
        "timestamp": "2025-11-04T11:00:00Z",
        "search_queries": ["negative carbon impact", "carbon emissions increase"],
        "sources_searched": 20,
        "contradictions_found": 1
      }
    }
  ],
  "contradictions": [
    {
      "id": "contradiction-001",
      "targets": ["conclusion-001"],
      "statement": "One report shows neutral carbon impact"
    }
  ]
}
```

**Coverage Calculation:**
- Total checkable: 2 (1 inference + 1 conclusion)
- Checked: 2 (both have `contradiction_check.performed: true`)
- Coverage: 2/2 = 100%

## Reporting Format

### Summary Report

```
Contradiction Coverage Report
========================================
File: lsa/artifacts/carbon_analysis.json
Total claims: 15
Checkable claims: 13 (2 exempt)
Checked claims: 12
Unchecked claims: 1
Coverage: 92.3%
Status: ✅ PASS (≥90% threshold)
========================================

Unchecked Claims:
  - inference-007: "Soil organic matter increased"
```

### Detailed Report

```json
{
  "file": "lsa/artifacts/carbon_analysis.json",
  "timestamp": "2025-11-04T12:00:00Z",
  "total_claims": 15,
  "exempt_claims": 2,
  "checkable_claims": 13,
  "checked_claims": 12,
  "unchecked_claims": 1,
  "coverage": 0.923,
  "threshold": 0.90,
  "status": "pass",
  "unchecked_ids": ["inference-007"],
  "exemptions": [
    {
      "id": "inference-002",
      "reason": "definitional"
    },
    {
      "id": "premise-001",
      "reason": "direct-quote"
    }
  ]
}
```

## Best Practices

1. **Always check conclusions**: Every conclusion should have contradiction search performed
2. **Document search queries**: Record what was searched to find contradictions
3. **Record sources searched**: Track how many sources were consulted
4. **Use appropriate exemptions**: Don't abuse exemptions to inflate coverage
5. **Timestamp checks**: Record when contradiction search was performed for audit trail

## Integration with CI/CD

```yaml
# .github/workflows/ci.yml
- name: Check Contradiction Coverage
  run: |
    python infra/github/calculate_contradiction_coverage.py lsa/artifacts/*.json
```

## FAQ

**Q: What if I find no contradictions?**
A: Still mark `contradiction_check.performed: true` and set `contradictions_found: 0`. This shows you searched.

**Q: How many sources should I search?**
A: Minimum 2 independent sources per claim. More for critical conclusions.

**Q: Can I exempt a claim after the fact?**
A: Yes, but document the reason. Exemptions should be rare.

**Q: What if a source is unavailable?**
A: Document in the check metadata: `"search_notes": "Source X unavailable, checked Y instead"`
