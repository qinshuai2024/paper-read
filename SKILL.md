---
name: paper-read
description: 精读单篇学术论文。从苏格拉底式分诊（值不值得读）→ 扩展引言式全局导览 → 逐章中文翻译+资深解读+批判性反问 → 合卷产出阅读笔记。适用于 arXiv 链接或本地 PDF。当用户说"精读这篇"、"帮我读这篇论文"、"read this paper"、"读论文"、"arxiv 链接 + 想精读"时触发。
license: MIT
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebFetch, WebSearch, AskUserQuestion
---

# Paper-Read: 资深科研者视角的论文精读流程

调用方式：`/paper-read <arxiv-url-or-pdf-path> [--stage triage|global|deep|synth] [--quick]`

精读对象: $ARGUMENTS

## 安装路径与运行环境

- 本 skill 自包含；`scripts/`、`prompts/`、`templates/` 都相对于本 `SKILL.md` 所在目录。执行示例中的 `<SKILL_ROOT>` 前，先解析为该目录的绝对路径并替换占位符；不假定安装在 `~/.claude/skills/`。
- 由宿主提供文件读写、终端、网页检索与用户交互能力。`$ARGUMENTS`、`AskUserQuestion`、`WebFetch` 等是 Claude Code 的写法；其他兼容宿主可用当前用户消息、原生交互和检索工具完成同等操作。提问工具有数量限制时分批询问。
- 下文提及的其他 skill / MCP 均为**可选集成，不随仓库分发，也不要求安装**。先检查可用性；没有学术搜索集成时，使用宿主网页搜索或直接读取 arXiv / DOI / 出版社的一手页面。没有检索能力时明确标注未能查证，不能编造来源；没有 wiki 集成时保留本地笔记即可。批判分析可直接按本 skill 的 prompt 完成。
- 默认输出中文、时间采用 `Asia/Shanghai`（北京时间）；用户明确指定其他语言或时区时，统一调整全文标注及时间命令。


## 设计哲学

吃透一篇论文的本质是 **对话与质疑**，而不是被动接受。资深科研者读论文有三个习惯，本 skill 完全围绕它们设计：

1. **先决断、后投入** —— 这篇论文值不值得读？读到什么颗粒度？（避免精读一篇水论文）
2. **自上而下、由粗到细** —— 先建立全局认知框架，再钻细节（避免迷失在公式里）
3. **始终带着批判 / 复现的眼光** —— 心里同时扮演审稿人和复现者（避免被作者牵着走）

## 与其他 skill 的定位

| Skill | 角色 |
|-------|------|
| `/arxiv` | 检索、下载 PDF、抓取元数据 |
| `/alphaxiv`、`/deepxiv` | 速读 / 分层浏览 |
| `/research-lit`、`/semantic-scholar` | 找相关工作 |
| **`/paper-read`** | **精读单篇：分诊 → 全局 → 逐章 → 合卷** |
| `/kill-argument`、`/ars-reviewer` | 审稿式批判（本 skill 在 Stage 3 内部调用） |
| `/research-wiki`、`/wiki-enrich` | 沉淀（本 skill 在 Stage 3 询问是否写入） |

上述集成仅在已安装且可用时使用；独立安装 paper-read 也能完成核心精读流程。

### 精读中查证外部引用的工具链 (防幻觉, 重要)

当精读 / 问答涉及**当前 PDF 正文之外**的事实 (被引论文具体做了什么、某相关工作的方法/数字、某概念出处、领域背景), **必须实际检索查证**, 不得凭训练记忆作答。按**准确度优先**的三级 fallback 链调用 (详见 "关键规则" 与 deep-read.md 问答段):

| 优先级 | 工具 | 数据源 | 何时用 |
|--------|------|--------|--------|
| ① 首选 | `/semantic-scholar "<被引论文标题>"` | Semantic Scholar API | 查证某篇被引工作: 直接命中论文实体, 带 TLDR + venue + 引用数, 误配率最低 |
| ② 预印本 | `/arxiv "<标题或 arXiv ID>"` | arXiv API | 被引工作是预印本时**可下 PDF 读原文** (准确度天花板) |
| ③ 兜底覆盖 | `/openalex "<标题>"` | OpenAlex 开放引用图 | S2 查不到的老论文 / 冷门会议 / 期刊, 覆盖最全 |
| ④ 网页兜底 | `mcp__exa-key__web_search_exa` (加 `category:"research paper"`) → 不行再 `WebSearch` | Exa 神经搜索 / 通用网页 | 上面学术库不可用或都无果时；Exa 需用户自行配置；按实际来源区分一手论文与二手转述 |
| 发散发现 | `/gemini-search` 或 exa | AI 发现 / 神经搜索 | "还有哪些漏引的相关工作" 这类**发散**查找 (不是精确查证某一篇) |

> **为何这样排序**: `/semantic-scholar` 返回结构化论文实体 (而非网页), 查"某引用做了什么"最对口; `/arxiv` 能直接读原文是准确度上限但只覆盖预印本; `/openalex` 覆盖最全作兜底; Exa MCP 仅在已配置时可用，否则直接用宿主网页检索；证据优先采用一手论文。`/gemini-search` 的 AI 中间层可能引入幻觉, 只用于发散发现, 不用于精确查证。

### 与 ARS plugin (`/ars-*`) 的边界

ARS 是**写作驱动**的批量科研流水线 (research → write → review → revise), 不是为单篇精读设计:

| 场景 | 该用什么 |
|------|---------|
| 我要把一篇论文吃透 + 留笔记复习 | **`/paper-read`** (本 skill) |
| 我要写自己的论文, 顺便读一批参考文献 | `/ars-full` 或 `/ars-lit-review` |
| 我要给一篇我或别人的论文做审稿 | `/ars-reviewer` (本 skill 在 Stage 3 也调用 kill-argument 思路, 但只针对当前精读对象) |
| 我要从一个研究方向出发批量产 idea | `/ars-plan` + `/idea-discovery` |

**核心区别**: ARS 把 paper 当**素材**, paper-read 把 paper 当**对象**。如果用户的目的是"理解这一篇", 始终选 paper-read; 如果用户已经在写论文且需要把这篇并入参考文献, 用 ARS 流程。

