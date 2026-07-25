# CyberSec RAG Agent — 网络安全领域 RAG 知识库系统

> 当前实现进度：**Phase 4：结构化切分与 chunk 落库**
> 权威实现规格见 [`Doc/文档2.MD`](Doc/文档2.MD)。
> Claude Code 仓库操作说明见根目录 [`CLAUDE.md`](CLAUDE.md)。

本仓库是一个面向**网络安全法规、标准、教材与知识资料**的 RAG 知识库后端项目。
当前已经完成：

- **Phase 0**：工程骨架、FastAPI、Docker Compose、PostgreSQL / Redis / Qdrant 联通
- **Phase 1**：ORM 模型、Alembic 迁移、初始数据库 schema、最小 CRUD、数据库测试基础
- **Phase 2**：`/documents/upload` 上传入口、本地原始文件存储、`file_hash` 计算、`document` / `document_version` / `ingest_task` 创建、Celery 异步任务投递入口
- **Phase 3**：PDF / Markdown / TXT 解析、页码保留、基础文本清洗、解析失败时 `ingest_task` 状态回写
- **Phase 4（当前）**：法规/标准切分、教材/手册/笔记切分、fallback recursive chunker、parent-child chunk、`chunk_hash` 生成、chunk 元数据组织与 PostgreSQL `chunks` 落库

当前仍**没有实现**：embedding、Qdrant 索引、PostgreSQL FTS 写入逻辑、reranker、检索问答、replace / chunk diff、评测流水线。

---

## 1. 当前阶段一句话说明

如果你要向面试官或同学快速描述当前项目状态，推荐这样说：

> 这是一个网络安全领域的 RAG 知识库后端项目，目前已经完成基础工程、数据库持久化地基、上传入口、原始文件解析与基础清洗，并推进到了 Phase 4 的“结构化切分与 chunk 落库”。也就是说，系统现在已经能把法规、标准、教材、手册或普通文本切成可追踪的 parent-child chunk 结构，生成稳定的 `chunk_hash`，保留页码与章节/条款等基础 metadata，并把 chunk 数据落到 PostgreSQL；但真正的 embedding、向量索引、关键词索引和检索问答仍留在后续 Phase。

---

## 2. 当前已实现能力

### Phase 0：工程可运行地基

- FastAPI 应用入口：`backend/app/main.py`
- 健康检查：`GET /health`
- 就绪检查：`GET /api/v1/health/ready`
- Docker Compose 编排：PostgreSQL / Redis / Qdrant / backend
- 配置集中管理：`backend/app/config.py`

### Phase 1：数据库与持久化地基

已实现核心表：

- `documents`
- `document_versions`
- `chunks`
- `ingest_tasks`
- `query_logs`
- `feedback`
- `eval_datasets`
- `eval_dataset_items`
- `eval_runs`
- `eval_run_items`

已实现内容：

- SQLAlchemy 2 ORM 模型
- Alembic 环境与初始迁移
- PostgreSQL 专用字段（如 `JSONB`、`TSVECTOR`）
- GIN 索引
- 最小 CRUD service
- Phase 1 模型 / CRUD 集成测试

### Phase 2：上传与异步任务入口

已实现内容：

- 上传接口：`POST /api/v1/documents/upload`
- Multipart 表单字段解析
- 上传文件基础校验
- 原始文件 SHA-256：`backend/app/utils/hash_utils.py`
- 本地文件存储：`backend/app/services/storage_service.py`
- 上传编排服务：`backend/app/services/upload_service.py`
- Celery app：`backend/app/workers/celery_app.py`
- 异步 ingest 任务入口

### Phase 3：解析与基础清洗

已实现内容：

- 统一解析输出结构：`ParsedPage` / `ParsedDocument`
- PDF 逐页解析并保留页码
- Markdown / TXT 解析为单页文档
- 基础文本清洗
- parser + cleaner 接入 worker
- 解析/清洗失败时将 `ingest_task.status` 更新为 `failed`

### Phase 4：结构化切分与 chunk 落库（当前重点）

已实现内容：

