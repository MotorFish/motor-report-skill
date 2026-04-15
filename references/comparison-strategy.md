# Comparison Strategy

Use this reference before drafting `关键指标对比`.

## Match Control And Boundary First

Choose the primary comparison set by both control method and physical boundary.

Priority order:

1. Same control method, same motor-only boundary.
2. Same motor-only boundary, different but explainable control method.
3. Same control method after a clearly stated transformation such as speed scaling or phase-to-line voltage conversion.
4. Whole-machine or motor-plus-reducer measured data versus motor-only simulation as trend reference only.

For PMSM magnetic-circuit operating reports, treat the result as motor-only FOC/SVPWM calculation unless the source clearly says otherwise. Therefore, compare PMSM magnetic-circuit operating points primarily with motor-only FOC measured data when such data exists. Compare square-wave finite-element or parametric scan results primarily with motor-only square-wave measured data. Do not compare a square-wave measured table as the main strict benchmark for FOC magnetic-circuit results, or vice versa, unless the report explicitly labels the comparison as cross-control trend reference.

Most software simulation results in this workflow are motor-only results. Do not treat magnetic-circuit, FEA back-EMF, or parametric-scan results as reducer or whole-machine simulations unless the evidence explicitly contains a reducer/system model.

## Build The Metric Map First

Before calculating differences, create a metric correspondence map between measured fields and simulation fields. Do not require names to be identical. Confirm correspondence from metric meaning, unit, axis, control mode, boundary, source context, and value scale.

Common mappings:

| Standard metric | Measured names | Simulation names | Notes |
|---|---|---|---|
| Output torque | `T`, `输出转矩` | `Tmech`, `机械转矩`, `输出转矩`, `负载转矩` | Confirm motor shaft vs reducer output shaft. |
| Output power | `Po`, `输出功率` | `Pmech`, `机械功率`, `输出功率` | Confirm motor shaft vs whole-machine output. |
| Input power | `Pi`, `输入功率` | `Pin`, `输入功率` | Controller/system input and motor electromagnetic input may differ. |
| Efficiency | `Eff`, `EFF`, `效率` | `eff`, `效率` | Confirm denominator and system boundary. |
| Speed | `n`, `转速` | `rspeed`, `speed`, `运行转速` | Confirm motor speed vs reducer output speed. |
| DC current | `I`, `Idc`, `母线电流` | `Idc`, `母线电流` | Compare only when both sides are DC input current. |
| Phase/line current | `相电流`, `线电流` | `相电流有效值`, `线电流有效值` | Do not compare directly to DC bus current. |
| DC voltage | `U`, `Udc`, `母线电压` | `Udc`, `母线电压` | Compare only when both sides are DC bus voltage. |
| Phase/line voltage | `相电压`, `线电压` | `相电压`, `线电压` | Do not compare directly to DC bus voltage. |
| No-load back-EMF | `反电势`, `Back-EMF`, oscilloscope voltage | `backef`, `E0`, `反电势` | Confirm phase/line basis and speed scaling. |

Try to map every measured table column. If a measured field has no defensible simulation counterpart, keep the field in the comparison table and mark the simulation value as unavailable or basis-mismatched instead of silently dropping it.

## Preserve Measured Table Shape

When a measured report provides a feature-point table, use that measured table as the comparison skeleton.

Rules:

- Keep the measured feature points as rows, such as no-load, maximum efficiency, rated, maximum output, and maximum torque.
- Preserve the main measured field order where practical, such as `U`, `I/Idc`, `Pi`, `T`, `n`, `Po`, and `Eff`.
- For each mapped field, show measured value, simulation value, and difference.
- If simulation data is a curve or scan, interpolate at the measured feature point when appropriate.
- If interpolation is not possible, use the nearest simulation point only with a nearest-point note and condition delta.
- If no simulation counterpart exists, keep the measured value and state `no counterpart`, `not extracted`, or `basis mismatch`.

A useful feature-point comparison table can use compact paired columns, for example:

| Feature point | T measured/sim | n measured/sim | Pi measured/sim | Po measured/sim | Eff measured/sim | Difference notes |
|---|---:|---:|---:|---:|---:|---|

or detailed triplets:

| Feature point | T measured | T sim | T diff | n measured | n sim | n diff | ... |
|---|---:|---:|---:|---:|---:|---:|---|

Do not replace the measured feature-point rows with simulation-native feature points. Simulation-native maximum efficiency or maximum output points may be discussed, but they do not substitute for comparing each measured feature point.

## Use All Comparable Evidence

Make the comparison section detailed. Do not keep only the easiest one or two metrics when more evidence is readable and can be placed in a defensible boundary.

Classify each comparison as:

- `direct`: same metric, same control method, same motor/system boundary, same or closely aligned condition.
- `transformed`: comparison after an explicit transformation such as speed scaling, phase-to-line voltage conversion, or known shaft conversion.
- `trend`: conditions, control method, or boundary differ, but the trend or feature point still has engineering value.
- `not_judged`: metric is readable, but boundary, unit basis, control mode, or condition is too unclear for a numeric judgment.

Only `direct` and well-explained `transformed` rows should carry strong numeric conclusions.

## Boundary Naming

Name measured boundaries precisely:

- Use `单电机轴端实测` only when the source clearly measures the motor shaft.
- Use `电机+减速器整机测试` or `整机输出端测试` when the source includes reducer, joint module, gearbox, or output shaft data.
- Use `控制器/系统输入` when voltage/current/power are measured at the DC bus or controller input.

When comparing whole-machine measured data to motor-only simulation:

- Place it after same-control same-boundary motor-only comparisons.
- Title it as trend or transformed reference, not strict validation.
- State the assumed speed ratio before comparing speed or torque.
- Do not treat reducer efficiency as known unless the source provides it.
- Treat motor-side current/voltage and DC bus current/voltage as different measurement bases.
- Prefer mechanical output power and speed/torque relationships when the electrical boundary is unclear.
- Do not conclude that motor-only software strictly validates whole-machine efficiency, current, or limit output.

## Report Shape

For each comparison group, include:

- data sources, control method, and boundary labels
- metric correspondence table or a short mapping sentence
- feature-point comparison table preserving measured rows when available
- difference explanation
- usability judgment

The key comparison section is incomplete if a measured feature-point table exists but the report does not compare each measured feature point against the best available same-control simulation evidence.
