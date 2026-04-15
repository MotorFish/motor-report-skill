#!/usr/bin/env python
import argparse
import csv
import json
import statistics
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


def numericValues(row):
    return [toFloat(item) for item in row if toFloat(item) is not None]


def readPolePairs(reportPath):
    if not reportPath:
        return None, [], None
    rows, encoding = readRows(reportPath)
    warnings = []
    for row in rows:
        labelText = " ".join(str(item).strip() for item in row if str(item).strip())
        values = numericValues(row)
        if not values:
            continue
        if "极对数" in labelText:
            polePairs = values[0]
            return polePairs, warnings, f"{Path(reportPath).name}: 极对数={polePairs} (encoding={encoding})"
        if "极数" in labelText:
            poleCount = values[0]
            polePairs = poleCount / 2
            uniqueValues = {round(value, 8) for value in values}
            if len(uniqueValues) > 1:
                warnings.append(f"Pole count row has multiple numeric values; using the first value {poleCount}.")
            return polePairs, warnings, f"{Path(reportPath).name}: 极数={poleCount}, 极对数={polePairs} (encoding={encoding})"
    warnings.append(f"Could not find 极数 or 极对数 in {reportPath}.")
    return None, warnings, None


def resolvePolePairs(args):
    if args.pole_pairs is not None:
        return args.pole_pairs, [], "command line --pole-pairs"
    if args.pole_count is not None:
        return args.pole_count / 2, [], "command line --pole-count"
    return readPolePairs(args.motor_report_csv)


def groupPeakTimes(points):
    if len(points) < 3:
        return []
    yValues = [point[1] for point in points]
    yMin = min(yValues)
    yMax = max(yValues)
    yRange = yMax - yMin
    if yRange <= 0:
        return []
    threshold = yMin + yRange * 0.75
    groups = []
    current = []
    for xValue, yValue in points:
        if yValue >= threshold:
            current.append((xValue, yValue))
        elif current:
            groups.append(current)
            current = []
    if current:
        groups.append(current)
    peakTimes = []
    for group in groups:
        peakTime, _ = max(group, key=lambda item: item[1])
        peakTimes.append(peakTime)
    return peakTimes


def localPeakTimes(points):
    if len(points) < 3:
        return []
    yValues = [point[1] for point in points]
    yMin = min(yValues)
    yMax = max(yValues)
    threshold = yMin + (yMax - yMin) * 0.55
    peaks = []
    for index in range(1, len(points) - 1):
        left = points[index - 1][1]
        value = points[index][1]
        right = points[index + 1][1]
        if value >= threshold and value >= left and value > right:
            peaks.append(points[index])
    if not peaks:
        return []
    duration = points[-1][0] - points[0][0]
    minSeparation = duration / 20 if duration > 0 else 0
    filtered = []
    for xValue, yValue in peaks:
        if not filtered or xValue - filtered[-1][0] >= minSeparation:
            filtered.append((xValue, yValue))
        elif yValue > filtered[-1][1]:
            filtered[-1] = (xValue, yValue)
    return [point[0] for point in filtered]


def estimateSpeedFromPeaks(points, polePairs):
    if polePairs is None or polePairs <= 0:
        return None, "pole pairs unavailable"
    sortedPoints = sorted(points, key=lambda item: item[0])
    peakTimes = groupPeakTimes(sortedPoints)
    method = "threshold peak grouping"
    if len(peakTimes) < 2:
        peakTimes = localPeakTimes(sortedPoints)
        method = "local peak fallback"
    periods = [peakTimes[index] - peakTimes[index - 1] for index in range(1, len(peakTimes)) if peakTimes[index] > peakTimes[index - 1]]
    if not periods:
        return None, "not enough adjacent positive peaks"
    period = statistics.median(periods)
    if period <= 0:
        return None, "invalid peak period"
    electricalFrequency = 1 / period
    mechanicalRpm = electricalFrequency / polePairs * 60
    variation = 0.0
    if len(periods) > 1:
        meanPeriod = statistics.mean(periods)
        variation = statistics.pstdev(periods) / meanPeriod if meanPeriod else 0.0
    confidence = 0.65
    if len(peakTimes) >= 3 and variation <= 0.05:
        confidence = 0.8
    elif len(peakTimes) == 2:
        confidence = 0.55
    return {
        "mechanicalSpeedRpm": mechanicalRpm,
        "electricalFrequencyHz": electricalFrequency,
        "electricalPeriodSec": period,
        "polePairs": polePairs,
        "peakTimesSec": peakTimes,
        "periodsSec": periods,
        "method": method,
        "confidence": confidence,
        "periodVariation": variation,
        "assumption": "Adjacent positive maxima in the measured line-voltage waveform represent one electrical period."
    }, None


def main():
    parser = argparse.ArgumentParser(description="Plot an oscilloscope waveform CSV. This is an example parser for the current Tektronix-like format.")
    parser.add_argument("csvFile", help="Oscilloscope CSV file.")
    parser.add_argument("--output", required=True, help="Output PNG path.")
    parser.add_argument("--title", default="Measured Oscilloscope Waveform", help="Plot title.")
    parser.add_argument("--evidence-output", help="Optional evidence JSON output path.")
    parser.add_argument("--motor-report-csv", help="Magnetic-circuit report CSV used to read pole count or pole pairs.")
    parser.add_argument("--pole-pairs", type=float, help="Override motor pole pairs for speed estimation.")
    parser.add_argument("--pole-count", type=float, help="Override motor pole count; pole pairs are pole count / 2.")
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
    polePairs, poleWarnings, poleSource = resolvePolePairs(args)
    warnings.extend(poleWarnings)
    speedEstimate, speedWarning = estimateSpeedFromPeaks(chosen["points"], polePairs)
    if speedWarning:
        warnings.append(f"Speed estimation skipped: {speedWarning}.")
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
    if poleSource:
        record["polePairsSource"] = poleSource
    if speedEstimate:
        record["speedEstimate"] = speedEstimate
        record["metricNames"].extend(["estimatedElectricalFrequency", "estimatedMechanicalSpeed"])
        record["notes"] += f"; estimated speed={speedEstimate['mechanicalSpeedRpm']:.3f} rpm from line-voltage peak period and pole pairs"
    result = {"warnings": warnings, "figures": [record]}
    outputText = json.dumps(result, ensure_ascii=False, indent=2)
    if args.evidence_output:
        Path(args.evidence_output).write_text(outputText, encoding="utf-8")
    print(outputText)


if __name__ == "__main__":
    main()
