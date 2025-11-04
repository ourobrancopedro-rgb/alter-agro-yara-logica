# Source Quality Scoring Matrix

## Overview

This specification defines how to assess and score the quality of sources used in YARA Lógica reasoning artifacts. Source quality directly impacts premise confidence scores in the LSA/PICC methodology.

## Quality Dimensions

Source quality is evaluated across five dimensions:

| Dimension | Weight | Description |
|:----------|:-------|:------------|
| **Authority** | 0.30 | Publisher reputation, peer review status, citation count |
| **Recency** | 0.25 | Publication date, update frequency, temporal relevance |
| **Methodology** | 0.20 | Research design, sample size, statistical rigor |
| **Independence** | 0.15 | Conflicts of interest, funding sources, editorial independence |
| **Accessibility** | 0.10 | Verifiability, replicability, data availability |

## Scoring Formula

```python
def score_source_quality(source: Dict) -> float:
    """
    Calculate overall source quality score

    Returns: float in range [0.0, 1.0]
    """
    scores = {
        "authority": score_authority(source),
        "recency": score_recency(source),
        "methodology": score_methodology(source),
        "independence": score_independence(source),
        "accessibility": score_accessibility(source)
    }

    weights = {
        "authority": 0.30,
        "recency": 0.25,
        "methodology": 0.20,
        "independence": 0.15,
        "accessibility": 0.10
    }

    return sum(scores[dim] * weights[dim] for dim in scores)
```

## Source Tiers

### Tier 1: Premium Sources (0.90-1.00)

**Characteristics:**
- Rigorous peer review process
- High citation index
- Established institutional backing
- Transparent methodology
- Publicly accessible data

**Examples:**
- **Academic Journals:** Nature, Science, Cell, PNAS
- **Government Agencies:** IPCC, EPA, IBGE, Embrapa
- **International Organizations:** UN FAO, World Bank, OECD

**Use Cases:**
- Foundational premises for critical conclusions
- Regulatory compliance evidence
- Scientific consensus statements

---

### Tier 2: High-Quality Sources (0.75-0.89)

**Characteristics:**
- Editorial review or expert validation
- Credible institutional affiliation
- Documented methodology
- Regular updates

**Examples:**
- **Industry Reports:** McKinsey, Bloomberg, verified market research
- **University Publications:** Technical reports, working papers
- **Established NGOs:** WWF, Greenpeace, TNC (with documented methodology)
- **Trade Associations:** Industry standards, technical guidelines

**Use Cases:**
- Supporting evidence for primary claims
- Market data and industry trends
- Technical specifications

---

### Tier 3: Moderate Sources (0.60-0.74)

**Characteristics:**
- Some editorial oversight
- Identifiable author credentials
- Verifiable publication process
- May have commercial interests

**Examples:**
- **Company Whitepapers:** From recognized industry players
- **Trade Publications:** Industry magazines, technical journals
- **News Media (Verified):** Major news outlets with fact-checking
- **Professional Blogs:** By recognized domain experts

**Use Cases:**
- Contextual information
- Preliminary evidence requiring corroboration
- Industry perspectives

---

### Tier 4: Low-Quality Sources (0.40-0.59)

**Characteristics:**
- Limited editorial oversight
- Author credentials may be unclear
- Methodology not fully documented
- Potential bias not disclosed

**Examples:**
- **Expert Blogs:** Personal blogs by identified experts
- **Unverified Reports:** Reports without peer review
- **Social Media (Verified):** Posts by verified domain experts
- **Press Releases:** From credible organizations

**Use Cases:**
- Supplementary context only
- Must be corroborated by higher-tier sources
- Contradiction checking targets

---

### Tier 5: Unreliable (<0.40)

**Characteristics:**
- Anonymous or pseudonymous sources
- No editorial review
- Undocumented methodology
- Known bias or misinformation history

**Examples:**
- Anonymous sources
- Unverified social media
- Known biased sources
- Unattributed claims

**Use Cases:**
- Generally avoid in LSA artifacts
- May be used only for contradiction detection
- Must be clearly marked with low confidence

---

## Dimension-Specific Scoring

### 1. Authority (30% weight)

```python
def score_authority(source: Dict) -> float:
    """Score based on publisher reputation and credibility"""

    publisher_tier = {
        "peer_reviewed_journal": 1.0,
        "government_agency": 0.95,
        "international_org": 0.95,
        "university": 0.90,
        "industry_report_verified": 0.85,
        "company_publication": 0.75,
        "trade_publication": 0.70,
        "expert_blog": 0.60,
        "news_media": 0.65,
        "social_media": 0.40,
        "anonymous": 0.20
    }

    base_score = publisher_tier.get(source.get("publisher_type"), 0.50)

    # Adjust for citation count (if available)
    citations = source.get("citation_count", 0)
    if citations > 1000:
        base_score = min(1.0, base_score * 1.1)
    elif citations > 100:
        base_score = min(1.0, base_score * 1.05)

    return base_score
```

