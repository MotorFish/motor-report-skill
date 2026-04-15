#!/usr/bin/env python
import argparse
import csv
import json
from pathlib import Path


ENCODINGS = ["utf-8-sig", "utf-8", "gb18030", "cp936", "latin-1"]

KEY_ROWS = [
    "电机型号",
    "极数",
    "相数",
    "转子位置",
    "电路类型",
    "控制算法",
    "调制方式",
    "正弦波频率",
    "输出功率",
    "负载转矩",
    "运行转速",
    "定子外径",
    "定子内径",
    "铁芯长度",
    "定子材料名称",
    "定子槽数",
    "定子槽形",
    "齿宽",
    "定子绕组形式",
    "绕组层数",
    "相带形式",
    "节距（槽数）",
    "并联支路数",
    "每槽导体数",
    "绕组线型",
    "圆线第一种线规裸线直径",
    "圆线第一种线规绝缘后直径",
    "定子线圈平均半匝长度",
    "定子绕组的导线材料",
    "定子槽满率",
    "转子类型",
    "转子磁极中心气隙",
    "转子外径",
    "转子内径",
    "转子铁芯长度",
    "转子铁芯材料",
    "磁钢材料",
    "磁钢工作温度",
    "剩磁密度",
    "矫顽力",
    "定子铁芯重量",
    "转子铁重",
    "磁钢重量",
    "电枢绕组相电阻(25度)",
    "绕组工作温度",
    "电枢绕组相电阻",
    "电枢绕组漏电抗",
    "电机相电流有效值",
    "定子槽部铜耗",
    "定子端部铜耗",
]


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


def to_float(value):
    try:
        text = str(value).strip()
        if text == "":
            return None
        return float(text)
    except ValueError:
        return None


def clean_cell(value):
    return str(value).strip()


def first_non_empty(values):
    for value in values:
        if value not in ("", None):
            return value
    return None


def unique_values(values):
    unique = []
    for value in values:
        if value in ("", None):
            continue
        if value not in unique:
            unique.append(value)
    return unique


def parse_report(path):
    rows, encoding = read_rows(path)
    case_names = []
    data = {}
    for row in rows:
        if not row:
            continue
        label = clean_cell(row[0])
        if not label:
            continue
        unit = clean_cell(row[1]) if len(row) > 1 else ""
        values = [clean_cell(item) for item in row[2:]]
        if label == "电机型号" and values:
            case_names = values
        data[label] = {
            "unit": unit,
            "values": values,
        }
    if not case_names:
        max_values = max((len(item["values"]) for item in data.values()), default=0)
        case_names = [f"工况{i + 1}" for i in range(max_values)]
    return data, case_names, encoding


def numeric_series(data, label):
    if label not in data:
        return []
    return [to_float(value) for value in data[label]["values"]]


def value_with_unit(value, unit):
    if value in ("", None):
        return None
    return f"{value} {unit}".strip()


def build_parameter_table(data):
    records = []
    for label in KEY_ROWS:
        if label not in data:
            continue
        unit = data[label]["unit"]
        values = data[label]["values"]
        unique = unique_values(values)
        display_value = first_non_empty(unique)
        if not display_value:
            continue
        if len(unique) == 1:
            display = value_with_unit(display_value, unit)
        else:
            display = "; ".join(value_with_unit(value, unit) for value in unique if value_with_unit(value, unit))
        records.append({
            "name": label,
            "unit": unit,
            "value": display,
            "values": values,
        })
    return records