- 统一 chunk 中间结构：`ChunkDraft`
- 文档类型分流：
  - `law / regulation / standard / policy`
  - `textbook / manual / note`
  - fallback recursive chunking
- 法规/标准优先按章/节/条切分
- 长条款继续拆 child chunk，并保留 `article_no`
- 教材/手册/笔记按标题层级与段落切分
- 代码块优先整体保留
- parent-child chunk 关系生成
- 基于 `normalized_text` 的稳定 `chunk_hash`
- 组织基础 metadata：
  - `chapter`
  - `section`
  - `article_no`
  - `page_start`
  - `page_end`
- `chunks` 表持久化
- worker 中接入：解析 → 清洗 → 切分 → chunk 落库

---

## 3. 当前明确未实现的内容

下面这些功能虽然在整体 RAG 架构里非常重要，但**当前阶段故意不做**：

- embedding 生成
- Qdrant upsert
- PostgreSQL FTS `search_tsv` 写入逻辑
- reranker
- 混合检索 / RRF / query pipeline
- answer generation / citation checker
- `/documents/{id}/replace`
- chunk diff 增量更新
- 评测执行链路

这样做是为了严格遵循 `Doc/文档2.MD` 的分阶段纪律：**每个 Phase 只实现该阶段要求，不偷跑后续功能。**

---

## 4. 目录结构（按当前实现理解）

```text
RAG_Sec/
├─ README.md
├─ CLAUDE.md
├─ docker-compose.yml
├─ .env.example
├─ pyproject.toml
├─ backend/
│  ├─ Dockerfile
│  ├─ alembic.ini
│  ├─ alembic/
│  ├─ app/
│  │  ├─ main.py
│  │  ├─ config.py
│  │  ├─ dependencies.py
│  │  ├─ api/
│  │  │  ├─ __init__.py
│  │  │  ├─ health.py
│  │  │  └─ upload.py
│  │  ├─ db/
│  │  ├─ models/
│  │  ├─ schemas/
│  │  ├─ services/
│  │  │  ├─ crud_service.py
│  │  │  ├─ storage_service.py
│  │  │  ├─ upload_service.py
│  │  │  ├─ parser_service.py
│  │  │  ├─ cleaner_service.py
│  │  │  └─ chunk_service.py
│  │  ├─ utils/
│  │  │  └─ hash_utils.py
│  │  └─ workers/
│  │     ├─ celery_app.py
│  │     └─ ingest_worker.py
│  └─ tests/
│     ├─ fixtures/
│     ├─ test_health.py
│     ├─ test_models.py
│     ├─ test_crud.py
│     ├─ test_upload.py
│     ├─ test_parser.py
│     ├─ test_cleaner.py
│     ├─ test_chunk_service.py
│     └─ test_ingest_worker.py
└─ Doc/
   ├─ 文档2.MD
   ├─ Phase0面试学习版.html
   ├─ Phase1面试学习版.html
   ├─ Phase2面试学习版.html
   └─ Phase3面试学习版.html
```

---

## 5. 当前切分链路是怎么工作的

### 5.1 Phase 3 到 Phase 4 的变化

Phase 3 解决的是：

- 原始文件如何被解析为统一文本结构
- 如何做基础清洗
- 解析/清洗失败如何写回任务状态

Phase 4 在此基础上新增：

- 按文档类型选择不同 chunker
- 生成 parent-child chunk 关系
- 生成稳定 `chunk_hash`
- 组织 chunk metadata
- 把 chunk 数据持久化到 PostgreSQL

### 5.2 chunk 中间结构

当前 `chunk_service.py` 会先生成统一的中间结果 `ChunkDraft`，再映射为 ORM 可持久化记录。

这样做的好处是：

- 切分逻辑与数据库落库逻辑解耦
- chunk 规则更容易单元测试
- 后续更容易调试“为什么这一段被切成这样”

### 5.3 文档类型分流策略

当前切分策略不是“一把梭”通用切分，而是按文档类型分流：

- **法规 / 标准 / policy 类**：优先按章/节/条切
- **教材 / 手册 / note 类**：优先按标题层级和段落切
- **结构不清晰文本**：走 fallback recursive chunker

