#!/usr/bin/env python
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_IGNORE_DIRS = {".git", "__pycache__", "report-output", "figures"}
DEFAULT_IGNORE_FILES = {"report-state.json", "evidence-ledger.json", "change-log.md"}


def readJson(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def fileHash(path, chunkSize=1024 * 1024):
    sha = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while True:
            chunk = handle.read(chunkSize)
            if not chunk:
                break
            sha.update(chunk)
    return sha.hexdigest()


def isIgnored(relativePath):
    path = Path(str(relativePath).replace("\\", "/"))
    if any(part in DEFAULT_IGNORE_DIRS for part in path.parts):
        return True
    return path.name in DEFAULT_IGNORE_FILES


def recordForPath(filePath, root, hashFiles):
    statResult = filePath.stat()
    try:
        relativePath = filePath.resolve().relative_to(root).as_posix()
    except ValueError:
        relativePath = filePath.resolve().as_posix()
    return {
        "sourceFile": str(filePath.resolve()),
        "relativePath": relativePath,
        "fileSize": statResult.st_size,
        "modifiedTime": datetime.fromtimestamp(statResult.st_mtime, timezone.utc).replace(microsecond=0).isoformat(),
        "contentHash": fileHash(filePath) if hashFiles else ""
    }


def sameModifiedTime(previousValue, currentValue):
    if previousValue == currentValue:
        return True
    try:
        previous = datetime.fromisoformat(str(previousValue).replace("Z", "+00:00"))
        current = datetime.fromisoformat(str(currentValue).replace("Z", "+00:00"))
        return int(previous.timestamp()) == int(current.timestamp())
    except (TypeError, ValueError):
        return False


def scanCurrentFiles(projectRoot, hashFiles):
    root = Path(projectRoot).resolve()
    current = {}
    for currentRoot, dirNames, fileNames in os.walk(root):
        dirNames[:] = [dirName for dirName in dirNames if dirName not in DEFAULT_IGNORE_DIRS]
        for fileName in fileNames:
            if fileName in DEFAULT_IGNORE_FILES:
                continue
            filePath = Path(currentRoot) / fileName
            try:
                record = recordForPath(filePath, root, hashFiles)
                current[record["relativePath"]] = record
            except OSError:
                continue
    return current


def ledgerIndex(ledger, projectRoot=None, sourceOnly=True):
    indexed = {}
    root = Path(projectRoot).resolve() if projectRoot else None
    for record in ledger.get("records", []) or []:
        if sourceOnly and record.get("sourceRole") == "figure":
            source_file = record.get("sourceFile")
        else:
            source_file = record.get("sourceFile") or record.get("generatedFile")
        key = record.get("relativePath") or source_file
        if not key:
            continue
        key = key.replace("\\", "/")
        if isIgnored(key):
            continue
        if root and source_file:
            try:
                file_path = Path(source_file).resolve()
                key = file_path.relative_to(root).as_posix()
            except (OSError, ValueError):
                key = str(source_file).replace("\\", "/")
        indexed[key] = record
    return indexed


def scanEvidenceSourceFiles(projectRoot, ledger, hashFiles):
    root = Path(projectRoot).resolve()
    current = {}
    warnings = []
    for relativePath, record in ledgerIndex(ledger, projectRoot, sourceOnly=True).items():
        sourceFile = record.get("sourceFile")
        filePath = Path(sourceFile) if sourceFile else root / relativePath
        if not filePath.is_absolute():
            filePath = root / filePath
        try:
            if filePath.exists() and filePath.is_file():
                current[relativePath] = recordForPath(filePath, root, hashFiles)
        except OSError as error:
            warnings.append(f"Could not stat evidence source {filePath}: {error}")
    return current, warnings


def compare(projectRoot, ledgerPath, hashFiles, scanAdded=False):
    ledger = readJson(ledgerPath)
    current, warnings = scanEvidenceSourceFiles(projectRoot, ledger, hashFiles)
    previous = ledgerIndex(ledger, projectRoot, sourceOnly=True)
    scannedAll = {}
    if scanAdded:
        scannedAll = scanCurrentFiles(projectRoot, hashFiles)

    added = []
    modified = []
    unchanged = []
    deleted = []

    if scanAdded:
        for relativePath, currentRecord in scannedAll.items():
            if relativePath not in previous:
                added.append(currentRecord)

    for relativePath, currentRecord in current.items():
        previousRecord = previous.get(relativePath)
        if not previousRecord:
            if not scanAdded:
                added.append(currentRecord)
            continue

        sizeChanged = previousRecord.get("fileSize") != currentRecord.get("fileSize")
        timeChanged = not sameModifiedTime(previousRecord.get("modifiedTime"), currentRecord.get("modifiedTime"))
        hashChanged = False
        if hashFiles and previousRecord.get("contentHash") and currentRecord.get("contentHash"):
            hashChanged = previousRecord.get("contentHash") != currentRecord.get("contentHash")

        if sizeChanged or timeChanged or hashChanged:
            changedRecord = dict(currentRecord)
            changedRecord["previous"] = {
                "fileSize": previousRecord.get("fileSize"),
                "modifiedTime": previousRecord.get("modifiedTime"),
                "contentHash": previousRecord.get("contentHash", "")
            }
            modified.append(changedRecord)
        else:
            unchanged.append(currentRecord)

    for relativePath, previousRecord in previous.items():
        if relativePath not in current:
            deleted.append(previousRecord)

    return {
        "projectRoot": str(Path(projectRoot).resolve()),
        "ledger": str(Path(ledgerPath).resolve()),
        "added": added,
        "modified": modified,
        "deleted": deleted,
        "unchangedCount": len(unchanged),
        "summary": {
            "added": len(added),
            "modified": len(modified),
            "deleted": len(deleted),
            "unchanged": len(unchanged)
        },
        "warnings": warnings,
        "mode": "evidence-source-files" if not scanAdded else "evidence-source-files-plus-added-scan"
    }


def main():
    parser = argparse.ArgumentParser(description="Compare a current project folder against an evidence ledger.")
    parser.add_argument("projectRoot", help="Project root to scan.")
    parser.add_argument("evidenceLedger", help="Existing evidence-ledger.json.")
    parser.add_argument("--hash-files", action="store_true", help="Compute content hashes for current files. Slower but more robust.")
    parser.add_argument("--scan-added", action="store_true", help="Also scan the project for added non-generated files. Default compares only evidence source files.")
    parser.add_argument("--output", help="Optional JSON output path.")
    args = parser.parse_args()

    result = compare(args.projectRoot, args.evidenceLedger, args.hash_files, args.scan_added)
    outputText = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(outputText, encoding="utf-8")
    else:
        print(outputText)


if __name__ == "__main__":
    main()
