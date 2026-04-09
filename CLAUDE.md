# CLAUDE.md

> Context for AI agents working on barcode-validator.

## What is barcode-validator?

Python tool. Validates barcodes on label proofs for Amazon FBA. Input: PDF/AI/PSD/image + optional expected values. Output: extracted barcodes, classification, pass/fail JSON.

**North Star:** Replace manual barcode scanner with one command.

**Users:** NCL ops team (CLI), AI agents (Python API). Fully offline.

## Quick Navigation

| Need | Go To |
| ---- | ----- |
| Product requirements | `docs/PRD.md` |
| Roadmap / epics | `docs/roadmap.md` |
| Architecture decisions | `spec/001-*.md` — `spec/006-*.md` |
| Research | `docs/research/` |
| Plans | `plans/active/` and `plans/complete/` |
| Test fixtures | `test_docs/` |

## Tech Stack (Locked)

| Component | Choice | ADR |
| --------- | ------ | --- |
| PDF/AI render | PyMuPDF (`fitz`) | `spec/002` |
| Decode (primary) | zxing-cpp v3.0.0 | `spec/001` |
| Decode (fallback) | pyzbar (optional) | `spec/001` |
| Preprocessing | OpenCV (`cv2`) | `spec/003` |
| Image/PSD | Pillow | `spec/006` |
| Classification | Custom Python | `spec/004` |
| CLI | argparse | `spec/005` |
| Package mgr | uv | — |
| Python | 3.13+ | `.python-version` |
| Testing | pytest | — |

**Locked.** Don't second-guess. Update ADR first if revisiting.

## ADRs

All in `spec/`. Locked.

| ADR | Decision |
| --- | -------- |
| 001 | zxing-cpp primary, pyzbar fallback |
| 002 | PyMuPDF PDF/AI render at 3x scale |
| 003 | OpenCV: raw first, then grayscale + blur + threshold |
| 004 | Priority-ordered pattern matching for classification |
| 005 | argparse CLI, JSON stdout, human stderr |
| 006 | Extension-based file format routing |

## Folder Structure

```text
barcode-validator/
├── CLAUDE.md
├── pyproject.toml
├── uv.lock
├── .python-version
├── docs/                    # PRD, roadmap, research
├── spec/                    # ADRs (locked)
├── plans/active|complete/   # Implementation plans
├── src/barcode_validator/   # Source
├── tests/                   # pytest
└── test_docs/               # Real label proofs (gitignored)
```

## Package Management

**`uv` only. Never `pip`.**

```bash
uv add <package>              # dependency
uv add --dev <package>        # dev dependency
uv add --optional pyzbar <pkg> # optional group
uv run <command>              # run in venv
uv run pytest                 # tests
uv sync                      # sync from lock
```

## Core Pipeline

```text
File → extension routing (ADR-006)
  → PDF/AI: PyMuPDF 2x → PSD: Pillow composite → Raster: Pillow open
  → zxing-cpp decode
  → miss? preprocess (gray → blur → threshold) → retry
  → still miss + pyzbar? fallback
  → raw barcodes (value, symbology, page)
  → classify → validate (regex, check digits) → compare expected
  → JSON output
```

## Output Schema

JSON per file. Full schema in `docs/PRD.md`. Key fields:

- `passed`: bool verdict
- `mode`: `"decode"` | `"comparison"`
- `barcodes[]`: value, type, symbology, page, valid_format, valid_checkdigit, matches_expected
- `expected_not_found`: unmatched expected values
- `summary`: human-readable one-liner

## Testing

**TDD.** Failing test → make pass → commit.

```bash
uv run pytest                                    # all
uv run pytest tests/test_decoding.py -v          # file
uv run pytest tests/test_decoding.py::test_name -v  # single
```

### Test Fixtures

Real proofs in `test_docs/` (gitignored):

| File | Format | Pages |
| ---- | ------ | ----- |
| `(proof)(BL6)(540837).pdf` | PDF 1.6 | 2 |
| `(proof)(BL6)(540841).pdf` | PDF 1.6 | 2 |
| `EXCEL PRINTPACK-0480-01 proof.pdf` | PDF 1.6 | — |
| `EXCEL PRINTPACK-0480-04 proof.pdf` | PDF 1.6 | — |
| `(label_artwork)(...)(Level_Off).ai` | PDF 1.6 | 1 |
| `(label_artwork)(...)(Level_Off).jpg` | JPEG 300dpi | 1 |
| `(label_artwork)(...)(Monolaurin_600mg)(...).eps` | EPS | — (unsupported) |