## 整体三阶段流程

```
┌─────────────────────────────────────────────────────────────┐
│  Stage 0: TRIAGE (苏格拉底式分诊)                            │
│    问 5 题(每题可跳过) + 客观分诊 → ReadingPlan.md           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Stage 1+2: DEEP READ (全局导览 + 逐章精读)                  │
│    一个文件 deep-read.md, 含:                                │
│      § 0 扩展引言 (Stage 1)                                  │
│      § 1, § 2, ... 各章精读 (Stage 2)                        │
│    章末三选项: 继续 / 提问 / 跳过下一章                       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  Stage 3: SYNTHESIZE (合卷)                                  │
│    单文件 reading-notes.md, 内嵌 summary/claims/             │
│    kill-arg/takeaway 精炼版                                  │
│    在 reading-notes/ 创建相对软链接                          │
│    询问是否写入 research-wiki                                │
└─────────────────────────────────────────────────────────────┘
```

每阶段可单独调用：`/paper-read <input> --stage triage|global|deep|synth`。`global` 只生成 §0 全局导览；`deep` 从全局导览进入逐章精读，已有进度时可从对应章节恢复。
默认一气呵成，但**每阶段之间必须等用户确认**才进入下一步。

## 常量

- **DEFAULT_OUTPUT_BASE** — 默认产出根目录 `./` (当前工作目录)，每次启动**必须询问用户确认**。
- **PAPER_DIR_PATTERN** — 每篇论文一个文件夹: `<OUTPUT_BASE>/papers/<dated-slug>/`
- **NOTES_DIR_PATTERN** — 全局阅读笔记文件夹: `<OUTPUT_BASE>/reading-notes/` (存放指向各论文的链接)
- **SLUG_RULE** — `<firstauthor-lastname>-<year>-<short-keyword>` (例如 `vaswani-2017-attention`)
- **DATED_SLUG_RULE** — 论文文件夹名与 reading-notes 软链接名都在 slug 前**加日期前缀**: `<dated-slug>` = `<MM-DD>-<slug>` (例如 `06-11-vaswani-2017-attention`)。
  - `<MM-DD>` 是**首次创建该论文文件夹当天**的月-日 (两位补零), 取自 `TZ=Asia/Shanghai date "+%m-%d"`。
  - **此前缀在整个精读生命周期内固定不变** —— 跨天续读 / 重读 / 合卷都沿用首次创建时记下的日期, 绝不按"今天"重算 (否则断点续读会找不到旧目录)。日期前缀记录在 `progress.json` 的 `dated_slug` 字段, 是 source of truth。
  - 全流程中凡出现 `papers/<slug>/` 或 `reading-notes/<slug>.md` 的占位符, **一律替换为** `papers/<dated-slug>/` 与 `reading-notes/<dated-slug>.md`。
- **TRANSLATION_LEVEL** — 翻译详尽度，默认 **HIGH**（全文完整中文翻译）。可由 ReadingPlan 调整。
- **PAUSE_POLICY** — 章末**三选项暂停**: `[继续 / 提问 / 跳过本章下一章]`。永远不自动连读。
- **QUICK_MODE** — 通过 `--quick` 跳过 Stage 0，直接进入 Stage 1。

## 工作流总览

### Step 0: 解析输入与初始化

解析 `$ARGUMENTS`:

- **输入类型**:
  - `arxiv.org/abs/XXXX.XXXXX` 或 `arxiv.org/pdf/XXXX.XXXXX` 或 `arxiv.org/html/XXXX.XXXXX` 或纯 arXiv ID → 走 arXiv 路径 (**HTML 优先, PDF 辅助**, 见 Step 0 "抓取论文内容")
  - 以 `.pdf` 结尾的本地路径 → 走本地 PDF 路径
  - 其他 URL → 若是论文 HTML 全文页先试 HTML 切分; 否则用 WebFetch 抓取，失败则告知用户改用上述两种
- **阶段标志**: `--stage triage|global|deep|synth`，缺省则全流程
- **快速模式**: `--quick` 跳过 Stage 0

询问产出位置 (必做，除非用户在 args 中显式指定):

```
默认把产出放在 <当前工作目录>/papers/<dated-slug>/。
要使用默认位置，还是指定其他位置？
```

确认后, 先确定 slug 与日期前缀, 再建立目录:

```bash
# slug 按 SLUG_RULE 推导, 例如 vaswani-2017-attention
DATE_PREFIX=$(TZ=Asia/Shanghai date "+%m-%d")     # 例如 06-11
DATED_SLUG="${DATE_PREFIX}-${SLUG}"               # 例如 06-11-vaswani-2017-attention
mkdir -p <OUTPUT_BASE>/papers/${DATED_SLUG}
mkdir -p <OUTPUT_BASE>/reading-notes
```

> **日期前缀只在首次创建时计算一次。** 之后所有阶段 (含跨天续读) 都从 `progress.json` 的 `dated_slug` 字段读取, 不要按"今天"重算。断点续读扫描已有目录时, 直接用磁盘上已存在的 `<dated-slug>` 目录名。

#### 幂等检查 (断点续读)

`mkdir` 之后**立刻**做断点检测。优先级:

1. **先看 `progress.json`** (有就直接用, 是 Source of Truth)
2. **没有则 fallback 扫文件** (扫 4 个 markdown 末尾, 推断进度)
3. **两者都没有 → 全新开始**

> **定位已有目录 (日期前缀)**: 由于目录名带日期前缀 (`<MM-DD>-<slug>`), 新会话回来时**不能**用"今天"重算前缀去找目录。应按 slug 后缀匹配已存在的目录: `ls -d <OUTPUT_BASE>/papers/*-<slug>/ 2>/dev/null`。若匹配到 (通常恰好一个), 用磁盘上的真实目录名作 `<dated-slug>`; 若匹配到多个 (同一篇换日期重读过), 用 AskUserQuestion 让用户选; 若无匹配, 才按上面的 `DATE_PREFIX=今天` 新建。

