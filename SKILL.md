---
name: motor-report-skill
description: Use for post-simulation motor trial-calculation projects where an agent must understand project folders, identify customer measured data and simulation results, compare measured vs simulated indicators, draft customer-facing Markdown technical reports, incrementally update an existing report after new/changed simulations, or produce a concise sales/customer external brief from a full technical report. Trigger for .em3 directories, motor test reports, FEA or magnetic-circuit result folders, back-EMF/torque/efficiency/current/voltage comparisons, first report drafting, report updates based on report-state or evidence-ledger files, and requests for customer-ready/sales-ready/external brief reports.
---

# Motor Report Skill

Use this skill to turn an already-computed motor trial project into a measured/simulation comparison and a customer-facing Markdown report draft, update an existing report after simulation results are added or changed, or produce a concise customer external brief from a full technical report. Do not operate electromagnetic simulation software, build models, click GUIs, or run solvers.

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

Use customer brief report mode when the user asks for a concise customer-ready, sales-ready, external-facing, or human-written summary report based on an existing technical report.

## Initial Report Workflow

1. Understand the user request, report goal, customer context, key indicators, and known test/simulation conditions.
2. For `.em3` inputs, obtain the hash-folder mapping before interpreting simulation results.
3. Run `scripts/scan_project.py` on the project root to build a file index.
4. Review the file index and classify candidates at a semantic level: measured data, simulation data, customer design input, report material, asset, or uncertain.
5. Read only promising files first. Use `scripts/read_tabular.py` for tabular/text-like files and `scripts/extract_pdf_text.py` for PDFs when useful.
6. For both full internal reports and concise customer briefs, extract motor/model basic design information from the magnetic-circuit `工况报表结果.csv` using `scripts/extract_motor_design_info.py` when such a report is available. The `电机与仿真模型基本参数` section must contain only single-value structural/model parameters. Do not expand repeated workpoint columns such as maximum efficiency, rated point, maximum torque, or maximum power in this section. Put operating-point inputs and results such as speed, load torque, current limit, working temperature, voltage, current, efficiency, power, and losses in simulation-result or comparison sections instead. If phase-resistance fields exist, include the single-value 25 C reference phase resistance in the basic-parameter section; discuss working-temperature resistance with operating conditions/results.
7. Copy the project geometry image using `scripts/resolve_report_figures.py` when `geo2d.png` is available.
8. Extract measured data and simulation data into the structures described in `references/data-models.md`.
9. Before matching numeric values, build an explicit metric correspondence map between measured names and simulation names. For example, measured `输出转矩 T` may correspond to simulation `机械转矩 Tmech`, and measured `输出功率 Po` may correspond to simulation `Pmech`. Match comparable indicators by metric meaning, unit, control method, condition, axis basis, system boundary, and source credibility. For PMSM magnetic-circuit operating reports, treat the result as motor-only FOC/SVPWM calculation unless the source clearly says otherwise; compare it primarily with motor-only FOC measured data. Compare square-wave simulation with motor-only square-wave measured data. Whole-machine or motor-plus-reducer measured data versus motor-only simulation is trend/reference only. Use `scripts/normalize_metrics.py` and `scripts/build_comparison.py` only as support.
10. Generate useful report figures when source data supports them: geometry image, measured waveforms, FEA result curves, magnetic-circuit external characteristics, and parametric scan performance maps.
11. Draft the Markdown report directly with the LLM. Do not mechanically stitch a fixed template.
12. Create a report state package using `scripts/create_report_state.py` or equivalent structured output. Save `report-state.json`, `evidence-ledger.json`, `change-log.md`, and `figures/` next to the report unless the user asks not to.
13. Use conservative engineering language for missing information, uncertain correspondence, or large differences.

## Incremental Update Workflow

1. Read the existing report and any available `report-state.json`, `evidence-ledger.json`, and `change-log.md`.
2. Identify the user-described change: new hash folder, changed existing hash folder, added measured data, revised measured data, changed design input, or report-only wording change.
3. For any new `.em3` hash folder, require the user to provide its simulation meaning before interpreting results.
4. Run `scripts/diff_project_state.py <project-root> <evidence-ledger.json>` to identify files that are new, modified, deleted, or unchanged.
5. Re-read only changed or newly relevant files unless the previous state is missing or unreliable.
6. Ensure the report has a `电机与仿真模型基本参数` section sourced from magnetic-circuit `工况报表结果.csv`, with the geometry image in the same section. If this section is missing, stale, too thin, or missing phase resistance, update it even when the user's change focuses on other results.
7. Reuse existing measured data and previous simulation data when their source files are unchanged.
8. Rebuild only affected comparison rows, then let the LLM update affected report sections and conclusions.
9. Redraw only figures whose source files changed or whose plotted variables changed.
10. Avoid rewriting the full report unless the change affects most sections or the prior state is missing.
11. Update `report-state.json`, `evidence-ledger.json`, and append a concise entry to `change-log.md`.

