# Workflow

Use this workflow when the user asks for a motor trial-calculation result summary, measured/simulation comparison, or customer-facing report draft.

## 1. Clarify Task Frame

Extract from the user message:

- project root or relevant folders
- customer name and project name if available
- target output, usually a Markdown report
- key concerns such as back-EMF, torque, current, voltage, speed, efficiency, loss, temperature, or rated point behavior
- known test conditions and simulation conditions

Do not ask for missing information unless it blocks a required precondition.

## 2. Enforce `.em3` Hash Mapping Gate

If the project includes a `.em3` folder, inspect only enough to identify hash-like child folders.

Before interpreting simulation semantics, require the user to provide a mapping from each hash folder to its simulation content.

Acceptable mapping examples:

- `25b41803d278`: no-load back-EMF finite-element simulation
- `afd8dedc2b9a`: rated operating point magnetic-circuit model
- `8f31a9...`: cogging torque finite-element simulation

If mapping is missing, ask for it plainly and stop deeper simulation interpretation. You may still scan general project files or measured/customer data, but do not claim that a hash folder corresponds to a simulation task unless the user provided that meaning.

After mapping is known, use the folder contents to infer result files inside that known simulation context.

## 3. Build File Index

Run:

```powershell
python scripts/scan_project.py "<project-root>"
```

Use the output as a working index, not as a final classification. The script gives metadata and low-confidence hints. The LLM must still decide what matters.

The scanner ignores generated and internal paths by default, including `.git`, `__pycache__`, `report-output`, `figures`, `report-state.json`, `evidence-ledger.json`, and `change-log.md`. Do not include generated artifacts in the evidence pool unless the user explicitly asks to audit report outputs.

## 4. Prioritize Evidence

Inspect files in this order unless the user request suggests otherwise:

- user-provided measured data folders and files
- customer design input files and images
- simulation result folders with known hash mapping
- report-like PDFs or Office documents
- table-like files with relevant names or units
- remaining uncertain files only if needed

Avoid reading every large finite-element mesh, field, node, edge, or binary file unless it is directly relevant.

## 5. Extract Information

For measured data, let the LLM decide whether the source is a test report, curve export, oscilloscope output, customer note, image, or table.

For simulation data, use the user-provided hash mapping as the simulation context, then infer the meaning of result files from names, columns, units, and nearby files.

Use scripts only to expose file content or simple numerical summaries.

### Required Motor/Model Basic Parameters

When a magnetic-circuit report such as `工况报表结果.csv` exists, the report must include a `电机与仿真模型基本参数` section in both full internal reports and customer-facing briefs.

Use:

```powershell
python scripts/extract_motor_design_info.py "<工况报表结果.csv>"
```

The basic-parameter section is a single-value structural table. Do not keep multiple workpoints as separate columns in `电机与仿真模型基本参数`, and do not compress different workpoint values into slash-separated cells. The script JSON keeps workpoint values only for audit and for use in simulation-result or comparison sections.

Extract a reasonably detailed list from the report CSV rather than from memory or file names. Include only parameters that have one structural/model value across the report. Include, when available:

- model/workpoint names, pole count, derived pole pairs, phase count, rotor position, circuit type, control/modulation method, excitation/calculation method;
- stator dimensions, stack length, lamination material, slot count, slot shape, key slot dimensions;
- winding type, layers, pitch, parallel branches, conductors per slot, wire diameter, material, slot fill;
- winding electrical parameters including single-value `电枢绕组相电阻(25度)` when present;
- rotor type, air gap, rotor dimensions, rotor material, magnet material, magnet size, magnet working temperature, remanence, coercive force.

Do not place these workpoint-varying rows in the basic-parameter section: output power, load torque, running speed, sine-wave frequency, current limit, efficiency target, power-factor target, winding working temperature, working-temperature phase resistance, voltage, current, power, efficiency, or losses. Put them in magnetic-circuit operating/result sections and use them during comparison.

Phase resistance handling:

- Include `电枢绕组相电阻(25度)` as the 25 C reference phase resistance in the basic-parameter section when available.
- Keep `绕组工作温度` and `电枢绕组相电阻` as operating/result evidence tied to the relevant workpoint.

