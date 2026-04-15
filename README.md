# motor-report-skill

`motor-report-skill` 是一个面向 Codex 的专业化 Skill，用于把已经完成计算的电机试算项目整理成“实测数据与仿真结果对比”工作流。它不负责建模、打开电磁仿真软件或运行求解器，而是帮助 Codex 在已有项目资料中识别数据来源、提取关键指标、判断可比工况，并起草面向客户的 Markdown 技术报告、增量更新已有报告，或从完整技术报告生成销售/客户可外发的精简报告。

本仓库中的 `README.md` 面向 GitHub 读者和维护者；真正被 Codex 触发和执行时读取的是 [`SKILL.md`](./SKILL.md) 以及其中按需引用的 `references/`、`scripts/` 资源。

## 当前修改概览

### Summary

当前修改把 Skill 从“生成/更新电机试算报告”的基础能力，扩展为更完整的报告后处理系统：新增客户外发精简报告模式，强化电机与仿真模型基本参数章节，补齐特征点对齐和可比性判断规则，增强有限元与示波器波形的线电压/周期/转速处理，并让增量更新默认只检查证据台账引用的源文件，避免把报告生成物再次纳入证据池。

### Description

延续“LLM 负责语义判断，脚本负责确定性辅助”的设计。`SKILL.md` 负责触发条件、硬性门禁和流程导航；`references/` 拆分为按需读取的渐进披露文档；`scripts/` 提供扫描、读取、归一化、比较、图表、状态维护等可重复步骤。报告文字、工程判断、差异解释、章节组织和客户可读表述仍由 LLM 基于证据自主撰写，不由固定模板脚本拼接。

### 修改日志

- 扩展 `SKILL.md` 触发描述：支持首版报告、增量更新、客户外发精简报告三种模式。
- 新增客户精简报告工作流：要求删除内部 Skill、脚本、证据台账和哈希目录管理细节，保留客户能理解和决策的结论。
- 强化 `电机与仿真模型基本参数`：当磁路法 `工况报表结果.csv` 存在时，完整报告和客户精简报告都必须包含该章节，并优先展示 `geo2d.png` 几何截面图和 25 ℃ 基准相电阻。
- 新增/扩展 `references/comparison-strategy.md` 与 `references/customer-brief-report.md`：分别约束关键指标对比和客户外发报告写法。
- 扩展 `references/workflow.md`、`references/data-models.md`、`references/report-style.md`、`references/figure-generation.md`、`references/curve-data-formats.md` 和 `references/examples.md`：补齐边界命名、特征点表保形、线电压转换、周期识别、增量更新范围和示例。
- 增强 `scripts/build_comparison.py`：增加单位转换、速度/电压/电流/温度/控制方式/相线电压口径检查，并输出 `comparabilityStatus`。
- 新增 `scripts/build_feature_point_table.py`：按实测特征点表保留行结构，将仿真曲线/扫描结果插值或就近匹配到实测点。
- 新增 `scripts/extract_motor_design_info.py`：从磁路法报表中提取单值结构/模型参数表，并把工况变化行放入 `skippedRows` 供后续章节使用。
- 新增 `scripts/extract_machine_basic_info.py`：从磁路法报表抽取更宽泛的电机基础信息，并复算相电阻，适合作为分析辅助。
- 增强 `scripts/plot_fea_curves.py`：对疑似三相反电势/电压波形自动转换为 AB/BC/CA 线电压/线反电势，并基于相邻正峰识别电周期、RMS 窗口和可选机械转速。
- 增强 `scripts/plot_scope_waveform.py`：在示波器波形缺少转速时，可从线电压相邻正峰和极对数估计机械转速。
- 增强 `scripts/diff_project_state.py` 与 `scripts/scan_project.py`：默认忽略报告输出、状态文件、图表、缓存和 `.git`，增量更新时默认只比较证据源文件，可显式开启新增证据扫描。
- 新增 `.gitignore`：忽略 Python 缓存、测试缓存、报告输出、图表、状态包和临时日志文件。