## Customer Brief Report Workflow

1. Read the existing full report first, then use `report-state.json`, `evidence-ledger.json`, `change-log.md`, and `figures/` only as supporting context.
2. Ensure the brief includes a compact `电机与仿真模型基本参数` section sourced from magnetic-circuit `工况报表结果.csv`, with the geometry image in that section. Do not omit 25 C reference phase resistance when available. Discuss working-temperature phase resistance with the relevant operating condition or result, not as a repeated structural parameter.
3. Do not redo the whole project analysis unless the user requests recalculation or the full report lacks enough evidence.
4. Read `references/customer-brief-report.md` before drafting the external-facing brief.
5. Produce a concise Markdown report, normally named `customer-brief-report.md` next to the full report unless the user specifies another path.
6. Remove internal development details such as hash-folder logistics, evidence-ledger mechanics, script validation notes, interpolation-test files, and Skill workflow discussion.
7. Keep customer-useful evidence: project purpose, measured/simulation source summary, key comparison table, selected polished figures, accuracy conclusion, difference explanation, and next-step suggestions.
8. Make conclusions clearer than the full technical report while staying evidence-bound. Highlight metrics that agree well; explain boundary-sensitive or mismatched metrics briefly instead of burying the conclusion in uncertainty.
9. If figures are reused, include only figures that help customer understanding. Avoid debug, validation, or intermediate-processing figures unless the user explicitly asks for them.

## Resource Navigation

Read `references/workflow.md` when planning or executing a full report workflow.

Read `references/incremental-update.md` when updating an existing report or when the user mentions added/changed simulation results.

Read `references/extraction-strategy.md` when deciding which files to inspect, how to treat measured data, or how to interpret `.em3` result folders after the hash mapping is known.

Read `references/data-models.md` when constructing measured data, simulation data, comparison rows, or report context.

Read `references/comparison-strategy.md` before drafting or revising the key indicator comparison section, especially when measured and simulated names differ, when motor-only and motor-plus-reducer whole-machine data coexist, or when the report should use all comparable data.

Read `references/report-style.md` before drafting or revising the customer-facing report.

Read `references/customer-brief-report.md` when producing a concise report intended for sales, customer external sharing, or leadership/customer non-developer readers.

Read `references/figure-generation.md` before adding figures to a report or updating figure evidence.

Read `references/curve-data-formats.md` when plotting scope waveforms, FEA CSV/ECSV curves, magnetic-circuit external characteristics, or parametric scan results.

Read `references/examples.md` when you need an example request, example hash mapping, or example output shape.

## Scripts

Use `scripts/scan_project.py <project-root>` to produce a JSON file index with file metadata and hash-folder candidates. By default it ignores generated/internal paths such as `.git`, `__pycache__`, `report-output`, `figures`, `report-state.json`, `evidence-ledger.json`, and `change-log.md`. Use `--include-generated` only when deliberately auditing generated artifacts.

Use `scripts/read_tabular.py <file>` to summarize csv, ecsv, dat, txt, json, xlsx, and similar table-like files.

Use `scripts/extract_pdf_text.py <file.pdf>` to extract PDF text when PDF libraries are available locally. If extraction fails, report the limitation and continue with other evidence.

Use `scripts/extract_motor_design_info.py <工况报表结果.csv>` to extract the motor/model basic design information table from a magnetic-circuit report. This section is required in full reports and customer briefs when the report CSV exists. The primary JSON and Markdown table are intentionally single-value per structural parameter. The script lists workpoint-varying operating/result rows in `skippedRows`; use those rows in simulation-result or comparison sections, not in the basic-parameter section. Phase resistance is required when present in the CSV: include the 25 C reference phase resistance as a basic parameter, and keep working-temperature resistance tied to operating/result conditions.

Use `scripts/normalize_metrics.py <data.json>` to normalize common motor metric names, numeric values, and units in already extracted records.

Use `scripts/build_comparison.py <data.json>` to produce measured/simulation comparison candidates. The script performs basic unit conversion, checks operating-condition comparability for speed, voltage, current, temperature, control mode, and phase/line voltage basis, then assigns `comparabilityStatus`: `comparable`, `condition_mismatch`, `unit_mismatch`, or `needs_review`. Treat the output as a candidate filter, not a final engineering judgment.

Use `scripts/build_feature_point_table.py --measured <measured.csv|json> --simulation <simulation.csv|json> --x <measuredField=simulationField> --map <measuredField=simulationField> ... --output <comparison.csv>` when a measured report provides feature-point rows and a simulation curve/scan can be interpolated or nearest-matched. The output preserves measured feature rows and adds simulation values and differences. Prefer this shape for the key performance comparison instead of replacing measured rows with simulation-native feature points.

For measured feature-point tables, map every meaningful measured field before drafting: for example `U=Udc`, `I=Idc`, `Pi=Pin`, `T=Tmech`, `n=rspeed`, `Po=Pmech`, and `Eff=eff` when those simulation fields exist and share the same basis. If a field basis differs, keep the measured field and state why it is not directly compared.

