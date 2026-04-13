#!/usr/bin/env python
import argparse
import csv
import json
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
    lastError = None
    for encoding in ENCODINGS:
        try:
            text = Path(path).read_text(encoding=encoding)
            return list(csv.reader(text.splitlines())), encoding
        except UnicodeError as error:
            lastError = error
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    return list(csv.reader(text.splitlines())), f"utf-8-replace ({lastError})"


def toFloat(value):
    try:
        text = str(value).strip()
        if text == "":
            return None
        return float(text)
    except ValueError:
        return None


def chooseColumns(rows):
    maxColumns = max((len(row) for row in rows), default=0)
    best = None
    for xCol in range(maxColumns):
        for yCol in range(maxColumns):
            if xCol == yCol:
                continue
            points = []
            for row in rows:
                if len(row) <= max(xCol, yCol):
                    continue
                xValue = toFloat(row[xCol])
                yValue = toFloat(row[yCol])
                if xValue is not None and yValue is not None:
                    points.append((xValue, yValue))
            if len(points) < 10:
                continue
            monotonicScore = sum(1 for i in range(1, len(points)) if points[i][0] >= points[i - 1][0])
            score = len(points) + monotonicScore * 0.2
            if best is None or score > best["score"]:
                best = {"xCol": xCol, "yCol": yCol, "points": points, "score": score}
    return best


def main():
    parser = argparse.ArgumentParser(description="Plot an oscilloscope waveform CSV. This is an example parser for the current Tektronix-like format.")
    parser.add_argument("csvFile", help="Oscilloscope CSV file.")
    parser.add_argument("--output", required=True, help="Output PNG path.")
    parser.add_argument("--title", default="Measured Oscilloscope Waveform", help="Plot title.")
    parser.add_argument("--evidence-output", help="Optional evidence JSON output path.")
    args = parser.parse_args()

    warnings = []
    try:
        plt = requireMatplotlib()
    except ImportError as error:
        result = {"warnings": [f"matplotlib is required for plotting: {error}"], "figures": []}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    rows, encoding = readRows(args.csvFile)
    chosen = chooseColumns(rows)
    if not chosen:
        result = {
            "warnings": ["Could not identify numeric time/value columns. LLM should inspect the CSV and adapt the script."],
            "figures": []
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    xValues = [point[0] for point in chosen["points"]]
    yValues = [point[1] for point in chosen["points"]]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=150)
    ax.plot(xValues, yValues, linewidth=1.2)
    ax.set_title(args.title)
    ax.set_xlabel(f"Column {chosen['xCol'] + 1} (likely time)")
    ax.set_ylabel(f"Column {chosen['yCol'] + 1} (likely voltage)")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)

    record = {
        "evidenceId": f"figure-scope-waveform-{Path(args.csvFile).stem}",
        "sourceFile": str(Path(args.csvFile).resolve()),
        "relativePath": str(Path(args.csvFile).name),
        "sourceRole": "figure",
        "generatedFile": str(output.resolve()),
        "figureKind": "measuredScopeWaveform",
        "metricNames": ["waveform"],
        "extractionMethod": "plot_scope_waveform.py",
        "confidence": 0.65,
        "notes": f"encoding={encoding}; xCol={chosen['xCol'] + 1}; yCol={chosen['yCol'] + 1}; example parser only"
    }
    result = {"warnings": warnings, "figures": [record]}
    outputText = json.dumps(result, ensure_ascii=False, indent=2)
    if args.evidence_output:
        Path(args.evidence_output).write_text(outputText, encoding="utf-8")
    print(outputText)


if __name__ == "__main__":
    main()
