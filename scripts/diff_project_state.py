#!/usr/bin/env python
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


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


def scanCurrentFiles(projectRoot, hashFiles):
    root = Path(projectRoot).resolve()
    current = {}
    for currentRoot, _, fileNames in os.walk(root):
        for fileName in fileNames:
            filePath = Path(currentRoot) / fileName
            try:
                relativePath = filePath.resolve().relative_to(root).as_posix()
                statResult = filePath.stat()
                contentHash = fileHash(filePath) if hashFiles else ""
                current[relativePath] = {
                    "sourceFile": str(filePath.resolve()),
                    "relativePath": relativePath,
                    "fileSize": statResult.st_size,
                    "modifiedTime": datetime.fromtimestamp(statResult.st_mtime, timezone.utc).replace(microsecond=0).isoformat(),
                    "contentHash": contentHash
                }
            except OSError:
                continue
    return current


def ledgerIndex(ledger):
    indexed = {}
    for record in ledger.get("records", []) or []:
        key = record.get("relativePath") or record.get("sourceFile")
        if key:
            indexed[key.replace("\\", "/")] = record
    return indexed


def compare(projectRoot, ledgerPath, hashFiles):
    ledger = readJson(ledgerPath)
    current = scanCurrentFiles(projectRoot, hashFiles)
    previous = ledgerIndex(ledger)

    added = []
    modified = []
    unchanged = []
    deleted = []

    for relativePath, currentRecord in current.items():
        previousRecord = previous.get(relativePath)
        if not previousRecord:
            added.append(currentRecord)
            continue

        sizeChanged = previousRecord.get("fileSize") != currentRecord.get("fileSize")
        timeChanged = previousRecord.get("modifiedTime") != currentRecord.get("modifiedTime")
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
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Compare a current project folder against an evidence ledger.")
    parser.add_argument("projectRoot", help="Project root to scan.")
    parser.add_argument("evidenceLedger", help="Existing evidence-ledger.json.")
    parser.add_argument("--hash-files", action="store_true", help="Compute content hashes for current files. Slower but more robust.")
    parser.add_argument("--output", help="Optional JSON output path.")
    args = parser.parse_args()

    result = compare(args.projectRoot, args.evidenceLedger, args.hash_files)
    outputText = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(outputText, encoding="utf-8")
    else:
        print(outputText)


if __name__ == "__main__":
    main()
