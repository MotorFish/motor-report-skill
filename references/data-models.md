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

## Notes

Use `null` for unknown numeric values.

Keep original source file paths in records.

Keep uncertainty visible rather than forcing incomplete data into a clean table.
