# Extraction Strategy

This skill is LLM-first. Scripts reveal file content; the LLM decides what the content means.

## File Understanding

Start with the file index. Use path, filename, extension, size, and neighboring files to choose what to inspect next.

Treat script-provided categories as hints only. Do not promote a hint to a conclusion without contextual evidence.

## Measured Data

Measured data may appear as:

- PDF test reports
- Excel or CSV tables
- oscilloscope exports
- Word or text notes
- images or screenshots
- numbers stated directly in conversation

Look for cues such as:

- words like measured, test, actual, 实测, 测试, 示波器, 曲线
- test conditions such as voltage, speed, current, control method, load, temperature
- axis labels, units, and chart titles
- customer-provided folders

Convert extracted facts into `MeasuredDatum` records. If only a trend or qualitative observation is available, keep it in `note` and avoid inventing numeric values.

## Simulation Data

For `.em3` projects, never infer the overall meaning of a hash folder without user mapping.

After mapping is known, infer result-file meaning using:

- file names such as `backef`, `torque`, `voltage`, `current`, `speed`, `flux`, `pfe`, `pcu`, `coreloss`
- Chinese winding or rotor names in dat files
- table headers and units
- companion files such as `machinedata.json`, `dsninfo`, `em3res.txt`, `fccouple.txt`, `attachments`

Examples:

- `backef.ecsv` or `backef_*.dat` inside a no-load back-EMF simulation can support back-EMF discussion.
- `torque.ecsv` or `torque_*.dat` inside a known torque simulation can support torque discussion.
- `额定功率-工况报表结果.csv` inside a known rated magnetic-circuit model can support rated operating-point discussion.

Do not read large mesh or field files unless the user specifically needs geometry/field evidence.

## Design Data

Customer design data may include CAD drawings, screenshots, geometry images, material notes, winding information, or machine parameter files.

Use design data to support report context, not to judge the customer design negatively.

## Reading Strategy By File Type

Use `read_tabular.py` for:

- `.csv`
- `.ecsv`
- `.dat`
- `.txt`
- `.json`
- `.xlsx`

Use `extract_pdf_text.py` for PDFs. If text extraction fails, mention the limitation and consider image-based interpretation only if the current agent environment supports it.

For images, inspect visually if available in the current environment. Otherwise record that visual extraction is not available and use filenames/context only.

## Confidence

Use confidence to express evidence quality:

- `0.8-1.0`: directly extracted from clear table/text with matching condition
- `0.6-0.8`: inferred from clear file context and readable value
- `0.4-0.6`: plausible but incomplete condition or weak source
- `<0.4`: keep as uncertain and avoid strong conclusions
