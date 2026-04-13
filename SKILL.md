---
name: motor-report-skill
description: Use for post-simulation motor trial-calculation projects where an agent must understand project folders, identify customer measured data and simulation results, compare measured vs simulated indicators, draft customer-facing Markdown technical reports, or incrementally update an existing report after new/changed simulations. Trigger for .em3 directories, motor test reports, FEA or magnetic-circuit result folders, back-EMF/torque/efficiency/current/voltage comparisons, first report drafting, and report updates based on report-state or evidence-ledger files.
---

# Motor Report Skill

Use this skill to turn an already-computed motor trial project into a measured/simulation comparison and a customer-facing Markdown report draft, or to update an existing report after simulation results are added or changed. Do not operate electromagnetic simulation software, build models, click GUIs, or run solvers.

## Core Stance

Let the LLM make high-semantic decisions: file purpose, useful evidence, measured/simulation correspondence, engineering explanation, and report wording.

Use scripts only for deterministic support: scanning folders, reading common file formats, extracting basic text/tables, normalizing numbers/units, and calculating simple comparison values.

## Hard Gate For `.em3`

If the input includes a `.em3` project, first check whether the user provided a mapping from each hash-named simulation folder to its simulation meaning.

Example mapping:

- `25b41803d278`: no-load back-EMF finite-element simulation
- `afd8dedc2b9a`: rated operating point magnetic-circuit model

If this mapping is missing, pause the simulation-result interpretation and ask the user to provide it. Do not infer the overall simulation task from a hash folder name alone. After the mapping is provided, use file names and contents inside each folder to infer which result files correspond to torque, voltage, current, back-EMF, loss, speed, efficiency, and related indicators.

## Modes

Use initial report mode when no prior report state exists or the user asks for a first report.

Use incremental update mode when the user provides an existing report, a previous `report-state.json`, an `evidence-ledger.json`, or says that a hash folder was added, recalculated, replaced, or changed.

## Initial Report Workflow

1. Understand the user request, report goal, customer context, key indicators, and known test/simulation conditions.
2. For `.em3` inputs, obtain the hash-folder mapping before interpreting simulation results.
3. Run `scripts/scan_project.py` on the project root to build a file index.
4. Review the file index and classify candidates at a semantic level: measured data, simulation data, customer design input, report material, asset, or uncertain.
5. Read only promising files first. Use `scripts/read_tabular.py` for tabular/text-like files and `scripts/extract_pdf_text.py` for PDFs when useful.
6. Extract measured data and simulation data into the structures described in `references/data-models.md`.
7. Match comparable indicators by metric meaning, unit, condition, and source credibility. Use `scripts/normalize_metrics.py` and `scripts/build_comparison.py` only as support.
8. Generate useful report figures when source data supports them: geometry image, measured waveforms, FEA result curves, magnetic-circuit external characteristics, and parametric scan performance maps.
9. Draft the Markdown report directly with the LLM. Do not mechanically stitch a fixed template.
10. Create a report state package using `scripts/create_report_state.py` or equivalent structured output. Save `report-state.json`, `evidence-ledger.json`, `change-log.md`, and `figures/` next to the report unless the user asks not to.
11. Use conservative engineering language for missing information, uncertain correspondence, or large differences.

## Incremental Update Workflow

1. Read the existing report and any available `report-state.json`, `evidence-ledger.json`, and `change-log.md`.
2. Identify the user-described change: new hash folder, changed existing hash folder, added measured data, revised measured data, changed design input, or report-only wording change.
3. For any new `.em3` hash folder, require the user to provide its simulation meaning before interpreting results.
4. Run `scripts/diff_project_state.py <project-root> <evidence-ledger.json>` to identify files that are new, modified, deleted, or unchanged.
5. Re-read only changed or newly relevant files unless the previous state is missing or unreliable.
6. Reuse existing measured data and previous simulation data when their source files are unchanged.
7. Rebuild only affected comparison rows, then let the LLM update affected report sections and conclusions.
8. Redraw only figures whose source files changed or whose plotted variables changed.
9. Avoid rewriting the full report unless the change affects most sections or the prior state is missing.
10. Update `report-state.json`, `evidence-ledger.json`, and append a concise entry to `change-log.md`.