If only one phase-resistance row exists and its temperature basis is not explicit, include it under the original row name and state that the temperature basis is only whatever the source row provides.

If the same parameter appears multiple times in the CSV, prefer the first design/model-definition occurrence for the basic-parameter section unless the report context clearly needs a calculated result row.

Place the project geometry figure from `geo2d.png` in this same section. Use `resolve_report_figures.py` to copy the image to the report `figures/` folder when needed.

## 6. Build Comparison Context

For each candidate comparison, record:

- measured metric and value
- simulation metric and value
- units
- operating condition
- source files
- confidence and uncertainty
- whether the conditions appear comparable

Do not force a comparison when conditions are not meaningfully aligned.

Before building numeric comparison rows, create a metric correspondence map. Confirm same-meaning metrics even when names differ, such as measured `输出转矩 T` vs simulation `机械转矩 Tmech`, measured `输出功率 Po` vs simulation `Pmech`, measured `输入功率 Pi` vs simulation `Pin`, and measured `效率 Eff/EFF` vs simulation `eff/效率`. Use units, axes, source context, and value scale to validate the mapping before calculating differences.

Match control method and physical boundary before deciding comparison strength. For PMSM magnetic-circuit operating reports, treat the result as motor-only FOC/SVPWM calculation unless the source clearly says otherwise; compare it primarily with motor-only FOC measured data. Compare square-wave finite-element or parametric-scan results primarily with motor-only square-wave measured data. Whole-machine or motor-plus-reducer measured data can be compared to motor-only simulation only as trend or transformed reference, not as strict validation.

When a measured source contains a feature-point table, use that measured table as the comparison skeleton. Keep measured feature points as rows and preserve the measured field order where practical, such as `U`, `I/Idc`, `Pi`, `T`, `n`, `Po`, and `Eff`. For every mapped field, try to provide measured value, simulation value, and difference. If simulation data is a curve or scan, interpolate at the measured feature point when appropriate; otherwise use the nearest point with a clear nearest-point note. Do not drop a measured row or field merely because the simulation name differs or the result is less favorable.

When the measured feature points and simulation curve/scan are already available as CSV/JSON tables, use `scripts/build_feature_point_table.py` to create a comparison CSV before drafting. Select the match axis according to the engineering relationship: commonly measured `T` to simulation `Tmech` for torque-axis reports, measured `n` to simulation speed for speed-axis reports, or another explicit feature-point axis. The generated table is support for the LLM; still review control mode, boundary, units, and interpolation suitability.

Use as much comparable data as the evidence supports. Separate strict direct comparisons, comparisons after clearly stated transformations, trend comparisons with condition/control/boundary caveats, and values that cannot be judged because their boundary/measurement basis is unclear.

Use `build_comparison.py` as a candidate filter. It first normalizes convertible units, then checks speed, voltage, current, temperature, control mode, and phase/line voltage basis. Its status values mean:

- `comparable`: units convert and checked conditions are aligned within tolerance;
- `condition_mismatch`: metric units convert, but operating conditions differ materially;
- `unit_mismatch`: values cannot be converted to a common unit;
- `needs_review`: important condition information is missing or ambiguous.

The LLM must still review `needs_review` rows and decide whether they can be discussed qualitatively.

## 7. Draft Report

The final Markdown report is written by the LLM. Use tables where they improve clarity, but do not mechanically fill a fixed template.

Use `report-style.md` for tone, difference explanation, and conclusion constraints.

Use `comparison-strategy.md` before drafting the key indicator comparison section.

For the first full report, make `电机与仿真模型基本参数` the third major section unless the user provides a different required structure.

## 8. Create State Package

After drafting the first report, create and save:

- `report-state.json`
- `evidence-ledger.json`
- `change-log.md`

Use `create_report_state.py` when a structured report context is available. If the context is only partially structured, create the closest valid state package and mark uncertain fields clearly.

This state package is required for reliable future incremental updates.

## 9. Deliver Output

Return the report path or the Markdown content requested by the user. Include short notes about:

- files used
- assumptions
- missing hash mappings or missing test conditions
- extraction failures that materially affect confidence
