# Confidence Propagation Rules

## 1. Base Confidence Assignment

Premises receive confidence from source quality:

| Source Type | Base Confidence |
|:------------|:----------------|
| Peer-reviewed journal | 0.95 |
| Government agency | 0.90 |
| Industry report (verified) | 0.85 |
| Company publication | 0.75 |
| Blog/news (verified) | 0.60 |
| Unverified source | 0.40 |

## 2. Inference Confidence Calculation

### Rule: Minimum of Supporting Evidence

```python
def calculate_inference_confidence(inference):
    """
    Confidence = min(supports) × methodology_factor × evidence_diversity_bonus
    """
    support_confidences = [get_confidence(s) for s in inference.supports]

    base_confidence = min(support_confidences)
    methodology_factor = get_methodology_factor(inference.methodology)
    diversity_bonus = calculate_diversity_bonus(inference.supports)

    return min(1.0, base_confidence × methodology_factor × diversity_bonus)
```

### Methodology Factors

| Methodology | Factor | Notes |
|:------------|:-------|:------|
| LSA::direct-citation | 1.0 | Direct quote/reference |
| LSA::convergent-evidence | 1.1 | Multiple sources agree |
| LSA::delta-carbon | 0.95 | Calculation-based |
| LSA::statistical-inference | 0.90 | Model-dependent |
| LSA::expert-opinion | 0.85 | Subjective judgment |

### Diversity Bonus

```python
def calculate_diversity_bonus(supports):
    """
    Bonus for having diverse, independent sources
    """
    unique_sources = count_unique_sources(supports)

    if unique_sources >= 3:
        return 1.05
    elif unique_sources == 2:
        return 1.02
    else:
        return 1.0
```

## 3. Time Decay Function

```python
def apply_time_decay(confidence, source_date, current_date, field):
    """
    Reduce confidence for stale data based on field volatility
    """
    age_months = (current_date - source_date).months

    decay_params = {
        "agronomic": {"threshold": 24, "rate": 0.02},  # 2% per month after 24mo
        "emissions": {"threshold": 12, "rate": 0.05},  # 5% per month after 12mo
        "regulatory": {"threshold": 6, "rate": 0.10}   # 10% per month after 6mo
    }

    params = decay_params.get(field, {"threshold": 12, "rate": 0.03})

    if age_months > params["threshold"]:
        excess_months = age_months - params["threshold"]
        decay_factor = 1.0 - (excess_months × params["rate"])
        return confidence × max(0.5, decay_factor)  # Floor at 50%

    return confidence
```

## 4. Contradiction Impact

When a contradiction is found:

```python
def apply_contradiction_penalty(confidence, contradiction):
    """
    Reduce confidence when contradicted by high-quality source
    """
    contradiction_confidence = get_confidence(contradiction.source)

    if contradiction_confidence > confidence:
        # Strong contradiction: reduce to 50% of original
        return confidence × 0.5
    else:
        # Weak contradiction: reduce by 20%
        return confidence × 0.8
```

## 5. Conclusion Confidence

```python
def calculate_conclusion_confidence(conclusion):
    """
    Conclusion confidence considers both support and contestation
    """
    support_confidences = [get_confidence(s) for s in conclusion.supports]
    contestation_confidences = [get_confidence(c) for c in conclusion.contested_by]

    if not support_confidences:
        return 0.0

    base = min(support_confidences)

    if contestation_confidences:
        max_contestation = max(contestation_confidences)
        # Contested conclusions have reduced confidence
        base = base × (1.0 - max_contestation × 0.5)

    return base
```

## 6. Validation Requirements

All LSA artifacts must:

1. **Premises**: Have confidence scores derived from source quality
2. **Inferences**: Have confidence ≤ min(supports) × 1.1 (allowing methodology bonus)
3. **Conclusions**: Reflect contestation impact if contested
4. **Time-sensitive data**: Apply time decay appropriately

## 7. Example Calculation

```json
{
  "premise-001": {
    "statement": "Study shows 10% carbon increase",
    "source_type": "peer-reviewed-journal",
    "confidence": 0.95
  },
  "inference-001": {
    "supports": ["premise-001"],
    "methodology": "LSA::delta-carbon",
    "confidence": 0.90  // 0.95 × 0.95 (methodology factor)
  },
  "conclusion-001": {
    "supports": ["inference-001"],
    "contested_by": ["contradiction-001"],
    "confidence": 0.72  // 0.90 × (1 - 0.40 × 0.5) = 0.72
  }
}
```

## 8. Audit Trail

All confidence calculations must be auditable:

```json
{
  "confidence": 0.72,
  "calculation": {
    "base": 0.90,
    "contestation_penalty": 0.80,
    "final": 0.72,
    "formula": "0.90 × 0.80 = 0.72"
  }
}
```
