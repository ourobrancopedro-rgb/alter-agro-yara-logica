# Carbon Credit Methodologies

This directory contains carbon credit methodologies from various standards bodies (Verra, Gold Standard, etc.).

---

## Documents

### Verra VCS Methodologies

```yaml
documents:
  - file: VM0047_v1.3.pdf
    title: "VM0047 Afforestation, Reforestation and Revegetation"
    version: "1.3"
    published: "2023-06-15"
    source_url: "https://verra.org/methodologies/vm0047/"
    classification: "verra-methodology"
    domain: "carbon_markets"
    language: "en"
    description: |
      Methodology for ARR (Afforestation, Reforestation, Revegetation) projects.
      Applicable to projects that increase carbon stocks through tree planting
      and forest restoration on previously non-forested land.

  - file: VM0042_v2.0.pdf
    title: "VM0042 Methodology for Improved Agricultural Land Management"
    version: "2.0"
    published: "2022-11-10"
    source_url: "https://verra.org/methodologies/vm0042/"
    classification: "verra-methodology"
    domain: "carbon_markets"
    language: "en"
    description: |
      Methodology for agricultural land management improvements that increase
      soil organic carbon and reduce GHG emissions from agricultural activities.
```

---

## Instructions

### Adding New Methodologies

1. Download official PDF from methodology registry
2. Rename file using convention: `{Standard}_{ID}_v{Version}.pdf`
3. Add metadata entry to this README
4. Commit: `docs: add {methodology name} v{version}`
5. Push → automatic ingestion into RAG

### Version Updates

When a methodology is revised:
- Add new version file (don't delete old)
- Update metadata with new version
- Commit: `docs: add {methodology name} v{new_version}`

This maintains historical versions in Git (each with unique SHA).

---

**Last Updated:** 2025-11-24
