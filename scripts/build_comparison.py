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


UNIT_ALIASES = {
    "": "",
    "v": "V",
    "volt": "V",
    "volts": "V",
    "伏": "V",
    "伏特": "V",
    "kv": "kV",
    "mv": "mV",
    "a": "A",
    "amp": "A",
    "amps": "A",
    "安": "A",
    "安培": "A",
    "ma": "mA",
    "rpm": "rpm",
    "r/min": "rpm",
    "转/分": "rpm",
    "转每分": "rpm",
    "hz": "Hz",
    "赫兹": "Hz",
    "w": "W",
    "瓦": "W",
    "kw": "kW",
    "千瓦": "kW",
    "n·m": "N·m",
    "n*m": "N·m",
    "n.m": "N·m",
    "nm": "N·m",
    "牛米": "N·m",
    "%": "%",
    "percent": "%",
    "℃": "C",
    "°c": "C",
    "c": "C",
    "摄氏度": "C",
    "k": "K",
    "欧姆": "ohm",
    "ω": "ohm",
    "ohm": "ohm",
}

UNIT_CONVERSIONS = {
    ("kV", "V"): lambda value: value * 1000,
    ("mV", "V"): lambda value: value / 1000,
    ("V", "kV"): lambda value: value / 1000,
    ("V", "mV"): lambda value: value * 1000,
    ("mA", "A"): lambda value: value / 1000,
    ("A", "mA"): lambda value: value * 1000,
    ("kW", "W"): lambda value: value * 1000,
    ("W", "kW"): lambda value: value / 1000,
    ("K", "C"): lambda value: value - 273.15,
    ("C", "K"): lambda value: value + 273.15,
}

DEFAULT_UNITS = {
    "speed": "rpm",
    "voltage": "V",
    "current": "A",
    "temperature": "C",
    "power": "W",
    "torque": "N·m",
    "efficiency": "%",
}

CONDITION_CHECKS = {
    "speed": {"aliases": ["speed", "转速", "rpm", "n"], "unit": "rpm", "tolerancePercent": 2.0, "toleranceAbs": 5.0},
    "voltage": {"aliases": ["voltage", "电压", "u", "v", "busVoltage", "dcVoltage", "母线电压"], "unit": "V", "tolerancePercent": 3.0, "toleranceAbs": 0.5},
    "current": {"aliases": ["current", "电流", "i", "irms", "idc"], "unit": "A", "tolerancePercent": 5.0, "toleranceAbs": 0.1},
    "temperature": {"aliases": ["temperature", "temp", "温度", "绕组温度", "magnetTemperature"], "unit": "C", "tolerancePercent": 0.0, "toleranceAbs": 5.0},
}

TEXT_CONDITION_CHECKS = {
    "controlMode": ["control", "controlMode", "控制方式", "控制算法", "driveMode", "驱动方式"],
    "voltageBasis": ["voltageBasis", "voltageType", "电压口径", "相线口径", "phaseLineBasis"],
}


def numericValue(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"[-+]?\d+(?:\.\d+)?", str(value).replace(",", ""))
    return float(match.group(0)) if match else None


def normalizeUnit(unit):
    text = str(unit or "").strip()
    key = text.lower().replace(" ", "")
    return UNIT_ALIASES.get(key, text)


def canonicalMetricUnit(metricName, unit):
    normalizedUnit = normalizeUnit(unit)
    if normalizedUnit:
        return normalizedUnit
    return DEFAULT_UNITS.get(metricName, "")


def convertValue(value, fromUnit, toUnit):
    fromUnit = normalizeUnit(fromUnit)
    toUnit = normalizeUnit(toUnit)
    if value is None:
        return None, fromUnit, False
    if not fromUnit or not toUnit or fromUnit == toUnit:
        return value, toUnit or fromUnit, True
    conversion = UNIT_CONVERSIONS.get((fromUnit, toUnit))
    if conversion:
        return conversion(value), toUnit, True
    return value, fromUnit, False


def getNested(record, path):
    current = record
    for part in path:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def firstPresent(record, aliases):
    candidates = [record]
    if isinstance(record.get("condition"), dict):
        candidates.append(record["condition"])
    for candidate in candidates:
        for alias in aliases:
            if alias in candidate and candidate.get(alias) not in (None, ""):
                return candidate.get(alias)
    return None


def firstUnit(record, aliases, defaultUnit):
    candidates = []
    if isinstance(record.get("condition"), dict):
        candidates.append(record["condition"])
    candidates.append(record)
    for candidate in candidates:
        for alias in aliases:
            for key in [f"{alias}Unit", f"{alias}_unit"]:
                if key in candidate and candidate.get(key):
                    return candidate.get(key)
            if alias in candidate and candidate.get(alias) not in (None, "") and candidate is not record and candidate.get("unit"):
                return candidate.get("unit")
    return defaultUnit


def compareNumericCondition(measured, simulation, name, config):
    measuredValue = numericValue(firstPresent(measured, config["aliases"]))
    simulationValue = numericValue(firstPresent(simulation, config["aliases"]))
    if measuredValue is None and simulationValue is None:
        return None
    if measuredValue is None or simulationValue is None:
        return {
            "name": name,
            "status": "needs_review",
            "reason": f"{name} condition missing on one side",
            "measuredValue": measuredValue,
            "simulationValue": simulationValue,
        }
    measuredUnit = firstUnit(measured, config["aliases"], config["unit"])
    simulationUnit = firstUnit(simulation, config["aliases"], config["unit"])
    convertedSimulation, targetUnit, ok = convertValue(simulationValue, simulationUnit, measuredUnit or config["unit"])
    if not ok:
        return {
            "name": name,
            "status": "unit_mismatch",
            "reason": f"{name} condition units are not convertible: {simulationUnit} -> {measuredUnit}",
            "measuredValue": measuredValue,
            "simulationValue": simulationValue,
        }
    difference = abs(convertedSimulation - measuredValue)
    tolerance = max(config["toleranceAbs"], abs(measuredValue) * config["tolerancePercent"] / 100)
    status = "comparable" if difference <= tolerance else "condition_mismatch"
    return {
        "name": name,
        "status": status,
        "measuredValue": measuredValue,
        "simulationValue": round(convertedSimulation, 6),
        "unit": targetUnit,
        "difference": round(difference, 6),
        "tolerance": round(tolerance, 6),
    }


