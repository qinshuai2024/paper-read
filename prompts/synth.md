# Stage 3 — SYNTHESIZE (合卷, 单文件产出)

## 目标

把分散在 `deep-read.md` 和 `qa-log.md` 中的所有认知**合卷**成**一个文件** `<paper_dir>/reading-notes.md`。该文件是用户日后**反复回看**的复习笔记, 必须精炼、信息密度高、5 分钟可回忆整篇论文。

**不再生成** summary.md / claims.md / kill-argument.md / takeaway.md 等独立文件 —— 全部精炼内嵌到 reading-notes.md 的对应小节。

唯一例外: `reproduce-skeleton.md` 仅在 **ReadingPlan 标记复现=是 且 用户明确说"我要复现骨架"** 时单独生成。

## 路径约定

本文件中所有 `<paper_dir>` 一律解析为 **SKILL.md Step 0 已创建的论文目录绝对路径**:

```
<paper_dir> = <OUTPUT_BASE>/papers/<dated-slug>/
```

> `<dated-slug>` = `<MM-DD>-<slug>` (日期前缀在 Stage 0 创建时定下, 见 SKILL.md DATED_SLUG_RULE)。本阶段从 `progress.json` 的 `dated_slug` 字段读取, 不重算日期。

`<OUTPUT_BASE>` 同时也是 reading-notes/ 全局笔记夹的根目录, 软链接相对路径以此为基。所有写盘命令必须用 SKILL.md 已确定的绝对路径替换占位符。

## 输入

- `<paper_dir>/deep-read.md` (§0 扩展引言 + 全部章节精读)
- `<paper_dir>/qa-log.md` (问答 + 未解疑点 + 声明-证据表)
- `<paper_dir>/ReadingPlan.md`

## 执行步骤

### Step 1: 生成 `reading-notes.md` (单文件)

按下面模板填充。要求所有引用都能 traceback 到 `[源自 §X]`。

```markdown
# Reading Notes: <Title>

**作者**: <First Author et al.>, <Year>, <Venue/arXiv>
**精读日期**: <YYYY-MM-DD>
**阅读时长**: <估算>
**ReadingPlan 深度**: <精读/正读/速览>
**链接**: <arXiv URL> | <原文: HTML 源写 [arXiv HTML](https://arxiv.org/html/<id>); PDF 源写 [原 PDF](./source.pdf)> | [完整精读](./deep-read.md) | [问答日志](./qa-log.md)

---

## 🎯 一句话定位
<25 字以内: 这篇论文做了什么>

## 💡 研究内容
<2-3 句: 具体研究什么问题, 在什么场景下, 输入输出>

## 🤔 动机
<2-3 句: 为什么这事重要, 现有方法的具体痛点>

## ✨ 创新点 (核心贡献)
1. **<创新点 1>**: ... [源自 §X]
2. **<创新点 2>**: ...
3. (如有) **<创新点 3>**: ...

## ⚙️ 主要方法
<3-5 段。含一张 ASCII 框图或文字流程图。
强调: 输入→模块→输出, 训练目标的高层意图, 哪一步是新的, 哪一步是已有的。
公式只列最关键的 1-2 个, 附一句直觉。>

```
[Input X] → [Module A (frozen)] → [Module B (★ new)] → [Output Y]
                                        ↑
                                  loss: L_main + λ L_aux
