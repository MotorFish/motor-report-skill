#!/usr/bin/env python
import argparse
import json
import re
from pathlib import Path


METRIC_SYNONYMS = {
    "backEmf": ["backemf", "backef", "反电势", "空载电势", "e0", "bemf"],
    "torque": ["torque", "转矩", "扭矩"],
    "current": ["current", "电流", "irms", "i_rms"],
    "voltage": ["voltage", "电压", "端电压", "u", "v_"],
    "speed": ["speed", "转速", "rpm"],
    "efficiency": ["efficiency", "效率", "eta"],
    "power": ["power", "功率", "输出功率", "pout"],
    "coreLoss": ["coreloss", "pfe", "铁耗"],
    "copperLoss": ["copperloss", "pcu", "铜耗"],
    "flux": ["flux", "磁链", "磁通"]
}

UNIT_SYNONYMS = {
    "v": "V",
    "volt": "V",
    "伏": "V",
    "a": "A",
    "amp": "A",
    "安": "A",
    "nm": "N·m",
    "n.m": "N·m",
    "n*m": "N·m",
    "rpm": "rpm",
    "r/min": "rpm",
    "w": "W",
    "kw": "kW",
    "%": "%",
    "percent": "%"
}


def normalizeMetricName(metricName):
    text = str(metricName or "").lower().replace(" ", "")
    for normalizedName, aliases in METRIC_SYNONYMS.items():
        if any(alias.lower() in text for alias in aliases):
            return normalizedName
    return str(metricName or "").strip()


def normalizeUnit(unit):
    text = str(unit or "").strip()
    key = text.lower().replace(" ", "")
    return UNIT_SYNONYMS.get(key, text)


def parseNumericValue(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"[-+]?\d+(?:\.\d+)?", str(value).replace(",", ""))
    if not match:
        return None
    return float(match.group(0))


def normalizeRecord(record):
    updated = dict(record)
    metricName = updated.get("metricName") or updated.get("name") or updated.get("metric")
    updated["normalizedMetricName"] = normalizeMetricName(metricName)
    updated["numericValue"] = parseNumericValue(updated.get("value"))
    updated["normalizedUnit"] = normalizeUnit(updated.get("unit"))
    return updated


def normalizeData(data):
    if isinstance(data, list):
        return [normalizeRecord(item) if isinstance(item, dict) else item for item in data]
    if isinstance(data, dict):
        updated = dict(data)
        for key in ["records", "measuredData", "simulationData", "comparisonRows"]:
            if isinstance(updated.get(key), list):
                updated[key] = normalizeData(updated[key])
        if "metricName" in updated or "value" in updated:
            updated = normalizeRecord(updated)
        return updated
    return data


def main():
    parser = argparse.ArgumentParser(description="Normalize motor metric names, units, and numeric values in JSON data.")
    parser.add_argument("inputJson", help="Input JSON file.")
    parser.add_argument("--output", help="Optional JSON output path.")
    args = parser.parse_args()

    data = json.loads(Path(args.inputJson).read_text(encoding="utf-8-sig"))
    result = normalizeData(data)
    outputText = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(outputText, encoding="utf-8")
    else:
        print(outputText)


if __name__ == "__main__":
    main()
