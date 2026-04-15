#!/usr/bin/env python
import argparse
import csv
import json
from pathlib import Path


ENCODINGS = ["utf-8-sig", "utf-8", "gb18030", "cp936", "latin-1"]

# The basic-parameter report section must describe the motor/model structure, not
# repeat operating points. Rows that can legitimately vary by workpoint are kept
# out of this extractor's primary Markdown table.
STRUCTURAL_PARAM_GROUPS = {
    "模型概况": [
        "电机型号",
        "极数",
        "极对数",
        "相数",
        "转子位置",
        "电路类型",
        "励磁类型",
        "计算方式",
        "控制算法",
        "调制方式",
    ],
    "定子与铁芯": [
        "定子冲片形状",
        "定子外径",
        "定子内径",
        "铁芯长度",
        "铁芯叠压系数",
        "定子材料名称",
        "定子槽数",
        "定子斜槽宽度(定子齿距)",
        "定子槽形",
        "齿宽",
        "定子槽尺寸b0",
        "定子槽尺寸b1",
        "定子槽尺寸b2",
        "定子槽尺寸h0",
        "定子槽尺寸h1",
        "定子槽尺寸h2",
    ],
    "绕组": [
        "定子绕组形式",
        "绕组层数",
        "相带形式",
        "节距（槽数）",
        "并联支路数",
        "每槽导体数",
        "第一种导线并绕根数",
        "圆线第一种线规裸线直径",
        "圆线第一种线规绝缘后直径",
        "定子线圈端部类型",
        "定子绕组直线部分伸出铁芯长度",
        "定子线圈平均半匝长度",
        "定子槽绝缘厚度",
        "定子绕组的导线材料",
        "定子槽满率",
    ],
    "基础电气参数": [
        "电枢绕组相电阻(25度)",
        "电枢绕组相电阻，25度",
        "直轴同步电感",
        "交轴同步电感",
        "电枢绕组漏电抗",
    ],
    "转子、磁钢与材料": [
        "转子类型",
        "转子磁极中心气隙",
        "转子外径",
        "转子内径",
        "转子铁芯长度",
        "转子铁芯材料",
        "转子铁芯叠压系数",
        "极弧系数",
        "磁钢材料",
        "磁钢厚度",
        "磁钢轴向长度",
        "D轴位置",
        "磁钢工作温度",
        "剩磁密度",
        "矫顽力",
    ],
}

OPERATING_OR_RESULT_ROWS = {
    "正弦波频率",
    "限幅电流",
    "输出功率",
    "工况类型",
    "负载转矩",
    "运行转速",
    "效率设计值",
    "功率因数设计值",
    "风摩损耗",
    "绕组工作温度",
    "电枢绕组相电阻",
    "电机相电流有效值",
    "线电流有效值",
    "相电流有效值",
    "线电压",
    "相电压",
    "输入功率",
    "效率",
    "总损耗",
    "定子槽部铜耗",
    "定子端部铜耗",
}


def read_rows(path):
    last_error = None
    for encoding in ENCODINGS:
        try:
            text = Path(path).read_text(encoding=encoding)
            return list(csv.reader(text.splitlines())), encoding
        except UnicodeError as error:
            last_error = error
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    return list(csv.reader(text.splitlines())), f"utf-8-replace ({last_error})"


def clean(value):
    return str(value).strip()


def to_float(value):
    try:
        text = clean(value)
        if not text:
            return None
        return float(text)
    except ValueError:
        return None


def normalize_numeric_text(value):
    number = to_float(value)
    if number is None:
        return clean(value)
    return f"{number:.12g}"


def unique_non_empty(values):
    unique = []
    for value in values:
        normalized = normalize_numeric_text(value)
        if not normalized:
            continue
        if normalized not in unique:
            unique.append(normalized)
    return unique


def find_workpoints(rows):
    for row in rows:
        if row and clean(row[0]) == "电机型号":
            names = [clean(value) for value in row[2:] if clean(value)]
            if names:
                return names
    max_values = 0
    for row in rows:
        max_values = max(max_values, max(0, len(row) - 2))
    return [f"工况{i + 1}" for i in range(max_values)]


def find_param_rows(rows):
    found = {}
    for row in rows:
        if not row:
            continue
        name = clean(row[0])
        if not name:
            continue
        unit = clean(row[1]) if len(row) > 1 else ""
        values = [clean(value) for value in row[2:]] if len(row) > 2 else []
        if name not in found:
            found[name] = {"name": name, "unit": unit, "values": values}
    return found


def derived_rows(found):
    derived = []
    pole_row = found.get("极数")
    if pole_row:
        values = []
        for value in pole_row["values"]:
            number = to_float(value)
            values.append("" if number is None else f"{number / 2:.12g}")
        if any(values):
            derived.append({"name": "极对数", "unit": "", "values": values, "derivedFrom": "极数 / 2"})
    return derived


def values_by_workpoint(values, workpoints):
    mapped = {}
    count = max(len(values), len(workpoints))
    for index in range(count):
        name = workpoints[index] if index < len(workpoints) and workpoints[index] else f"工况{index + 1}"
        value = clean(values[index]) if index < len(values) else ""
        mapped[name] = value
    return mapped