```bash
PROGRESS="<paper_dir>/progress.json"
if [ -f "$PROGRESS" ]; then
  # 优先用 progress.json (结构化, 信息完整)
  STAGE=$(python3 -c "import json; print(json.load(open('$PROGRESS'))['current_stage'])")
  NEXT=$(python3 -c "import json; d=json.load(open('$PROGRESS')); n=d.get('next_action',{}); print(f\"{n.get('stage','?')} / {n.get('section_id','?')} / {n.get('strategy','?')}\")")
else
  # Fallback: 扫文件
  EXISTS=""
  for f in ReadingPlan.md deep-read.md reading-notes.md qa-log.md; do
    [ -f "<paper_dir>/$f" ] && EXISTS="$EXISTS $f"
  done
fi
```

如果检测到已有进度, **必须**用 AskUserQuestion 让用户三选一, 默认不覆盖:

| 选项 | 动作 |
|------|------|
| 继续上次 (Recommended) | 读 `progress.json` 的 `next_action`, 跳到对应阶段/章节; 在终端先回显**断点摘要** (见下) 让用户对齐 |
| 重新分诊 | 把现有 5 个文件 (含 progress.json) 备份到 `<paper_dir>/.backup-<timestamp>/`, 然后从 Stage 0 重来 |
| 换新位置 | 询问新的 slug 后缀 (如 `-v2`), 在新目录开始 |

**禁止行为**: 不询问就覆盖任何已存在的 ReadingPlan / deep-read / reading-notes / qa-log / progress.json。

**断点摘要回显模板** (新会话/隔段时间回来必显示):

```
== 检测到上次进度 ==
论文: <title>  (目录: <dated-slug>)
上次更新: <YYYY-MM-DD HH:MM>  (距今 <N> 小时/天)
已完成阶段: Stage 0 ✓ / Stage 1 ✓ / Stage 2 进行中 (§0..§<X> 完成)
当前位置: <next_action.stage> → <next_action.section_id> (策略: <STR>)
进度统计:
  · 已精读章节: <N> / <Total>
  · qa-log 问答: <M> 条 (其中 <K> 条 #critical-question)
  · 未解疑点: <U> 条 (Part 2)
  · 章末声明: <C> 条 (Part 3)
下一步: <next_action.hint, 例如 "§1 SKIP 后自动推进到 §2 STANDARD">
👉 完整查看: cat papers/<dated-slug>/progress.json
👉 上次读到的章节: cat papers/<dated-slug>/deep-read.md  (滚到末尾)

接下来:
  [1] 继续 → 按 next_action 推进
  [2] 重读上一章 → 重写 §<X>
  [3] 跳到 Stage 3 → 直接合卷
  [4] 重新分诊 → 备份后从 Stage 0 重来
```

恢复进度的判断规则 (无 progress.json 时的 fallback):
- 仅 `ReadingPlan.md` 存在 → 已完成 Stage 0, 进 Stage 1
- `ReadingPlan.md` + `deep-read.md` 存在 → 检查 deep-read.md 末尾最新章节号, 询问"从 §<N+1> 继续 / 重读 §N / 跳到 Stage 3"
- 三/四文件齐全 → 询问"重看 reading-notes.md / 仅追加问答 / 重做 Stage 3"

> **Fallback 触发后, 立刻在恢复阶段把 progress.json 补出来** (从 ReadingPlan / deep-read 读出已有信息), 之后继续按正常 progress.json 流程跑。

抓取论文内容 (**HTML 优先, PDF 辅助**):

> **为什么 HTML 优先**: 部分 arXiv 论文 (LaTeX 投稿) 提供 `https://arxiv.org/html/<id>` 的 LaTeXML/ar5iv 渲染版。它带**显式的 `<section>` 结构、带编号的标题层级、`ltx_abstract` 摘要块、`figcaption` 图表标题**, 比 PDF 的字体/坐标启发式切分**更干净、更准、零依赖** (纯 stdlib, 不需要 PyMuPDF)。因此 arXiv 路径**默认先试 HTML, 失败再退回 PDF**。本地 PDF 路径不受影响。

- **arXiv 路径 (HTML 优先三级链)**:
  1. **① HTML (首选)** — 从 arXiv ID 拼出 `https://arxiv.org/html/<id>`, 调用 HTML 切分脚本 (见下)。脚本会把 HTML 存档思路同 PDF: 同时用 `curl -sL "https://arxiv.org/html/<id>" -o "<paper_dir>/source.html"` 留一份本地存档。**无论 HTML 是否成功, 都额外 `curl` 下载一份 PDF 存档到 `<paper_dir>/source.pdf`** (arXiv 论文一定有 PDF; 供公式/图表回查、离线阅读、和 HTML 交叉核对)。退出码 `0` = 切分成功, 直接进 Stage 0 (仍保留已下的 PDF 存档)。
  2. **② PDF (辅助)** — 若 HTML 脚本退出码非 0 (404 无 HTML 版 / 内容过短 / 0 章节), **自动退回 PDF**: 优先 `/arxiv` skill 拿元数据 + PDF; 不可用则 `curl` 下载 PDF 到 `<paper_dir>/source.pdf`, 再走 PDF 切分脚本。
  3. **③ 摘要页兜底** — HTML、PDF 都拿不到结构时, `WebFetch` 抓 `https://arxiv.org/abs/<id>` 至少补齐 title + abstract (见"切分失败三级回退")。
- **本地 PDF 路径**: 复制（或 symlink）到 `<paper_dir>/source.pdf`, 直接走 PDF 切分脚本 (无 HTML 可用)。
- **其他 URL**:
  - 若是已知的论文 HTML 页 (含 `arxiv.org/html/`、ar5iv、期刊 HTML 全文), 先试 HTML 切分脚本。
  - 否则 `WebFetch` 抓取, 失败则告知用户改用 arXiv 链接或本地 PDF。

**① HTML 切分 (首选)** —— 调用 `scripts/html_to_sections.py` (详见脚本头注释):

```bash
# arXiv ID 形如 2604.18486 或 cs/0301013, 从输入解析得到
python3 "<SKILL_ROOT>/scripts/html_to_sections.py" \
    "https://arxiv.org/html/<id>" \
    --output "<paper_dir>/sections.json"
HTML_RC=$?
# 顺手留一份 HTML 本地存档 (供回查 / 离线)
curl -sL "https://arxiv.org/html/<id>" -o "<paper_dir>/source.html" 2>/dev/null || true
# 同时下载 PDF 存档 (arXiv 一定有 PDF; 即使 HTML 切分成功也保留, 供公式/图表回查、离线、交叉核对)
curl -sL "https://arxiv.org/pdf/<id>" -o "<paper_dir>/source.pdf" 2>/dev/null || true
```

