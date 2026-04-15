# Examples

## Example User Request

> 使用 `外转子关节电机-试算.em3`，整理客户实测数据与仿真结果，输出一份 Markdown 试算报告。哈希目录映射如下：`25b41803d278` 为空载反电势有限元仿真，`afd8dedc2b9a` 为额定工况磁路法模型。

## Example `.em3` Hash Mapping

```json
{
  "25b41803d278": "空载反电势有限元仿真",
  "afd8dedc2b9a": "额定工况磁路法模型"
}
```

## Example File Interpretation

Given the mapping above:

- `25b41803d278/backef.ecsv` can be inspected as a back-EMF result candidate.
- `25b41803d278/V_定子绕组A.dat` can be inspected as a phase voltage or back-EMF waveform candidate within the no-load back-EMF context.
- `afd8dedc2b9a/attachments/额定功率-工况报表结果.csv` can be inspected as a rated operating-point magnetic-circuit report candidate.
- `客户提供资料/实测数据/*.pdf` can be inspected as measured test reports.
- `客户提供资料/实测数据/*示波器导出.csv` can be inspected as measured waveform data.
- `客户提供资料/设计数据/*.dwg` should be treated as customer design input, not directly parsed unless a CAD-reading capability is available.

## Example Report Opening

```markdown
# 外转子关节电机试算结果说明

## 1. 项目概述

本报告基于当前项目目录中已识别到的客户实测资料、设计输入资料以及仿真结果文件，对电机方案试算结果进行整理，并对关键性能指标进行实测与仿真对比。
```

## Example Motor Basic Parameter Section

When `afd8dedc2b9a/attachments/工况报表结果.csv` exists, include a section like this in the full report, normally as Chapter 3:

```markdown
## 3. 电机与仿真模型基本参数

![电机二维几何截面](figures/geometry-section.png)

本节参数来自磁路法工况报表 `工况报表结果.csv`。

| 参数 | 数值 | 单位 |
|---|---:|---|
| 极数 / 极对数 | 28 / 14 |  |
| 相数 | 3 |  |
| 转子位置 | 外转子 |  |
| 定子槽数 | 24 |  |
| 定子外径 / 内径 | 60 / 40 | mm |
| 转子外径 / 内径 | 67.1 / 60.6 | mm |
| 绕组形式 | 集中绕组 |  |
| 电枢绕组相电阻(25度) | 0.262365 | Ω |
| 绕组工作温度 | 75 / 115 | ℃ |
| 电枢绕组相电阻 | 0.31282 / 0.353183 | Ω |
| 磁钢材料 | N45SH_爱科 |  |
```

The actual report may use a more detailed grouped table generated from `extract_motor_design_info.py`.

## Example Conservative Conclusion

```markdown
基于当前已识别到的资料，空载反电势及额定工况相关结果可用于方案性能评估与设计校核参考。对于测试条件与仿真边界条件尚未完全一致的指标，建议结合具体测试电压、转速、控制方式及温度状态进一步校核。
```

## Example Incremental Update Request

> Use `$motor-report-skill` to update the existing report `report-output/motor-trial-report.md`. Existing state files are `report-output/report-state.json` and `report-output/evidence-ledger.json`. The original `25b41803d278` no-load back-EMF FEA simulation has been recalculated. Please re-read that hash folder, compare the changed back-EMF result with the existing measured data, and update only affected report sections.

## Example New Simulation Request

> Use `$motor-report-skill` to update the existing report. A new hash folder `abc123ef4567` was added and corresponds to cogging torque finite-element simulation. Please compare it with available measured data if comparable, otherwise add it as simulation-only supplemental evidence and update the report state package.

## Example State Package Paths

```text
report-output/
├── motor-trial-report.md
├── report-state.json
├── evidence-ledger.json
└── change-log.md
```

## Example Customer Brief Request

> Use `$motor-report-skill` to create a concise customer external brief from `report-output/motor-trial-report.md`. The brief should be suitable for sales to send to the customer, sound like a human engineering report, remove Skill/testing/internal evidence-ledger details, and make the software accuracy conclusion clearer. Save it as `report-output/customer-brief-report.md`.

## Example Customer Brief Conclusion

```markdown
综合额定点、最高效率点和最大输出功率点的对比结果，软件计算结果与实测数据整体吻合较好，可用于当前电机方案的性能评估和设计校核。对于空载效率和最大转矩点等边界敏感指标，差异主要受低功率效率计算敏感性、供电压降、驱动限流、温升和测试边界影响，不宜单独作为软件精度的主要评价依据。
```

## Example FEA Line Back-EMF Rule

When `25b41803d278/backef.ecsv` is selected for no-load back-EMF comparison and the result name does not explicitly indicate `线电压` or `线反电势`, treat the three plotted winding series as phase back-EMF. Convert them to `AB = A - B`, `BC = B - C`, and `CA = C - A`, then compare the converted line RMS values with customer oscilloscope or measured line back-EMF data.

## Example Scope Speed Estimation Request

> The oscilloscope CSV does not state the motor speed. Use `$motor-report-skill` to plot the measured line back-EMF waveform, read pole count from `afd8dedc2b9a/attachments/工况报表结果.csv`, estimate electrical frequency from adjacent positive peaks in the line-voltage waveform, calculate mechanical speed from pole pairs, and use that estimated speed when comparing measured and simulated no-load back-EMF.
