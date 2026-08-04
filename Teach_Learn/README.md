# Teach_Learn · RAG_Sec 完整课程

> 目标：让你能**自己读懂**这个由 AI 构建的网络安全 RAG 项目，并在定位问题、提出修改需求时更精确。

## 使用方式

1. 先读 [`MISSION.md`](MISSION.md)，确认学习目标。
2. 按课号顺序打开 `lessons/` 下的 HTML。
3. 每课都有练习；先自己答，再展开参考答案。
4. 需要速查时打开 `reference/`。
5. 任何不清楚的地方，直接在对话里问老师（Claude）。

## 课程总览（12 课）

| 课号 | 文件 | 一句话目标 |
|------|------|------------|
| 0001 | [读懂项目结构地图](lessons/0001-read-the-project-map.html) | 从用户动作反推代码入口 |
| 0002 | [启动项目并完成第一次验证](lessons/0002-start-and-verify.html) | 能本地/Compose 跑通并知道验证点 |
| 0003 | [后端分层：API / Service / Worker](lessons/0003-backend-layering.html) | 知道业务逻辑该在哪一层 |
| 0004 | [上传与异步入库链路](lessons/0004-upload-ingest-flow.html) | 跟完整条 upload → ingest 路径 |
| 0005 | [Parent-Child Chunk 与索引](lessons/0005-chunk-and-index.html) | 理解只索引 child 的设计 |
| 0006 | [查询前处理：安全 / 意图 / 改写](lessons/0006-query-preparation.html) | 搞清 answer 前半段流水线 |
| 0007 | [混合检索与 RRF 融合](lessons/0007-hybrid-retrieval.html) | 向量 + FTS 如何变成证据列表 |
| 0008 | [答案生成与引用校验](lessons/0008-answer-and-citation.html) | 证据如何变成带 citation 的回答 |
| 0009 | [替换、增量更新与软删除](lessons/0009-replace-and-soft-delete.html) | chunk_hash diff 与三库可见性 |
| 0010 | [评测体系：golden dataset 与指标](lessons/0010-eval-system.html) | 如何量化“系统变好了没有” |
| 0011 | [前端 MVP 如何对接后端](lessons/0011-frontend-map.html) | 页面与 API 的对应关系 |
| 0012 | [从症状定位文件：调试方法论](lessons/0012-debug-from-symptom.html) | 把“不会用”变成“会排查” |

## 参考材料

| 文档 | 用途 |
|------|------|
| [项目结构速查图](reference/project-map.html) | 目录职责与四条主流程 |
| [术语表](reference/glossary.html) | 统一中英术语，避免混用 |
| [四条主流程图](reference/four-flows.html) | 上传 / 查询 / 替换 / 评测 |
| [数据模型速查](reference/data-model.html) | 核心表与可见性规则 |
| [检索管线参数](reference/retrieval-pipeline.html) | top_k、RRF、rerank 默认值 |

## 学习路径建议

```text
地图 (0001)
  → 能跑起来 (0002)
  → 懂分层 (0003)
  → 四条主流程 (0004–0010)
  → 前端与调试 (0011–0012)
```

完成 0001–0008 后，你应能独立解释一次完整问答；完成 0009–0012 后，你应能根据 bug 描述指出优先排查文件。

## 文件夹说明

- `lessons/`：短小的 HTML 课程，每节课解决一个具体学习目标。
- `reference/`：可反复查看的速查表、图谱、术语表。
- `assets/`：课程共用样式和交互组件。
- `learning-records/`：记录已经掌握的关键理解，帮助后续课程调整难度。
- `MISSION.md`：学习这个项目的目标。
- `RESOURCES.md`：可信资源列表。
- `NOTES.md`：教学偏好和工作笔记。

## 相关文件

- 权威规格：[`../Doc/文档2.MD`](../Doc/文档2.MD)
- 架构说明：[`../CLAUDE.md`](../CLAUDE.md)
- 当前状态：[`../README.md`](../README.md)
- 资源清单：[`RESOURCES.md`](RESOURCES.md)