> **为什么 HTML 成功也要下 PDF**: HTML 切分只用于喂给下游 prompt (省 token、结构准), 但 HTML 渲染版偶有公式/图表丢失或错排; PDF 是作者投稿的权威版式, 留一份供 (a) 回查复杂公式/图表原貌 (b) 离线阅读 (c) 与 HTML 交叉核对可疑内容。下载失败 (`|| true`) 不阻塞流程——HTML 已足够进 Stage 0。

- **依赖**: 纯 Python stdlib (urllib + html.parser), **无需 pip 安装**。
- **退出码语义** (决定是否退回 PDF):
  - `0` — 健康 (`n_sections ≥ 1` 且有 title/abstract): 直接进 Stage 0 (PDF 已作存档下载, 但**不走 PDF 切分**——sections.json 用 HTML 版即可)。
  - `1` — 已抓到 HTML 但退化 (0 章节 / 疑似无 HTML 版): **退回 ② PDF**。
  - `2` — 获取失败 (常见 404 = 该论文无 HTML 版): **退回 ② PDF**。
  - `3` — 解析异常: **退回 ② PDF**。
- **输出 schema 与 PDF 一致**: `html_to_sections.py` 产出的 sections.json 字段与 `pdf_to_sections.py` **完全对齐** (`title/abstract/n_sections/sections[]/captions[]`), 仅 `backend="arxiv-html"`、`page`/`n_pages` 为 `null`、多一个 `source_html` 字段。下游 triage / deep-read / synth **无需改动即可消费**。

**② PDF 切分 (HTML 不可用时辅助)** —— 调用 `scripts/pdf_to_sections.py`（详见脚本头注释）:

```bash
# 仅在 HTML_RC != 0 时执行
python3 "<SKILL_ROOT>/scripts/pdf_to_sections.py" \
    "<paper_dir>/source.pdf" \
    --output "<paper_dir>/sections.json"
```

**PyMuPDF 依赖自检**（仅 PDF 路径需要）：脚本第一步检查 `PyMuPDF` 是否安装，没有时输出友好提示:

```
[paper-read] 未检测到 PyMuPDF。请运行: pip install pymupdf
（或: pip3 install pymupdf；conda 用户: conda install -c conda-forge pymupdf）
```

> **注意**: HTML 路径无任何 pip 依赖。只有退回 PDF 路径才可能触发 PyMuPDF 自检。

#### 切分失败回退阶梯 (HTML → PDF → 摘要页 → 手动)

无论走 HTML 还是 PDF 切分, 调用脚本后**必须**验证 sections.json 质量, 不能盲目进入 Stage 0:

```bash
N_SEC=$(python3 -c "import json; d=json.load(open('<paper_dir>/sections.json')); print(d['n_sections'])" 2>/dev/null || echo 0)
ABS_LEN=$(python3 -c "import json; d=json.load(open('<paper_dir>/sections.json')); print(len(d.get('abstract','')))" 2>/dev/null || echo 0)
BACKEND=$(python3 -c "import json; print(json.load(open('<paper_dir>/sections.json')).get('backend','?'))" 2>/dev/null || echo "?")
```

- **健康** (`N_SEC ≥ 3` 且 `ABS_LEN ≥ 100`): 直接进 Stage 0 (HTML 源常一次到位)
- **退化级 0 (HTML → PDF)** — HTML 脚本退出码非 0, 或产出 `N_SEC < 3` / `ABS_LEN < 100`: **退回 PDF 路径** (下载 PDF + `pdf_to_sections.py`), 重新验证。这是 arXiv 论文最常见的回退方向。
- **退化级 1 (PDF backend 内部)** — 未安装 PyMuPDF 时脚本自动尝试 `pdftotext`；若 PyMuPDF 已安装但结果较弱，人工核对原 PDF，必要时另用 `pdftotext -layout` 读取正文；脚本不会自动按解析质量切换后端
- **退化级 2 (摘要页兜底)** — HTML、PDF 都得到章节数 = 0 或 abstract 空: 用 `WebFetch` 抓 arXiv abs 页 / DOI 着陆页, 至少拿到 title + abstract + 章节列表, 写入 `<paper_dir>/sections.json` 的对应字段
- **退化级 3** — 完全无法机器解析 (扫描版无 OCR / 公式图扫描): 不要硬撑, 用 AskUserQuestion 让用户三选一:

  | 选项 | 动作 |
  |------|------|
  | 手动粘贴 (Recommended) | 让用户依次粘贴 title / abstract / 章节列表 / Intro 全文, 写入 sections.json 的最小可用字段 |
  | 改用 OCR | 提示 `ocrmypdf source.pdf source-ocr.pdf` 后重跑 |
  | 仅速览模式 | 跳过 sections.json, 用 PDF 直接进 Stage 0 速览 (建议深度=速览, 仅做分诊不精读) |

**禁止行为**: 拿到 `n_sections=0` 的 sections.json 还硬塞给 Stage 0, 会让 triage / deep-read 全程胡编。

### Step 1: 执行 Stage 0 — TRIAGE

加载 prompt: `<SKILL_ROOT>/prompts/triage.md`

按该 prompt 完成苏格拉底分诊。产出 `<paper_dir>/ReadingPlan.md`。

**Stop & Confirm**: 把 ReadingPlan 展示给用户，等用户确认或修改后再进入 Stage 1。

### Step 2: 执行 Stage 1+2 — DEEP READ (合并)

加载 prompt: `<SKILL_ROOT>/prompts/deep-read.md`

按该 prompt：

1. 先生成 `<paper_dir>/deep-read.md` 的 § 0 扩展引言段；展示并停下接受用户提问。
2. 用户说"开始精读"或"下一章"后，**逐章追加**到同一个 `deep-read.md` 文件（用 `## §X` 二级标题分隔），不再为每章建独立文件。
3. 每章末追加三选项暂停。**绝不自动连读**。
4. 全程把问答、未解疑点、声明-证据条目**追加**到同一个 `<paper_dir>/qa-log.md`（按 section 分块）。

