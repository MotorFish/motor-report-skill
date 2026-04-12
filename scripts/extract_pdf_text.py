#!/usr/bin/env python
import argparse
import json
from pathlib import Path


def extractWithPypdf(path, maxPages):
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    pages = []
    for index, page in enumerate(reader.pages[:maxPages]):
        pages.append({
            "page": index + 1,
            "text": page.extract_text() or ""
        })
    return {
        "method": "pypdf",
        "pageCount": len(reader.pages),
        "pages": pages
    }


def extractWithPdfplumber(path, maxPages):
    import pdfplumber
    pages = []
    with pdfplumber.open(str(path)) as pdf:
        for index, page in enumerate(pdf.pages[:maxPages]):
            tables = page.extract_tables() or []
            pages.append({
                "page": index + 1,
                "text": page.extract_text() or "",
                "tables": tables[:5]
            })
        return {
            "method": "pdfplumber",
            "pageCount": len(pdf.pages),
            "pages": pages
        }


def extractPdf(filePath, maxPages):
    path = Path(filePath)
    errors = []
    for extractor in [extractWithPypdf, extractWithPdfplumber]:
        try:
            result = extractor(path, maxPages)
            result["file"] = str(path.resolve())
            result["warnings"] = errors
            return result
        except ImportError as error:
            errors.append(f"{extractor.__name__} unavailable: {error}")
        except Exception as error:
            errors.append(f"{extractor.__name__} failed: {error}")
    return {
        "file": str(path.resolve()),
        "method": None,
        "pageCount": None,
        "pages": [],
        "warnings": errors + ["No PDF extraction backend succeeded."]
    }


def main():
    parser = argparse.ArgumentParser(description="Extract basic text and tables from a PDF.")
    parser.add_argument("filePath", help="PDF file path.")
    parser.add_argument("--max-pages", type=int, default=20, help="Maximum pages to extract.")
    parser.add_argument("--output", help="Optional JSON output path.")
    args = parser.parse_args()

    result = extractPdf(args.filePath, args.max_pages)
    outputText = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(outputText, encoding="utf-8")
    else:
        print(outputText)


if __name__ == "__main__":
    main()
