#!/usr/bin/env python
import argparse
import csv
import json
import re
import statistics
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
            return row, rows[index + 1:], index
    if rows:
        return rows[0], rows[1:], 0
    return [], [], 0


def metadataSeriesNames(rows, headerIndex, yCount):
    for row in reversed(rows[max(0, headerIndex - 5):headerIndex]):
        values = [str(value).strip() for value in row if str(value).strip()]
        lowerValues = [value.lower() for value in values]
        if lowerValues and all(value in {"true", "false"} for value in lowerValues):
            continue
        if len(values) == yCount and numericCount(values) == 0:
            return values
    return []


def cleanHeader(header, yHints=None):
    cleaned = []
    seen = {}
    yOffset = 0
    for index, value in enumerate(header):
        text = str(value).strip() or f"col{index + 1}"
        if index > 0 and yHints and yOffset < len(yHints):
            hint = yHints[yOffset]
            if hint and hint not in text:
                text = f"{hint} {text}"
            yOffset += 1
        count = seen.get(text, 0)
        seen[text] = count + 1
        if count:
            text = f"{text}_{count + 1}"
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


def rms(values):
    numericValues = [value for value in values if value is not None]
    if not numericValues:
        return None
    return (sum(value * value for value in numericValues) / len(numericValues)) ** 0.5


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


def analyzePeriodFromPeaks(points, polePairs=None):
    sortedPoints = sorted(points, key=lambda item: item[0])
    if len(sortedPoints) < 3:
        return None, "not enough points"
    duration = sortedPoints[-1][0] - sortedPoints[0][0]
    if duration <= 0:
        return None, "x-axis duration is not positive"
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
    variation = 0.0
    if len(periods) > 1:
        meanPeriod = statistics.mean(periods)
        variation = statistics.pstdev(periods) / meanPeriod if meanPeriod else 0.0
    analysis = {
        "electricalPeriodSec": period,
        "electricalFrequencyHz": electricalFrequency,
        "peakTimesSec": peakTimes,
        "periodsSec": periods,
        "periodVariation": variation,
        "cyclesCovered": duration / period,
        "method": method,
        "rmsWindowSec": [peakTimes[0], peakTimes[1]] if len(peakTimes) >= 2 else None,
        "confidence": 0.65,
        "assumption": "Adjacent positive maxima in the FEA time-domain waveform represent one electrical period.",
    }
    if len(peakTimes) >= 3 and variation <= 0.05:
        analysis["confidence"] = 0.82
    elif len(peakTimes) == 2:
        analysis["confidence"] = 0.58
    if polePairs is not None and polePairs > 0:
        analysis["polePairs"] = polePairs
        analysis["mechanicalSpeedRpm"] = electricalFrequency / polePairs * 60
    return analysis, None


def rmsInWindow(points, window):
    if not window:
        return None
    start, end = window
    values = [y for x, y in points if start <= x <= end]
    return rms(values)


def seriesDerivedMetrics(label, xValues, yValues, polePairs=None):
    points = validSeries(xValues, yValues)
    if not points:
        return {}, "no valid points for period/RMS metrics"
    fullRms = rms([y for _, y in points])
    analysis, warning = analyzePeriodFromPeaks(points, polePairs=polePairs)
    periodRms = rmsInWindow(points, analysis.get("rmsWindowSec")) if analysis else None
    preferredRms = periodRms if periodRms is not None else fullRms
    metrics = {
        f"{label} RMS": preferredRms,
        f"{label} fullSequenceRMS": fullRms,
        label: {
            "rms": preferredRms,
            "rmsFullSequence": fullRms,
            "rmsPeriodWindow": periodRms,
            "periodAnalysis": analysis,
            "rmsBasis": "adjacent-positive-peak period window" if periodRms is not None else "full sequence fallback",
        },
    }
    return metrics, warning


def isSpectrum(filePath, xHeader, headers):
    text = (Path(filePath).name + " " + xHeader + " " + " ".join(headers)).lower()
    return "fft" in text or "order" in text or "阶次" in text


def isBackEmfOrVoltage(filePath, headers):
    text = (Path(filePath).name + " " + " ".join(headers)).lower()
    return any(token in text for token in ["backef", "back-emf", "反电动势", "反电势", "voltage", "电压", "emf"])