### Step 3: 执行 Stage 3 — SYNTHESIZE

加载 prompt: `<SKILL_ROOT>/prompts/synth.md`

产出 **1 份**最终文档 `<paper_dir>/reading-notes.md`，内嵌：

- ⚡ 三档摘要（原 summary.md 的内容）
- 📜 声明清单 + 强度评分（原 claims.md 的核心表）
- 🗡️ 200 字 reject + 🛡️ 200 字 defense（原 kill-argument.md）
- 🔧 可继承资产 + 弱点 + 延伸 RQ（原 takeaway.md）
- 📚 精选 Q&A（从 qa-log 选 3-8 条）
- 🔁 3 个月复习题（3 道）
- 🔗 关联文档链接

随后在 `<OUTPUT_BASE>/reading-notes/` 下建立**相对软链接**：

```bash
cd "<OUTPUT_BASE>/reading-notes" && \
ln -sf "../papers/<dated-slug>/reading-notes.md" "<dated-slug>.md"
```

确保使用相对路径，整个工作树移动后链接仍有效。

可选：如果 ReadingPlan 标记"复现骨架=是" **且** 用户读完后明确说要复现骨架，才单独生成 `<paper_dir>/reproduce-skeleton.md`；否则不生成。

**Stop & Confirm**: 询问是否写入 research-wiki（如果项目下有 `research-wiki/` 目录）:

```
检测到 research-wiki/。需要把本篇沉淀进知识库吗？(将调用 /wiki-enrich 或 research_wiki.py)
```

## 触发词

| 用户说 | 触发动作 |
|--------|---------|
| `/paper-read <input>` | 全流程 |
| `/paper-read <input> --quick` | 跳过 Stage 0 |
| `/paper-read --stage deep` | 仅 Stage 1+2 |
| `/paper-read --stage synth` | 仅 Stage 3 合卷 |
| "精读这篇 <link>" | 全流程 |
| "帮我读这篇论文 <link>" | 全流程 |
| "read this paper <link>" | 全流程 |
| "下一章" / "继续" | Stage 2 推进 |
| "跳过本章" | Stage 2 跳过 |

## 终端回显规则 (Token 节省核心)

**原则**: 凡是已经写入文件的长内容, 终端不再重复输出。每个阶段写盘后, 只回显:

- 文件路径 + 新增字数估算
- ≤ 200 token 的结构骨架预览
- 下一步可选动作

### 公式书写规则 (LaTeX in files, plain in terminal)

**核心**: **写盘的 markdown 文档里, 所有公式一律用 LaTeX 书写** (行内 `$...$`, 独立公式 `$$...$$`); **终端回显里绝不用 LaTeX**, 改用纯文本 (Unicode 符号 / ASCII)。

| 位置 | 公式写法 | 理由 |
|------|---------|------|
| `deep-read.md` / `reading-notes.md` / `qa-log.md` 等**写盘文档** | LaTeX (`$D_{\text{KL}}(v_i\|v_j)=\sum_a \pi_\theta(a\|s_i)\log\frac{\pi_\theta(a\|s_i)}{\pi_\theta(a\|s_j)}$`) | markdown 渲染器 (含 KaTeX/MathJax) 能正常显示, 三个月后回看是干净排版 |
| **终端回显** (摘要/骨架/三选项/Q&A 短摘要) | 纯文本 (`D_KL(v_i‖v_j) = ∑_a π(a|s_i) log[π(a|s_i)/π(a|s_j)]`) | 终端**无法渲染 LaTeX**, 打 `$\frac{}{}$` 只会显示一堆反斜杠, 反而更难读 |

**转写约定** (终端纯文本):
- 下标用 `_`: $x_t$ → `x_t`; 上标用 `^`: $v^+$ → `v^+`
- 分式用 `[分子/分母]` 或 `a/b`: $\frac{a}{b}$ → `[a/b]` 或 `a/b`
- 常用符号用 Unicode: `∑ ∏ ∫ √ ≤ ≥ ≠ ≈ × ÷ ± ∞ ∈ ∉ ⊂ ∪ ∩ → ⇒ ∀ ∃ ∇ ∂ θ π λ γ δ ε σ μ β α ‖ ·`
- 复杂多行推导: 终端只给"一句话直觉 + 公式编号", 完整 LaTeX 留在文件里 (符合"写盘即少回显")

**禁止**: 在终端输出 `$...$` / `$$...$$` / `\frac` / `\sum` 这类裸 LaTeX 源码 (用户看到的是未渲染的反斜杠, 不是公式)。

### 各阶段回显模板

**Stage 0 写完 ReadingPlan**:
```
== Stage 0 分诊完成 ==
文件: papers/<dated-slug>/ReadingPlan.md
建议深度: <精读/正读/速览/跳过>
重点章节: §X, §Y  | 可跳过: §Z
🚩 红旗: <1 句话, 多个用逗号>  🟢 绿旗: <同>
👉 完整查看: cat papers/<dated-slug>/ReadingPlan.md
[确认开始 / 调整配置]
```

**Stage 1 § 0 扩展引言写完**:
```
== § 0 扩展引言完成 ==
文件: papers/<dated-slug>/deep-read.md (新增约 <N> 字)
骨架: ① 背景 → ② Gap → ③ 核心洞察 → ④ 方法概览 → ⑤ 实验 → ⑥ 贡献 → ⑦ 结论
核心洞察一句话: <30 字内>
🚩 已看出的疑点: <若有, 一句话>
👉 完整查看: cat papers/<dated-slug>/deep-read.md
[开始精读 / 提问 / 重写某段]
```

**Stage 2 每章写完**:
```
== §X <章节英文标题> 精读完成 ==
文件: deep-read.md (新增约 <N> 字, 翻译策略: FULL/STANDARD/DIGEST/SKIP)
本章骨架:
  · §X.1 <小节> · §X.2 <小节> ...
  · 关键公式: <若有, 仅给编号和 1 句直觉>
  · 关键图: <Fig.X — 一句话>
核心声明 C-X.1 (强度: 强/中/弱): <≤ 30 字>
反问已生成: Q1 理解 / Q2 假设 / Q3 替代 / Q4 实验 / Q5 边界 (按 ReadingPlan 强度增减)
👉 完整查看: cat papers/<dated-slug>/deep-read.md
[继续 §<X+1> / 提问 / 跳过 §<X+1>]
```

