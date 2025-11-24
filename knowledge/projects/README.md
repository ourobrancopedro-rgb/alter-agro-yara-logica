# Project-Specific Documents

This directory contains project-specific documentation such as Project Design Documents (PDDs), feasibility studies, monitoring reports, and validation/verification reports.

---

## ⚠️ Confidentiality Notice

Project documents often contain **business-sensitive information** and should be stored in a **private repository** if they include:
- Proprietary methodologies
- Financial projections
- Landowner agreements
- Competitive business strategies

For public repositories, only store:
- De-identified example PDDs (for template purposes)
- Publicly registered project documents (already on Verra/Gold Standard registries)

---

## Document Types

### Project Design Documents (PDDs)

```yaml
# Example:
documents:
  - file: PROJ001-PDD-2025-01-15.pdf
    project_id: "PROJ001"
    project_name: "Alto Cerrado ARR Project"
    methodology: "VM0047"
    area_ha: 8000
    submitted_date: "2025-01-15"
    classification: "project-document"
    domain: "carbon_markets"
```

### Monitoring Reports

```yaml
  - file: PROJ001-monitoring-report-2025-Q1.pdf
    project_id: "PROJ001"
    reporting_period: "2025-Q1"
    classification: "project-document"
```

### Validation/Verification Reports

```yaml
  - file: PROJ001-validation-report-2025-02.pdf
    project_id: "PROJ001"
    auditor: "SCS Global Services"
    report_type: "validation"
    classification: "project-document"
```

---

## File Naming Convention

- PDDs: `{project-id}-PDD-{date}.pdf`
- Monitoring: `{project-id}-monitoring-report-{period}.pdf`
- Validation: `{project-id}-validation-report-{date}.pdf`
- Verification: `{project-id}-verification-report-{date}.pdf`

---

**Last Updated:** 2025-11-24