def hasLineVoltageMarker(filePath, headers):
    text = (Path(filePath).name + " " + " ".join(headers)).lower()
    if "线电压" in text or "线反电动势" in text or "线反电势" in text:
        return True
    if re.search(r"(^|[^a-z])line([-_ ]?to[-_ ]?line|[-_ ]?(voltage|emf|bemf))", text):
        return True
    if re.search(r"(^|[^a-z])ll[-_ ]?(voltage|emf|bemf)", text):
        return True
    return "_line" in text or "-line" in text or "_ll" in text or "-ll" in text


def shouldConvertToLineVoltage(filePath, headers, xIndex, yIndices, lineVoltageMode):
    if lineVoltageMode == "off":
        return False
    if len(yIndices) < 3:
        return False
    if isSpectrum(filePath, headers[xIndex], headers):
        return False
    if not isBackEmfOrVoltage(filePath, headers):
        return False
    if lineVoltageMode == "force":
        return True
    return not hasLineVoltageMarker(filePath, headers)


def lineVoltageSeries(headers, columns, yIndices, xValues=None, polePairs=None):
    firstThree = yIndices[:3]
    values = [columns.get(index, []) for index in firstThree]
    if len(values) < 3:
        return [], {}, []
    labels = [
        f"线电压/线反电势 AB ({headers[firstThree[0]]} - {headers[firstThree[1]]})",
        f"线电压/线反电势 BC ({headers[firstThree[1]]} - {headers[firstThree[2]]})",
        f"线电压/线反电势 CA ({headers[firstThree[2]]} - {headers[firstThree[0]]})",
    ]
    pairs = [(0, 1), (1, 2), (2, 0)]
    series = []
    derivedMetrics = {}
    warnings = []
    for label, (leftIndex, rightIndex) in zip(labels, pairs):
        yValues = []
        for left, right in zip(values[leftIndex], values[rightIndex]):
            yValues.append(None if left is None or right is None else left - right)
        series.append((label, yValues))
        if xValues is not None:
            metrics, warning = seriesDerivedMetrics(label, xValues, yValues, polePairs=polePairs)
            derivedMetrics.update({key: value for key, value in metrics.items() if value is not None})
            if warning:
                warnings.append(f"{label}: {warning}")
        else:
            valueRms = rms(yValues)
            if valueRms is not None:
                derivedMetrics[f"{label} RMS"] = valueRms
    return series, derivedMetrics, warnings


def figureKind(filePath, headers):
    text = (Path(filePath).name + " " + " ".join(headers)).lower()
    if "fft" in text or "order" in text or "阶次" in text:
        return "feaSpectrum"
    if "backef" in text or "back-emf" in text or "反电动势" in text or "反电势" in text:
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


