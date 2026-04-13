# motor-report-skill

`motor-report-skill` 是一个面向 Codex 的专业化 Skill，用于把已经完成计算的电机试算项目整理成“实测数据与仿真结果对比”工作流。它不负责建模、打开电磁仿真软件或运行求解器，而是帮助 Codex 在已有项目资料中识别数据来源、提取关键指标、判断可比工况，并起草面向客户的 Markdown 技术报告。

本仓库中的 `README.md` 面向 GitHub 读者和维护者；真正被 Codex 触发和执行时读取的是 [`SKILL.md`](./SKILL.md) 以及其中按需引用的 `references/`、`scripts/` 资源。

## 适用场景

该 Skill 适用于以下类型的电机试算后处理任务：

- `.em3` 项目目录分析；
- 客户实测报告、测试曲线、示波器导出数据的识别与整理；
- 有限元仿真结果、磁路法结果、参数化扫描结果、外特性曲线和工况报表的读取；
- 反电势、转矩、转速、电流、电压、功率、效率和损耗等指标的对比；
- 生成客户可读的工程化 Markdown 报告草稿；
- 基于已有报告、状态文件和证据台账进行增量更新；
- 生成报告配套图表，包括几何模型图、示波器波形、有限元曲线、磁路法外特性曲线和参数扫描性能曲线；
- 在测试条件、仿真条件或口径不完全一致时，给出保守、清晰的差异说明。

不适用于：

- 操作电磁仿真软件 GUI；
- 新建或修改电机模型；
- 运行有限元或磁路法求解；
- 替代工程师对设计方案做最终判断。

## 设计原则

该 Skill 采用“LLM 负责语义判断，脚本负责确定性辅助”的方式组织：

- Codex 负责判断文件用途、数据可信度、工况是否可比、报告如何表述；
- 脚本负责扫描项目、读取常见表格/文本文件、提取 PDF 文本、标准化指标、计算简单差异、维护报告状态和绘制常见数据曲线；
- 对缺失信息、弱证据和不一致工况保持保守，不强行制造精确结论；
- 对 `.em3` 中哈希命名的仿真目录，必须先获得人工提供的目录含义映射，再解释仿真结果。
- 对报告文字、分析逻辑和新增章节，优先由 LLM 基于证据直接撰写，不使用固定模板或固定写作脚本拼接。

## 仓库结构

```text
motor-report-skill/
├── README.md
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── curve-data-formats.md
│   ├── data-models.md
│   ├── examples.md
│   ├── extraction-strategy.md
│   ├── figure-generation.md
│   ├── incremental-update.md
│   ├── report-style.md
│   └── workflow.md
└── scripts/
    ├── build_comparison.py
    ├── convert_prmresult.py
    ├── create_report_state.py
    ├── diff_project_state.py
    ├── extract_pdf_text.py
    ├── normalize_metrics.py
    ├── plot_fea_curves.py
    ├── plot_mc_external_characteristics.py
    ├── plot_parametric_performance.py
    ├── plot_scope_waveform.py
    ├── read_tabular.py
    ├── resolve_report_figures.py
    ├── scan_project.py
    └── update_evidence_ledger.py
```

### 核心文件说明

| 路径 | 作用 |
|---|---|
| `SKILL.md` | Skill 的主入口，包含触发描述、核心流程和资源导航。 |
| `agents/openai.yaml` | 面向 Codex UI 的展示元数据。 |
| `references/workflow.md` | 完整报告工作流说明。 |
| `references/incremental-update.md` | 已有报告增量更新流程、状态文件和证据复用策略。 |
| `references/extraction-strategy.md` | 数据源识别、实测资料处理和仿真结果解释策略。 |
| `references/data-models.md` | 项目信息、实测数据、仿真数据和对比行的数据结构建议。 |
| `references/report-style.md` | 客户报告的语气、差异说明和结论表达约束。 |
| `references/figure-generation.md` | 报告图表生成、插入和证据登记规则。 |
| `references/curve-data-formats.md` | 示波器、有限元、磁路法外特性、参数扫描等曲线数据格式说明。 |
| `references/examples.md` | 示例请求、哈希目录映射和输出形态参考。 |
| `scripts/scan_project.py` | 扫描项目目录并生成文件索引。 |
| `scripts/read_tabular.py` | 读取 CSV、ECSV、DAT、TXT、JSON、XLSX 等表格/文本类文件摘要。 |
| `scripts/extract_pdf_text.py` | 在本地可用 PDF 库存在时提取 PDF 文本。 |
| `scripts/normalize_metrics.py` | 对已提取指标做名称、数值和单位标准化辅助。 |
| `scripts/build_comparison.py` | 对已整理的实测和仿真记录生成简单对比行。 |
| `scripts/create_report_state.py` | 生成 `report-state.json`、`evidence-ledger.json` 和 `change-log.md`。 |
| `scripts/diff_project_state.py` | 基于证据台账识别新增、修改、删除或未变化的项目文件。 |
| `scripts/update_evidence_ledger.py` | 将新增或更新的证据记录合并进证据台账。 |
| `scripts/resolve_report_figures.py` | 将 `.em3` 项目中的几何模型图等报告资产复制到图表目录。 |
| `scripts/plot_scope_waveform.py` | 按当前示波器 CSV 示例格式绘制采样波形；其他格式由 LLM 现场适配。 |
| `scripts/plot_fea_curves.py` | 绘制由 LLM 选择的有限元 CSV/ECSV 曲线结果，不限定固定文件名。 |
| `scripts/plot_mc_external_characteristics.py` | 绘制永磁同步电机磁路法外特性五轴图，默认以转速为横轴。 |
| `scripts/convert_prmresult.py` | 将参数化扫描 `prmresult.json` 转换为 CSV。 |
| `scripts/plot_parametric_performance.py` | 绘制参数扫描性能多轴图，默认以输出机械转矩为横轴并滤除负转矩数据。 |

