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

## Example Conservative Conclusion

```markdown
基于当前已识别到的资料，空载反电势及额定工况相关结果可用于方案性能评估与设计校核参考。对于测试条件与仿真边界条件尚未完全一致的指标，建议结合具体测试电压、转速、控制方式及温度状态进一步校核。
```
