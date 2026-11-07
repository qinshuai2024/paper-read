# Stage 0 — TRIAGE (苏格拉底式分诊)

## 目标

在用户投入大量时间精读之前，**先问清楚他为什么读、读到什么程度**，再用资深科研者眼光对论文做客观分诊，给出"精读 / 正读 / 速览 / 跳过"建议。最终产出 `ReadingPlan.md`，作为后续所有阶段的契约。

## 路径约定

本文件中所有 `<paper_dir>` 一律解析为 **SKILL.md Step 0 创建并已 `mkdir -p` 完成的论文目录绝对路径**, 即:

```
<paper_dir> = <OUTPUT_BASE>/papers/<dated-slug>/
```

其中 `<OUTPUT_BASE>` 是用户 Step 0 确认过的输出根目录 (默认当前工作目录 `./`), `<dated-slug>` = `<MM-DD>-<slug>`, 形如 `06-11-vaswani-2017-attention` (日期前缀见 SKILL.md DATED_SLUG_RULE, 创建时定下不再变)。

写盘时**必须**用 SKILL.md 已计算好的绝对路径, 不要复用 `<paper_dir>` 这个字符串字面量。

## 输入

- `<paper_dir>/sections.json` —— 已切分好的论文结构（至少含 title, authors, abstract, intro 全文, section list, conclusion）
- 用户的初始命令上下文

## 执行步骤

### Step 1: 主观分诊 —— 苏格拉底 5 题

**使用 AskUserQuestion 工具**，一次性提出以下 5 个问题。**每个问题都附带"跳过"选项**。如果用户在最初的命令里已经回答过某题，跳过那一题。

按以下 5 题逐一询问（用 AskUserQuestion 一次性发出，每题独立 single-select；选项末尾都加上 `跳过 / 让 Claude 推断` 兜底）：

| # | header | 问题 | 选项建议 |
|---|--------|------|---------|
| Q1 | 阅读动机 | 你目前在研究 / 关心什么问题？这篇论文如何进入你的视野？ | A. 正在做相关课题 B. 看到引用想追溯 C. 综述调研 D. 单纯好奇 / 学习 E. 跳过 |
| Q2 | 期望收获 | 你期待从这篇论文获得什么？ | A. 方法借鉴 (核心算法/架构) B. 完整复现 C. 综述定位/相关工作 D. 批判性反驳素材 E. 仅了解大意 F. 跳过 |
| Q3 | 背景熟悉度 | 你对这个子领域已有什么背景？ | A. 小白 (术语都不太懂) B. 初学 (读过 1-2 篇) C. 熟悉 (能讨论) D. 同行 (在做相关工作) E. 跳过 |
| Q4 | 时间预算 | 你的时间预算是？ | A. 10 分钟速览 B. 1 小时正读 C. 3 小时精读 D. 含复现的深度阅读 E. 跳过 |
| Q5 | 信任先验 | 你对作者 / 团队 / 期刊会议会议有先验印象吗？ | A. 强信任 (大牛/顶会) B. 中等 C. 不熟悉 D. 有疑虑 (听说水/争议) E. 跳过 |

把回答汇总**直接内嵌**到 `<paper_dir>/ReadingPlan.md` 的"用户分诊回答"段（**不再生成独立的 triage-answers.md**）。对于"跳过"的题，写入 "用户跳过；Claude 推断：..."并基于已有信息合理推测。

### Step 2: 客观分诊 —— Claude 视角

读完 sections.json 中的 title/abstract/intro/conclusion 后，**像资深科研者一样**做 6 项客观判断：

1. **核心声明 (1 句话)**：这篇论文最核心的"我们做到了 X"是什么？
2. **论文类型**：
   - 新方法 (new method)
   - 新理论 (new theory)
   - 新数据集/benchmark
   - 综述 (survey)
   - 实证研究 (empirical study)
   - 立场/意见 (position paper)
   - 工程报告 (system/engineering)
3. **可复现性信号**：是否开源？有代码？有数据？有详细超参？
4. **与用户问题的相关性**：基于 Q1/Q2 答案，0-5 分打分，并给 1 句话理由。
5. **🚩 红旗信号清单** (每条都引用 1 句原文佐证)：
   - 自卖自夸语言密度 ("first", "state-of-the-art", "novel" 滥用)
   - 是否缺 ablation
   - 是否缺关键基线
   - 是否说 "first" 但没引用近 1-2 年的近邻工作
   - 实验规模是否过小 / 数据集是否过窄
   - 是否过度依赖单一指标
   - 是否回避了显然该比较的对手方法
6. **🟢 绿旗信号清单**：
   - 是否清晰承认 limitations
   - 是否给了消融
   - 是否提供 failure cases
   - 是否给了多个 seeds / 置信区间
   - 是否开源 + 文档齐全

### Step 3: 综合建议 —— 给阅读决策

基于 Step 1 + Step 2，给出**资深科研者会给的建议**：

- **建议读到的深度**: 精读 / 正读 / 速览 / 跳过
- **理由 (3 句以内)**
- **预计阅读时长**（与用户时间预算对比，若不匹配明确指出）
- **重点章节**（哪些必读）
- **可跳过章节**（哪些可以略过）
- **阅读时要特别警惕的点**（基于红旗信号）

### Step 4: 写入 ReadingPlan.md

用 `templates/ReadingPlan.md` 作为骨架，填充完毕后写入 `<paper_dir>/ReadingPlan.md`。

#### 阅读深度配置 (全局)

- **公式推导**: 默认"按需"; 若用户 Q2=B (复现) 或 Q3=D (同行) → 升为 "必须"。
- **复现骨架**: 默认"否"(仅在 Stage 3 用户明确请求时才单独生成); 若 Q2=B (复现) → 改为"是"。
- **批判问答强度**: 默认 "中"(每章 3 题); 若 Q2=D (批判反驳素材) → "高"(每章 5 题); 若 Q4=A (10 分钟速览) → "低"(每章 1-2 题)。

