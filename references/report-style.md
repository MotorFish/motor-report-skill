# Report Style

Use this reference before drafting customer-facing reports.

## Tone

Use neutral, conservative, engineering-oriented language.

Do not criticize customer design, customer tests, or model quality directly.

Avoid these phrases:

- 客户设计不合理
- 客户测试有问题
- 模型明显错误
- 仿真证明客户数据错误

## Suggested Sections

The LLM may adapt the structure, but a typical report includes:

1. 项目概述
2. 已识别资料来源
3. 电机与仿真模型基本参数
4. 实测数据来源说明
5. 仿真结果来源说明
6. 关键指标对比
7. 差异说明
8. 结论与适用性说明

When magnetic-circuit `工况报表结果.csv` exists, the `电机与仿真模型基本参数` section is required. Include the project geometry image in this section and use a detailed parameter table sourced from the report CSV. Include phase resistance whenever it exists in the source, and keep 25 C reference resistance separate from working-temperature resistance.

## Basic Parameter Section

The `电机与仿真模型基本参数` section is not a workpoint report excerpt.

Use single-value structural tables only:

| 参数 | 数值 | 单位 | 说明 |
|---|---:|---|---|

Each parameter row must have exactly one value. Do not create columns for `最大效率点`, `额定点`, `最大输出转矩`, `最大输出功率`, or other workpoints in this section. Do not write slash-joined multi-workpoint values in one cell.

Include motor/model structure, geometry, material, winding, magnetic steel, circuit type, control/modulation definition, and 25 C reference phase resistance when available.

Move operating/result quantities to later sections: running speed, load torque, output power target, current limit, sine-wave frequency, working temperature, working-temperature phase resistance, phase/line current, phase/line voltage, input/output power, efficiency, and losses.

## Key Comparison Section

Before writing numeric comparisons, state or imply the metric mapping used. Names may differ between measured and simulation data. For example, measured `T` or `输出转矩` can correspond to simulation `Tmech` or `机械转矩`; measured `Po` can correspond to simulation `Pmech`; measured `Pi` can correspond to simulation `Pin`; measured `EFF` can correspond to simulation `eff`.

Compare same control method and same physical boundary first. For PMSM magnetic-circuit reports, treat the calculation as motor-only FOC/SVPWM unless the source says otherwise, and compare it primarily with motor-only FOC measured data. Compare square-wave simulation or parametric-scan results primarily with motor-only square-wave measured data. Put whole-machine or motor-plus-reducer measured data after motor-only comparisons and label it as trend or transformed reference.

When a measured report has a feature-point table, use that table's row structure for the comparison. Keep measured rows such as no-load, maximum efficiency, rated, maximum output, and maximum torque. Preserve measured columns such as `U`, `I`, `Pi`, `T`, `n`, `Po`, and `Eff` whenever possible, and add simulation value and difference columns for each mapped metric. Do not replace measured feature rows with simulation-native feature points.

Use all evidence that is meaningfully comparable. Organize it by comparison boundary and confidence instead of dropping difficult rows:

- direct same-boundary comparisons
- comparisons after explicit speed/torque/voltage/back-EMF scaling
- trend comparisons where conditions differ but the engineering relationship is still useful
- items with unclear basis that should be discussed but not assigned a strict pass/fail judgment

When measured data is motor plus reducer or whole-machine output data, name it that way in headings and tables. Do not call it single-motor test data unless the source clearly says the measured shaft is the motor shaft. Do not use strict accuracy or validation wording for whole-machine efficiency, current, or limit output when the simulation is motor-only.

## Difference Wording

Small difference:

> 该指标仿真结果与实测较为接近，可作为当前方案性能评估的参考依据。

Medium difference:

> 该指标整体趋势与实测基本一致，数值上存在一定差异，可能与测试条件、温升状态、材料参数取值及损耗建模有关。

Large difference:

> 当前该指标仿真与实测存在较明显差异，建议结合具体测试边界条件、控制策略及温度状态进一步校核。

Condition mismatch:

> 当前实测与仿真的工况条件尚未完全对齐，因此该对比更适合作为趋势性参考，不宜作为严格数值校核结论。

Missing data:

> 当前资料中尚未明确检索到该项参数，后续可结合补充测试或设计输入进一步完善。

## Accuracy Claim

Prefer:

> 基于当前已识别到的设计参数、仿真结果与实测资料，软件计算结果与实测表现总体具有可比关系，可用于该类电机方案的性能评估与设计校核参考。

Avoid overclaiming:

- 完全一致
- 充分证明
- 绝对准确
- 无需进一步校核

## Tables

Use tables for:

- file sources
- machine parameters
- measured data
- simulation data
- key comparisons

Do not create overly precise tables from weak evidence.
