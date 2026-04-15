#!/usr/bin/env python
import argparse
import csv
import json
from pathlib import Path


ENCODINGS = ["utf-8-sig", "utf-8", "gb18030", "cp936", "latin-1"]


def read_text(path):
    last_error = None
    for encoding in ENCODINGS:
        try:
            return Path(path).read_text(encoding=encoding), encoding
        except UnicodeError as error:
            last_error = error
    return Path(path).read_text(encoding="utf-8", errors="replace"), f"utf-8-replace ({last_error})"


def read_table(path):
    text, encoding = read_text(path)
    suffix = Path(path).suffix.lower()
    if suffix == ".json":
        data = json.loads(text)
        if isinstance(data, list):
            return data, encoding
        if isinstance(data, dict):
            for key in ["rows", "data", "records", "featurePoints"]:
                if isinstance(data.get(key), list):
                    return data[key], encoding
        raise ValueError(f"JSON table must be a list or contain rows/data/records/featurePoints: {path}")
    return list(csv.DictReader(text.splitlines())), encoding


def to_float(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_pair(text):
    if "=" not in text:
        raise ValueError(f"Expected FIELD=FIELD mapping, got: {text}")
    left, right = text.split("=", 1)
    left = left.strip()
    right = right.strip()
    if not left or not right:
        raise ValueError(f"Expected non-empty FIELD=FIELD mapping, got: {text}")
    return left, right


def row_value(row, field):
    return row.get(field)


def numeric_row_value(row, field):
    return to_float(row_value(row, field))


def sorted_numeric_rows(rows, field):
    numeric = []
    for row in rows:
        value = numeric_row_value(row, field)
        if value is not None:
            numeric.append((value, row))
    numeric.sort(key=lambda item: item[0])
    return numeric


def nearest_row(rows_with_x, x_value):
    if not rows_with_x:
        return None, None
    best_x, best_row = min(rows_with_x, key=lambda item: abs(item[0] - x_value))
    return best_row, best_x


def interpolate_value(left, right, x_field, y_field, x_value):
    x0 = numeric_row_value(left, x_field)
    x1 = numeric_row_value(right, x_field)
    y0 = numeric_row_value(left, y_field)
    y1 = numeric_row_value(right, y_field)
    if None in (x0, x1, y0, y1) or x0 == x1:
        return None
    return y0 + (y1 - y0) * (x_value - x0) / (x1 - x0)


def interpolate_row(rows_with_x, x_field, x_value, metric_fields):
    if not rows_with_x:
        return {}, None, "no simulation x values"
    if x_value is None:
        return {}, None, "measured x missing"
    exact_matches = [(sim_x, row) for sim_x, row in rows_with_x if sim_x == x_value]
    if exact_matches:
        sim_x, row = exact_matches[0]
        return {field: numeric_row_value(row, field) for field in metric_fields}, sim_x, "exact"
    lower = None
    upper = None
    for sim_x, row in rows_with_x:
        if sim_x < x_value:
            lower = (sim_x, row)
        elif sim_x > x_value and upper is None:
            upper = (sim_x, row)
            break
    if lower and upper:
        values = {}
        for field in metric_fields:
            values[field] = interpolate_value(lower[1], upper[1], x_field, field, x_value)
        return values, x_value, f"linear interpolation between {lower[0]} and {upper[0]}"
    row, sim_x = nearest_row(rows_with_x, x_value)
    if row is None:
        return {}, None, "no simulation row"
    return {field: numeric_row_value(row, field) for field in metric_fields}, sim_x, "nearest endpoint"


def build_rows(measured_rows, simulation_rows, point_field, x_pair, mappings, mode):
    measured_x_field, simulation_x_field = x_pair
    simulation_metric_fields = sorted({simulation_x_field, *[right for _, right in mappings]})
    rows_with_x = sorted_numeric_rows(simulation_rows, simulation_x_field)
    output = []
    for index, measured in enumerate(measured_rows, start=1):
        measured_x = numeric_row_value(measured, measured_x_field)
        if mode == "nearest":
            sim_row, sim_x = nearest_row(rows_with_x, measured_x)
            sim_values = {field: numeric_row_value(sim_row, field) for field in simulation_metric_fields} if sim_row else {}
            match_note = "nearest" if sim_row else "no simulation row"
        else:
            sim_values, sim_x, match_note = interpolate_row(rows_with_x, simulation_x_field, measured_x, simulation_metric_fields)
        out = {
            "featurePoint": row_value(measured, point_field) if point_field else row_value(measured, "featurePoint") or row_value(measured, "特征点") or str(index),
            "matchByMeasuredField": measured_x_field,
            "matchBySimulationField": simulation_x_field,
            "matchedMeasuredX": measured_x,
            "matchedSimulationX": sim_x,
            "matchMethod": match_note,
        }
        for measured_field, simulation_field in mappings:
            measured_value = numeric_row_value(measured, measured_field)
            simulation_value = sim_values.get(simulation_field)
            diff = None
            diff_pct = None
            if measured_value is not None and simulation_value is not None:
                diff = simulation_value - measured_value
                if measured_value != 0:
                    diff_pct = diff / measured_value * 100
            label = measured_field
            out[f"{label}_measured"] = measured_value
            out[f"{label}_simulationField"] = simulation_field
            out[f"{label}_simulation"] = simulation_value
            out[f"{label}_diff"] = diff
            out[f"{label}_diffPercent"] = diff_pct
            if simulation_value is None:
                out[f"{label}_note"] = "no numeric simulation counterpart"
        output.append(out)
    return output


def write_csv(rows, path):
    fieldnames = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with Path(path).open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Build a feature-point measured/simulation comparison table while preserving measured report rows.")
    parser.add_argument("--measured", required=True, help="Measured feature-point CSV or JSON.")
    parser.add_argument("--simulation", required=True, help="Simulation curve/scan CSV or JSON.")
    parser.add_argument("--x", required=True, help="Match axis as measuredField=simulationField, for example T=Tmech.")
    parser.add_argument("--map", action="append", default=[], help="Metric mapping measuredField=simulationField. Repeat for each metric.")
    parser.add_argument("--point-field", help="Measured row label field, such as featurePoint or 特征点.")
    parser.add_argument("--mode", choices=["linear", "nearest"], default="linear", help="Use linear interpolation or nearest simulation point.")
    parser.add_argument("--output", required=True, help="Output comparison CSV.")
    parser.add_argument("--json-output", help="Optional JSON output path.")
    args = parser.parse_args()

    measured_rows, measured_encoding = read_table(args.measured)
    simulation_rows, simulation_encoding = read_table(args.simulation)
    x_pair = parse_pair(args.x)
    mappings = [parse_pair(item) for item in args.map]
    if not mappings:
        raise ValueError("At least one --map measuredField=simulationField mapping is required.")
    rows = build_rows(measured_rows, simulation_rows, args.point_field, x_pair, mappings, args.mode)
    write_csv(rows, args.output)
    result = {
        "measured": str(Path(args.measured).resolve()),
        "simulation": str(Path(args.simulation).resolve()),
        "measuredEncoding": measured_encoding,
        "simulationEncoding": simulation_encoding,
        "matchAxis": {"measured": x_pair[0], "simulation": x_pair[1]},
        "mappings": [{"measured": left, "simulation": right} for left, right in mappings],
        "mode": args.mode,
        "output": str(Path(args.output).resolve()),
        "rows": rows,
    }
    if args.json_output:
        Path(args.json_output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