#### 章节级翻译策略 (核心)

不再有全局的"翻译详尽度"开关, 改为**逐章节**给出翻译策略, 写入"全局阅读地图"表。

四档:

| 策略 | 内容 | 默认适用 |
|------|------|---------|
| `SKIP` | 不翻译, 章末 2 句小结即可 | Intro / Conclusion (已被 § 0 扩展引言覆盖) |
| `DIGEST` | 4-6 句中文摘要式概括 | Related Work, Background (除非 Q3=A 小白) |
| `STANDARD` | 关键段中译 + 其余意译 + 公式逐行 + 图表 caption 中译 | 一般章节默认 |
| `FULL` | 完整逐段中译 + 术语对照 + 公式逐行 + 推导提示 | 重点 Method / Results 章 |

**自动建议规则**:

```
对每个章节:
  if 章节 ∈ {Introduction, Conclusion} 且 § 0 扩展引言会覆盖:
      strategy = SKIP
  elif 章节 ∈ {Related Work, Background}:
      if Q3 ∈ {A 小白, B 初学}:
          strategy = STANDARD
      else:
          strategy = DIGEST
  elif 章节 ∈ {Method, Approach, Model, Algorithm, Architecture}:
      strategy = FULL
  elif 章节 ∈ {Experiments, Results, Evaluation, Analysis}:
      if Q2 ∈ {A 方法借鉴, B 复现, D 批判反驳}:
          strategy = FULL
      else:
          strategy = STANDARD
  elif 章节 ∈ {Ablation, Discussion}:
      strategy = STANDARD
  elif 章节 ∈ {Appendix, Supplementary}:
      strategy = SKIP
  else:
      strategy = STANDARD
```

特殊覆写:
- 若 ReadingPlan 建议"速览/跳过", 全部章节降一档 (FULL → STANDARD, STANDARD → DIGEST, ...).
- 若 Q2=B (完整复现), 把 Method + Experiments + Training Details 强制升为 FULL.
- 若 Q3=A (小白), 把 Background / Preliminaries 升为 FULL.

用户可在 Stage 0 输出时**逐行调整**。

### Step 5: 展示与确认 (按全局回显规则)

**不要把整份 ReadingPlan 完整打印到终端**。按 SKILL.md "终端回显规则"中 Stage 0 模板回显:

```
== Stage 0 分诊完成 ==
文件: papers/<dated-slug>/ReadingPlan.md
建议深度: <精读/正读/速览/跳过>
重点章节 (FULL 策略): §X, §Y  | 可跳过 (SKIP 策略): §Z
🚩 红旗: <一句话, 多个用逗号>
🟢 绿旗: <一句话>
👉 完整查看: cat papers/<dated-slug>/ReadingPlan.md

如同意按此计划阅读, 回复 "开始" / "进入下一阶段"。
如要调整某章的翻译策略 (如 "§2 改为 STANDARD"), 告诉我即可。
如建议是"跳过"但仍想读, 可直接说"继续", 自动降级配置。
```

**不要自动进入 Stage 1。等用户明确指令。**

## ReadingPlan.md 结构（参考 templates/ReadingPlan.md）

```markdown
# Reading Plan: <Paper Title>

**论文**: <Title>
**作者**: <First Author et al.>, <Year>
**arXiv/DOI**: <id>
**分诊日期**: <YYYY-MM-DD>

## 用户分诊回答
- Q1 阅读动机: ...
- Q2 期望收获: ...
- Q3 背景熟悉度: ...
- Q4 时间预算: ...
- Q5 信任先验: ...

## 客观分诊
- 核心声明: ...
- 论文类型: ...
- 可复现性信号: ...
- 与用户问题相关性: X/5 — <理由>
- 🚩 红旗信号:
  - ...
- 🟢 绿旗信号:
  - ...

## 阅读建议
- 建议深度: **精读 / 正读 / 速览 / 跳过**
- 理由: ...
- 预计时长: ...
- 阅读时警惕: ...

## 全局阅读地图 (含章节级翻译策略)

| 章节 | 重要性 | 翻译策略 | 备注 |
|------|--------|---------|------|
| §1 Introduction | ⭐⭐⭐ | SKIP | 已由 § 0 扩展引言覆盖 |
| §2 Related Work | ⭐⭐ | DIGEST | 文献综述, 摘要式即可 |
| §3 Model Architecture | ⭐⭐⭐ | FULL | 核心方法, 完整精读 |
| §4 Why Self-Attention | ⭐⭐ | STANDARD | |
| §5 Training | ⭐⭐ | STANDARD | |
| §6 Results | ⭐⭐⭐ | FULL | Q2=方法借鉴, 升级 FULL |
| §7 Conclusion | ⭐ | SKIP | 已由 § 0 覆盖 |

## 全局配置
| 项 | 配置 |
|----|------|
| 公式推导 | 必须 / 按需 / 跳过 |
| 复现骨架 | 是 / 否 (默认否, Stage 3 按需生成) |
| 批判问答强度 | 高 (5 题/章) / 中 (3 题/章) / 低 (1-2 题/章) |

## 用户最终决定
- [ ] 同意按此计划阅读
- [ ] 调整: ...
```

## 关键规则

- **每一题都允许跳过**。不要让用户感到被审问。
- **客观分诊不要假装中立**。读出来的红旗就是红旗，不替作者圆场。
- **建议不是命令**。即使建议"跳过"，用户仍可坚持读，配置降为"速览"即可。
- **不要为了让用户满意而高估相关性打分**。低就是低。
