# Curve Data Formats

Use this reference when plotting motor report figures.

## Scope CSV Example

The current oscilloscope example has metadata in early columns and the actual sample pair in later columns:

```text
Record Length,2.50E+03,,-0.0125,9.6
Sample Interval,1.00E-05,,-0.01249,9.8
...
,,,-0.01247,10
```

For this file, column 4 is time and column 5 is voltage. Other oscilloscopes may use completely different layouts. Treat `plot_scope_waveform.py` as an example parser, not a universal parser.

When the oscilloscope export does not state motor speed, estimate speed only if the waveform is a line-voltage or line back-EMF sequence and pole pairs are known:

- Read pole pairs directly if a report row contains `极对数`.
- Otherwise read `极数` from a magnetic-circuit report such as `工况报表结果.csv` and use `极对数 = 极数 / 2`.
- Find adjacent positive maxima in the line-voltage sequence; the median interval is the electrical period.
- Calculate `electricalFrequencyHz = 1 / electricalPeriodSec`.
- Calculate `mechanicalSpeedRpm = electricalFrequencyHz / polePairs * 60`.
- Record the peak times, period, pole-pair source, and assumption in evidence. If the waveform has strong noise, unclear repeated peaks, or is not line voltage, state that the estimate is unreliable and do not use it as a hard test condition.

Use `plot_scope_waveform.py <scope.csv> --output <png> --motor-report-csv <工况报表结果.csv>` to read pole count from a magnetic-circuit report. Use `--pole-pairs` or `--pole-count` only when the report source is unavailable or the user explicitly provides the value.

## FEA CSV/ECSV

FEA result `.ecsv` files are CSV-like text. They may contain metadata rows before the actual header.

Examples:

```text
#codec=UTF-8
back-emf
定子绕组A,定子绕组B,定子绕组C
1
Time[sec],back-emf[volt],back-emf[volt],back-emf[volt]
0,0,0,0
```

```text
HOrder_of_定子绕组A
定子绕组A
true
Order[],Amplitude[volt]
0,0.000276204
```

`plot_fea_curves.py` finds the numeric table and plots numeric y columns against a likely x column such as time, order, length, angle, or speed.

For back-EMF or voltage waveform result files, apply line-voltage comparison rules:

- If the result name or series name does not clearly include a line-voltage marker such as `线_`, `线电压`, `线反电势`, `line voltage`, or `line-to-line`, assume the first three waveform series are phase back-EMF/phase voltage.
- Convert the first three phase series to line values before plotting: `AB = A - B`, `BC = B - C`, `CA = C - A`.
- Compare customer oscilloscope waveforms or customer-provided back-EMF RMS values against the converted line voltage/line back-EMF, not against phase voltage.
- If the file already clearly represents line voltage, do not convert it again.
- For no-load back-EMF RMS comparison at different speeds, scale by speed only when both speeds are known and the no-load linear speed relationship is appropriate; state the scaling assumption in the report.
- For time-domain FEA waveforms, identify the electrical period from adjacent positive maxima. Do not use the full data-sequence length as one period unless the file metadata explicitly says the sequence covers exactly one period.
- If adjacent peak detection indicates the sequence covers two periods, use one detected electrical period or an integer-period window for RMS and speed calculation.
- Record the peak times, detected period, period variation, cycle count, pole-pair source, and RMS basis in evidence when reporting FEA speed or RMS.

The script default is `--line-voltage-mode auto`. Use `--line-voltage-mode off` only when the report intentionally needs phase quantities, or `--line-voltage-mode force` when the file naming is ambiguous but engineering context confirms that conversion is needed. Pass `--motor-report-csv`, `--pole-pairs`, or `--pole-count` when the report should derive mechanical speed from the detected electrical period.

## Magnetic-Circuit External Characteristics CSV

`外特性仿真结果.csv` uses two header rows. The second row contains repeated pairs like:

```text
转速[转/分],输出转矩[牛米],转速[转/分],输入功率[千瓦],...
```

The script finds columns by metric names and plots true multiple y-axes. Default x-axis is speed. Use `--x-axis torque` only when a torque-axis external characteristic figure is explicitly requested.

## Parametric Scan JSON

`prmresult.json` stores input scan variables and output variables separately:

```json
{
  "caseresults": [{"values": [...]}],
  "inputvars": [{"varname": "rspeed", "values": [...]}],
  "outvars": [{"expr": "Pin", "name": "o_Pin"}]
}
```

`convert_prmresult.py` converts this into one CSV row per case:

- input variable columns such as `rspeed`
- output variable columns such as `Tmech`, `Pin`, `Pmech`, `eff`, `Udc`, `Idc`

When the measured report uses torque as the x-axis, use `Tmech` as the x-axis, filter out negative mechanical torque values by default, start the plot range at 0 torque, and interpolate other columns at measured torque feature points if needed.

When converting curve or feature-point data into comparison records, include condition fields whenever possible: speed, voltage, current, temperature, control mode, and voltage basis (`phase` or `line`). These fields allow `build_comparison.py` to classify candidates as comparable, condition-mismatched, unit-mismatched, or needing review.
