# Skills

Skill = versioned engineering module, not prompt text.

Target package contract:

```text
skills/<skill-id>/
├── SKILL.md
├── manifest.json
├── references/
├── schemas/
├── scripts/
├── tests/
│   ├── unit/
│   ├── golden/
│   ├── regression/
│   └── negative/
└── CHANGELOG.md
```

A Skill is READY only after schema, unit, golden, negative, safety and independent review gates pass.