**Stage 3 reading-notes 写完**:
```
== Stage 3 合卷完成 ==
文件: papers/<dated-slug>/reading-notes.md
一句话定位: <抄文件里的"🎯 一句话定位">
声明评分: 强 X 条 / 中 Y 条 / 弱 Z 条 / 无证据 W 条
软链接: reading-notes/<dated-slug>.md → ../papers/<dated-slug>/reading-notes.md
👉 完整查看: cat papers/<dated-slug>/reading-notes.md
[3 个月后回看 / 沉淀到 wiki / 找相关工作]
```

### 兜底机制

- 用户随时可说 "show §X" / "完整显示第 X 章" / "终端打印" → 此时才把对应章节内容输出到对话。
- 用户提的实质性**问答**仍然在对话里完整回答 (不写文件的部分), 不受此规则限制。
- **写盘失败 / 不完整** 时必须把内容回显到对话, 让用户能看到。

### qa-log.md 写盘约定 (与 deep-read / reading-notes 一致)

**核心原则**: qa-log.md **沿用 "写盘即少回显" 主规则** — 完整内容写盘, 终端只给短摘要。

| 内容类型 | 终端 | qa-log.md |
|---------|------|----------|
| 章节翻译 / 扩展引言 / 合卷笔记 (deep-read / reading-notes) | 短预览 (≤200 token) | 完整内容 |
| **用户提问的实质性回答** | **短摘要 (3-6 行: 一句话结论 + 关键要点 bullet)** | **完整解释 (含表格/伪代码/ASCII 图/推导链)** |
| 简单的进度提示 / 三选项菜单 | 显示 | 不写 |

**为什么 qa-log 也要遵守"少回显"**:
- 用户**不需要终端是文件副本**; 终端是导航/进度面板, 文件才是档案。
- 完整解释占 token 多, 在终端打两遍是浪费; 用户想看完整解释 → `cat papers/<dated-slug>/qa-log.md` 就行。
- 三个月后回看靠文件; 当下复习靠"终端摘要 + 必要时翻文件", 不靠"终端长输出"。

**正确行为**:
- ✅ Claude 内部先写出完整解释 (含表格 / 伪代码 / ASCII 图 / 推导链), **直接 append 到 qa-log Part 1**。
- ✅ 终端只输出**3-6 行短摘要**: 一句话结论 + 2-4 个关键 bullet + `👉 完整解释: cat papers/<dated-slug>/qa-log.md` 跳转提示。
- ✅ 用户说 "show qa Q3" / "终端打印 Q3 完整版" 时, 才把对应 Q&A 完整输出到对话。
- ✅ 用户挑出歧义后的"修订版表述", 修订版并入 qa-log 对应条目, 终端只回"已修订, 见 Q<n>.A.<x>"。

**禁止行为**:
- ❌ 在终端打完整的表格/推导链, 然后又把同样内容写盘 (重复占 token)。
- ❌ 写盘只写要点版, 把完整解释只留在终端 (终端日志会消失, 档案残缺)。
- ❌ qa-log 只写一句结论, 完整推理过程靠用户自己回去翻对话历史。

**终端摘要模板** (Q&A 答完后的短回显):

```
== Q<n> 已答 + 写入 qa-log ==
一句话结论: <≤30 字>
关键要点:
  · <bullet 1, ≤20 字>
  · <bullet 2, ≤20 字>
  · <bullet 3, ≤20 字>
👉 完整解释 (含表格/伪代码/推导): cat papers/<dated-slug>/qa-log.md
```

**qa-log Part 1 写入模板** (与之前一致, 完整版):

```markdown
### [§X 全局/章节] Q<n>: <一句话问题摘要>

**时间**: 2026-06-07 13:21 (北京时间)

**Q**: <用户原问 (原文照抄)>

**A**: <完整解释, 含所有表格/伪代码/ASCII 图/推导链>

#### A.1 <子标题 1>
...

**标签**: #stageX #topic1
```

> **时间戳要求**:
> - **必须用当前真实时间**, 不要凭印象/推断填 — 写盘前先 `TZ=Asia/Shanghai date "+%Y-%m-%d %H:%M"` 取一下
> - **格式**: `YYYY-MM-DD HH:MM (北京时间)` (人类可读, 不用 ISO 那种 `T...+08:00` 的机器格式)
> - **位置**: 标题下方独立一行 `**时间**: ...`, **不要塞进标题** (标题留给主题摘要, 干净好扫)
> - **粒度**: 分钟即可, 用于回看时还原 Q&A 先后顺序 (同一会话连续多个 Q 时间可相同, 不强求秒级)
> - **追溯回填**: 若是给历史 Q&A 补时间戳, 加备注 `(追溯回填, ±数分钟)` 提醒精度

## progress.json 断点续读元数据

每个 `<paper_dir>/` 维护一份 `progress.json`, 是**断点续读的 source of truth**。每次写盘都更新它, 新会话/隔段时间回来都先读它。

### Schema