这样做的原因是：法规类文本和教材类文本的组织结构完全不同，强行套一个切分器会导致 metadata 很混乱。

### 5.4 parent-child 为什么现在就做

虽然真正索引还没开始，但 Phase 4 就必须开始遵守：

- **child chunk**：未来检索主单元
- **parent chunk**：未来上下文回填单元

也就是说，Phase 4 的设计已经在为 Phase 5/6 的检索能力铺路。

### 5.5 chunk_hash 为什么重要

当前 `chunk_hash` 基于 `normalized_text` 生成。
这样做的意义是：

- 对无意义空白变化不敏感
- 对真实文本变化敏感
- 为后续 Phase 9 的 chunk diff 增量更新打基础

---

## 6. ingest worker 当前做到哪一步

`backend/app/workers/ingest_worker.py` 当前的主流程是：

1. 读取 `document_id / version_id / task_id / file_path`
2. 把任务状态更新为 `processing`
3. 调用 parser
4. 调用 cleaner
5. 调用 `chunk_service.generate_chunks(...)`
6. 调用 `build_chunk_records(...)`
7. 将 parent / child chunk 写入 `chunks` 表
8. 成功时更新任务说明
9. 失败时把 `ingest_task.status` 更新为 `failed`

### 当前成功语义要怎么理解

当前 worker 成功，**不代表系统已经具备检索能力**。
它只代表：

> Phase 4 所要求的“解析、清洗、结构化切分与 chunk 落库”已完成。

后续真正进入可检索状态，还需要 Phase 5 补 embedding / index，Phase 6 补 retrieval。

---

## 7. 环境与配置

### 7.1 基础设施

当前 `docker-compose.yml` 编排了：

- `postgres`
- `redis`
- `qdrant`
- `backend`
- `worker`

### 7.2 关键依赖

当前切分阶段主要依赖：

- `PyMuPDF`：PDF 解析
- 项目内 `chunk_service.py`
- 项目内 `hash_utils.py`

### 7.3 Python 环境约束

本项目后续 Python 操作应始终使用**项目专用虚拟环境 / conda 环境**，不要使用用户全局 Python。

---

## 8. 常用命令

> 说明：当前会话中要求优先使用项目专用 conda / 虚拟环境。下面命令默认都应在该环境内执行。

### 8.1 安装依赖

```bash
pip install -e ".[test]"
```

### 8.2 启动基础设施

```bash
docker compose up -d postgres redis qdrant
```

### 8.3 启动全部服务（含 backend / worker）

```bash
docker compose up -d --build
```

### 8.4 本地启动 FastAPI

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 8.5 启动 Celery worker（本地）

```bash
cd backend
celery -A app.workers.celery_app.celery_app worker --loglevel=INFO
```

### 8.6 数据库迁移

```bash
cd backend
alembic upgrade head
```

### 8.7 运行测试

```bash
# 默认测试（非 integration）
pytest

# Phase 4 切分测试
pytest backend/tests/test_chunk_service.py

# worker 集成测试
pytest backend/tests/test_ingest_worker.py -m integration
```

---

## 9. 当前最值得阅读的文件

如果你想快速理解现在的项目，建议按这个顺序读：

1. `Doc/文档2.MD`：权威规格
2. `backend/app/services/chunk_service.py`：Phase 4 核心切分逻辑
3. `backend/app/utils/hash_utils.py`：`normalized_text` 与 `chunk_hash`
4. `backend/app/models/chunk.py`：chunk 持久化结构
5. `backend/app/workers/ingest_worker.py`：解析 → 清洗 → 切分 → 落库 主链路
6. `backend/tests/test_chunk_service.py`
7. `backend/tests/test_ingest_worker.py`

---

## 10. 下一步会进入什么阶段

按规格，后续阶段会逐步进入：

- Phase 5：embedding / 索引
- Phase 6：混合检索
- Phase 7：查询理解与安全边界
- Phase 8：答案生成与引用校验
- Phase 9：replace / 增量更新
- Phase 10：评测体系

所以当前 Phase 4 的本质，是把“可解析的文档文本”，升级为“可被后续检索系统索引和引用的结构化 chunk 数据”。
