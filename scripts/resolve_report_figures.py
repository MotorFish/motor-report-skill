#!/usr/bin/env python
import argparse
import json
import shutil
from pathlib import Path


def findGeometryImage(projectRoot):
    root = Path(projectRoot).resolve()
    rootGeo = root / "geo2d.png"
    if rootGeo.exists():
        return rootGeo, "root-geo2d"

    candidates = sorted(root.glob("*/geo2d.png"))
    if candidates:
        return candidates[0], "hash-folder-geo2d"
    return None, "not-found"


def main():
    parser = argparse.ArgumentParser(description="Resolve common report figures such as the .em3 geometry image.")
    parser.add_argument("projectRoot", help="Project root, usually a .em3 folder.")
    parser.add_argument("--output-dir", required=True, help="Report figures output directory.")
    parser.add_argument("--name", default="geometry-section.png", help="Output file name for geometry image.")
    parser.add_argument("--evidence-output", help="Optional evidence JSON output path.")
    args = parser.parse_args()

    outputDir = Path(args.output_dir)
    outputDir.mkdir(parents=True, exist_ok=True)

    source, sourceKind = findGeometryImage(args.projectRoot)
    if not source:
        result = {
            "warnings": ["No geo2d.png found at project root or one-level hash folders."],
            "figures": []
        }
    else:
        dest = outputDir / args.name
        shutil.copy2(source, dest)
        record = {
            "evidenceId": "figure-geometry-section",
            "sourceFile": str(source.resolve()),
            "relativePath": source.name,
            "sourceRole": "figure",
            "generatedFile": str(dest.resolve()),
            "figureKind": "geometrySection",
            "metricNames": [],
            "usedInReportSections": ["电机与仿真模型基本参数"],
            "extractionMethod": "resolve_report_figures.py",
            "confidence": 0.9,
            "notes": sourceKind
        }
        result = {"warnings": [], "figures": [record]}

    outputText = json.dumps(result, ensure_ascii=False, indent=2)
    if args.evidence_output:
        Path(args.evidence_output).write_text(outputText, encoding="utf-8")
    print(outputText)


if __name__ == "__main__":
    main()
