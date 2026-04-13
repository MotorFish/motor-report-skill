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
  "source": ""
}
```

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

## ReportContext

```json
{
  "projectMeta": {},
  "machineBasicInfo": {},
  "measuredData": [],
  "simulationData": [],
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
