<p align="center">
  <a href="assets/readme-banner.svg"><img src="assets/readme-banner.svg" alt="从问题出发，让结论可复现。华为杯研究生数模助手：规则、模型、论文与提交。" width="960" /></a>
</p>

<h1 align="center">华为杯研究生数模助手</h1>

<p align="center">
  面向中国研究生数学建模竞赛的中文 Skill<br />
  <strong>核验规则 · 建立基线 · 验证结果 · 整合论文 · 审计提交</strong>
</p>

<p align="center">
  <a href="https://github.com/Nopon-Knowledge/huawei-cup-modeling-skill/actions/workflows/tests.yml"><img src="https://github.com/Nopon-Knowledge/huawei-cup-modeling-skill/actions/workflows/tests.yml/badge.svg" alt="Tests" /></a>
  <img src="https://img.shields.io/badge/Python-3.9%2B-2563EB?logo=python&amp;logoColor=white" alt="Python 3.9+" />
  <img src="https://img.shields.io/badge/Codex-Skill-172B4D" alt="Codex Skill" />
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-0F766E" alt="MIT License" /></a>
</p>

<p align="center">
  <a href="#快速开始">快速开始</a> &nbsp;·&nbsp;
  <a href="#竞赛工作流">竞赛工作流</a> &nbsp;·&nbsp;
  <a href="#图表与论文">图表与论文</a> &nbsp;·&nbsp;
  <a href="#脚本工具">脚本工具</a> &nbsp;·&nbsp;
  <a href="#使用边界">使用边界</a>
</p>

---

把分散的竞赛工作串起来：从带来源的规则快照，到能运行的模型、可追溯的图表，再到锁稿后的文件核验。队伍始终主导选题、假设与结论，Skill 帮助组织过程、检查证据、减少遗漏。

<table align="center">
  <tr>
    <th align="center" width="280">规则有据</th>
    <th align="center" width="280">结果可查</th>
    <th align="center" width="280">交付有序</th>
  </tr>
  <tr>
    <td align="center">核验规则<br />标注缺口</td>
    <td align="center">跑通基线<br />追溯结果</td>
    <td align="center">统一图表<br />复核提交</td>
  </tr>
</table>

## 快速开始

### 1. 安装 Skill

在 Codex 中发送：

```text
使用 $skill-installer 从下面的 GitHub 路径安装 huawei-cup-modeling：
https://github.com/Nopon-Knowledge/huawei-cup-modeling-skill/tree/main/huawei-cup-modeling
```

<details>
<summary><strong>手动安装与目录说明</strong></summary>

也可以把仓库中的整个 `huawei-cup-modeling/` 文件夹复制到以下任一位置，保留其中的脚本和参考资料。

<table align="center">
  <tr><th align="center">安装范围</th><th align="center">目录</th></tr>
  <tr><td>当前仓库</td><td><code>.agents/skills/huawei-cup-modeling/</code></td></tr>
  <tr><td>个人全局</td><td><code>~/.agents/skills/huawei-cup-modeling/</code></td></tr>
</table>