def single_structural_value(row):
    unique = unique_non_empty(row.get("values", []))
    if len(unique) != 1:
        return None, unique
    return unique[0], unique


def build_sections(found, workpoints):
    sections = []
    skipped_rows = []
    derived = {row["name"]: row for row in derived_rows(found)}
    source = dict(found)
    source.update(derived)

    for title, names in STRUCTURAL_PARAM_GROUPS.items():
        rows = []
        for name in names:
            row = source.get(name)
            if not row:
                continue
            value, unique = single_structural_value(row)
            if value is None:
                skipped_rows.append({
                    "name": name,
                    "unit": row.get("unit", ""),
                    "reason": "multiple workpoint values; not emitted in the single-value structural table",
                    "uniqueValues": unique,
                    "valuesByWorkpoint": values_by_workpoint(row.get("values", []), workpoints),
                })
                continue
            output_row = {
                "name": name,
                "unit": row.get("unit", ""),
                "value": value,
                "uniqueValues": unique,
                "valuesByWorkpoint": values_by_workpoint(row.get("values", []), workpoints),
            }
            if "derivedFrom" in row:
                output_row["derivedFrom"] = row["derivedFrom"]
            rows.append(output_row)
        if rows:
            sections.append({"title": title, "rows": rows})

    for name in OPERATING_OR_RESULT_ROWS:
        row = found.get(name)
        if not row:
            continue
        unique = unique_non_empty(row.get("values", []))
        if unique:
            skipped_rows.append({
                "name": name,
                "unit": row.get("unit", ""),
                "reason": "operating-condition or result row; use in simulation/result sections, not the structural parameter section",
                "uniqueValues": unique,
                "valuesByWorkpoint": values_by_workpoint(row.get("values", []), workpoints),
            })
    return sections, skipped_rows


def markdown_table(sections):
    lines = []
    for section in sections:
        lines.append(f"### {section['title']}")
        lines.append("")
        lines.append("| 参数 | 数值 | 单位 | 备注 |")
        lines.append("|---|---:|---|---|")
        for row in section["rows"]:
            note = f"由 {row['derivedFrom']} 计算" if row.get("derivedFrom") else ""
            lines.append("| " + " | ".join([row["name"], row["value"], row.get("unit", ""), note]) + " |")
        lines.append("")
    return "\n".join(lines).strip()


def full_workpoint_markdown(sections, workpoints):
    lines = []
    workpoint_headers = workpoints or ["工况1"]
    for section in sections:
        lines.append(f"### {section['title']}（原始工况值审计）")
        lines.append("")
        header = ["参数", *workpoint_headers, "单位", "备注"]
        lines.append("| " + " | ".join(header) + " |")
        lines.append("|" + "|".join(["---", *["---:" for _ in workpoint_headers], "---", "---"]) + "|")
        for row in section["rows"]:
            note = f"由 {row['derivedFrom']} 计算" if row.get("derivedFrom") else ""
            values = row.get("valuesByWorkpoint", {})
            cells = [values.get(workpoint, "") for workpoint in workpoint_headers]
            lines.append("| " + " | ".join([row["name"], *cells, row.get("unit", ""), note]) + " |")
        lines.append("")
    return "\n".join(lines).strip()


def main():
    parser = argparse.ArgumentParser(description="Extract single-value motor structural/basic model information from a magnetic-circuit report CSV.")
    parser.add_argument("reportCsv", help="Magnetic-circuit report CSV, usually 工况报表结果.csv.")
    parser.add_argument("--markdown-output", help="Optional Markdown table output path.")
    parser.add_argument("--json-output", help="Optional JSON output path.")
    parser.add_argument("--full-workpoint-markdown-output", help="Optional audit table that preserves original workpoint columns.")
    args = parser.parse_args()

    rows, encoding = read_rows(args.reportCsv)
    found = find_param_rows(rows)
    workpoints = find_workpoints(rows)
    sections, skipped_rows = build_sections(found, workpoints)
    result = {
        "sourceFile": str(Path(args.reportCsv).resolve()),
        "encoding": encoding,
        "workpoints": workpoints,
        "sections": sections,
        "skippedRows": skipped_rows,
        "markdown": markdown_table(sections),
        "warnings": [] if sections else ["No expected single-value motor structural parameters were found."],
        "notes": [
            "The primary Markdown is intentionally single-value per parameter for the report section 电机与仿真模型基本参数.",
            "Rows that vary by workpoint or represent operating/result quantities are listed in skippedRows for use in simulation result sections.",
        ],
    }

    output_text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.json_output:
        Path(args.json_output).write_text(output_text, encoding="utf-8")
    if args.markdown_output:
        Path(args.markdown_output).write_text(result["markdown"] + "\n", encoding="utf-8")
    if args.full_workpoint_markdown_output:
        Path(args.full_workpoint_markdown_output).write_text(full_workpoint_markdown(sections, workpoints) + "\n", encoding="utf-8")
    print(output_text)


if __name__ == "__main__":
    main()