```json
{
  "slug": "lu-2026-onevl",
  "dated_slug": "06-06-lu-2026-onevl",
  "title": "Xiaomi OneVL: One-Step Latent Reasoning ...",
  "arxiv_id": "2604.18486",
  "paper_dir": "/abs/path/to/papers/06-06-lu-2026-onevl/",
  "created": "2026-06-06T23:52+08:00",
  "last_updated": "2026-06-07T00:53+08:00",

  "current_stage": "stage2",
  "stages_completed": ["stage0", "stage1"],
  "stages_pending": ["stage2", "stage3"],

  "sections_total": 10,
  "sections_done": [
    {"id": "§0", "title": "扩展引言", "strategy": "—", "ts": "2026-06-07T00:15+08:00", "new_chars": 15800},
    {"id": "§1", "title": "Introduction", "strategy": "SKIP", "ts": "...+08:00", "new_chars": 320}
  ],
  "sections_pending": [
    {"id": "§2", "title": "Related Work", "strategy": "STANDARD"},
    {"id": "§3", "title": "Method (Architecture)", "strategy": "FULL"}
  ],

  "next_action": {
    "stage": "stage2",
    "section_id": "§2",
    "strategy": "STANDARD",
    "hint": "进入 §2 Related Work, 重点展开 COCONUT/CODI/SIM-CoT 机制"
  },

  "qa_count": 6,
  "open_questions_count": 6,
  "claims_count": 5,
  "critical_questions_count": 1,

  "config": {
    "translation_default": "STANDARD",
    "critique_strength": "中",
    "cot_callout_mode": true,
    "reproduce_skeleton": false
  },

  "session_log": [
    {"ts": "2026-06-06T23:55+08:00", "event": "Stage 0 ReadingPlan written"},
    {"ts": "2026-06-07T00:15+08:00", "event": "§0 extended intro written", "new_chars": 15800},
    {"ts": "2026-06-07T00:30+08:00", "event": "Q1-Q4 answered", "qa_added": 4},
    {"ts": "2026-06-07T00:53+08:00", "event": "Q5-Q6 answered + sentence revision", "qa_added": 2}
  ]
}
```

### 写入时机 (强制)

| 触发 | 更新字段 |
|------|---------|
| Stage 0 写完 ReadingPlan | `stages_completed += ["stage0"]`; `current_stage = "stage1"`; 解析 ReadingPlan 的"全局阅读地图"填 `sections_pending`; `next_action = {stage:"stage1", section_id:"§0", ...}`; `config` |
| §0 扩展引言写完 | `sections_done += [{"id":"§0",...}]`; `sections_pending` 弹出 §0; `current_stage="stage2"`; `next_action` 指向第一个非 SKIP 章 |
| 每章 §X 写完 | `sections_done += [...]`; `sections_pending` 弹出 §X; `next_action` 指向下一个未读章 (含其策略) |
| Q&A 答完 | `qa_count++`; 如打了 `#critical-question`, `critical_questions_count++` |
| 章末追加未解疑点/声明 | `open_questions_count`, `claims_count` 累加 |
| Stage 3 写完 reading-notes | `stages_completed += ["stage3"]`; `current_stage="done"`; `next_action = {stage:"done", hint:"3 个月后回看 / 沉淀到 wiki"}` |
| 任何写盘 | `last_updated`; `session_log` 追加一条 |

### 实现约束

- **轻量**: 用 `python3 -c "import json; ..."` 内联读写, 不写脚本
- **`dated_slug` 一次写定**: Stage 0 创建时写入 `dated_slug` (= `<MM-DD>-<slug>`) 与 `paper_dir`；`dated_slug` 之后**永不修改**，不重算日期。跨电脑移动资料夹后，以实际输出根目录与固定 `dated_slug` 重新解析 `paper_dir`，并更新失效的旧绝对路径。
- **原子写**: `json.dump → tmp → os.replace` (避免半截写入坏掉)
- **不超 50KB**: `session_log` 超过 50 条时, 只保留最近 30 条
- **不进 deep-read.md / qa-log.md**: 这是元数据, 不进主文档
- **可被用户读懂**: JSON 字段名都用英文, 但 `hint` 字段允许中文
- **时间戳用北京时间 (UTC+8) 且显式标注时区**: 格式 `YYYY-MM-DDTHH:MM+08:00` (ISO 8601 with offset)。默认所有 `created` / `last_updated` / `sections_done[].ts` / `session_log[].ts` 都用这个格式。**禁止裸时间戳** (会被误读成 UTC)。

### 终端断点摘要 (新会话回来必显示)

每次启动时, 如果 `progress.json` 存在, **第一件事是输出断点摘要** (模板见上方"幂等检查"小节), 让用户瞬间对齐"上次读到哪了"。这是断点续读的核心 UX。

## 分级翻译策略 (章节级)

`ReadingPlan.md` 中的"全局阅读地图"表为**每个章节**单独指定翻译策略, 四档:

| 策略 | 内容 | 适用 |
|------|------|------|
| `SKIP` | 不翻译, 章末仅 2 句小结 | 已在 § 0 覆盖的 Intro/Conclusion |
| `DIGEST` | 4-6 句中文摘要式概括 | Related Work, 已熟悉的 Background |
| `STANDARD` (默认) | 关键段中译 + 其余意译 + 公式逐行 + 图表 caption 中译 | 常规章节 |
| `FULL` | 完整逐段中译 + 术语对照 + 公式逐行 + 推导提示 | 重点 Method / Results / 不熟领域 |

Stage 0 客观分诊时根据 Q2 (期望收获)、Q3 (背景熟悉度)、章节性质**自动建议**, 用户可调。无脑全文 FULL 是反模式。

## 关键规则