def plotFile(filePath, outputDir, titlePrefix, lineVoltageMode, polePairs=None, poleSource=None):
    rows, encoding = readRows(filePath)
    header, dataRows, headerIndex = findTable(rows)
    yHints = metadataSeriesNames(rows, headerIndex, max(0, len(header) - 1))
    headers = cleanHeader(header, yHints)
    xIndex = chooseXColumn(headers)
    columns = tableToColumns(headers, dataRows)
    xValues = columns.get(xIndex, [])
    yIndices = [index for index in range(len(headers)) if index != xIndex and any(value is not None for value in columns.get(index, []))]

    if not yIndices:
        return None, [f"No plottable y columns found in {filePath}."]

    plt = requireMatplotlib()
    convertedToLineVoltage = shouldConvertToLineVoltage(filePath, headers, xIndex, yIndices, lineVoltageMode)
    suffix = "-line" if convertedToLineVoltage else ""
    outputPath = Path(outputDir) / f"fea-{safeStem(filePath)}{suffix}.png"
    outputPath.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=150)
    plotted = []
    derivedMetrics = {}
    warnings = []
    if convertedToLineVoltage:
        plotSeries, derivedMetrics, metricWarnings = lineVoltageSeries(headers, columns, yIndices, xValues=xValues, polePairs=polePairs)
        warnings.extend(metricWarnings)
    else:
        plotSeries = [(headers[yIndex], columns.get(yIndex, [])) for yIndex in yIndices]
        if isBackEmfOrVoltage(filePath, headers) and not isSpectrum(filePath, headers[xIndex], headers):
            for label, yValues in plotSeries:
                metrics, warning = seriesDerivedMetrics(label, xValues, yValues, polePairs=polePairs)
                derivedMetrics.update({key: value for key, value in metrics.items() if value is not None})
                if warning:
                    warnings.append(f"{label}: {warning}")

    for label, yValues in plotSeries:
        points = validSeries(xValues, yValues)
        if not points:
            continue
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        if "fft" in Path(filePath).name.lower() or "order" in headers[xIndex].lower() or "阶次" in headers[xIndex].lower():
            ax.bar(xs, ys, label=label, alpha=0.75, width=0.6)
        else:
            ax.plot(xs, ys, label=label, linewidth=1.2)
        plotted.append(label)

    if not plotted:
        plt.close(fig)
        return None, [f"No valid numeric points found in {filePath}."] + warnings

    conversionTitle = "线电压/线反电势 " if convertedToLineVoltage else ""
    title = f"{titlePrefix} {conversionTitle}{Path(filePath).name}".strip()
    ax.set_title(title)
    ax.set_xlabel(headers[xIndex])
    ax.set_ylabel("Line value" if convertedToLineVoltage else "Value")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(outputPath)
    plt.close(fig)

    record = {
        "evidenceId": f"figure-fea-{safeStem(filePath)}{suffix}",
        "sourceFile": str(Path(filePath).resolve()),
        "relativePath": str(Path(filePath).name),
        "sourceRole": "figure",
        "generatedFile": str(outputPath.resolve()),
        "figureKind": figureKind(filePath, headers),
        "metricNames": plotted,
        "extractionMethod": "plot_fea_curves.py",
        "confidence": 0.75,
        "notes": f"encoding={encoding}; x={headers[xIndex]}; LLM selected source curve",
    }
    if convertedToLineVoltage:
        record["figureKind"] = "feaLineVoltage" if record["figureKind"] == "feaVoltage" else "feaLineBackEmf"
        record["transformation"] = "phase_to_line_voltage"
        record["sourceMetricNames"] = [headers[index] for index in yIndices[:3]]
        record["derivedMetrics"] = derivedMetrics
        record["notes"] += "; converted first three phase back-EMF/voltage series to AB/BC/CA line values for measured line-voltage comparison"
    elif derivedMetrics:
        record["derivedMetrics"] = derivedMetrics
    if poleSource:
        record["polePairsSource"] = poleSource
    if derivedMetrics:
        record["notes"] += "; RMS/period metrics prefer adjacent positive peak period windows for time-domain waveforms"
    return record, warnings


def main():
    parser = argparse.ArgumentParser(description="Plot LLM-selected FEA CSV/ECSV result curves.")
    parser.add_argument("curveFiles", nargs="+", help="CSV/ECSV curve files selected by the LLM.")
    parser.add_argument("--output-dir", required=True, help="Output figures directory.")
    parser.add_argument("--title-prefix", default="", help="Optional title prefix.")
    parser.add_argument("--evidence-output", help="Optional evidence JSON output path.")
    parser.add_argument("--line-voltage-mode", choices=["auto", "force", "off"], default="auto", help="Convert likely phase back-EMF/voltage waveforms to line voltage. Default: auto.")
    parser.add_argument("--motor-report-csv", help="Magnetic-circuit report CSV used to read pole count or pole pairs for speed estimation.")
    parser.add_argument("--pole-pairs", type=float, help="Override motor pole pairs for speed estimation.")
    parser.add_argument("--pole-count", type=float, help="Override motor pole count; pole pairs are pole count / 2.")
    args = parser.parse_args()

    warnings = []
    figures = []
    try:
        requireMatplotlib()
    except ImportError as error:
        result = {"warnings": [f"matplotlib is required for plotting: {error}"], "figures": []}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    polePairs, poleWarnings, poleSource = resolvePolePairs(args)
    warnings.extend(poleWarnings)
    for filePath in args.curveFiles:
        record, fileWarnings = plotFile(filePath, args.output_dir, args.title_prefix, args.line_voltage_mode, polePairs=polePairs, poleSource=poleSource)
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
