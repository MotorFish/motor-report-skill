---
name: motor-report-skill
description: Use for post-simulation motor trial-calculation projects where an agent must understand project folders, identify customer measured data and simulation results, compare measured vs simulated indicators, and draft customer-facing Markdown technical reports. Trigger for .em3 directories, motor test reports, FEA or magnetic-circuit result folders, back-EMF/torque/efficiency/current/voltage comparisons, and report drafting after simulation results already exist.
---

# Motor Report Skill

Use this skill to turn an already-computed motor trial project into a measured/simulation comparison and a customer-facing Markdown report draft. Do not operate electromagnetic simulation software, build models, click GUIs, or run solvers.

## Core Stance

Let the LLM make high-semantic decisions: file purpose, useful evidence, measured/simulation correspondence, engineering explanation, and report wording.

Use scripts only for deterministic support: scanning folders, reading common file formats, extracting basic text/tables, normalizing numbers/units, and calculating simple comparison values.

## Hard Gate For `.em3`

If the input includes a `.em3` project, first check whether the user provided a mapping from each hash-named simulation folder to its simulation meaning.

Example mapping:

- `25b41803d278`: no-load back-EMF finite-element simulation
- `afd8dedc2b9a`: rated operating point magnetic-circuit model

If this mapping is missing, pause the simulation-result interpretation and ask the user to provide it. Do not infer the overall simulation task from a hash folder name alone. After the mapping is provided, use file names and contents inside each folder to infer which result files correspond to torque, voltage, current, back-EMF, loss, speed, efficiency, and related indicators.

## Workflow

1. Understand the user request, report goal, customer context, key indicators, and known test/simulation conditions.
2. For `.em3` inputs, obtain the hash-folder mapping before interpreting simulation results.
3. Run `scripts/scan_project.py` on the project root to build a file index.
4. Review the file index and classify candidates at a semantic level: measured data, simulation data, customer design input, report material, asset, or uncertain.
5. Read only promising files first. Use `scripts/read_tabular.py` for tabular/text-like files and `scripts/extract_pdf_text.py` for PDFs when useful.
6. Extract measured data and simulation data into the structures described in `references/data-models.md`.
7. Match comparable indicators by metric meaning, unit, condition, and source credibility. Use `scripts/normalize_metrics.py` and `scripts/build_comparison.py` only as support.
8. Draft the Markdown report directly with the LLM. Do not mechanically stitch a fixed template.
9. Use conservative engineering language for missing information, uncertain correspondence, or large differences.

## Resource Navigation

Read `references/workflow.md` when planning or executing a full report workflow.

Read `references/extraction-strategy.md` when deciding which files to inspect, how to treat measured data, or how to interpret `.em3` result folders after the hash mapping is known.

Read `references/data-models.md` when constructing measured data, simulation data, comparison rows, or report context.

Read `references/report-style.md` before drafting or revising the customer-facing report.

Read `references/examples.md` when you need an example request, example hash mapping, or example output shape.

## Scripts

Use `scripts/scan_project.py <project-root>` to produce a JSON file index with file metadata and hash-folder candidates.

Use `scripts/read_tabular.py <file>` to summarize csv, ecsv, dat, txt, json, xlsx, and similar table-like files.

Use `scripts/extract_pdf_text.py <file.pdf>` to extract PDF text when PDF libraries are available locally. If extraction fails, report the limitation and continue with other evidence.

Use `scripts/normalize_metrics.py <data.json>` to normalize common motor metric names, numeric values, and units in already extracted records.

Use `scripts/build_comparison.py <data.json>` to compute simple matched comparison rows from measured and simulation records. Treat its output as a draft aid, not a final engineering judgment.

## Report Expectations

Generate a Markdown report draft that normally includes project overview, identified data sources, measured data summary, simulation source summary, key indicator comparison, difference explanation, and conservative conclusion.

Keep report language neutral and engineering-oriented. Do not write that the customer design is unreasonable, the customer test is wrong, or the model is obviously wrong.

When information is incomplete, say that the conclusion is based on currently identified materials and mark missing or uncertain items clearly.

## Failure Handling

If one file cannot be read, record the warning and continue.

If a value cannot be extracted reliably, keep the source and qualitative observation instead of inventing a number.

If measured and simulation conditions do not match clearly, explain the mismatch and avoid overconfident conclusions.

If `.em3` hash-folder meanings are missing, ask for the mapping before interpreting simulation result semantics.