- **三阶段之间必须停下等用户**。绝不连贯执行到底而不交互。
- **每章精读后给三选项**: `继续 / 提问 / 跳过`。
- **苏格拉底反问每题都带"跳过"选项**。读完后还可根据本论文实际内容追加新问题。
- **分级翻译**: 按 ReadingPlan 中每章的策略执行 (SKIP/DIGEST/STANDARD/FULL), 不一刀切。
- **写盘即少回显** (含 qa-log): 完整内容写盘, 终端只给短摘要 (3-6 行: 一句话结论 + 关键 bullet + cat 跳转提示)。三个月后回看靠文件, 当下导航靠终端摘要。详见 "qa-log.md 写盘约定"。
- **每次写盘必更新 progress.json**: Stage 0 / §0 / 每章 / Q&A / Stage 3 完成后, **同一回合**内更新 `progress.json` 的 `current_stage` / `sections_done` / `next_action` / `last_updated`。详见 "progress.json 断点续读元数据" 节。
- **新会话回来必显示断点摘要**: 用户隔几天/新对话再来时, 若 `progress.json` 存在, 第一句话就是断点摘要 + 三选项 (继续/重读/Stage 3/重新分诊), 不要直接动笔。
- **客观分诊不替用户决定**: 给建议（精读/正读/速览/跳过），最终决定权在用户。
- **批判不要客气**: kill-argument 阶段必须以 reject 视角写。
- **永远 traceback**: deep-read 与 reading-notes 中的论点都标 `[源自 §X]`。
- **公式: 文档用 LaTeX, 终端用纯文本**: 写盘的 markdown (`deep-read.md`/`reading-notes.md`/`qa-log.md`) 里公式一律 LaTeX (`$...$`/`$$...$$`, 渲染后正常显示); 终端回显绝不打裸 LaTeX, 改用 Unicode/ASCII 纯文本 (终端无法渲染 LaTeX)。详见 "终端回显规则 → 公式书写规则"。
- **外部引用必查证, 禁止凭记忆瞎编** (防幻觉硬规则):
  - **触发判定**: 用户的提问 / 你要写的内容是否涉及**当前 PDF 正文之外**的事实? 包括: 某被引论文 / 相关工作**具体做了什么**、它的方法或数字、某概念/方法的出处、领域背景的具体事实。
    - **是** → **必须先实际检索查证再回答**, 禁止纯凭训练记忆作答。按准确度链调用: `/semantic-scholar` → (预印本) `/arxiv` → `/openalex` → (兜底) `mcp__exa-key__web_search_exa` (`category:"research paper"`) / `WebSearch`。详见上方 "精读中查证外部引用的工具链"。
    - **否** (问的是本文方法/公式/实验本身) → 用 `[源自 §X]` 即可, 无需外部检索。
  - **三态出处标注** (查证结果必须诚实分档, 绝不含糊):
    - `[据检索: <标题 / arXiv ID / URL>]` — 已实际查证, 给出可点击/可核对来源。
    - `[本文转述: §X]` — 只复述了**本文作者对该工作的描述** (未独立核原文, 可能带本文作者偏见), 显式提示用户。
    - `⚠️[未能查证]` — 没搜到 / 搜到的不可靠: 明确告知"以下是我的印象, **未经核实**, 建议你自查 X", **绝不**伪装成已知事实。
  - **Why**: 被引论文的细节不在当前 PDF 里, 模型只能靠记忆 → 高幻觉风险 (记错方法 / 张冠李戴 / 编数字)。本规则把"编造"强制转为"查证或标注不确定", 保证精读输出**有迹可循**。
  - **"搜不到 ≠ 编 / 也 ≠ 不存在"**: 查证失败只能标 `⚠️[未能查证]` (= 没查到, 建议自查), **绝不**凭记忆补一个看似合理的来源, 也**绝不**反向断定"该论文/ID 不存在"。否定存在性的唯一充分证据是权威库 abs 页明确 not-found; 作者页 404 / 搜索无结果 / 时间线看着可疑都不算。
  - **subagent 查证结论要复核**: 把查证派给 subagent 时, 它的否定/存在性结论不能直接采信, 亲自复核关键断言一次 (自己 fetch 该 abs 页)——subagent 可能误读或用无效证据下结论。
  - **不滥查**: 常识性背景、或本文已说清的内容, 不必联网; 精读主流程 (翻译 + 解读本文) 仍只读已切分的 sections.json (HTML 或 PDF 来源)。只在涉及外部事实且用户追问时触发, 默认偏向"宁可查"。
- **产出位置必询问**: 默认 `./papers/<dated-slug>/`，必须用 AskUserQuestion 确认。
- **HTML 优先, PDF 辅助**: arXiv 输入**先试 `https://arxiv.org/html/<id>`** (`html_to_sections.py`, 纯 stdlib 零依赖, 切分更准); 退出码非 0 或 `n_sections<3` 才退回 PDF (`pdf_to_sections.py`)。本地 PDF 直接走 PDF 路径。HTML 源的 sections.json `page` 为 null, 原文索引省略页码。详见 Step 0 "抓取论文内容"。
- **PyMuPDF 自检**: 仅 PDF 路径需要; scripts/pdf_to_sections.py 第一步检查依赖，给出 pip 命令而非直接报错退出。HTML 路径无 pip 依赖。
- **Large file handling**: 如果 Write 因体积失败，立即改用 Bash heredoc (`cat <<'EOF' > file`) 分块写入，不询问用户。


## 输出目录结构

```
<OUTPUT_BASE>/
├── papers/
│   └── <dated-slug>/                  # 单篇资料夹, 名形如 06-11-vaswani-2017-attention
│       ├── source.html               # 原始 HTML 存档 (HTML 源时, 首选路径)
│       ├── source.pdf                # 原始 PDF (PDF 源时, 或 HTML 不可用退回)
│       ├── sections.json             # 切分结果 (HTML 或 PDF backend; prompt 消费, 用户少看)
│       ├── ReadingPlan.md            # Stage 0 (含 triage 5 题回答)
│       ├── deep-read.md              # ★ Stage 1+2 合并: 扩展引言 + 逐章精读
│       ├── qa-log.md                 # 全程问答 + 未解疑点 + 声明-证据 (三合一)
│       ├── reading-notes.md          # ★ Stage 3 最终复习笔记 (内嵌精炼版)
│       ├── progress.json             # ★ 断点续读元数据 (Stage 进度 / 当前章 / 下一步)
│       └── reproduce-skeleton.md     # (可选) 仅复现需求 + 用户明确请求时生成
└── reading-notes/                    # 全局笔记夹 (软链接)
    ├── <dated-slug>.md → ../papers/<dated-slug>/reading-notes.md   (相对软链接, 名形如 06-11-vaswani-2017-attention.md)
    └── ...
```

软链接由以下命令创建（在 Step 3 末尾）：

```bash
cd "<OUTPUT_BASE>/reading-notes" && \
ln -sf "../papers/<dated-slug>/reading-notes.md" "<dated-slug>.md"
```

这样 `cat reading-notes/<dated-slug>.md` 等同于 `cat papers/<dated-slug>/reading-notes.md`。

## Composing with Other Skills

```
/arxiv "topic"              -> 找候选论文
   ↓
/paper-read <link>          <- 你在这里 (精读)
   ↓
/research-wiki ingest       -> 沉淀到知识库
   ↓
/research-refine            -> 把读到的 idea 转成自己的方案
```

## 进入哪个 Phase

- 直接执行**所有 Step 0–4**，每阶段之间停下确认；
- 若用户指定 `--stage`，只跑对应 Step；
- 若用户在中途说"重新分诊 / 重读引言 / 重读第 N 章"，回到对应 Step；
- 永远把当前所处的 Stage 显式告知用户。