def normalizeText(value):
    text = str(value or "").strip().lower()
    replacements = {
        "foc": "foc",
        "svpwm": "svpwm",
        "方波": "square-wave",
        "六步": "square-wave",
        "线电压": "line",
        "线反电势": "line",
        "line": "line",
        "line-to-line": "line",
        "相电压": "phase",
        "相反电势": "phase",
        "phase": "phase",
    }
    for key, normalized in replacements.items():
        if key in text:
            return normalized
    return text


def compareTextCondition(measured, simulation, name, aliases):
    measuredText = normalizeText(firstPresent(measured, aliases))
    simulationText = normalizeText(firstPresent(simulation, aliases))
    if not measuredText and not simulationText:
        return None
    if not measuredText or not simulationText:
        return {"name": name, "status": "needs_review", "reason": f"{name} missing on one side", "measuredValue": measuredText, "simulationValue": simulationText}
    status = "comparable" if measuredText == simulationText else "condition_mismatch"
    return {"name": name, "status": status, "measuredValue": measuredText, "simulationValue": simulationText}


def conditionChecks(measured, simulation):
    checks = []
    for name, config in CONDITION_CHECKS.items():
        check = compareNumericCondition(measured, simulation, name, config)
        if check:
            checks.append(check)
    for name, aliases in TEXT_CONDITION_CHECKS.items():
        check = compareTextCondition(measured, simulation, name, aliases)
        if check:
            checks.append(check)
    return checks


def candidateStatus(unitOk, checks):
    if not unitOk:
        return "unit_mismatch"
    statuses = {check["status"] for check in checks}
    if "unit_mismatch" in statuses:
        return "unit_mismatch"
    if "condition_mismatch" in statuses:
        return "condition_mismatch"
    if "needs_review" in statuses or not checks:
        return "needs_review"
    return "comparable"


def statusReasons(status, checks, unitOk, fromUnit, toUnit):
    reasons = []
    if not unitOk:
        reasons.append(f"Metric units are not convertible: {fromUnit} -> {toUnit}")
    for check in checks:
        if check["status"] != "comparable":
            reasons.append(check.get("reason") or f"{check['name']} is {check['status']}")
    if status == "needs_review" and not reasons:
        reasons.append("Conditions are incomplete; LLM should verify comparability.")
    return reasons


def sourceSummary(measured, simulation):
    measuredSource = measured.get("sourceFile") or measured.get("source") or ""
    simulationSource = simulation.get("sourceFile") or simulation.get("source") or ""
    return f"Measured: {measuredSource}; Simulation: {simulationSource}"


def buildComparison(data):
    measuredData = data.get("measuredData", [])
    simulationData = data.get("simulationData", [])
    candidatesOut = []
    comparableRows = []

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
            measuredUnit = canonicalMetricUnit(measuredMetric, measured.get("unit"))
            simulationUnit = canonicalMetricUnit(simulationMetric, simulation.get("unit"))
            convertedSimulationValue, outputUnit, unitOk = convertValue(simulationValue, simulationUnit, measuredUnit)
            checks = conditionChecks(measured, simulation)
            status = candidateStatus(unitOk, checks)
            relativeError = None
            if unitOk and measuredValue != 0:
                relativeError = (convertedSimulationValue - measuredValue) / measuredValue * 100
            candidate = {
                "metricName": measured.get("metricName") or simulation.get("metricName"),
                "normalizedMetricName": measuredMetric,
                "measuredValue": measuredValue,
                "simulationValue": round(convertedSimulationValue, 6) if unitOk else simulationValue,
                "rawSimulationValue": simulationValue,
                "unit": outputUnit or measuredUnit or simulationUnit,
                "measuredUnit": measuredUnit,
                "simulationUnit": simulationUnit,
                "relativeError": round(relativeError, 3) if relativeError is not None else None,
                "comparabilityStatus": status,
                "conditionChecks": checks,
                "reasons": statusReasons(status, checks, unitOk, simulationUnit, measuredUnit),
                "condition": {
                    "measured": measured.get("condition") or {},
                    "simulation": simulation.get("condition") or {},
                },
                "sourceSummary": sourceSummary(measured, simulation),
                "confidence": min(float(measured.get("confidence", 0.5)), float(simulation.get("confidence", 0.5)))
            }
            candidates.append(candidate)

        statusRank = {"comparable": 0, "needs_review": 1, "condition_mismatch": 2, "unit_mismatch": 3}
        for candidate in sorted(candidates, key=lambda item: statusRank.get(item["comparabilityStatus"], 9))[:5]:
            candidatesOut.append(candidate)
            if candidate["comparabilityStatus"] == "comparable":
                row = dict(candidate)
                row["comment"] = "Comparable draft row after unit conversion and condition checks; LLM should still verify engineering suitability."
                comparableRows.append(row)

    return {"comparisonCandidates": candidatesOut, "comparisonRows": comparableRows}


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
