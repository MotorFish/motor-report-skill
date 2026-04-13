#!/usr/bin/env python
import argparse
import csv
import json
import re
from pathlib import Path


ENCODINGS = ["utf-8-sig", "utf-8", "gb18030", "cp936", "latin-1"]
X_HINTS = ["time", "order", "length", "angle", "position", "speed", "时间", "阶次", "长度", "角度", "位置", "转速", "电角度"]


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


def numericCount(row):
    return sum(1 for item in row if toFloat(item) is not None)


def findTable(rows):
    for index, row in enumerate(rows[:-1]):
        nextRow = rows[index + 1]
        if len(row) >= 2 and numericCount(nextRow) >= 2 and numericCount(row) < len(row):
            return row, rows[index + 1:]
    if rows:
        return rows[0], rows[1:]
    return [], []


def cleanHeader(header):
    cleaned = []
    for index, value in enumerate(header):
        text = str(value).strip() or f"col{index + 1}"
        cleaned.append(text)
    return cleaned


def chooseXColumn(headers):
    lowerHeaders = [header.lower() for header in headers]
    for hint in X_HINTS:
        for index, header in enumerate(lowerHeaders):
            if hint.lower() in header:
                return index
    return 0


def tableToColumns(headers, dataRows):
    columns = {index: [] for index in range(len(headers))}
    for row in dataRows:
        for index in range(len(headers)):
            value = toFloat(row[index]) if index < len(row) else None
            columns[index].append(value)
    return columns


def validSeries(xValues, yValues):
    points = [(x, y) for x, y in zip(xValues, yValues) if x is not None and y is not None]
    return points if len(points) >= 2 else []


def figureKind(filePath, headers):
    text = (Path(filePath).name + " " + " ".join(headers)).lower()
    if "fft" in text or "order" in text or "阶次" in text:
        return "feaSpectrum"
    if "backef" in text or "back-emf" in text or "反电势" in text:
        return "feaBackEmf"
    if "airgap" in text or "bn" in text or "气隙" in text:
        return "feaAirgapFlux"
    if "torque" in text or "转矩" in text:
        return "feaTorque"
    if "current" in text or "电流" in text:
        return "feaCurrent"
    if "voltage" in text or "电压" in text:
        return "feaVoltage"
    return "feaCurve"


def safeStem(path):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", Path(path).stem).strip("_") or "curve"


def plotFile(filePath, outputDir, titlePrefix):
    rows, encoding = readRows(filePath)
    header, dataRows = findTable(rows)
    headers = cleanHeader(header)
    xIndex = chooseXColumn(headers)
    columns = tableToColumns(headers, dataRows)
    xValues = columns.get(xIndex, [])
    yIndices = [index for index in range(len(headers)) if index != xIndex and any(value is not None for value in columns.get(index, []))]

    if not yIndices:
        return None, [f"No plottable y columns found in {filePath}."]

    plt = requireMatplotlib()
    outputPath = Path(outputDir) / f"fea-{safeStem(filePath)}.png"
    outputPath.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=150)
    plotted = []
    for yIndex in yIndices:
        points = validSeries(xValues, columns.get(yIndex, []))
        if not points:
            continue
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        label = headers[yIndex]
        if "fft" in Path(filePath).name.lower() or "order" in headers[xIndex].lower():
            ax.bar(xs, ys, label=label, alpha=0.75, width=0.6)
        else:
            ax.plot(xs, ys, label=label, linewidth=1.2)
        plotted.append(label)

    if not plotted:
        plt.close(fig)
        return None, [f"No valid numeric points found in {filePath}."]

    title = f"{titlePrefix} {Path(filePath).name}".strip()
    ax.set_title(title)
    ax.set_xlabel(headers[xIndex])
    ax.set_ylabel("Value")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(outputPath)
    plt.close(fig)

    record = {
        "evidenceId": f"figure-fea-{safeStem(filePath)}",
        "sourceFile": str(Path(filePath).resolve()),
        "relativePath": str(Path(filePath).name),
        "sourceRole": "figure",
        "generatedFile": str(outputPath.resolve()),
        "figureKind": figureKind(filePath, headers),
        "metricNames": plotted,
        "extractionMethod": "plot_fea_curves.py",
        "confidence": 0.75,
        "notes": f"encoding={encoding}; x={headers[xIndex]}; LLM selected source curve"
    }
    return record, []


def main():
    parser = argparse.ArgumentParser(description="Plot LLM-selected FEA CSV/ECSV result curves.")
    parser.add_argument("curveFiles", nargs="+", help="CSV/ECSV curve files selected by the LLM.")
    parser.add_argument("--output-dir", required=True, help="Output figures directory.")
    parser.add_argument("--title-prefix", default="", help="Optional title prefix.")
    parser.add_argument("--evidence-output", help="Optional evidence JSON output path.")
    args = parser.parse_args()

    warnings = []
    figures = []
    try:
        requireMatplotlib()
    except ImportError as error:
        result = {"warnings": [f"matplotlib is required for plotting: {error}"], "figures": []}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    for filePath in args.curveFiles:
        record, fileWarnings = plotFile(filePath, args.output_dir, args.title_prefix)
        warnings.extend(fileWarnings)
        if record:
            figures.append(record)

    result = {"warnings": warnings, "figures": figures}
    outputText = json.dumps(result, ensure_ascii=False, indent=2)
    if args.evidence_output:
        Path(args.evidence_output).write_text(outputText, encoding="utf-8")
    print(outputText)


if __name__ == "__main__":
    main()