Codex 会自动检测 Skill 变更；若未出现，可重启。目录位置与调用方式见 [OpenAI Skills 官方文档](https://learn.chatgpt.com/docs/build-skills)。

</details>

### 2. 从一个具体任务开始

```text
$huawei-cup-modeling 帮我核对 2026 华为杯报名、赛程和 AI 使用规则，
区分已确认、尚未发布和仅有往届先例的信息，并附上来源与核验日期。
```

Skill 会先识别任务阶段、整理已有材料，再给出当前可执行的下一步。以上为 Codex 调用方式；在 ChatGPT 桌面端可用 `@` 选择已安装的 Skill，详见 [官方文档](https://learn.chatgpt.com/docs/build-skills)。

<details>
<summary><strong>更多示例：往届题训练、三人协作、图表润色、提交审计</strong></summary>

**公开往届题训练**

```text
$huawei-cup-modeling 这是已经公开的往届赛题。
请拆解子问题、明确评价指标，设计一条覆盖全题的可复现基线。
```

**三人团队规划**

```text
$huawei-cup-modeling 根据当届已核验规则，为三人队制定竞赛计划，
给出角色分工、关键检查点、锁稿缓冲和模型失败时的降级方案。
```

**图表与论文润色**

```text
$huawei-cup-modeling 请基于保存的实验输出优化这些论文图表：
统一字体、配色、单位和有效数字，居中排版，并检查最终 PDF 的可读性。
保留原始数值，指出缺少实验记录或来源的位置。
```

**提交前审计**

```text
$huawei-cup-modeling 审计这份最终 PDF；
先从当届公告确认文件名、大小和匿名起始页，再执行机械预检。
```

</details>

## 竞赛工作流

先核验规则，再建立覆盖全题的基线；有了验证证据，再整合论文和锁定文件。**实时赛题须先确认当届 AI 允许范围**，各阶段按已核验规则执行。

<p align="center">
  <a href="assets/readme-workflow.svg"><img src="assets/readme-workflow.svg" alt="五阶段竞赛工作流：规则核验→问题拆解与基线→模型比较与验证→图表与论文整合→预检、锁稿与上传复核。实时赛题先核验 AI 允许范围，范围不明时仅核对规则与机械检查。" width="800" /></a>
</p>
<p align="center"><sub>每一阶段都有对应产物；发现问题时回到相应阶段修正。点击图可查看原图。</sub></p>

三人分工、100 小时参考时间线、五个检查点和模型降级策略，见 [竞赛执行指南](huawei-cup-modeling/references/contest-operations.md)。时间安排是可调整的参考，赛程以当届公告为准。

## 图表与论文

**图表既要清楚，也要有据可查。** 从保存的实验结果生成图表，关联结果账本，再引用到正文和摘要，让每个定量结论都能回到一次具体运行。

<p align="center">
  <a href="assets/readme-evidence.svg"><img src="assets/readme-evidence.svg" alt="论文证据链：数据与代码通过 run_id 对应实验输出，输出中的数值经复核后通过 claim_id 对应论文图表、正文与摘要；数字不一致时回查来源重新生成。" width="800" /></a>
</p>
<p align="center"><sub>从数据到结论保留来源；复核后的同一结果，使用一致的单位、精度与表述。</sub></p>

<table align="center">
  <tr><th align="center">维度</th><th align="center">交付标准</th></tr>
  <tr><td><strong>选图</strong></td><td>围绕一个比较或结论选图；坐标、单位、图例、误差含义完整。</td></tr>
  <tr><td><strong>样式</strong></td><td>统一字体、字号和配色；颜色搭配线型或标记，缩小后仍可辨认。</td></tr>
  <tr><td><strong>居中</strong></td><td>图与表相对正文版心居中，多子图成组对齐；题注遵循官方模板。</td></tr>
  <tr><td><strong>导出</strong></td><td>统计图优先矢量格式；位图按最终尺寸导出，检查字体和边缘裁切。</td></tr>
  <tr><td><strong>溯源</strong></td><td>保留源数据、绘图脚本和运行标识；正文、摘要与图表数字一致。</td></tr>
</table>

图型选择、配色建议、Markdown / Word / LaTeX 居中方式和导出检查，见 [图表与排版指南](huawei-cup-modeling/references/figures-and-tables.md)；写作与逐层审计见 [论文整合指南](huawei-cup-modeling/references/paper-and-compliance.md)。

## 脚本工具

提供两个无第三方 Python 依赖的本地辅助脚本。以下命令在仓库根目录执行，**全大写参数值需要替换**为真实路径或已核验条件。

### 初始化竞赛工作区

```bash
python3 huawei-cup-modeling/scripts/init_competition_workspace.py TEAM_WORKSPACE \
  --year CONTEST_YEAR \
  --title "项目名称"
```

生成规则快照目录、数据与图表目录、来源 / 实验 / 结果账本、AI 使用日志和提交清单，并保留已有文件。三人分工与时间安排按 [竞赛执行指南](huawei-cup-modeling/references/contest-operations.md)制定。

### 提交前预检

```bash
python3 huawei-cup-modeling/scripts/preflight_submission.py PAPER.pdf \
  --expected-name OFFICIAL_FILENAME.pdf \
  --max-paper-bytes VERIFIED_BYTE_LIMIT \
  --identity "学校名称" \
  --identity-start-page OFFICIAL_START_PAGE \
  --strict \
  --manifest HASH_REPORT.json
```

检查 PDF 结构、文件名、字节大小和指定页后的身份关键词，生成 MD5 与 SHA-256 清单。年度条件来自当届官方公告；若官方只写 MB 而未说明换算方式，应记录采用的约定，并把字节检查视为保守筛查。

<details>
<summary><strong>锁稿后验证文件是否变化</strong></summary>

```bash
python3 huawei-cup-modeling/scripts/preflight_submission.py PAPER.pdf \
  --expected-md5 RECORDED_MD5 \
  --strict
```

提交 MD5 后冻结对应字节文件；上传前核验同一文件，不再编辑、压缩或重导出。预检清单不覆盖已有文件，重做时使用新文件名。

</details>

## 环境与质量

<table align="center">
  <tr><th align="center">环境</th><th align="center">要求 / 用途</th></tr>
  <tr><td>Python 3.9+</td><td>运行脚本；无需第三方 Python 包</td></tr>
  <tr><td>macOS / Linux</td><td>GitHub Actions 覆盖的平台</td></tr>
  <tr><td>Poppler · <code>pdfinfo</code></td><td>PDF 结构检查</td></tr>
  <tr><td>Poppler · <code>pdftotext</code></td><td>身份关键词文本扫描</td></tr>
</table>

Poppler 需独立安装，本仓库不捆绑其二进制。工具缺失时，脚本会提示未完成的检查；启用 `--strict` 后，这类检查会被视为失败。

```bash
python3 -m unittest discover -s huawei-cup-modeling/tests -v
```

测试覆盖初始化回滚、链接防覆盖、已有清单保护、年度参数、字节边界、PDF 结构、身份词扫描和哈希验证。

<details>
<summary><strong>项目结构与资料入口</strong></summary>

```text
.
├── README.md
├── assets/                         # README 矢量封面与图示
└── huawei-cup-modeling/
    ├── SKILL.md                     # 任务路由与核心约束
    ├── agents/openai.yaml           # 界面元数据
    ├── references/
    │   ├── current-rules.md         # 带核验日期的年度快照
    │   ├── contest-operations.md    # 分工、时间线与检查点
    │   ├── figures-and-tables.md    # 图表质量、居中与导出
    │   └── paper-and-compliance.md  # 论文、引用与提交审计
    ├── scripts/
    │   ├── init_competition_workspace.py
    │   └── preflight_submission.py
    └── tests/test_scripts.py
```

</details>

## 使用边界

当届官方公告和附件优先，缓存快照用于定位检查项。实时赛题的 AI 规定或允许范围无法核验时，Skill 仅协助规则核对、材料整理和非实质性机械检查。数据、实验、文献与运行结果必须真实，关键假设和最终结论由队伍理解并确认。

脚本提供辅助证据，完整的模板、匿名和视觉版式仍需人工逐页复核。

<details>
<summary><strong>数据、隐私与哈希说明</strong></summary>

- 两个 Python 脚本自身不联网。通过 Codex 使用 Skill 时，材料可能由用户配置的 AI 服务处理，应遵守相应的数据控制与保留政策。
- 初始化工作区的 `.gitignore` 默认忽略竞赛材料目录。忽略规则不是访问控制，正式比赛材料仍应保存在受控位置。
- AI 使用日志只记录必要摘要，公开前须脱敏；不保存无关的完整对话。
- 哈希清单默认隐藏绝对路径与身份词原文，但仍含文件名、大小、时间和文件哈希，比赛期间不要公开。
- MD5 用于赛事要求的字节锁定流程，SHA-256 提供补充完整性证据；MD5 不作为安全哈希使用。

</details>

## 维护与贡献

[年度规则快照](huawei-cup-modeling/references/current-rules.md)需要持续核验。更新时采用竞赛官网、当届正式附件或培养单位通知，保留来源链接、发布日期和核验日期，明确区分已确认、尚未发布与往届先例。脚本参数变化应补充相应回归测试。

欢迎通过 [Issue](https://github.com/Nopon-Knowledge/huawei-cup-modeling-skill/issues) 或 Pull Request 提交规则更新、脚本修复和工作流改进。贡献内容不得包含实时未公开赛题、队内论文或数据、真实身份、完整 AI 对话、官方模板或 Logo，以及无权再授权的论文与代码。

<details>
<summary><strong>独立项目声明与许可证</strong></summary>

本项目是独立的开源辅助工具，与华为、中国研究生数学建模竞赛组委会、承办单位及研创网不存在隶属、授权或背书关系。“华为杯”等名称及相关商标归其权利人所有。

规则摘要用于定位检查项，不能替代当届官方公告、附件和系统提示，也不构成法律或竞赛合规意见。项目不保证规则始终准确及时，不保证匿名、模板、原创性、提交成功、获奖或 AI 使用一定被允许。

项目原创代码与文档采用 [MIT License](LICENSE)。外部链接、官方文件、赛事名称和商标的权利仍归各自权利人所有。Poppler 按其自身许可证提供。

</details>

---

<p align="center">
  <strong>让每个结论有据可查，让每次交付有迹可循。</strong><br />
  <sub>规则有来源 · 模型可复现 · 图表可读 · 提交可核验</sub>
</p>