def calculate_phase_resistance(data, case_names):
    phase_current = numeric_series(data, "电机相电流有效值")
    slot_loss = numeric_series(data, "定子槽部铜耗")
    end_loss = numeric_series(data, "定子端部铜耗")
    direct_25c = numeric_series(data, "电枢绕组相电阻(25度)")
    direct_working = numeric_series(data, "电枢绕组相电阻")
    winding_temp = numeric_series(data, "绕组工作温度")

    count = max(len(case_names), len(phase_current), len(slot_loss), len(end_loss), len(direct_working), len(direct_25c))
    results = []
    for index in range(count):
        current = phase_current[index] if index < len(phase_current) else None
        slot = slot_loss[index] if index < len(slot_loss) else None
        end = end_loss[index] if index < len(end_loss) else None
        total_loss = None if slot is None or end is None else slot + end
        calculated = None
        if current not in (None, 0) and total_loss is not None:
            calculated = total_loss / (3 * current * current)
        direct = direct_working[index] if index < len(direct_working) else None
        error = None
        if calculated is not None and direct not in (None, 0):
            error = (calculated - direct) / direct
        results.append({
            "caseName": case_names[index] if index < len(case_names) else f"工况{index + 1}",
            "windingTemperatureC": winding_temp[index] if index < len(winding_temp) else None,
            "phaseResistance25Cohm": direct_25c[index] if index < len(direct_25c) else None,
            "phaseResistanceReportedOhm": direct,
            "phaseCurrentArms": current,
            "slotCopperLossW": slot,
            "endCopperLossW": end,
            "totalCopperLossW": total_loss,
            "phaseResistanceCalculatedOhm": calculated,
            "calculationFormula": "R_phase = (slotCopperLossW + endCopperLossW) / (3 * phaseCurrentArms^2)",
            "relativeDifferenceVsReported": error,
        })
    return results


def markdown_table(parameter_records, phase_resistance):
    lines = ["| 项目 | 数值 |", "|---|---|"]
    for record in parameter_records:
        if record["name"] in {"电机相电流有效值", "定子槽部铜耗", "定子端部铜耗"}:
            continue
        lines.append(f"| {record['name']} | {record['value']} |")
    lines.append("| 相电阻计算 | 见下表，按 `R_phase = (定子槽部铜耗 + 定子端部铜耗) / (3 * 相电流有效值^2)` 复算 |")
    lines.append("")
    lines.append("| 工况 | 绕组温度 °C | 报表相电阻 Ω | 复算相电阻 Ω | 25°C 相电阻 Ω |")
    lines.append("|---|---:|---:|---:|---:|")
    for item in phase_resistance:
        lines.append(
            "| {case} | {temp} | {reported} | {calculated} | {r25} |".format(
                case=item["caseName"],
                temp=format_number(item["windingTemperatureC"]),
                reported=format_number(item["phaseResistanceReportedOhm"]),
                calculated=format_number(item["phaseResistanceCalculatedOhm"]),
                r25=format_number(item["phaseResistance25Cohm"]),
            )
        )
    return "\n".join(lines) + "\n"


def format_number(value):
    if value is None:
        return ""
    if abs(value) >= 100:
        return f"{value:.3f}".rstrip("0").rstrip(".")
    return f"{value:.6g}"


def main():
    parser = argparse.ArgumentParser(description="Extract motor basic design information from a magnetic-circuit report CSV.")
    parser.add_argument("reportCsv", help="Magnetic-circuit report CSV, such as 工况报表结果.csv.")
    parser.add_argument("--output", help="Optional JSON output path.")
    parser.add_argument("--markdown-output", help="Optional Markdown table output path.")
    args = parser.parse_args()

    data, case_names, encoding = parse_report(args.reportCsv)
    parameter_records = build_parameter_table(data)
    phase_resistance = calculate_phase_resistance(data, case_names)
    result = {
        "sourceFile": str(Path(args.reportCsv).resolve()),
        "encoding": encoding,
        "caseNames": case_names,
        "machineBasicParameters": parameter_records,
        "phaseResistanceCalculation": phase_resistance,
        "notes": [
            "Use this output as deterministic support. The LLM should still decide which parameters are most useful for the report.",
            "Phase resistance must be included in both detailed and customer brief reports when magnetic-circuit report data is available.",
        ],
    }
    output_text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output_text, encoding="utf-8")
    if args.markdown_output:
        Path(args.markdown_output).write_text(markdown_table(parameter_records, phase_resistance), encoding="utf-8")
    print(output_text)


if __name__ == "__main__":
    main()
