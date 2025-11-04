<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="360" height="140" viewBox="0 0 360 140" role="img" aria-labelledby="title desc">
  <title id="title">YARA Lógica Integrity Seal</title>
  <desc id="desc">Integrity badge derived from the SHA-256 hash of infra/github/hash_ledger.json.</desc>
  <defs>
    <linearGradient id="bg" x1="0%" x2="100%" y1="0%" y2="100%">
      <stop offset="0%" stop-color="#10172a"/>
      <stop offset="100%" stop-color="#1f2937"/>
    </linearGradient>
    <style type="text/css"><![CDATA[
      text { font-family: "IBM Plex Mono", "Fira Code", "Consolas", monospace; }
      .label { font-size: 14px; fill: #cbd5f5; letter-spacing: 0.08em; }
      .value { font-size: 16px; fill: #f8fafc; }
      .footer { font-size: 12px; fill: #94a3b8; }
      .title { font-size: 20px; fill: #fef3c7; font-weight: 600; }
      .divider { stroke: #334155; stroke-width: 1; stroke-dasharray: 4 3; }
    ]]></style>
  </defs>
  <rect width="360" height="140" rx="16" ry="16" fill="url(#bg)" stroke="#38bdf8" stroke-width="2"/>
  <g transform="translate(20,32)">
    <text class="title">YARA Lógica — Integrity Seal</text>
  </g>
  <line class="divider" x1="20" x2="340" y1="56" y2="56"/>
  <g transform="translate(20,76)">
    <text class="label">HASH (SHA-256 · hash_ledger.json)</text>
  </g>
  <g transform="translate(20,96)">
    <text class="value">{{LEDGER_SHA256}}</text>
  </g>
  <g transform="translate(20,122)">
    <text class="footer">Updated: {{UPDATED_ISO}} · BUSL-1.1 · Alter Agro Ltda.</text>
  </g>
</svg>