## 适用场景

该 Skill 适用于以下类型的电机试算后处理任务：

- `.em3` 项目目录分析；
- 客户实测报告、测试曲线、示波器导出数据的识别与整理；
- 有限元仿真结果、磁路法结果、参数化扫描结果、外特性曲线和工况报表的读取；
- 从磁路法工况报表中提取电机与仿真模型基本参数，并在报告中配合几何截面图展示；
- 反电势、转矩、转速、电流、电压、功率、效率和损耗等指标的对比；
- 生成客户可读的工程化 Markdown 技术报告草稿；
- 基于已有报告、状态文件和证据台账进行增量更新；
- 基于完整技术报告补充输出销售或客户可外发的精简报告；
- 生成报告配套图表，包括几何模型图、示波器波形、有限元曲线、磁路法外特性曲线和参数扫描性能曲线；
- 在测试条件、仿真条件、控制方式或系统边界不完全一致时，给出保守、清晰的差异说明。

不适用于：

- 操作电磁仿真软件 GUI；
- 新建或修改电机模型；
- 运行有限元或磁路法求解；
- 读取大型网格、场文件或二进制求解中间文件并替代专业后处理器；
- 替代工程师对设计方案做最终判断。

## 实现方法

### 分层加载

Skill 采用渐进披露结构，尽量让 Codex 只读取当前任务真正需要的信息：

1. `SKILL.md` frontmatter：始终可见，用 `name` 和 `description` 判断何时触发。
2. `SKILL.md` 正文：触发后读取，包含硬性门禁、三种工作模式、核心流程和资源导航。
3. `references/*.md`：按任务阶段读取，例如完整报告读 `workflow.md`，关键对比读 `comparison-strategy.md`，客户外发报告读 `customer-brief-report.md`。
4. `scripts/*.py`：不必全部载入上下文，Codex 在需要确定性处理时运行脚本，得到 JSON、CSV、Markdown 表格或 PNG 图表，再由 LLM 判断如何写入报告。

### LLM 与脚本分工

LLM 自主负责：

- 判断文件用途、数据来源可信度和工况是否可比；
- 根据 `.em3` 哈希目录映射解释仿真任务语义；
- 建立实测字段与仿真字段之间的指标映射；
- 判断单电机、整机、减速器输出端、控制器输入等边界差异；
- 选择应绘制和应引用的图表；
- 撰写报告章节、差异解释、结论、客户外发摘要和后续建议；
- 在证据不足时保留不确定性，而不是编造数值或结论。

脚本确定性辅助：

- 扫描项目、读取表格/PDF/JSON；
- 标准化常见指标名、数值和单位；
- 从磁路法报表提取结构/模型基础参数；
- 生成候选对比行、特征点插值/就近匹配表；
- 复制几何图、绘制示波器/有限元/磁路法/参数扫描图；
- 创建和更新 `report-state.json`、`evidence-ledger.json`、`change-log.md`。

### `.em3` 哈希目录门禁

如果输入包含 `.em3` 项目，Codex 必须先获得用户提供的“哈希目录名到仿真内容”的映射，例如：

```text
25b41803d278 = 空载反电势有限元仿真
afd8dedc2b9a = 额定工况磁路法模型
```

缺少该映射时，Skill 允许扫描文件和识别客户资料，但不能把哈希目录自行解释为某个仿真任务。拿到映射后，Codex 再结合文件名、表头、单位、邻近文件和内容判断具体结果文件对应转矩、电压、电流、反电势、损耗、转速、效率等指标。

### 报告状态与增量更新

首版报告完成后，建议在报告目录旁保存：

```text
report-output/
├── motor-trial-report.md
├── report-state.json
├── evidence-ledger.json
├── change-log.md
└── figures/
```

