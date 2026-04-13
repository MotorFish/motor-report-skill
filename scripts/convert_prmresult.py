#!/usr/bin/env python
import argparse
import csv
import json
from pathlib import Path


def readJson(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def outputName(outVar):
    return outVar.get("expr") or outVar.get("desc") or outVar.get("name") or "outvar"


def convert(data):
    inputVars = data.get("inputvars", []) or []
    outVars = data.get("outvars", []) or []
    caseResults = data.get("caseresults", []) or []

    headers = [item.get("varname", f"input{index + 1}") for index, item in enumerate(inputVars)]
    headers.extend([outputName(item) for item in outVars])

    rows = []
    for caseIndex, case in enumerate(caseResults):
        row = {}
        values = case.get("values", []) or []
        for inputIndex, inputVar in enumerate(inputVars):
            name = inputVar.get("varname", f"input{inputIndex + 1}")
            values = inputVar.get("values", []) or []
            row[name] = values[caseIndex] if caseIndex < len(values) else None

        caseValues = case.get("values", []) or []
        outputOffset = len(inputVars) if len(caseValues) == len(outVars) + len(inputVars) else 0
        for outIndex, outVar in enumerate(outVars):
            name = outputName(outVar)
            valueIndex = outIndex + outputOffset
            row[name] = caseValues[valueIndex] if valueIndex < len(caseValues) else None

        row["caseidx"] = case.get("caseidx", caseIndex + 1)
        row["filtered"] = case.get("filtered", None)
        rows.append(row)

    return headers + ["caseidx", "filtered"], rows


def main():
    parser = argparse.ArgumentParser(description="Convert EM parametric prmresult.json to CSV.")
    parser.add_argument("jsonFile", help="prmresult.json path.")
    parser.add_argument("--output", required=True, help="Output CSV path.")
    parser.add_argument("--metadata-output", help="Optional JSON metadata output path.")
    args = parser.parse_args()

    data = readJson(args.jsonFile)
    headers, rows = convert(data)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    metadata = {
        "sourceFile": str(Path(args.jsonFile).resolve()),
        "generatedFile": str(output.resolve()),
        "rowCount": len(rows),
        "inputVariables": [item.get("varname", "") for item in data.get("inputvars", []) or []],
        "outputVariables": [outputName(item) for item in data.get("outvars", []) or []],
        "class": data.get("class", "")
    }
    if args.metadata_output:
        Path(args.metadata_output).write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