Use `scripts/create_report_state.py --context <context.json> --report <report.md> --output-dir <dir>` after initial report generation to create `report-state.json`, `evidence-ledger.json`, and `change-log.md`.

Use `scripts/diff_project_state.py <project-root> <evidence-ledger.json>` before incremental updates to detect changed evidence source files. By default it compares only files already referenced by the evidence ledger and ignores generated/internal paths. Use `--scan-added` only when intentionally searching the project for new non-generated evidence.

Use `scripts/update_evidence_ledger.py --ledger <evidence-ledger.json> --new-evidence <new-evidence.json>` after extracting new or changed evidence.

Use `scripts/resolve_report_figures.py <project-root> --output-dir <figures-dir>` to copy the project-level `geo2d.png` geometry image into the report figures folder.

Use `scripts/plot_scope_waveform.py <scope.csv> --output <png>` as an example reader for the current oscilloscope CSV format. If the measured waveform lacks motor speed, pass a magnetic-circuit report with `--motor-report-csv <工况报表结果.csv>` or manually pass `--pole-pairs`/`--pole-count`; the script estimates electrical frequency from adjacent positive peaks in the measured line-voltage waveform and derives mechanical speed as `rpm = electricalFrequencyHz / polePairs * 60`. If it does not fit another oscilloscope export, the LLM should inspect the CSV and adapt or rewrite the plotting logic.

Use `scripts/plot_fea_curves.py <curve-file> [<curve-file> ...] --output-dir <figures-dir>` for LLM-selected FEA result CSV/ECSV curves. The LLM must choose relevant files based on the hash-folder meaning and report goal; the script is not limited to a fixed filename list. For likely back-EMF or voltage waveforms, the script defaults to `--line-voltage-mode auto`: if the result name does not clearly indicate line voltage, it treats the first three phase series as phase back-EMF/voltage, converts them to AB/BC/CA line values, plots the line curves, and records line RMS values for measured line-voltage comparison. For time-domain back-EMF or voltage waveforms, use adjacent positive peaks to determine the electrical period; do not treat the full sequence length as one electrical period.

Use `scripts/plot_mc_external_characteristics.py <external-characteristics.csv> --output <png>` for PMSM magnetic-circuit external characteristic curves. Default x-axis is speed unless the user specifies torque.

Use `scripts/convert_prmresult.py <prmresult.json> --output <csv>` to convert parametric scan JSON into tabular CSV.

Use `scripts/plot_parametric_performance.py <converted.csv> --output <png>` to plot parametric scan performance against `Tmech` by default when comparing with torque-axis measured reports. By default, filter out points with negative mechanical torque and start the x-axis at 0.

## Report Expectations

Generate a Markdown report draft that normally includes project overview, `电机与仿真模型基本参数`, identified data sources, measured waveform or measured curve figures when available, simulation source summary, simulation curve figures, key indicator comparison, difference explanation, and conservative conclusion.

For `关键指标对比`, compare same control method and same boundary first. If a measured feature-point table exists, use it as the comparison skeleton and attempt to map every measured field such as `U`, `I/Idc`, `Pi`, `T`, `n`, `Po`, and `Eff` to the best available simulation field. Report measured value, simulation value, and difference for each mapped field. If no same-boundary simulation counterpart exists, keep the measured value and mark the reason rather than omitting it.

The `电机与仿真模型基本参数` section is required when a magnetic-circuit `工况报表结果.csv` exists. Put the project geometry image from `geo2d.png` in this section, then include grouped single-value tables with motor/model structural parameters extracted from the report CSV. Each parameter row in this section must have exactly one value. Do not include workpoint-varying operating inputs or results such as speed, load torque, output power, current limit, working temperature, working-temperature resistance, voltage, current, efficiency, power, or losses. Prefer a more complete structural parameter list over a minimal nameplate-style list. For both internal and customer brief reports, include 25 C phase resistance when available, especially `电枢绕组相电阻(25度)`; keep working-temperature resistance in operating/result discussion.

For customer brief reports, prioritize readability and decision value over audit completeness. Keep internal traceability artifacts out of the body unless the user explicitly wants an appendix.

Keep report language neutral and engineering-oriented. Do not write that the customer design is unreasonable, the customer test is wrong, or the model is obviously wrong.

When information is incomplete, say that the conclusion is based on currently identified materials and mark missing or uncertain items clearly.

## Failure Handling

If one file cannot be read, record the warning and continue.

If a value cannot be extracted reliably, keep the source and qualitative observation instead of inventing a number.

If measured and simulation conditions do not match clearly, explain the mismatch and avoid overconfident conclusions.

If `.em3` hash-folder meanings are missing, ask for the mapping before interpreting simulation result semantics.

If an existing report lacks `report-state.json` or `evidence-ledger.json`, perform a best-effort update from the report text and current files, but tell the user that future incremental updates will be more reliable after a state package is created.