## Resource Navigation

Read `references/workflow.md` when planning or executing a full report workflow.

Read `references/incremental-update.md` when updating an existing report or when the user mentions added/changed simulation results.

Read `references/extraction-strategy.md` when deciding which files to inspect, how to treat measured data, or how to interpret `.em3` result folders after the hash mapping is known.

Read `references/data-models.md` when constructing measured data, simulation data, comparison rows, or report context.

Read `references/report-style.md` before drafting or revising the customer-facing report.

Read `references/figure-generation.md` before adding figures to a report or updating figure evidence.

Read `references/curve-data-formats.md` when plotting scope waveforms, FEA CSV/ECSV curves, magnetic-circuit external characteristics, or parametric scan results.

Read `references/examples.md` when you need an example request, example hash mapping, or example output shape.

## Scripts

Use `scripts/scan_project.py <project-root>` to produce a JSON file index with file metadata and hash-folder candidates.

Use `scripts/read_tabular.py <file>` to summarize csv, ecsv, dat, txt, json, xlsx, and similar table-like files.

Use `scripts/extract_pdf_text.py <file.pdf>` to extract PDF text when PDF libraries are available locally. If extraction fails, report the limitation and continue with other evidence.

Use `scripts/normalize_metrics.py <data.json>` to normalize common motor metric names, numeric values, and units in already extracted records.

Use `scripts/build_comparison.py <data.json>` to compute simple matched comparison rows from measured and simulation records. Treat its output as a draft aid, not a final engineering judgment.

Use `scripts/create_report_state.py --context <context.json> --report <report.md> --output-dir <dir>` after initial report generation to create `report-state.json`, `evidence-ledger.json`, and `change-log.md`.

Use `scripts/diff_project_state.py <project-root> <evidence-ledger.json>` before incremental updates to detect changed source files.

Use `scripts/update_evidence_ledger.py --ledger <evidence-ledger.json> --new-evidence <new-evidence.json>` after extracting new or changed evidence.

Use `scripts/resolve_report_figures.py <project-root> --output-dir <figures-dir>` to copy the project-level `geo2d.png` geometry image into the report figures folder.

Use `scripts/plot_scope_waveform.py <scope.csv> --output <png>` as an example reader for the current oscilloscope CSV format. If it does not fit another oscilloscope export, the LLM should inspect the CSV and adapt or rewrite the plotting logic.

Use `scripts/plot_fea_curves.py <curve-file> [<curve-file> ...] --output-dir <figures-dir>` for LLM-selected FEA result CSV/ECSV curves. The LLM must choose relevant files based on the hash-folder meaning and report goal; the script is not limited to a fixed filename list.

Use `scripts/plot_mc_external_characteristics.py <external-characteristics.csv> --output <png>` for PMSM magnetic-circuit external characteristic curves. Default x-axis is speed unless the user specifies torque.

Use `scripts/convert_prmresult.py <prmresult.json> --output <csv>` to convert parametric scan JSON into tabular CSV.

Use `scripts/plot_parametric_performance.py <converted.csv> --output <png>` to plot parametric scan performance against `Tmech` by default when comparing with torque-axis measured reports. By default, filter out points with negative mechanical torque and start the x-axis at 0.

## Report Expectations

Generate a Markdown report draft that normally includes project overview, geometry image, identified data sources, measured waveform or measured curve figures when available, simulation source summary, simulation curve figures, key indicator comparison, difference explanation, and conservative conclusion.

Keep report language neutral and engineering-oriented. Do not write that the customer design is unreasonable, the customer test is wrong, or the model is obviously wrong.

When information is incomplete, say that the conclusion is based on currently identified materials and mark missing or uncertain items clearly.

## Failure Handling

If one file cannot be read, record the warning and continue.

If a value cannot be extracted reliably, keep the source and qualitative observation instead of inventing a number.

If measured and simulation conditions do not match clearly, explain the mismatch and avoid overconfident conclusions.

If `.em3` hash-folder meanings are missing, ask for the mapping before interpreting simulation result semantics.

If an existing report lacks `report-state.json` or `evidence-ledger.json`, perform a best-effort update from the report text and current files, but tell the user that future incremental updates will be more reliable after a state package is created.