## 安装方式

将本仓库放入 Codex 可发现的 Skills 目录，例如：

```powershell
$env:CODEX_HOME = "$HOME\.codex"
git clone <repo-url> "$env:CODEX_HOME\skills\motor-report-skill"
```

如果已经在其他位置维护本仓库，也可以将仓库复制或同步到：

```text
%CODEX_HOME%\skills\motor-report-skill
```

安装后，Codex 会通过 `SKILL.md` frontmatter 中的 `name` 和 `description` 判断何时触发该 Skill。

## 使用方式

用户请求中可以直接说明使用该 Skill，并提供待分析项目路径。例如：

```text
Use $motor-report-skill to analyze this project:
D:\Projects\example.em3

Hash folder mapping:
25b41803d278 = 空载反电势有限元仿真
afd8dedc2b9a = 额定工况磁路法模型

Please identify measured data, simulation result sources, compare key indicators, and draft a customer-facing Markdown report.
```

当输入包含 `.em3` 项目时，请同时提供哈希目录映射。该映射用于说明每个哈希目录对应的仿真任务，例如“空载反电势有限元仿真”“额定工况磁路法模型”等。缺少该映射时，Skill 会暂停仿真语义解释，避免把哈希目录误判为具体仿真内容。

对于已有报告的增量更新，可以说明新增或变化的哈希目录、变化的结果文件或新增的实测资料。例如：

```text
Use $motor-report-skill to incrementally update the existing report:
D:\Projects\example.em3\report-output

Project root:
D:\Projects\example.em3

Hash folder mapping:
25b41803d278 = 空载反电势有限元仿真
afd8dedc2b9a = 额定工况及扩展工况磁路法模型

Change:
afd8dedc2b9a\attachments\工况报表结果.csv 新增了最大转矩、最大输出功率、最高效率点。

Please reuse unchanged measured data and existing report sections, update only affected comparisons, figures, and conclusions.
```

对于图表功能，可以要求 Skill 生成并插入报告图表。有限元曲线由 Codex 根据“哈希目录含义 + 报告目标 + 文件内容”自主选择，不要求用户预先列出固定文件名。

## 输出内容

典型输出包括：

- 已识别的客户实测资料；
- 已识别的仿真结果来源；
- 电机基本参数摘要；
- 几何模型图、实测波形图、仿真曲线图或外特性图等报告配图；
- 实测数据和仿真数据的关键指标；
- 可比工况下的差异表；
- 对不一致工况、缺失条件和口径差异的说明；
- 面向客户的 Markdown 技术报告草稿；
- 用于后续增量更新的 `report-state.json`、`evidence-ledger.json`、`change-log.md`。

报告语言应保持中性、工程化和保守，不将测试或模型简单判定为“错误”，也不在证据不足时做过度结论。

## 本地验证

修改 `SKILL.md` 或资源文件后，可使用 `skill-creator` 提供的校验脚本检查基本格式：

```powershell
python C:\Users\Yang\.codex\skills\.system\skill-creator\scripts\quick_validate.py .
```

如果只修改 README，一般不影响 Codex 运行时行为；仍建议在发布前至少检查：

- `SKILL.md` frontmatter 是否只有 `name` 和 `description`；
- `description` 是否准确描述触发条件；
- `references/` 中被 `SKILL.md` 引用的文件是否存在；
- `scripts/` 中脚本是否能在目标环境中运行。

## 维护约定

- 将运行时关键指令写入 `SKILL.md`，不要只写在 README 中；
- 将详细参考资料放入 `references/`，并在 `SKILL.md` 中说明何时读取；
- 将可重复、确定性的处理逻辑放入 `scripts/`，但不要把报告撰写、工程判断和图文分析固化为脚本；
- 新增图表脚本时，应让 LLM 保留选择数据源、判断曲线意义和解释差异的主动权；
- 涉及 `.em3` 哈希目录时，必须继续要求用户提供“哈希目录名到仿真内容”的映射；
- 涉及增量更新时，应维护报告状态、证据台账和变更日志，避免无必要地重写整篇报告；
- 不在 Skill 中保存客户敏感项目数据或具体交付报告；
- 示例内容应尽量脱敏，只保留能说明工作流的必要信息。

## 数据与保密

该 Skill 常用于处理客户测试报告、设计图纸、仿真结果和项目交付材料。使用或发布仓库时，请确保仓库中不包含未经授权公开的客户原始资料、项目报告、图纸、波形数据或其他敏感文件。
