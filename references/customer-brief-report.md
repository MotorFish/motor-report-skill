# Customer Brief Report

Use this reference when the user asks for a concise report that sales or an engineer can send externally to a customer. The brief is derived from a full technical report and should read like a human engineering summary, not like a Skill test artifact.

## Goal

Create a shorter customer-facing Markdown report that:

- states the software accuracy conclusion clearly;
- preserves the most persuasive measured-vs-simulated evidence;
- explains non-ideal or mismatched data without sounding defensive;
- removes internal development, workflow, and evidence-ledger details;
- helps the recipient quickly understand whether the simulation result is credible for design evaluation.

## Default Output

Unless the user specifies another path, write the brief next to the full report:

```text
customer-brief-report.md
```

Reuse existing report figures only when they improve customer understanding. Do not regenerate figures unless the user asks or the full report is missing an important customer-facing figure.

## Source Priority

Read sources in this order:

1. Existing full report, usually `motor-trial-report.md`.
2. Final comparison tables and conclusions inside the full report.
3. Existing polished figures under `figures/`.
4. `report-state.json` and `evidence-ledger.json` only when the full report does not make a source clear enough.
5. Raw simulation or measured files only when the brief cannot be written reliably from existing report evidence.

## Keep

Keep information that directly supports customer decision-making:

- project objective and simulation/test scope;
- a compact motor/model basic-parameter section sourced from magnetic-circuit `工况报表结果.csv`;
- a short description of measured data and simulation data sources;
- geometry or representative performance figures, if already available;
- one compact key comparison table;
- clear statements of where software results agree well with measurement;
- short explanations for low-confidence or boundary-sensitive points;
- practical recommendations for further confirmation when needed.

## Remove

Remove or translate internal details:

- `Skill`, `LLM`, agent workflow, script names, validation prompts, or testing notes;
- hash-folder directory names unless the customer already uses them as part of project traceability;
- `report-state.json`, `evidence-ledger.json`, `change-log.md`, file digest, or incremental-update mechanics;
- interpolation-test files, negative-torque filtering tests, parser behavior, or plotting implementation details;
- long file inventories and source audit tables;
- tentative development wording such as "本次增量更新" unless the customer needs revision history.

## Suggested Structure

Adapt the structure to the case, but a concise external report usually works well as:

1. 项目说明
2. 电机与仿真模型基本参数
3. 数据来源与对比口径
4. 关键结果对比
5. 软件计算精度评价
6. 差异原因说明
7. 结论与建议

For a very short sales brief, use:

1. 项目背景
2. 电机与仿真模型基本参数
3. 核心对比结果
4. 结论

## Motor/Model Basic Parameters

Even in a concise customer brief, include a short `电机与仿真模型基本参数` section when a magnetic-circuit `工况报表结果.csv` exists. Put the geometry image in this section, then include a compact parameter table.

Use the magnetic-circuit report as the source, not the old full report text alone. Prefer a compact table with the most customer-useful fields:

- motor structure: outer rotor, pole/slot/phase count, pole pairs;
- key dimensions: stator/rotor diameters, stack length, air gap;
- winding and connection: winding type, circuit type, conductors per slot, wire diameter, slot fill;
- phase resistance: include the 25 C reference phase resistance in the basic-parameter table; discuss working-temperature phase resistance only with the relevant operating condition or result;
- magnet and material: magnet material, lamination material, magnet temperature;
- simulation setup: control algorithm, modulation mode, representative speed/torque/power inputs.

Do not include every slot-dimension row in the customer brief unless it helps the customer understand the result. The full internal report may include a more detailed grouped table.

Do not omit 25 C reference phase resistance in the customer brief. If working-temperature phase resistance is useful, keep it outside the structural table and tie it to the operating condition. Use compact wording such as:

```text
基础相电阻：0.262365 Ω @ 25 ℃。在高负载工况讨论中另行说明 75 ℃ / 115 ℃ 工作温度下的相电阻。
```

## Accuracy Conclusion

Make the conclusion clear and layered:

- Strong agreement: state that the software result agrees well with measured data for that metric and can support design evaluation.
- Trend agreement: state that trend and operating-point correspondence are consistent, while exact values are affected by test or model boundary differences.
- Boundary-sensitive metric: explain the likely reason briefly and avoid treating it as primary software accuracy evidence.
- Not comparable: say the data cannot be strictly compared under the current information, then explain what extra data would improve the comparison.

Prefer wording like:

```text
综合额定点、最高效率点和最大输出功率点的对比结果，软件计算结果与实测数据整体吻合较好，可用于该电机方案的性能评估和设计校核。
```

For points that do not match as well:

```text
最大转矩点受供电压降、驱动限流、温升和极限工况控制策略影响较大，因此该点更适合作为极限能力趋势参考，不宜作为软件精度的主要判断点。
```

For low-power efficiency:

```text
空载或低输出功率点的效率对机械损耗、采样精度和微小功率差异非常敏感，因此该点效率偏差不宜单独用于评价软件精度。
```

## Tone

Use confident but evidence-bound engineering language. The brief may be more decisive than the full technical report, but it must not overclaim.

Prefer:

- "吻合较好"
- "趋势一致"
- "可用于方案性能评估"
- "可作为设计校核依据"
- "该差异主要受测试边界和系统损耗口径影响"

Avoid:

- "完全一致"
- "仿真绝对准确"
- "客户测试有问题"
- "软件已经证明实测错误"
- "无需进一步验证"

## Handling System vs Motor-Only Differences

When measured data is from a motor + gearbox system and simulation is motor-side:

- clearly state the difference in one short paragraph;
- compare power, speed/torque correspondence, and trend first;
- avoid strict current, voltage, or efficiency judgment unless conversion assumptions are available;
- explain gearbox loss, controller efficiency, temperature, and test boundary as possible causes.

When measured data is single-motor and simulation is the same drive mode:

- give a stronger accuracy statement for matched operating points;
- identify any outlier points and explain why they are less representative;
- use the matched rated, maximum-efficiency, and maximum-output points as primary evidence when available.

## Figures

Use only customer-meaningful figures:

- geometry section image;
- measured waveform or measured performance curve;
- simulated performance curve;
- final comparison figure.

Avoid figures that mainly prove internal tooling behavior:

- parser/debug outputs;
- interpolation-test figures;
- evidence-ledger diagrams;
- duplicated charts that make the brief feel padded.

## Length

Aim for 2 to 5 pages in Markdown form. Keep tables compact. If the full report has many sections, collapse them into a few customer-readable conclusions.

## Final Check

Before finishing, check that:

- the brief can stand alone without the full technical report;
- the conclusion says clearly whether the software result is accurate enough for design evaluation;
- every limitation is paired with a practical reason or next-step suggestion;
- no internal Skill development or test artifacts remain in the customer-facing body.
