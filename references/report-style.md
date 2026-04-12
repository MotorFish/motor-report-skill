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
3. 电机基本参数
4. 实测数据来源说明
5. 仿真结果来源说明
6. 关键指标对比
7. 差异说明
8. 结论与适用性说明

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