`report-state.json` 保存结构化项目上下文、已提取数据、对比行、章节和历史；`evidence-ledger.json` 保存证据源文件、哈希、修改时间、派生图表和用途；`change-log.md` 记录人可读的更新历史。增量更新优先复用未变化的证据，只重读新增或变化的源文件，并只修改受影响的报告段落、表格、图和结论。

## 仓库结构

```text
motor-report-skill/
├── README.md
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── comparison-strategy.md
│   ├── curve-data-formats.md
│   ├── customer-brief-report.md
│   ├── data-models.md
│   ├── examples.md
│   ├── extraction-strategy.md
│   ├── figure-generation.md
│   ├── incremental-update.md
│   ├── report-style.md
│   └── workflow.md
└── scripts/
    ├── build_comparison.py
    ├── build_feature_point_table.py
    ├── convert_prmresult.py
    ├── create_report_state.py
    ├── diff_project_state.py
    ├── extract_machine_basic_info.py
    ├── extract_motor_design_info.py
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

## 渐进披露参考文档

| 文档 | 何时读取 | 主要内容 |
|---|---|---|
| `references/workflow.md` | 首版完整报告或需要梳理端到端流程时 | 任务框定、`.em3` 哈希映射门禁、文件索引、证据优先级、基础参数章节、比较上下文、报告撰写、状态包创建和交付说明。 |
| `references/extraction-strategy.md` | 判断文件是否为实测、仿真、设计输入或不确定资料时 | 文件理解策略、实测资料线索、仿真结果线索、设计资料使用方式、文件类型读取方式和置信度分级。 |
| `references/data-models.md` | 构造结构化上下文、证据台账或增量更新状态时 | `ProjectMeta`、`FileRecord`、`MachineBasicInfo`、`MeasuredDatum`、`SimulationDatum`、`ComparisonCandidate`、`ReportState`、`EvidenceRecord` 等建议结构。 |
| `references/comparison-strategy.md` | 撰写或修订 `关键指标对比` 前 | 先匹配控制方式和物理边界，再建立指标映射；保留实测特征点表结构；区分 direct、transformed、trend、not_judged；避免把整机测试当作单电机严格验证。 |
| `references/report-style.md` | 撰写完整客户技术报告前 | 报告语气、建议章节、基础参数章节规则、关键对比写法、差异话术、准确性声明和表格使用约束。 |
| `references/customer-brief-report.md` | 输出销售/客户外发精简报告时 | 精简报告目标、来源优先级、应保留/删除的信息、推荐结构、基础参数简表、精度评价、系统边界差异和最终检查。 |
| `references/figure-generation.md` | 生成或更新报告图表时 | `figures/` 目录、几何图放置、示波器波形、有限元曲线、磁路法外特性、参数扫描图和证据台账登记规则。 |
| `references/curve-data-formats.md` | 绘制或解释曲线文件时 | 示波器 CSV 示例、转速估算、FEA CSV/ECSV 解析、三相相量到线量转换、磁路法外特性 CSV、`prmresult.json` 转换和条件字段记录。 |
| `references/incremental-update.md` | 用户要求已有报告更新、补仿真或换实测数据时 | 状态包输入、更新范围判断、证据源 diff、各类变化的局部编辑规则、无状态包兜底和 `change-log.md` 格式。 |
| `references/examples.md` | 需要示例请求、哈希映射或输出形态时 | 用户请求示例、`.em3` 映射示例、文件解释示例、报告开头、基础参数章节、增量更新请求、客户精简报告请求、FEA 线反电势规则和示波器转速估算请求。 |

## Python 脚本职责

| 脚本 | 输入 | 输出 | 作用与边界 |
|---|---|---|---|
| `scripts/scan_project.py` | 项目根目录 | JSON 文件索引 | 扫描文件路径、大小、扩展名、哈希目录候选和低置信度分类提示。默认忽略 `.git`、`__pycache__`、`report-output`、`figures`、状态文件和变更日志；分类结果只是线索，不是最终语义判断。 |
| `scripts/read_tabular.py` | CSV、ECSV、DAT、TXT、JSON、XLSX/XLSM 等表格或文本文件 | JSON 摘要 | 尝试多种编码，识别分隔符，返回表头候选、样例行、文本预览或 Excel sheet 样例。它只暴露内容结构，不判断指标意义。 |
| `scripts/extract_pdf_text.py` | PDF 文件 | JSON 文本/表格抽取结果 | 优先用 `pypdf`，再尝试 `pdfplumber`。依赖库不可用或抽取失败时返回 warning，LLM 需要说明限制并改用其他证据。 |
| `scripts/normalize_metrics.py` | 含指标记录的 JSON | 标准化 JSON | 给常见电机指标增加 `normalizedMetricName`、`numericValue`、`normalizedUnit`，支持反电势、转矩、电流、电压、转速、效率、功率、铁耗、铜耗、磁链等。 |
| `scripts/build_comparison.py` | 包含 `measuredData` 与 `simulationData` 的 JSON | `comparisonCandidates` 与可直接候选的 `comparisonRows` | 做基础单位转换和条件一致性检查，输出 `comparable`、`condition_mismatch`、`unit_mismatch`、`needs_review`。结果是候选过滤器，最终可比性仍由 LLM 审核。 |
| `scripts/build_feature_point_table.py` | 实测特征点 CSV/JSON、仿真曲线或扫描 CSV/JSON、匹配轴和字段映射 | 对比 CSV，可选 JSON | 保留实测报告的特征点行结构，把仿真值线性插值或就近匹配到实测点，并计算差值/百分比差异。适合 `T=Tmech`、`n=speed` 等特征点对齐场景。 |
| `scripts/extract_motor_design_info.py` | 磁路法 `工况报表结果.csv` | 单值结构参数 Markdown/JSON，可选工况审计表 | 提取电机与仿真模型结构参数，分组输出模型概况、定子铁芯、绕组、基础电气参数、转子磁钢等。只把单一结构值放进报告基础参数表；随工况变化的速度、转矩、温度、电流、效率、损耗等放入 `skippedRows`，供其他章节使用。 |
| `scripts/extract_machine_basic_info.py` | 磁路法 `工况报表结果.csv` | JSON，可选 Markdown | 抽取更宽泛的基础信息，并基于铜耗和相电流复算相电阻。适合作为相电阻核对或旧式基础信息整理辅助；正式基础参数章节优先用 `extract_motor_design_info.py`。 |
| `scripts/resolve_report_figures.py` | `.em3` 项目根目录 | 复制后的几何图和 figure evidence JSON | 查找根目录 `geo2d.png`，缺失时查找一级哈希目录 `geo2d.png`，复制到报告 `figures/` 并生成证据记录。 |
| `scripts/plot_scope_waveform.py` | 示波器 CSV | PNG 图和 figure evidence JSON | 面向当前示波器 CSV 示例格式的绘图脚本。自动选择最像时间/电压的数值列；可从磁路法报表、`--pole-pairs` 或 `--pole-count` 获得极对数，再用相邻正峰估算电频率和机械转速。其他示波器格式需 LLM 现场适配。 |
| `scripts/plot_fea_curves.py` | LLM 选择的 FEA CSV/ECSV 曲线文件 | PNG 图和 figure evidence JSON | 识别数值表、选择 x 轴、绘制曲线或频谱。对疑似三相反电势/电压波形默认把前三相转换为 AB/BC/CA 线值，并基于相邻正峰估算电周期、RMS 窗口和可选转速。不是固定文件名扫描器，文件选择必须由 LLM 根据哈希映射和报告目标决定。 |
| `scripts/plot_mc_external_characteristics.py` | 磁路法 `外特性仿真结果.csv` | 多 y 轴 PNG 和 evidence JSON | 绘制永磁同步电机磁路法外特性，默认以转速为横轴，也可用输出转矩为横轴；通常包含输出转矩/转速、输出功率、输入功率、效率、功率因数等。 |
| `scripts/convert_prmresult.py` | 参数化扫描 `prmresult.json` | CSV 和可选元数据 JSON | 把 `inputvars`、`outvars`、`caseresults` 展平为一行一个 case 的 CSV，供图表、插值和特征点对比使用。 |
| `scripts/plot_parametric_performance.py` | `convert_prmresult.py` 生成的 CSV | 多 y 轴 PNG，可选插值 CSV 和 evidence JSON | 默认以 `Tmech` 为横轴，过滤负转矩，绘制 `Pin`、`Pmech`、`eff`、`Udc`、`Idc`、`rspeed` 等列，并可在指定特征点插值。 |
| `scripts/create_report_state.py` | 结构化 report context JSON、报告路径、输出目录 | `report-state.json`、`evidence-ledger.json`、`change-log.md` | 为首版报告创建增量更新状态包，记录证据源文件、内容哈希、报告章节和历史。 |
| `scripts/diff_project_state.py` | 项目根目录、`evidence-ledger.json` | added/modified/deleted/unchanged JSON | 默认只比较证据台账中已引用的源文件，并忽略生成物；`--scan-added` 才全项目寻找新增非生成证据；`--hash-files` 可计算内容哈希。 |
| `scripts/update_evidence_ledger.py` | 旧证据台账、新证据 JSON | 更新后的台账和可选 changelog 条目 | 按 `evidenceId`、`relativePath` 或 `sourceFile` 合并/替换证据记录，可追加人可读更新日志。 |

## 能力边界

### 能识别和处理的实测数据

Skill 能处理的实测资料包括：

- PDF 测试报告：可在本地有 `pypdf` 或 `pdfplumber` 时抽取文本和部分表格；
- Excel 表格：`.xlsx`、`.xlsm` 在本地有 `openpyxl` 时可读取样例行；
- CSV/ECSV/DAT/TXT/JSON：可抽取表头、样例行、数值列和文本预览；
- 示波器 CSV：当前脚本可处理一种典型“前几列元数据、后几列时间/电压采样”的导出形式，并可在满足线电压/极对数条件时估算转速；
- 图片或截图：只有在当前 Codex 环境支持视觉读取时才可直接判断；否则只能使用文件名、路径和上下文；
- 用户在对话中直接给出的测试条件、数值和说明。

实测边界必须明确标注。若资料显示包含减速器、关节模组、整机输出端、控制器输入或系统级测试，报告中必须写成 `电机+减速器整机测试`、`整机输出端测试` 或类似边界，不能简化为单电机实测。

### 能识别和处理的仿真结果

Skill 能处理的仿真资料包括：

- `.em3` 项目结构，但必须先有用户提供的哈希目录映射；
- 有限元 CSV/ECSV/DAT/TXT 类结果，如 `backef`、`torque`、`voltage`、`current`、`speed`、`flux`、`pfe`、`pcu`、`coreloss` 等文件名或表头线索；
- 有限元反电势/电压波形或频谱，可识别时间、阶次、角度、长度、速度等常见横轴；
- 磁路法 `工况报表结果.csv`，用于提取结构参数、工况输入、运行结果、相电阻、效率、电流、电压、功率和损耗等；
- 磁路法 `外特性仿真结果.csv`，用于绘制外特性曲线；
- 参数化扫描 `prmresult.json`，可转换为 CSV 并绘制性能曲线；
- `.em3` 根目录或一级哈希目录中的 `geo2d.png` 几何截面图。

Skill 不会从哈希目录名本身推断仿真含义，不会读取大型网格/场文件作为默认证据，也不会在没有可读表格或曲线的情况下凭文件夹存在就制造指标。

### 能自主撰写的内容

按照 `SKILL.md` 和 `references/` 的规则，LLM 可以自主撰写：

- 项目概述、资料来源说明和数据识别说明；
- `电机与仿真模型基本参数` 章节，包括几何图引用和结构参数表；
- 实测数据与仿真结果来源说明；
- 指标映射说明，例如 `T` 到 `Tmech`、`Po` 到 `Pmech`、`Eff` 到 `eff`；
- 关键指标对比表、特征点对比表和差异说明；
- 对控制方式、相/线电压口径、单电机/整机边界、温度和工况不一致的解释；
- 保守结论、适用性说明和后续建议；
- 已有报告的局部增量更新内容；
- 销售或客户可外发的精简 Markdown 报告。

LLM 不应自主撰写：

- 未被证据支持的具体数值；
- 把不一致工况写成严格验证结论；
- 把客户测试、客户设计或仿真模型简单判定为“错误”；
- 对未知控制策略、未知温度、未知电压口径做确定性推断；
- 内部 Skill 实现细节、脚本验证过程或证据台账机制，除非用户明确要求内部报告保留这些信息。

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

对于已经生成的完整技术报告，可以要求补充输出客户外发精简报告。例如：

```text
Use $motor-report-skill to create a concise customer external brief from:
D:\Projects\example.em3\report-output\motor-trial-report.md