### Test: yes

- Check digit validation (correct + incorrect)
- Format classification per barcode type
- Decode-only vs comparison mode shapes
- Error paths: unsupported file, no barcodes
- Integration: full pipeline against `test_docs/`

### Test: no

- Library internals (PyMuPDF/zxing-cpp/Pillow)
- Network (none exists)

## Plans

`plans/active/` during work → `plans/complete/` when done. Create for multi-step/epic work. Skip for bug fixes, single-file changes.

## Common Tasks

**New module:** `src/barcode_validator/<mod>.py` + `tests/test_<mod>.py`. TDD cycle.

**Add dependency:** `uv add <pkg>` → verify `pyproject.toml` + `uv.lock` → commit both.

**Fix bug:** repro test (fails) → fix → test passes → commit together.

## Coding Guidelines

### Think First

- State assumptions. If uncertain, ask.
- Multiple interpretations? Present them, don't pick silently.
- Simpler approach exists? Say so. Push back when warranted.

### Simplicity

- No extras beyond ask.
- No single-use abstractions.
- No impossible-scenario error handling.
- No speculative flexibility.
- 200 lines when 50 work? Rewrite.

### Surgical Changes

- Don't touch adjacent code, comments, formatting.
- Don't refactor working code.
- Match existing style.
- Remove imports/vars YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

Every line traces to task at hand.

### Goal-Driven

- "Add validation" → tests for invalid inputs, make pass
- "Fix bug" → repro test, make pass
- "Refactor X" → tests pass before and after

### Python Style

- Type hints on signatures. Not locals unless unclear.
- Dataclasses over dicts.
- `pathlib.Path` over strings.
- f-strings. Explicit imports. One class per file if substantial.

## Barcode Types

| Type | Format | Validation |
| ---- | ------ | ---------- |
| FNSKU | `X00` + 7 alphanum (Code 128) | Regex, value match |
| UPC-A | 12 digits | MOD 10 check digit |
| UPC-E | 8 digits | Check digit |
| EAN-13 | 13 digits | MOD 10 check digit |
| EAN-8 | 8 digits | Check digit |
| ISBN-13 | 13 digits, 978/979 prefix | Check digit |
| ASIN | 10 alphanum, B0 prefix | Regex |
| Code 128 | Variable alphanum | Symbology check |
| Code 39 | Variable alphanum | Symbology check |

## Living Documents

Agents maintain these across sessions. Keep concise.

| File | Purpose | Lifespan |
| ---- | ------- | -------- |
| `MEMORY.md` | Project memory — discoveries, gotchas, env notes. Under 200 lines. | Persistent. Append + consolidate. |
| `ERRORS.md` | Known bugs. Open vs Resolved sections. | Persistent. Move to Resolved when fixed. |
| `.ai/active-plan.md` | Session reference — current epic/task/branch, progress. | **Ephemeral.** Clean at session start. |

### Rules

- **MEMORY.md:** Only non-obvious stuff — ground-truth values, workarounds, env quirks. Don't duplicate CLAUDE.md or ADRs. Consolidate to prevent bloat.
- **ERRORS.md:** Short description, date, repro steps. Move to Resolved with commit hash when fixed.
- **.ai/active-plan.md:** Fill Current Work at session start. Update Progress as you go. Scratch only — won't persist.

## Checklist for AI Agents

### Before Work

- [ ] Read this file
- [ ] Read relevant ADRs in `spec/`
- [ ] Check `docs/roadmap.md` for epic status
- [ ] Check `plans/active/` for in-progress plans
- [ ] Read `MEMORY.md` and `ERRORS.md`
- [ ] Clean `.ai/active-plan.md`, fill Current Work
- [ ] `uv run pytest` — establish baseline

### After Work

- [ ] `uv run pytest` — all pass
- [ ] Update `MEMORY.md` with session discoveries/gotchas
- [ ] Update `ERRORS.md` if bugs found/resolved
- [ ] Update `docs/roadmap.md` if epic status changed
- [ ] Move done plans to `plans/complete/`
- [ ] Commit with message describing "why"
