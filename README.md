# 华为杯研究生数学建模竞赛辅助 Skill

[![Tests](https://github.com/Nopon-Knowledge/huawei-cup-modeling-skill/actions/workflows/tests.yml/badge.svg)](https://github.com/Nopon-Knowledge/huawei-cup-modeling-skill/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个面向 Codex 与 ChatGPT 桌面端的中文 Skill，用于辅助“华为杯”中国研究生数学建模竞赛的规则核验、备赛组织、合规建模、论文整合和提交审计。

它的目标不是替参赛队完成竞赛，而是把容易失控的部分做成一套可复核的工作流：年度规则与往届先例分离，模型结论可追溯，论文数字有账本，最终 PDF 可以锁稿并验证哈希。

> [!WARNING]
> 本项目不是华为或竞赛组委会的官方项目；规则快照会过期；不要提交、上传或公开实时竞赛中的未公开赛题、论文、数据、身份信息和队内材料。

## 能做什么

- 区分规则查询、赛前准备、公开往届题、实时赛题、论文整合和提交审计等模式；
- 在实时赛题场景先核验当届 AI 规定与允许范围；
- 提供三人团队分工、100 小时时间线、检查点和降级策略；
- 建立数据、实验、来源、AI 使用和结果账本；
- 初始化不会覆盖已有文件的竞赛工作区；
- 检查 PDF 结构、文件名、大小、匿名关键词、附件及 MD5/SHA-256；
- 锁稿后用已记录的哈希验证上传文件没有发生变化。

## 不做什么

- 不把往届规则、经验帖或未公开阈值冒充当届要求；
- 不虚构数据、实验、文献、代码运行结果或获奖保证；
- 不把机械预检描述成模板、匿名或学术规范的完整证明；
- 当实时赛题的 AI 规定尚未发布或无法核验时，不生成核心模型、结果、代码或可提交正文。

## 安装

推荐在 Codex 中调用内置的 `$skill-installer`，让它从以下 GitHub 子目录安装：

```text
使用 $skill-installer 从下面的 GitHub 路径安装 huawei-cup-modeling：
https://github.com/Nopon-Knowledge/huawei-cup-modeling-skill/tree/main/huawei-cup-modeling
```

也可以将 `huawei-cup-modeling/` 复制到当前仓库的 `.agents/skills/`，作为仓库级 Skill；放入个人的 `~/.agents/skills/` 则可跨仓库使用。Codex 会自动检测 Skill 变更，未出现时可重启 Codex。目录位置和调用方式以 [OpenAI Skills 官方文档](https://learn.chatgpt.com/docs/build-skills)为准。

## 使用示例

显式调用：

```text
$huawei-cup-modeling 帮我核对 2026 华为杯报名、赛程和当前仍待发布的规则。
```

```text
$huawei-cup-modeling 这是已经公开的往届赛题，请先拆解子问题并设计可复现基线。
```

```text
$huawei-cup-modeling 审计这份最终 PDF；先从当届公告确认文件名、大小和匿名起始页。
```

## 脚本

初始化竞赛工作区：

```bash
python3 huawei-cup-modeling/scripts/init_competition_workspace.py TEAM_WORKSPACE \
  --year CONTEST_YEAR \
  --title "项目名称"
```

提交前预检：

```bash
python3 huawei-cup-modeling/scripts/preflight_submission.py PAPER.pdf \
  --expected-name OFFICIAL_FILENAME.pdf \
  --max-paper-bytes VERIFIED_BYTE_LIMIT \
  --identity "学校名称" \
  --identity-start-page OFFICIAL_START_PAGE \
  --strict \
  --manifest HASH_REPORT.json
```

年度条件必须来自当届官方公告。若官方只给出 MB 而未说明换算方式，请记录采用的换算约定，并把字节检查视为保守筛查。

## 环境与测试

- Python 3.9 或更高版本；
- 首发支持 macOS 和 Linux；Windows 尚未纳入完整回归范围；
- Python 脚本不依赖第三方包；
- PDF 结构检查使用 Poppler 的 `pdfinfo`；
- 身份文本扫描使用 Poppler 的 `pdftotext`；
- 缺少 Poppler 时脚本会警告，`--strict` 会将未完成的检查视为失败。

Poppler 由用户独立安装并按其自身许可证提供，本仓库不捆绑其二进制。

运行测试：

```bash
python3 -m unittest discover -s huawei-cup-modeling/tests -v
```

当前回归集覆盖初始化回滚、符号链接、硬链接防覆盖、已有清单保护、年度参数、字节边界、PDF 结构、身份词和哈希验证。

## 数据与隐私

- 两个 Python 脚本自身不联网；通过 Codex 使用 Skill 时，用户提供的提示词和材料可能由其配置的 AI 服务处理，请遵守相应的数据控制与保留政策。
- 初始化脚本生成的 `.gitignore` 默认忽略赛题、数据、代码、实验、论文、日志和提交目录；忽略规则不是访问控制，正式比赛材料仍应保存在受控位置。
- AI 使用日志只记录必要摘要，不保存与任务无关的完整对话；公开日志前必须脱敏。
- 预检清单默认不记录绝对路径或身份词原文，但仍包含文件名、大小、修改时间和文件哈希。它可能构成未公开论文的指纹，比赛期间不要公开。
- MD5 仅用于赛事要求的字节锁定流程，不应视为安全哈希；脚本同时记录 SHA-256 作为补充完整性证据。

## 项目结构

```text
huawei-cup-modeling/
├── SKILL.md
├── agents/openai.yaml
├── references/
│   ├── current-rules.md
│   ├── contest-operations.md
│   └── paper-and-compliance.md
├── scripts/
│   ├── init_competition_workspace.py
│   └── preflight_submission.py
└── tests/test_scripts.py
```

## 规则维护原则

`references/current-rules.md` 是带核验日期的年度快照，不是永久规则。更新时请：

1. 只采用竞赛官网、当届正式附件或培养单位的校内通知；
2. 区分已确认要求、尚未发布内容和往届先例；
3. 保留来源链接、发布日期和最后核验日期；
4. 为脚本参数变化补充回归测试；
5. 不提交实时竞赛中的未公开题目、论文、数据或队内材料。

欢迎通过 Issue 或 Pull Request 提交规则更新、脚本修复和工作流改进。

贡献内容不得包含实时未公开赛题、队内论文或数据、真实身份、完整 AI 对话、官方模板或 Logo、无权再授权的论文与代码。提交 Pull Request 即表示贡献者有权按本仓库许可证提供其原创改动。安全问题请使用最小、脱敏的复现材料，不要附上真实竞赛文件。

## 免责声明

本项目是独立的开源辅助工具，与华为、中国研究生数学建模竞赛组委会、承办单位及研创网不存在隶属、授权或背书关系。“华为杯”等名称及相关商标归其权利人所有。

仓库中的规则摘要仅用于帮助定位检查项，不能替代当届官方公告、附件和系统提示，也不构成法律或竞赛合规意见。项目不保证规则始终准确及时，也不保证匿名、模板、原创性、提交成功、获奖或 AI 使用一定被允许。人工逐页检查和官网复核不可替代。

## 许可证

项目原创代码与文档采用 [MIT License](LICENSE)。外部链接、官方文件、赛事名称和商标的权利仍归各自权利人所有。
