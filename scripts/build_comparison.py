#!/usr/bin/env python
import argparse
import json
import re
from pathlib import Path


def normalizeMetricName(metricName):
    text = str(metricName or "").lower().replace(" ", "")
    groups = {
        "backEmf": ["backemf", "backef", "反电势", "空载电势", "e0", "bemf"],
        "torque": ["torque", "转矩", "扭矩"],
        "current": ["current", "电流", "irms"],
        "voltage": ["voltage", "电压"],
        "speed": ["speed", "转速", "rpm"],
        "efficiency": ["efficiency", "效率", "eta"],
        "power": ["power", "功率"],
        "coreLoss": ["coreloss", "pfe", "铁耗"],
        "copperLoss": ["copperloss", "pcu", "铜耗"]
    }
    for normalizedName, aliases in groups.items():
        if any(alias.lower() in text for alias in aliases):
            return normalizedName
    return str(metricName or "").strip()


def numericValue(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"[-+]?\d+(?:\.\d+)?", str(value).replace(",", ""))
    return float(match.group(0)) if match else None


def sourceSummary(measured, simulation):
    measuredSource = measured.get("sourceFile") or measured.get("source") or ""
    simulationSource = simulation.get("sourceFile") or simulation.get("source") or ""
    return f"Measured: {measuredSource}; Simulation: {simulationSource}"


def buildComparison(data):
    measuredData = data.get("measuredData", [])
    simulationData = data.get("simulationData", [])
    rows = []

    for measured in measuredData:
        measuredMetric = normalizeMetricName(measured.get("metricName"))
        measuredValue = numericValue(measured.get("value"))
        if measuredValue is None:
            continue

        candidates = []
        for simulation in simulationData:
            simulationMetric = normalizeMetricName(simulation.get("metricName"))
            if simulationMetric != measuredMetric:
                continue
            simulationValue = numericValue(simulation.get("value"))
            if simulationValue is None:
                continue
            candidates.append((simulation, simulationValue))

        for simulation, simulationValue in candidates[:3]:
            relativeError = None
            if measuredValue != 0:
                relativeError = (simulationValue - measuredValue) / measuredValue * 100
            unit = measured.get("unit") or simulation.get("unit") or ""
            rows.append({
                "metricName": measured.get("metricName") or simulation.get("metricName"),
                "measuredValue": measuredValue,
                "simulationValue": simulationValue,
                "unit": unit,
                "condition": measured.get("condition") or simulation.get("condition") or {},
                "relativeError": round(relativeError, 3) if relativeError is not None else None,
                "sourceSummary": sourceSummary(measured, simulation),
                "comment": "Draft comparison row; LLM must verify condition match and report suitability.",
                "confidence": min(float(measured.get("confidence", 0.5)), float(simulation.get("confidence", 0.5)))
            })

    return {"comparisonRows": rows}


def main():
    parser = argparse.ArgumentParser(description="Build draft measured/simulation comparison rows from JSON data.")
    parser.add_argument("inputJson", help="Input JSON with measuredData and simulationData arrays.")
    parser.add_argument("--output", help="Optional JSON output path.")
    args = parser.parse_args()

    data = json.loads(Path(args.inputJson).read_text(encoding="utf-8-sig"))
    result = buildComparison(data)
    outputText = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(outputText, encoding="utf-8")
    else:
        print(outputText)


if __name__ == "__main__":
    main()