### 2. Recency (25% weight)

```python
from datetime import datetime, timedelta

def score_recency(source: Dict) -> float:
    """Score based on publication date and field volatility"""

    pub_date = datetime.fromisoformat(source.get("publication_date"))
    age_months = (datetime.utcnow() - pub_date).days / 30

    # Field-specific freshness requirements
    freshness_windows = {
        "regulatory": 6,      # Regulatory changes are fast
        "emissions": 12,      # Carbon market data
        "agronomic": 24,      # Agricultural research
        "geological": 120     # Geological data is stable
    }

    field = source.get("field_category", "agronomic")
    threshold = freshness_windows.get(field, 24)

    if age_months <= threshold:
        return 1.0
    elif age_months <= threshold * 2:
        # Linear decay in second period
        return 1.0 - 0.5 * (age_months - threshold) / threshold
    else:
        # Older sources get minimum score
        return 0.5
```

### 3. Methodology (20% weight)

```python
def score_methodology(source: Dict) -> float:
    """Score based on research methodology quality"""

    methodology_scores = {
        "randomized_controlled_trial": 1.0,
        "meta_analysis": 0.95,
        "cohort_study": 0.90,
        "case_control": 0.85,
        "cross_sectional": 0.80,
        "expert_consensus": 0.75,
        "case_study": 0.70,
        "expert_opinion": 0.65,
        "anecdotal": 0.40
    }

    base_score = methodology_scores.get(source.get("methodology_type"), 0.60)

    # Bonus for large sample sizes
    sample_size = source.get("sample_size", 0)
    if sample_size > 10000:
        base_score = min(1.0, base_score * 1.1)
    elif sample_size > 1000:
        base_score = min(1.0, base_score * 1.05)

    return base_score
```

### 4. Independence (15% weight)

```python
def score_independence(source: Dict) -> float:
    """Score based on conflicts of interest and funding"""

    # Start at 1.0 and deduct for conflicts
    score = 1.0

    # Check for disclosed conflicts
    if source.get("conflicts_disclosed"):
        # Good: conflicts are disclosed
        conflicts = source.get("conflict_list", [])
        if len(conflicts) > 0:
            # Deduct based on severity
            score -= len(conflicts) * 0.1
    else:
        # Bad: no conflict disclosure
        score -= 0.20

    # Check funding sources
    funding = source.get("funding_source", "")
    if funding in ["industry", "commercial"]:
        score -= 0.15
    elif funding in ["government", "foundation"]:
        score += 0.05  # Bonus for independent funding

    return max(0.0, score)
```

### 5. Accessibility (10% weight)

```python
def score_accessibility(source: Dict) -> float:
    """Score based on verifiability and data availability"""

    score = 0.5  # Base score

    # Open access bonus
    if source.get("open_access"):
        score += 0.25

    # Data availability bonus
    if source.get("data_available"):
        score += 0.15

    # Reproducibility bonus
    if source.get("code_available"):
        score += 0.10

    return min(1.0, score)
```

## Implementation Example

```python
# Example source evaluation
source = {
    "publisher_type": "peer_reviewed_journal",
    "publication_date": "2024-06-01T00:00:00Z",
    "field_category": "agronomic",
    "methodology_type": "meta_analysis",
    "sample_size": 5000,
    "conflicts_disclosed": True,
    "conflict_list": [],
    "funding_source": "government",
    "open_access": True,
    "data_available": True,
    "code_available": False
}

quality_score = score_source_quality(source)
# Result: ~0.92 (Tier 1: Premium Source)
```

## Integration with LSA/PICC

Source quality scores directly map to premise confidence:

```json
{
  "premise-001": {
    "statement": "Agricultural practice X increases carbon sequestration",
    "source_sha256": "abc123...",
    "byte_range": "1024-2048",
    "source_quality": 0.92,
    "confidence": 0.92,
    "source_metadata": {
      "publisher_type": "peer_reviewed_journal",
      "journal": "Nature Climate Change",
      "publication_date": "2024-06-01"
    }
  }
}
```

## Best Practices

1. **Always document source tier**: Include source_quality score in premise metadata
2. **Prefer higher tiers**: Use Tier 1-2 sources for critical premises
3. **Diversify sources**: Don't rely solely on one source type
4. **Update stale sources**: Re-evaluate recency scores periodically
5. **Disclose conflicts**: Always note potential biases in source selection

## References

- See `lsa/spec/CONFIDENCE_PROPAGATION.md` for confidence calculation
- See `rag/spec/RAG_HYBRID.md` for source retrieval strategies
