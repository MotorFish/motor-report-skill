# Incremental Update

Use this reference when the user asks to revise an existing motor trial report after new simulation work, changed simulation results, added measured data, or leadership/customer feedback.

## Goal

Avoid regenerating the entire report when only part of the evidence changed.

Preserve useful existing report content, reuse unchanged measured data and simulation data, and update only affected comparison rows, tables, explanations, and conclusions.

## Required Inputs

Prefer these inputs:

- existing report Markdown
- `report-state.json`
- `evidence-ledger.json`
- project root
- user-described change

The user-described change should identify one of:

- new hash folder and its simulation meaning
- changed existing hash folder and what changed
- added or replaced measured data
- revised design input
- report wording/formatting request only

If a new `.em3` hash folder is involved, require the user to provide the hash-folder meaning before interpreting it.

## State Package

After the first report, maintain:

```text
report-output/
├── motor-trial-report.md
├── report-state.json
├── evidence-ledger.json
└── change-log.md
```

`report-state.json` stores extracted data, comparisons, hash mapping, report sections, and update history.

`evidence-ledger.json` stores source-file evidence with file size, modified time, optional content hash, source role, metrics, and report-section usage.

`change-log.md` stores concise human-readable update history.

## Update Workflow

1. Read the existing report and state package.
2. Parse the user's change request.
3. If a new `.em3` hash folder is mentioned, confirm its simulation meaning is provided.
4. Run `diff_project_state.py` to compare current evidence source files against the previous evidence ledger.
5. Decide affected scope:
   - new simulation folder: inspect only that folder and related existing measured data
   - changed simulation folder: re-read only records tied to that folder
   - added measured data: inspect the new measured files and compare with existing relevant simulations
   - report wording only: avoid data re-extraction
6. Rebuild affected `simulationData`, `measuredData`, and `comparisonRows`.
7. Ask the LLM to update only affected report sections unless the change broadly affects the report.
8. Update state files and append `change-log.md`.

`diff_project_state.py` compares only files already referenced by `evidence-ledger.json` by default. It ignores generated/internal paths such as `.git`, `__pycache__`, `report-output`, `figures`, `report-state.json`, `evidence-ledger.json`, and `change-log.md`. Use `--scan-added` only when the user says new evidence was added but does not provide a path, or when the existing state is incomplete.

## Affected Scope Rules

New hash folder:

- require mapping
- add mapping to `report-state.json`
- scan and inspect the folder
- compare its extracted indicators against existing measured data if comparable
- add new report subsection or rows

Changed hash folder:

- locate previous evidence records with the same `hashFolder`
- re-read changed files only
- replace or revise affected `simulationData`
- update comparison rows and related explanation

Added measured data:

- inspect new measured source files
- add `MeasuredDatum` records
- compare with existing simulation data where conditions align
- update source tables and comparison sections

Deleted source file:

- mark evidence as unavailable
- remove or qualify affected report statements
- avoid silently retaining obsolete conclusions

## Local Report Editing Guidance

Prefer local section-level edits:

- update source tables
- append or replace affected comparison rows
- revise difference explanation for affected metrics
- revise conclusion only if the new/changed evidence changes overall confidence

Do not rewrite unrelated project overview or unchanged measured-data sections unless needed for consistency.

## No State Package Fallback

If the old report has no `report-state.json` or `evidence-ledger.json`:

- read the report text
- scan current project files
- use the user's change description to focus work
- create a new state package after the update
- tell the user that future updates will be more reliable with the new state package

## Change Log Format

Use this shape in `change-log.md`:

```markdown
## 2026-04-13 15:30

- Request: Added cogging torque FEA simulation.
- Affected hash folders: `abc123...`
- Evidence changes: added `abc123.../torque.ecsv`
- Report updates: added cogging torque comparison row and revised conclusion.
- Notes: No matching measured cogging torque data was found; result is reported as simulation-only reference.
```
