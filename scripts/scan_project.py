#!/usr/bin/env python
import argparse
import json
import os
import re
from pathlib import Path


HASH_DIR_PATTERN = re.compile(r"^[0-9a-fA-F]{8,}$")


def guessCategory(relativePath, extension):
    lowerPath = relativePath.lower()
    tags = []
    score = 0.2
    category = "unknown"

    measuredWords = ["实测", "测试", "measured", "test", "scope", "oscilloscope", "示波器", "波形"]
    simulationWords = ["backef", "torque", "voltage", "current", "speed", "flux", "pfe", "pcu", "coreloss", "fem2d", "em3res", "fccouple", "仿真", "工况", "外特性"]
    designWords = ["设计", "dwg", "dxf", "machinedata", "dsninfo", "材料", "磁钢", "铁芯"]
    assetWords = ["logo", "封面", "免责声明", "template", "模板"]

    if any(word in lowerPath for word in measuredWords):
        category = "measuredData"
        tags.append("measured-cue")
        score = 0.55
    if any(word in lowerPath for word in simulationWords):
        category = "simulationData"
        tags.append("simulation-cue")
        score = max(score, 0.55)
    if any(word in lowerPath for word in designWords):
        category = "customerDesignInput"
        tags.append("design-cue")
        score = max(score, 0.5)
    if any(word in lowerPath for word in assetWords):
        category = "assets"
        tags.append("asset-cue")
        score = max(score, 0.45)

    if extension in [".png", ".jpg", ".jpeg", ".bmp", ".webp"]:
        tags.append("image")
    elif extension in [".pdf"]:
        tags.append("pdf")
    elif extension in [".csv", ".ecsv", ".dat", ".txt", ".json", ".xlsx", ".xls"]:
        tags.append("readable-data")
    elif extension in [".field", ".node", ".edge", ".ele", ".neigh", ".bin"]:
        tags.append("large-simulation-artifact")

    return category, tags, round(score, 2)


def scanProject(projectRoot, maxFiles):
    rootPath = Path(projectRoot).resolve()
    records = []
    warnings = []
    hashFolders = []

    if not rootPath.exists():
        raise FileNotFoundError(f"Project root not found: {rootPath}")

    for currentRoot, dirNames, fileNames in os.walk(rootPath):
        currentPath = Path(currentRoot)
        try:
            relativeDir = currentPath.relative_to(rootPath)
        except ValueError:
            relativeDir = currentPath

        for dirName in dirNames:
            if HASH_DIR_PATTERN.match(dirName):
                hashFolders.append(str((relativeDir / dirName).as_posix()))

        for fileName in fileNames:
            if len(records) >= maxFiles:
                warnings.append(f"Reached maxFiles={maxFiles}; remaining files skipped.")
                return buildOutput(rootPath, records, hashFolders, warnings)

            filePath = currentPath / fileName
            try:
                statResult = filePath.stat()
                relativePath = filePath.relative_to(rootPath).as_posix()
                extension = filePath.suffix.lower()
                category, tags, confidence = guessCategory(relativePath, extension)
                records.append({
                    "relativePath": relativePath,
                    "absolutePath": str(filePath.resolve()),
                    "fileName": fileName,
                    "extension": extension,
                    "size": statResult.st_size,
                    "directoryDepth": len(Path(relativePath).parts) - 1,
                    "categoryCandidate": category,
                    "semanticTags": tags,
                    "confidence": confidence
                })
            except OSError as error:
                warnings.append(f"Could not stat {filePath}: {error}")

    return buildOutput(rootPath, records, hashFolders, warnings)


def buildOutput(rootPath, records, hashFolders, warnings):
    return {
        "projectRoot": str(rootPath),
        "fileCount": len(records),
        "hashFolderCandidates": sorted(set(hashFolders)),
        "records": records,
        "warnings": warnings
    }


def main():
    parser = argparse.ArgumentParser(description="Scan a motor trial project and output a JSON file index.")
    parser.add_argument("projectRoot", help="Project root path to scan.")
    parser.add_argument("--max-files", type=int, default=5000, help="Maximum number of files to index.")
    parser.add_argument("--output", help="Optional JSON output path.")
    args = parser.parse_args()

    result = scanProject(args.projectRoot, args.max_files)
    outputText = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(outputText, encoding="utf-8")
    else:
        print(outputText)


if __name__ == "__main__":
    main()