```

[源自 §3, Fig.1]

## 📊 实验大致结论
<2-3 句: 在哪些 benchmark 上, 对比谁, 提升幅度量级 (大/中/小), 关键消融发现>
[源自 §6]

---

## 📜 声明-证据评分 (内嵌 claims)

> 评分: 强(完整对比+消融+多 seed) / 中(基线不够或缺消融) / 弱(单数字/缺基线) / 无(口头声称)

| ID | 声明 | 证据位置 | Claude 评分 |
|----|------|---------|-----------|
| C-X.1 | ... | Tab.2 | 强 |
| C-X.2 | ... | §X 推导 | 中 |
| C-X.3 | ... | (无) | 无 🚩 |

**与作者贡献清单对照**:
| 作者贡献 | 实际证据 | Claude 评分 | 名实相符? |
|---------|---------|-----------|---------|
| C1: ... | C-X.1 | 强 | 是 |
| C2: ... | (无) | 无 | 否 🚩 |

---

## 🗡️ Kill Argument (内嵌 kill-argument)

### Reject Memo (200 字)
> 严厉但公允的顶会审稿人视角, 论证为何拒稿。

<200 字 reject>

### Defense (200 字)
> 没读过原文的辩护者视角, 针对上面 reject 辩护。

<200 字 defense>

### Verdict
- 最大风险: ...
- 最大让步建议: ...
- 对我的启示: ...

---

## 🚧 局限与风险
- **作者承认的**: ...
- **我读出来的**: ...

## 🔧 可继承资产 (内嵌 takeaway)

### 可借鉴的方法
- <方法/技巧> — 适用场景: ... — 风险: ...

### 可引用的句子
- "..." (§X) — 用法: 综述背景 / 对比基线

### 可批判的弱点
- 弱点 1: ...
- 弱点 2: ...

### 可延伸的研究问题
- RQ-1: ...
- RQ-2: ...

### 应关注的近邻工作
- <Paper A> — 本文未引但应该引
- <Paper B> — 与本文形成对照的并行工作

> ⚠️ 此处列的"本文未引的近邻工作"涉及当前 PDF 之外的知识。**凡写出具体论文名/做法, 必须先检索查证** (`/semantic-scholar` → `/arxiv` → `/openalex` → exa) 并标 `[据检索:...]`; 查不到就标 `⚠️[未能查证]` 或干脆不写, **不要凭记忆编造论文**。

---

## 📚 精选问答 (从 qa-log 选 3-8 条)

> 选 #critical-question 标签的, 加上讨论较多 / Claude 提的好反问。
> 宁缺毋滥, 8 条以内。
> **保留出处标注**: 若某 Q&A 答案带 `[据检索: <来源>]` / `[本文转述:§X]` / `⚠️[未能查证]`, 合卷时**原样保留**, 不要为了精炼把外部来源/不确定标记抹掉 —— 这是有迹可循的关键。

### Q1 [<标签>] <问题, 注明"我问"/"Claude 反问">
**A**: <精炼答案, 保留 [源自 §X] / [据检索:...] / ⚠️[未能查证] 等标注>
**为什么值得记**: <一句话>

### Q2 ...

...

---

## 🔁 三个月后再看时回答这三题 (复习钩子)

> 试着先答, 再看下面的隐藏答案。

1. **<题 1>** (考核核心声明)
   <details><summary>答案</summary>...</details>
2. **<题 2>** (考核方法关键步骤)
   <details><summary>答案</summary>...</details>
3. **<题 3>** (考核局限或批判点)
   <details><summary>答案</summary>...</details>

---

## 🔗 相关文档
- 完整精读 (扩展引言 + 全部章节): [deep-read.md](./deep-read.md)
- 问答日志 + 未解疑点 + 声明-证据全表: [qa-log.md](./qa-log.md)
- 阅读契约: [ReadingPlan.md](./ReadingPlan.md)
- 原文: HTML 源 → arXiv HTML `https://arxiv.org/html/<id>` (或本地 `source.html`); PDF 源 → [source.pdf](./source.pdf)
```

### Step 2: 创建相对软链接 (替代旧索引方式)

```bash
mkdir -p "<OUTPUT_BASE>/reading-notes"
cd "<OUTPUT_BASE>/reading-notes" && \
ln -sf "../papers/<dated-slug>/reading-notes.md" "<dated-slug>.md"

# 验证: 软链接是否真的可读 (Windows/WSL/NTFS 上 ln 可能静默失败)
if [ -L "<dated-slug>.md" ] && [ -r "<dated-slug>.md" ] && head -1 "<dated-slug>.md" >/dev/null 2>&1; then
  echo "[paper-read] ✓ 软链接已创建: reading-notes/<dated-slug>.md"