Please make it suitable for sales to send to the customer, remove internal Skill/testing/state-file details, reuse only customer-meaningful figures, and make the software accuracy conclusion clearer. Save it as:
D:\Projects\example.em3\report-output\customer-brief-report.md
```

## 典型输出

典型输出包括：

- 已识别的客户实测资料；
- 已识别的仿真结果来源；
- 电机与仿真模型基本参数，来源于磁路法 `工况报表结果.csv`，并包含几何模型图和相电阻；
- 几何模型图、实测波形图、仿真曲线图或外特性图等报告配图；
- 实测数据和仿真数据的关键指标；
- 可比工况下的差异表；
- 对不一致工况、缺失条件和口径差异的说明；
- 面向客户的 Markdown 技术报告草稿；
- 销售或客户外发用的精简版 Markdown 报告；
- 用于后续增量更新的 `report-state.json`、`evidence-ledger.json`、`change-log.md`。

报告语言应保持中性、工程化和保守，不将测试或模型简单判定为“错误”，也不在证据不足时做过度结论。

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

## 本地验证

修改 `SKILL.md` 或资源文件后，可使用 `skill-creator` 提供的校验脚本检查基本格式：

```powershell
python C:\Users\Yang\.codex\skills\.system\skill-creator\scripts\quick_validate.py .
```

发布前建议至少检查：

- `SKILL.md` frontmatter 是否只有 `name` 和 `description`；
- `description` 是否准确描述触发条件；
- `SKILL.md` 是否明确引用所有需要按需读取的 `references/` 文档；
- `references/` 中被 `SKILL.md` 引用的文件是否存在；
- 新增或修改的脚本是否能在目标环境中运行；
- README 中的脚本清单是否与 `scripts/` 目录一致。

## 维护约定

- 将运行时关键指令写入 `SKILL.md`，不要只写在 README 中；
- 将详细参考资料放入 `references/`，并在 `SKILL.md` 中说明何时读取；
- 将可重复、确定性的处理逻辑放入 `scripts/`，但不要把报告撰写、工程判断和图文分析固化为脚本；
- 新增图表脚本时，应让 LLM 保留选择数据源、判断曲线意义和解释差异的主动权；
- 涉及 `.em3` 哈希目录时，必须继续要求用户提供“哈希目录名到仿真内容”的映射；
- 涉及增量更新时，应维护报告状态、证据台账和变更日志，避免无必要地重写整篇报告；
- 输出客户外发精简报告时，应删除内部开发、脚本验证、证据台账和哈希目录管理细节，保留客户能理解和决策的结论；
- 不在 Skill 中保存客户敏感项目数据或具体交付报告；
- 示例内容应尽量脱敏，只保留能说明工作流的必要信息。

## 数据与保密

该 Skill 常用于处理客户测试报告、设计图纸、仿真结果和项目交付材料。使用或发布仓库时，请确保仓库中不包含未经授权公开的客户原始资料、项目报告、图纸、波形数据或其他敏感文件。
