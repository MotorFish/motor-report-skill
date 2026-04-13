#!/usr/bin/env python
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def utcNow():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def readJson(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def writeJson(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def evidenceKey(record):
    return record.get("evidenceId") or record.get("relativePath") or record.get("sourceFile")


def loadNewEvidence(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if isinstance(data.get("records"), list):
            return data["records"]
        if isinstance(data.get("newEvidence"), list):
            return data["newEvidence"]
        return [data]
    return []


def mergeLedger(ledger, newEvidence, mode):
    existing = {}
    for record in ledger.get("records", []) or []:
        key = evidenceKey(record)
        if key:
            existing[key] = record

    added = 0
    updated = 0
    for record in newEvidence:
        if not isinstance(record, dict):
            continue
        key = evidenceKey(record)
        if not key:
            continue
        if key in existing:
            if mode == "replace":
                existing[key] = {**existing[key], **record}
            else:
                merged = dict(existing[key])
                for field, value in record.items():
                    if value not in [None, "", []]:
                        merged[field] = value
                existing[key] = merged
            updated += 1
        else:
            existing[key] = record
            added += 1

    ledger["records"] = list(existing.values())
    ledger["updatedAt"] = utcNow()
    return ledger, {"added": added, "updated": updated, "total": len(ledger["records"])}


def appendChangeLog(path, summary, note):
    if not path:
        return
    logPath = Path(path)
    entry = [
        f"## {utcNow()}",
        "",
        f"- Request: Evidence ledger updated.",
        f"- Evidence changes: added {summary['added']}, updated {summary['updated']}, total {summary['total']}.",
    ]
    if note:
        entry.append(f"- Notes: {note}")
    entry.append("")
    logPath.parent.mkdir(parents=True, exist_ok=True)
    with logPath.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(entry) + "\n")


def main():
    parser = argparse.ArgumentParser(description="Merge new evidence records into evidence-ledger.json.")
    parser.add_argument("--ledger", required=True, help="Existing evidence-ledger.json.")
    parser.add_argument("--new-evidence", required=True, help="JSON file containing a record, records array, or newEvidence array.")
    parser.add_argument("--output", help="Optional output path. Defaults to overwriting ledger.")
    parser.add_argument("--mode", choices=["merge", "replace"], default="merge", help="Merge non-empty fields or replace matching records.")
    parser.add_argument("--change-log", help="Optional change-log.md path to append a human-readable entry.")
    parser.add_argument("--note", default="", help="Optional note for change log.")
    args = parser.parse_args()

    ledger = readJson(args.ledger)
    newEvidence = loadNewEvidence(readJson(args.new_evidence))
    updatedLedger, summary = mergeLedger(ledger, newEvidence, args.mode)
    outputPath = args.output or args.ledger
    writeJson(outputPath, updatedLedger)
    appendChangeLog(args.change_log, summary, args.note)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
