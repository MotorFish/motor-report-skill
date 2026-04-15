# Data Models

Use these shapes as semantic targets. They do not require strict Python classes unless useful.

## ProjectMeta

```json
{
  "projectName": "",
  "customerName": "",
  "projectRoot": "",
  "notes": []
}
```

## FileRecord

```json
{
  "relativePath": "",
  "absolutePath": "",
  "fileName": "",
  "extension": "",
  "size": 0,
  "categoryCandidate": "unknown",
  "semanticTags": [],
  "confidence": 0.0
}
```

## MachineBasicInfo

```json
{
  "machineType": "",
  "rotorPosition": "",
  "slotCount": null,
  "poleCount": null,
  "phaseCount": null,
  "ratedVoltage": null,
  "ratedPower": null,
  "ratedSpeed": null,
  "statorOuterDiameter": null,
  "statorInnerDiameter": null,
  "rotorOuterDiameter": null,
  "rotorInnerDiameter": null,
  "windingInfo": "",
  "magnetMaterial": "",
  "laminationMaterial": "",
  "controlAlgorithm": "",
  "modulationMode": "",
  "circuitType": "",
  "currentLimit": null,
  "frequency": null,
  "airGap": null,
  "wireDiameter": null,
  "slotFill": null,
  "phaseResistance25C": null,
  "windingTemperature": null,
  "phaseResistanceWorkingTemp": null,
  "magnetTemperature": null,
  "magnetRemanence": null,
  "magnetCoerciveForce": null,
  "geometryFigure": "",
  "source": ""
}
```

Populate `MachineBasicInfo` from magnetic-circuit `工况报表结果.csv` when available. Treat this as required report context, not optional decoration. The section should also reference the copied geometry figure derived from project `geo2d.png`. Phase resistance is required when present in the source report; keep the 25 C reference value and working-temperature value distinct.

The report-facing `MachineBasicInfo` table must use one value per structural/basic parameter. When a magnetic-circuit report contains multiple workpoints, keep the original values keyed by workpoint name in structured evidence for audit, but only promote rows with a single structural value to the `电机与仿真模型基本参数` section. Workpoint-varying rows such as speed, load torque, current limit, working temperature, working-temperature resistance, voltage, current, power, efficiency, and losses belong in operating/result data, not in `MachineBasicInfo`.

Use workpoint-keyed values in evidence like this when a row is useful outside the basic-parameter section:

```json
{
  "name": "电枢绕组相电阻",
  "unit": "欧姆",
  "valuesByWorkpoint": {
    "额定点": "0.31282",
    "最大输出转矩": "0.353183"
  }
}
```

For phase resistance, put `电枢绕组相电阻(25度)` in `phaseResistance25C` when available. Put `绕组工作温度` and `电枢绕组相电阻` at working temperature into simulation/operating condition records, or into notes attached to the relevant workpoint.

## MeasuredDatum

```json
{
  "metricName": "",
  "value": null,
  "unit": "",
  "condition": {},
  "sourceFile": "",
  "sourceType": "",
  "extractionMethod": "",
  "confidence": 0.0,
  "note": ""
}
```

## SimulationDatum

```json
{
  "metricName": "",
  "value": null,
  "unit": "",
  "condition": {},
  "sourceFile": "",
  "sourceType": "",
  "simulationKind": "",
  "hashFolder": "",
  "extractionMethod": "",
  "confidence": 0.0,
  "note": ""
}
```

## ComparisonRow

```json
{
  "metricName": "",
  "measuredValue": null,
  "simulationValue": null,
  "unit": "",
  "condition": {},
  "relativeError": null,
  "sourceSummary": "",
  "comment": "",
  "confidence": 0.0
}
```

## ComparisonCandidate

`build_comparison.py` emits candidates before final LLM judgment:

```json
{
  "metricName": "",
  "normalizedMetricName": "",
  "measuredValue": null,
  "simulationValue": null,
  "unit": "",
  "relativeError": null,
  "comparabilityStatus": "comparable | condition_mismatch | unit_mismatch | needs_review",
  "conditionChecks": [],
  "reasons": [],
  "sourceSummary": "",
  "confidence": 0.0
}
```

Only `comparable` candidates should become strict numeric comparison rows automatically. `condition_mismatch` and `needs_review` candidates may still be discussed qualitatively with clear caveats.

## ReportContext

```json
{
  "projectMeta": {},
  "machineBasicInfo": {},
  "measuredData": [],
  "simulationData": [],
  "comparisonCandidates": [],
  "comparisonRows": [],
  "fileIndex": [],
  "hashFolderMapping": {},
  "conclusionHints": []
}
```

## ReportState

Persist this next to the generated report as `report-state.json`.

```json
{
  "schemaVersion": "1.0",
  "reportPath": "",
  "projectRoot": "",
  "projectMeta": {},
  "machineBasicInfo": {},
  "hashFolderMapping": {},
  "measuredData": [],
  "simulationData": [],
  "comparisonRows": [],
  "reportSections": [
    {
      "sectionId": "",
      "title": "",
      "dependsOnEvidenceIds": [],
      "notes": ""
    }
  ],
  "lastUpdatedAt": "",
  "updateHistory": []
}
```

Use `ReportState` as the primary memory for incremental updates. Reuse unchanged `measuredData`, `simulationData`, and `comparisonRows` instead of extracting everything again.

## EvidenceRecord

Persist evidence records in `evidence-ledger.json`.

```json
{
  "evidenceId": "",
  "sourceFile": "",
  "relativePath": "",
  "sourceRole": "measuredData",
  "generatedFile": "",
  "figureKind": "",
  "hashFolder": "",
  "hashFolderMeaning": "",
  "metricNames": [],
  "usedInReportSections": [],
  "fileSize": 0,
  "modifiedTime": "",
  "contentHash": "",
  "extractionMethod": "",
  "confidence": 0.0,
  "notes": ""
}
```

## EvidenceLedger

```json
{
  "schemaVersion": "1.0",
  "projectRoot": "",
  "createdAt": "",
  "updatedAt": "",
  "records": []
}
```

Use the ledger to decide whether a report update can reuse existing evidence or must re-read changed files.

## ChangeLogEntry

Append human-readable entries to `change-log.md`. Each entry should include:

- date/time
- requested change
- affected hash folders
- added/modified/deleted evidence
- affected report sections
- summary of report edits

## Notes

Use `null` for unknown numeric values.

Keep original source file paths in records.

Keep uncertainty visible rather than forcing incomplete data into a clean table.
