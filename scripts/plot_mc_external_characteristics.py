#!/usr/bin/env python
import argparse
import csv
import json
import re
from pathlib import Path


ENCODINGS = ["utf-8-sig", "utf-8", "gb18030", "cp936", "latin-1"]


def requireMatplotlib():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "Arial Unicode MS", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False
    return plt


def readRows(path):
    for encoding in ENCODINGS:
        try:
            text = Path(path).read_text(encoding=encoding)
            return list(csv.reader(text.splitlines())), encoding
        except UnicodeError:
            continue
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    return list(csv.reader(text.splitlines())), "utf-8-replace"


def toFloat(value):
    try:
        text = str(value).strip()
        if text == "":
            return None
        return float(text)
    except ValueError:
        return None


def makeUnique(headers):
    counts = {}
    unique = []
    for header in headers:
        clean = str(header).strip() or "column"
        counts[clean] = counts.get(clean, 0) + 1
        suffix = f"#{counts[clean]}" if counts[clean] > 1 else ""
        unique.append(f"{clean}{suffix}")
    return unique


def parseTable(path):
    rows, encoding = readRows(path)
    if len(rows) < 3:
        raise ValueError("External characteristics CSV needs at least two header rows and data rows.")
    headers = makeUnique(rows[1])
    dataRows = rows[2:]
    columns = {index: [] for index in range(len(headers))}
    for row in dataRows:
        for index in range(len(headers)):
            value = toFloat(row[index]) if index < len(row) else None
            columns[index].append(value)
    return headers, columns, encoding


def findColumn(headers, aliases, occurrence=0):
    matches = []
    for alias in aliases:
        aliasLower = alias.lower()
        for index, header in enumerate(headers):
            baseHeader = header.split("#", 1)[0]
            lower = baseHeader.lower()
            if aliasLower == lower or aliasLower in lower:
                matches.append(index)
        if matches:
            break
    if not matches:
        return None
    return matches[min(occurrence, len(matches) - 1)]


def series(headers, columns, index):
    values = columns.get(index, [])
    return [value for value in values]


def pairedPoints(xValues, yValues):
    return [(x, y) for x, y in zip(xValues, yValues) if x is not None and y is not None]


def safeStem(path):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", Path(path).stem).strip("_") or "external"


def addMultiAxis(host, xValues, yValues, label, color, axisIndex, plt):
    if axisIndex == 0:
        axis = host
    else:
        axis = host.twinx()
        axis.spines["right"].set_position(("axes", 1 + 0.12 * (axisIndex - 1)))
        axis.spines["right"].set_visible(True)
    axis.plot(xValues, yValues, color=color, linewidth=1.3, label=label)
    axis.set_ylabel(label, color=color)
    axis.tick_params(axis="y", colors=color)
    return axis


def main():
    parser = argparse.ArgumentParser(description="Plot PMSM magnetic-circuit external characteristics with true multiple y-axes.")
    parser.add_argument("csvFile", help="External characteristics CSV, such as 外特性仿真结果.csv.")
    parser.add_argument("--output", required=True, help="Output PNG path.")
    parser.add_argument("--x-axis", choices=["torque", "speed"], default="speed", help="Default x-axis is speed.")
    parser.add_argument("--evidence-output", help="Optional evidence JSON output path.")
    args = parser.parse_args()

    try:
        plt = requireMatplotlib()
    except ImportError as error:
        result = {"warnings": [f"matplotlib is required for plotting: {error}"], "figures": []}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    headers, columns, encoding = parseTable(args.csvFile)
    xAliases = ["输出转矩"] if args.x_axis == "torque" else ["转速"]
    xIndex = findColumn(headers, xAliases)
    if xIndex is None:
        raise ValueError(f"Could not find x-axis column for {args.x_axis}.")

    metricSpecs = []
    if args.x_axis == "torque":
        metricSpecs.append(("转速", ["转速"]))
    else:
        metricSpecs.append(("输出转矩", ["输出转矩", "转矩"]))
    metricSpecs.extend([
        ("输出功率", ["输出功率"]),
        ("输入功率", ["输入功率"]),
        ("效率", ["效率"]),
        ("功率因数", ["功率因数"])
    ])

    xValues = series(headers, columns, xIndex)
    colors = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#17becf"]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    fig, host = plt.subplots(figsize=(9, 5.2), dpi=150)
    axes = []
    plotted = []
    warnings = []
    for axisIndex, (label, aliases) in enumerate(metricSpecs):
        yIndex = findColumn(headers, aliases)
        if yIndex is None or yIndex == xIndex:
            warnings.append(f"Column not found or same as x-axis: {label}")
            continue
        points = pairedPoints(xValues, series(headers, columns, yIndex))
        if len(points) < 2:
            warnings.append(f"Not enough points for {label}")
            continue
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        axis = addMultiAxis(host, xs, ys, label, colors[len(plotted) % len(colors)], len(plotted), plt)
        axes.append(axis)
        plotted.append(label)

    host.set_xlabel(headers[xIndex])
    host.set_title("Magnetic-Circuit External Characteristics")
    host.grid(True, alpha=0.3)
    lines = []
    labels = []
    for axis in axes:
        axisLines, axisLabels = axis.get_legend_handles_labels()
        lines.extend(axisLines)
        labels.extend(axisLabels)
    if lines:
        host.legend(lines, labels, loc="best", fontsize=8)
    fig.subplots_adjust(right=0.62)
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)

    record = {
        "evidenceId": f"figure-mc-external-{safeStem(args.csvFile)}",
        "sourceFile": str(Path(args.csvFile).resolve()),
        "relativePath": str(Path(args.csvFile).name),
        "sourceRole": "figure",
        "generatedFile": str(output.resolve()),
        "figureKind": "mcExternalCharacteristics",
        "metricNames": plotted,
        "extractionMethod": "plot_mc_external_characteristics.py",
        "confidence": 0.75,
        "notes": f"encoding={encoding}; x={headers[xIndex]}; true multi-axis"
    }
    result = {"warnings": warnings, "figures": [record]}
    outputText = json.dumps(result, ensure_ascii=False, indent=2)
    if args.evidence_output:
        Path(args.evidence_output).write_text(outputText, encoding="utf-8")
    print(outputText)


if __name__ == "__main__":
    main()