else
  echo "[paper-read] ⚠ 软链接验证失败 (可能跨文件系统), 回退为硬拷贝"
  rm -f "<dated-slug>.md"
  cp "../papers/<dated-slug>/reading-notes.md" "<dated-slug>.md"
  echo "[paper-read] ⚠ 已用硬拷贝替代; 注意: papers/<dated-slug>/reading-notes.md 后续修改不会自动同步到此处。"
fi
```

**关键点**:
- 用 `-sf` 让重复运行幂等 (覆盖旧链接)
- 用**相对路径** `../papers/...`, 整个目录树移动后链接仍有效
- 软链接名带日期前缀 (`<dated-slug>.md`, 如 `06-11-vaswani-2017-attention.md`), 在 reading-notes/ 里天然按时间排序
- 不再写 markdown 索引文件; 用户 `cat reading-notes/<dated-slug>.md` 等同 `cat papers/<dated-slug>/reading-notes.md`
- **验证三件套** `[ -L ] && [ -r ] && head -1`: 同时确认是链接 + 可读 + 内容可访问
- 硬拷贝兜底时必须在终端明确告知用户"不同步", 以免日后疑惑

### Step 3 (可选): 复现骨架

仅在以下**两个条件同时满足**时生成 `<paper_dir>/reproduce-skeleton.md`:
1. `ReadingPlan.md` 中 "复现骨架=是"
2. 用户在 Stage 3 完成后明确说 "我要复现骨架" / "give me reproduce skeleton" / "出复现骨架"

否则**不生成此文件**, 保持目录精简。

模板见 `templates/reproduce-skeleton.md`。

### Step 4: 询问是否写入 research-wiki

```bash
if [ -d "<OUTPUT_BASE>/research-wiki" ]; then
  # AskUserQuestion: 是否调用 /research-wiki ingest_paper 沉淀
fi
```

不存在则跳过。

### Step 5: 收尾汇报 (按全局回显规则)

**不要在终端重复打印 reading-notes.md 全部内容**。按 SKILL.md "终端回显规则"中 Stage 3 模板回显:

```
== Stage 3 合卷完成 ==
文件: papers/<dated-slug>/reading-notes.md (约 <N> 字)
一句话定位: <抄文件里的"🎯 一句话定位">
声明评分: 强 X 条 / 中 Y 条 / 弱 Z 条 / 无证据 W 条
Kill verdict: <最大风险一句话>
软链接: reading-notes/<dated-slug>.md → ../papers/<dated-slug>/reading-notes.md ✓
👉 完整查看: cat papers/<dated-slug>/reading-notes.md

精简产出 (papers/<dated-slug>/):
  source.pdf / sections.json / ReadingPlan.md / deep-read.md / qa-log.md / reading-notes.md
(可选) 若需复现骨架, 说 "出复现骨架"。

后续:
  · 3 个月后回看 reading-notes.md 末尾的复习题
  · 沉淀到知识库: /research-wiki ingest
  · 找相关工作: /research-lit
```

## 关键规则

- **单文件产出**: `reading-notes.md` 内嵌 summary / claims / kill-argument / takeaway 的精炼版本, 不再分散为 4 个文件。
- **软链接而非索引文件**: `reading-notes/<dated-slug>.md` 用 `ln -sf ../papers/<dated-slug>/reading-notes.md`, 相对路径。
- **复现骨架默认不生成**, 按需才出。
- **精选问答要凶**: 8 条以内, 宁缺毋滥。
- **复习题要刁钻**: 能考到核心声明 / 隐藏假设 / 关键步骤的题才好。
- **永远 traceback**: 每个论点末尾 `[源自 §X]` 不能省。
- **外部来源标注不抹掉**: 精选问答 / 近邻工作 / 可引用句子等涉及外部事实的内容, 合卷时保留 `[据检索:...]` / `[本文转述:§X]` / `⚠️[未能查证]`; 新写外部论文名必须先查证再写, 不凭记忆编。详见 SKILL.md "关键规则"。
- **不替作者圆场**: claims 中"弱声明"敢写"弱"。
