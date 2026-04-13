#!/usr/bin/env python
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def utcNow():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def readJson(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def writeJson(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def fileHash(path, chunkSize=1024 * 1024):
    sha = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while True:
            chunk = handle.read(chunkSize)
            if not chunk:
                break
            sha.update(chunk)
    return sha.hexdigest()


def safeStat(path, projectRoot):
    sourcePath = Path(path)
    if not sourcePath.is_absolute() and projectRoot:
        sourcePath = Path(projectRoot) / sourcePath
    try:
        statResult = sourcePath.stat()
        relativePath = str(sourcePath.resolve())
        if projectRoot:
            try:
                relativePath = sourcePath.resolve().relative_to(Path(projectRoot).resolve()).as_posix()
            except ValueError:
                relativePath = sourcePath.name
        return {
            "sourceFile": str(sourcePath.resolve()),
            "relativePath": relativePath,
            "fileSize": statResult.st_size,
            "modifiedTime": datetime.fromtimestamp(statResult.st_mtime, timezone.utc).replace(microsecond=0).isoformat(),
            "contentHash": fileHash(sourcePath)
        }
    except OSError:
        return {
            "sourceFile": str(sourcePath),
            "relativePath": str(path),
            "fileSize": None,
            "modifiedTime": "",
            "contentHash": ""
        }


def makeEvidenceId(role, index, record):
    seed = f"{role}|{index}|{record.get('sourceFile','')}|{record.get('metricName','')}"
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]


def recordsFromData(context, projectRoot):
    records = []
    for role, dataKey in [("measuredData", "measuredData"), ("simulationData", "simulationData")]:
        for index, item in enumerate(context.get(dataKey, []) or []):
            if not isinstance(item, dict):
                continue
            sourceFile = item.get("sourceFile") or item.get("source") or ""
            statInfo = safeStat(sourceFile, projectRoot) if sourceFile else {}
            records.append({
                "evidenceId": item.get("evidenceId") or makeEvidenceId(role, index, item),
                "sourceFile": statInfo.get("sourceFile", sourceFile),
                "relativePath": statInfo.get("relativePath", sourceFile),
                "sourceRole": role,
                "hashFolder": item.get("hashFolder", ""),
                "hashFolderMeaning": item.get("simulationKind", ""),
                "metricNames": [item.get("metricName", "")] if item.get("metricName") else [],
                "usedInReportSections": item.get("usedInReportSections", []),
                "fileSize": statInfo.get("fileSize"),
                "modifiedTime": statInfo.get("modifiedTime", ""),
                "contentHash": statInfo.get("contentHash", ""),
                "extractionMethod": item.get("extractionMethod", ""),
                "confidence": item.get("confidence", 0.0),
                "notes": item.get("note", "")
            })
    for dataKey in ["figures", "figureEvidence"]:
        for index, item in enumerate(context.get(dataKey, []) or []):
            if not isinstance(item, dict):
                continue
            sourceFile = item.get("sourceFile") or ""
            statInfo = safeStat(sourceFile, projectRoot) if sourceFile else {}
            records.append({
                "evidenceId": item.get("evidenceId") or makeEvidenceId("figure", index, item),
                "sourceFile": statInfo.get("sourceFile", sourceFile),
                "relativePath": statInfo.get("relativePath", sourceFile),
                "sourceRole": "figure",
                "generatedFile": item.get("generatedFile", ""),
                "figureKind": item.get("figureKind", ""),
                "hashFolder": item.get("hashFolder", ""),
                "hashFolderMeaning": item.get("hashFolderMeaning", ""),
                "metricNames": item.get("metricNames", []),
                "usedInReportSections": item.get("usedInReportSections", []),
                "fileSize": statInfo.get("fileSize"),
                "modifiedTime": statInfo.get("modifiedTime", ""),
                "contentHash": statInfo.get("contentHash", ""),
                "extractionMethod": item.get("extractionMethod", ""),
                "confidence": item.get("confidence", 0.0),
                "notes": item.get("notes", "")
            })
    return records


def loadReportSections(reportPath):
    if not reportPath or not Path(reportPath).exists():
        return []
    sections = []
    for line in Path(reportPath).read_text(encoding="utf-8-sig", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            title = stripped.lstrip("#").strip()
            sectionId = hashlib.sha1(title.encode("utf-8")).hexdigest()[:12]
            sections.append({
                "sectionId": sectionId,
                "title": title,
                "dependsOnEvidenceIds": [],
                "notes": ""
            })
    return sections


def createState(context, reportPath, outputDir):
    projectRoot = context.get("projectRoot") or context.get("projectMeta", {}).get("projectRoot", "")
    now = utcNow()
    evidenceRecords = recordsFromData(context, projectRoot)

    reportState = {
        "schemaVersion": "1.0",
        "reportPath": str(Path(reportPath).resolve()) if reportPath else "",
        "projectRoot": projectRoot,
        "projectMeta": context.get("projectMeta", {}),
        "machineBasicInfo": context.get("machineBasicInfo", {}),
        "hashFolderMapping": context.get("hashFolderMapping", {}),
        "measuredData": context.get("measuredData", []),
        "simulationData": context.get("simulationData", []),
        "comparisonRows": context.get("comparisonRows", []),
        "figures": context.get("figures", []) or context.get("figureEvidence", []),
        "reportSections": loadReportSections(reportPath),
        "lastUpdatedAt": now,
        "updateHistory": [
            {
                "time": now,
                "type": "initial-report-state-created",
                "notes": "Created report state package."
            }
        ]
    }

    evidenceLedger = {
        "schemaVersion": "1.0",
        "projectRoot": projectRoot,
        "createdAt": now,
        "updatedAt": now,
        "records": evidenceRecords
    }

    outputPath = Path(outputDir)
    outputPath.mkdir(parents=True, exist_ok=True)
    writeJson(outputPath / "report-state.json", reportState)
    writeJson(outputPath / "evidence-ledger.json", evidenceLedger)

    changeLogPath = outputPath / "change-log.md"
    if not changeLogPath.exists():
        changeLogPath.write_text(
            f"## {now}\n\n- Request: Initial report state created.\n- Evidence records: {len(evidenceRecords)}\n- Report: {reportState['reportPath']}\n\n",
            encoding="utf-8"
        )

    return {
        "reportState": str((outputPath / "report-state.json").resolve()),
        "evidenceLedger": str((outputPath / "evidence-ledger.json").resolve()),
        "changeLog": str(changeLogPath.resolve()),
        "evidenceRecordCount": len(evidenceRecords)
    }


def main():
    parser = argparse.ArgumentParser(description="Create report-state.json and evidence-ledger.json for incremental motor report updates.")
    parser.add_argument("--context", required=True, help="JSON report context containing measuredData, simulationData, comparisons, and metadata.")
    parser.add_argument("--report", required=False, default="", help="Generated report Markdown path.")
    parser.add_argument("--output-dir", required=True, help="Directory where state files should be written.")
    args = parser.parse_args()

    context = readJson(args.context)
    result = createState(context, args.report, args.output_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
