---
name: LSA Decision Record
about: Create an audit-grade decision record using the PICC methodology
title: '[LSA] '
labels: 'lsa, decision-record, needs-review'
assignees: ''
---

## Decision Question

<!-- What decision are you documenting? Be specific and actionable. -->

**Question:**

---

## Premises

<!-- List all foundational facts, assumptions, and expert opinions supporting this decision. -->
<!-- Use format: P1, P2, P3... -->
<!-- For FACT premises, include ≥2 HTTPS evidence URLs -->

### P1: [Type: FACT/ASSUMPTION/EXPERT_OPINION]
**Text:**

**Evidence:**
- https://
- https://

### P2: [Type: FACT/ASSUMPTION/EXPERT_OPINION]
**Text:**

**Evidence:**
-

---

## Inferences

<!-- Logical deductions derived from the premises above. -->
<!-- Use format: I1, I2, I3... -->

- **I1:**
- **I2:**

---

## Contradictions

<!-- Opposing evidence, limitations, or conflicting information that challenges this decision. -->
<!-- Use format: C1, C2, C3... -->

- **C1:**
- **C2:**

---

## Conclusion

<!-- Final decision statement. Be clear and actionable. -->

**Decision:**

**Confidence Level:** [LOW / MEDIUM / HIGH]

---

## Falsifier (Popperian Validation)

<!-- Define measurable criteria that would invalidate this decision if met. -->

- **Metric:** <!-- What to measure (e.g., "Auditor_NCs", "Customer_Complaints") -->
- **Threshold:** <!-- Falsification trigger (e.g., ">0", ">5 cases") -->
- **Evaluation Date:** <!-- When to review (YYYY-MM-DD) -->
- **Action if Falsified:** <!-- What to do if threshold is exceeded -->

---

## Metadata

**Author:** <!-- Your name or team -->
**Created:** <!-- YYYY-MM-DD -->
**Context:** <!-- Project, phase, or use case -->
**Approvers Required:** <!-- List reviewers if applicable -->

---

## Attachments

<!-- Link to supporting documents, specifications, or evidence -->

-
-

---

## Instructions for Manual Records

1. **Fill in all required sections** above
2. **For FACT premises:** Include at least 2 HTTPS evidence URLs
3. **Add appropriate labels:**
   - Keep: `lsa`, `decision-record`
   - Add confidence: `low-confidence`, `medium-confidence`, or `high-confidence`
   - Remove: `needs-review` after validation
4. **Request approvals** from relevant stakeholders
5. **Once approved:** A hash will be generated and added to the issue

---

**Note:** Automated decision records created via the n8n workflow will auto-populate this template and include cryptographic hashes for audit integrity.
