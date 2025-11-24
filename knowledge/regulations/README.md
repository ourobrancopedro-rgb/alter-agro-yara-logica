# Regulations & Legal References

This directory contains Brazilian and international environmental regulations, laws, and compliance requirements.

---

## Documents

### Brazilian Federal Laws

```yaml
documents:
  - file: forest-code-lei-12651-2012.pdf
    title: "Lei 12.651/2012 - Código Florestal Brasileiro"
    published: "2012-05-25"
    source_url: "http://www.planalto.gov.br/ccivil_03/_ato2011-2014/2012/lei/l12651.htm"
    classification: "regulation-brazil"
    domain: "compliance_legal"
    language: "pt-BR"
    description: |
      Brazilian Forest Code defining Legal Reserve (RL) and Permanent
      Preservation Areas (APP) requirements for rural properties.

  - file: lgpd-lei-13709-2018.pdf
    title: "Lei 13.709/2018 - Lei Geral de Proteção de Dados (LGPD)"
    published: "2018-08-14"
    source_url: "http://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm"
    classification: "regulation-brazil"
    domain: "compliance_legal"
    language: "pt-BR"
    description: |
      Brazilian data protection law (equivalent to GDPR). Relevant for
      project participant data collection and storage.
```

---

## Instructions

### File Naming Convention

- Federal laws: `{topic}-lei-{number}-{year}.pdf`
- State decrees: `{state}-{topic}-decree-{number}-{year}.pdf`
- International: `{country}-{topic}-{year}.pdf`

### Adding New Regulations

1. Download official text from government source
2. Verify authenticity (use official .gov.br domains)
3. Add metadata entry to this README
4. Commit: `docs: add {law name}`
5. Push → automatic ingestion into RAG

---

**Last Updated:** 2025-11-24
