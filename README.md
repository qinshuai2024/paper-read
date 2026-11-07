# paper-read

**把一篇论文读透，并留下以后能复习的笔记。**

一个为 Claude Code 设计的中文论文精读 skill：从“值不值得读”，到建立全局理解、逐章翻译与批判讨论，最后合卷成有来源、有证据的阅读笔记。支持 arXiv 链接和本地 PDF，支持中断后继续。

[English overview](#english-overview) · [安装](#安装) · [使用](#使用) · [输出](#输出) · [常见问题](#常见问题)

## 它怎样帮你读论文

```text
Stage 0  分诊        为什么读？读多深？     → ReadingPlan.md
                      ↓ 确认
Stage 1  全局导览    扩展引言，先建立框架   → deep-read.md 的 §0
                      ↓ 开始精读
Stage 2  逐章精读    翻译、解释、质疑、证据 → deep-read.md + qa-log.md
                      ↓ 每章可继续 / 提问 / 跳过
Stage 3  合卷        提炼可复习的笔记       → reading-notes.md
```

- **按目标调整深度**：先了解背景、动机和时间预算，再给出阅读建议与章节地图。
- **分级翻译**：`SKIP` / `DIGEST` / `STANDARD` / `FULL`，重点方法与实验可以细读，熟悉的背景可以略读。
- **读的时候就质疑**：记录论点、证据强度、未解问题，以及审稿人与复现者视角的分析。
- **来源可追溯**：本文内容标注章节；涉及其他论文的事实先查证，查不到就明确标注。
- **断点续读**：`progress.json` 记录阶段、已读章节和下一步，新会话不必从头开始。
- **本地留档**：完整内容写入 Markdown，聊天中保留简短导航，避免长篇重复输出。

## 安装

### Claude Code：个人安装（推荐）

需要已安装 Claude Code、Git 和 Python 3.9+。在 macOS、Linux 或 Windows 的 WSL / Git Bash 终端执行：

```bash
mkdir -p "$HOME/.claude/skills"
git clone https://github.com/qinshuai2024/paper-read.git "$HOME/.claude/skills/paper-read"
```

重新打开 Claude Code 会话，然后输入 `/paper-read`。如果目标目录已经存在，请先备份旧版，或按下方“更新”操作；不要直接覆盖自己的修改。

只想在单个项目使用，可以在该项目根目录执行：

```bash
mkdir -p .claude/skills
git clone https://github.com/qinshuai2024/paper-read.git .claude/skills/paper-read
```

也可在 GitHub 点击 **Code → Download ZIP**，解压后将包含 `SKILL.md` 的整个文件夹命名为 `paper-read`，放入对应的 skills 目录。

### PDF 可选依赖

**arXiv HTML 解析只使用 Python 标准库，无需 pip 依赖。** 本地 PDF 或 HTML 失败后的 PDF 回退，需要二选一：

```bash
# 推荐：PyMuPDF，安装到运行脚本所使用的 Python 环境
python3 -m pip install -r "$HOME/.claude/skills/paper-read/requirements-pdf.txt"

# 或：Poppler（macOS）
brew install poppler

# 或：Poppler（Debian / Ubuntu / WSL）
sudo apt install poppler-utils
```

若系统 Python 不允许直接安装包，可使用虚拟环境，再在启动 Claude Code 前激活它：

```bash
python3 -m venv "$HOME/.claude/skills/paper-read/.venv"
source "$HOME/.claude/skills/paper-read/.venv/bin/activate"
python3 -m pip install -r "$HOME/.claude/skills/paper-read/requirements-pdf.txt"
```

**不需要专用 API key 或额外 skill。** 外部引用查证使用宿主已有的网页搜索 / 抓取能力。Semantic Scholar、arXiv、OpenAlex、Exa 和 research-wiki 集成都是可选项，不随本仓库安装；没有联网工具时会标注无法独立查证。

### 其他兼容宿主

核心资源是 `SKILL.md`、提示词、模板和 Python 脚本。支持 Agent Skills 的宿主可将整个目录放入自己的 skills 路径；Claude Code 的工具名与 `/paper-read` 命令需要按宿主能力映射。当前文档以 Claude Code 为主要使用方式；其他宿主需要自行验证交互与文件权限。

### 更新与卸载

```bash
# 更新；存在本地修改时先处理修改，再拉取
git -C "$HOME/.claude/skills/paper-read" pull --ff-only
```

卸载时移走 `paper-read` skill 文件夹即可。阅读产出放在你指定的输出目录，请另行备份。

## 使用

### 从一篇论文开始

在 Claude Code 对话中输入：

```text
/paper-read https://arxiv.org/abs/1706.03762
```

也支持 arXiv 的 `/pdf/`、`/html/` 链接、纯 arXiv ID，或本地 PDF：

```text
/paper-read /path/to/paper.pdf
```

首次启动会确认输出目录，询问阅读目标、背景和时间预算；每题都可以跳过。生成阅读计划后，回复“开始”进入全局导览，再回复“开始精读”逐章讨论。章节末可以“继续”“提问”或“跳过”。

### 快速进入 / 单独运行阶段

```text
/paper-read https://arxiv.org/abs/1706.03762 --quick
/paper-read https://arxiv.org/abs/1706.03762 --stage triage
/paper-read https://arxiv.org/abs/1706.03762 --stage global
/paper-read https://arxiv.org/abs/1706.03762 --stage deep
/paper-read https://arxiv.org/abs/1706.03762 --stage synth
```

`--quick` 跳过分诊。阶段选择：`triage` 分诊、`global` 全局导览、`deep` 全局导览与逐章精读、`synth` 合卷；后续阶段应指向已有阅读材料，缺少输入时先补齐。

继续读时，提供原论文和原输出位置，例如：

```text
/paper-read https://arxiv.org/abs/1706.03762 --stage deep
继续上次，输出目录仍然是 /path/to/my-reading。
```

skill 会读取已有 `progress.json` 并展示进度，等待你选择继续、重读或重新分诊。也可以随时说“§3 改为 FULL”“解释这个公式”或“进入合卷”。读完后明确说“出复现骨架”，才会在相应计划配置下额外生成复现文档。

## 输出

```text
<你选择的输出目录>/
├── papers/
│   └── <MM-DD>-<作者>-<年份>-<关键词>/
│       ├── source.html            # 有可用 HTML 时存档
│       ├── source.pdf             # 本地 PDF / arXiv 下载成功时存档
│       ├── sections.json          # 结构化章节
│       ├── ReadingPlan.md         # 阅读计划
│       ├── deep-read.md           # 全局导览 + 逐章精读
│       ├── qa-log.md              # 问答、未解问题、声明与证据
│       ├── reading-notes.md       # 最终复习笔记
│       ├── progress.json          # 可恢复的阅读进度
│       └── reproduce-skeleton.md  # 可选，按需生成
└── reading-notes/
    └── <dated-slug>.md            # 指向最终笔记的相对软链接
```

合卷笔记包括研究定位、动机、创新点、方法与实验、声明证据评分、reject / defense 分析、可借鉴资产、精选问答和复习题。软链接不可用时可回退为副本，副本不会自动同步。

**换电脑时**：重新克隆 skill 就能获得同一套流程。若还要继续之前的论文，请同步整个输出目录（同时保留 `papers/` 和 `reading-notes/`）；skill 仓库不保存你的阅读记录。相对软链接在支持链接的平台上可以随目录移动，进度中的旧绝对路径需按新位置更新。

## 仓库结构

```text
paper-read/
├── SKILL.md                       # skill 入口与编排规则
├── prompts/
│   ├── triage.md                  # 分诊与阅读深度
│   ├── deep-read.md               # 全局导览与逐章精读
│   └── synth.md                   # 合卷笔记
├── scripts/
│   ├── html_to_sections.py        # arXiv / LaTeXML HTML 切分
│   └── pdf_to_sections.py         # PDF 切分
├── templates/                     # 阅读计划、声明证据表、复现骨架
├── tests/                         # PDF 标题提取回归测试
├── .github/workflows/checks.yml    # Python 3.9 / 3.12 检查
├── requirements-pdf.txt           # 可选 PDF 依赖
├── CONTRIBUTING.md
└── LICENSE
```

也可以独立运行切分脚本：

```bash
python3 scripts/html_to_sections.py https://arxiv.org/html/1706.03762 -o /tmp/sections-html.json
python3 scripts/pdf_to_sections.py /path/to/paper.pdf -o /tmp/sections-pdf.json
```

开发验证：`python3 -m unittest discover -s tests -v`。回归测试使用自构造数据，不下载或分发论文。

HTML 脚本适配 arXiv / LaTeXML 的结构，不是任意网页解析器。切分脚本只提取内容；完整精读由宿主模型按 skill 提示词完成。

## 常见问题

**看不到 `/paper-read`？** 确认路径是 `~/.claude/skills/paper-read/SKILL.md`，没有多套一层目录，再重新打开会话。

**arXiv 没有 HTML 或下载失败？** 流程会尝试 PDF，再回退到摘要页或手动提供内容。网络访问受限时，可以直接给本地 PDF。

**PDF 切分结果为空、缺公式或章节识别不准？** 文本抽取受双栏、字体和扫描件影响。需要回看原 PDF 的图表与公式；扫描件应先 OCR。PyMuPDF 不存在时脚本会自动尝试 `pdftotext`，但不会自动按质量切换后端。

**换电脑是不是还要配置 Exa 等服务？** 不需要。它们是可选搜索集成；已有的通用网页工具也可查证。工具不可用时，明确保留未查证标记。

**会上传论文或笔记吗？** 两个切分脚本将提取结果写入本地，HTML 脚本会访问你提供的 URL。完整阅读需要模型处理论文内容，数据如何发送取决于所使用的宿主和模型服务。`.gitignore` 默认忽略仓库根目录中的 `papers/`、`reading-notes/` 等阅读产出。

## English overview

**paper-read** is a Chinese-first academic paper reading skill originally built for Claude Code. It guides a conversation through triage, a global overview, section-by-section reading, and a final synthesis, with local Markdown notes and resumable progress.

It accepts arXiv links / IDs and local PDFs. The arXiv HTML extractor uses only Python's standard library; PDF extraction optionally uses PyMuPDF or Poppler. Additional research skills, MCP integrations and dedicated API keys are not required. Other Agent Skills hosts may reuse the resources with tool-name and interaction adaptations; the documented primary workflow targets Claude Code.

Install into `~/.claude/skills/paper-read` using the Git clone command above, reopen your session, and invoke `/paper-read <arxiv-url-or-pdf-path>`. Update with `git pull --ff-only`. Reading outputs are stored separately in the directory you choose; sync that entire directory to resume on another computer.

## 贡献与许可证

欢迎通过 [Issues](https://github.com/qinshuai2024/paper-read/issues) 和 Pull Request 分享问题与改进，参见 [贡献指南](CONTRIBUTING.md)。

本仓库的 skill 指令、模板和脚本按 [MIT License](LICENSE) 开源。所阅读论文与第三方依赖仍适用各自许可证。
