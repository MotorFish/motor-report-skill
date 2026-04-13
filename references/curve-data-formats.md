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

`plot_fea_curves.py` finds the numeric table and plots all numeric y columns against a likely x column such as time, order, length, angle, or speed.

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
