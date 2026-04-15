# Figure Generation

Use this reference when a report should include visual evidence. The LLM decides which figures are useful and how to discuss them; scripts only generate deterministic image artifacts.

## Figure Folder

Create a `figures/` folder next to the report:

```text
report-output/
├── motor-trial-report.md
├── report-state.json
├── evidence-ledger.json
├── change-log.md
└── figures/
```

Use relative image links in Markdown:

```markdown
![电机径向截面](figures/geometry-section.png)
```

## Geometry Figure

Most `.em3` roots contain `geo2d.png`, a radial section image of the motor. Prefer the root-level `geo2d.png` as the report overview figure. If the root-level image is missing, the LLM may choose a hash-folder `geo2d.png` based on context.

Use `resolve_report_figures.py` to copy the image into the report figures folder and create a figure evidence record.

Place the geometry image inside the `电机与仿真模型基本参数` section when that section is present. Do not leave it as a detached appendix or only in a generic project-overview section.

## Measured Waveforms

Use `plot_scope_waveform.py` only as an example parser for the current oscilloscope CSV format. Oscilloscope exports vary by model and vendor. If the script cannot parse a file, inspect the CSV and adapt the plotting code for the actual format.

The report should state whether a measured waveform is motor-only or system-level data such as motor plus reducer.

If the measured oscilloscope waveform does not specify motor speed, estimate speed from the line-voltage waveform when possible. Use the time interval between adjacent positive maxima as the electrical period, then use pole pairs from the magnetic-circuit report to calculate mechanical speed. Record this as an estimated test speed and include the assumption in the report. Do not use the estimate when the waveform is not clearly line voltage/line back-EMF or the peak sequence is ambiguous.

## FEA Curves

For finite-element results, the LLM must first use the user-provided hash-folder mapping, then decide which curve files matter for the report. Do not hard-code the result file list.

Prefer CSV/ECSV result files over `.dat` files. `.ecsv` files in this workflow are treated as CSV-like text with optional metadata rows.

Examples of useful FEA curves include:

- back-EMF waveform or spectrum
- air-gap flux density
- torque waveform
- current or voltage waveform
- loss curves

Use `plot_fea_curves.py` for LLM-selected CSV/ECSV result files and write the generated figures to `figures/`.

For finite-element back-EMF or voltage waveform files, align the plotted quantity with measured data before analysis. Unless the result name clearly says it is line voltage or line back-EMF, treat three-phase waveform results as phase quantities and convert them to line values before plotting and comparison. Customer oscilloscope waveforms and customer-provided back-EMF values are usually line voltage or line back-EMF RMS, so the report should compare against converted `AB/BC/CA` line curves and line RMS values. Do not compare a simulated phase RMS value directly with a measured line RMS value.

Do not treat the full FEA time sequence as one electrical period by default. A FEA waveform may contain one, two, or more electrical periods. For time-domain back-EMF or voltage data, determine the electrical period from adjacent positive maxima in the waveform, the same way measured oscilloscope waveforms are handled. Use the detected period for speed estimation and RMS windows when available. If peak detection is ambiguous, state that the period/speed estimate is unreliable rather than inventing a period from the sequence length.

## Magnetic-Circuit External Characteristics

Use `plot_mc_external_characteristics.py` for PMSM magnetic-circuit external characteristic CSV files such as `外特性仿真结果.csv`.

Default x-axis is speed when the user does not specify otherwise. Use true multiple y-axes by default. If the user explicitly requests torque-axis external characteristics, use `--x-axis torque`. If the figure becomes hard to read, the LLM may additionally create a simplified figure, but the default script output should preserve the true multi-axis behavior.

## Parametric Scan Results

Use `convert_prmresult.py` to convert `prmresult.json` to CSV. Use `plot_parametric_performance.py` to plot torque-axis performance curves.

When comparing with measured torque-axis reports, prefer `Tmech` as the x-axis, filter out rows where mechanical torque is below 0, start the x-axis at 0 torque, and plot `Pin`, `Pmech`, `eff`, `Udc`, `Idc`, and speed-related columns if available.

## Evidence Ledger

Each generated figure should be recorded as evidence:

```json
{
  "sourceRole": "figure",
  "sourceFile": "25b41803d278/backef.ecsv",
  "generatedFile": "figures/fea-backef.png",
  "figureKind": "feaCurve",
  "metricNames": ["backEmf"],
  "extractionMethod": "plot_fea_curves.py"
}
```

During incremental updates, redraw only figures whose source files or plotted variable choices changed.
