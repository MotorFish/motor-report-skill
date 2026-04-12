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

## 7. Draft Report

The final Markdown report is written by the LLM. Use tables where they improve clarity, but do not mechanically fill a fixed template.

Use `report-style.md` for tone, difference explanation, and conclusion constraints.

## 8. Deliver Output

Return the report path or the Markdown content requested by the user. Include short notes about:

- files used
- assumptions
- missing hash mappings or missing test conditions
- extraction failures that materially affect confidence
