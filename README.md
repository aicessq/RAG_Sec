# CyberSec RAG Agent — 网络安全领域 RAG 知识库系统

> 当前实现进度：**Phase 2：上传入口 / 原始文件落盘 / 异步入库任务入口**
> 权威实现规格见 [`Doc/文档2.MD`](Doc/文档2.MD)。
> Claude Code 仓库操作说明见根目录 [`CLAUDE.md`](CLAUDE.md)。

本仓库是一个面向**网络安全法规、标准、教材与知识资料**的 RAG 知识库后端项目。
当前已经完成：

- **Phase 0**：工程骨架、FastAPI、Docker Compose、PostgreSQL / Redis / Qdrant 联通
- **Phase 1**：ORM 模型、Alembic 迁移、初始数据库 schema、最小 CRUD、数据库测试基础
- **Phase 2（当前）**：`/documents/upload` 上传入口、本地原始文件存储、`file_hash` 计算、`document` / `document_version` / `ingest_task` 创建、Celery 异步任务投递入口

当前仍**没有实现**：真实解析、清洗、chunk 切分、embedding、Qdrant 索引、全文检索索引写入、检索问答、replace 版本更新、评测流水线。

---

## 1. 当前阶段一句话说明

如果你要向面试官或同学快速描述当前项目状态，推荐这样说：

> 这是一个网络安全领域的 RAG 知识库后端项目，目前已经完成基础工程、数据库持久化地基，以及 Phase 2 的“新文档上传入口”。也就是说，系统现在已经能接收一个新文件、做基础校验、把原始文件按 document/version 维度落盘、计算 SHA-256、创建数据库记录，并投递一个异步入库任务；但真正的解析、切分、索引和问答链路还留在后续 Phase 实现。

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

### Phase 2：上传与异步任务入口（当前重点）

已实现内容：

- 上传接口：`POST /api/v1/documents/upload`
- Multipart 表单字段解析
- 上传文件基础校验：
  - 文件不能为空
  - 扩展名必须在白名单内
  - MIME 类型必须在白名单内
  - 文件大小必须在限制内
- 原始文件 SHA-256：`backend/app/utils/hash_utils.py`
- 本地文件存储：`backend/app/services/storage_service.py`
- 上传编排服务：`backend/app/services/upload_service.py`
- 上传响应 schema：`backend/app/schemas/upload.py`
- Celery app：`backend/app/workers/celery_app.py`
- 占位 ingest worker：`backend/app/workers/ingest_worker.py`
- Docker Compose 中新增 `worker` 服务

---

## 3. 当前明确未实现的内容

下面这些功能虽然在整体 RAG 架构里非常重要，但**当前阶段故意不做**：

- PDF / Markdown / TXT 真正解析
- 文本清洗 / 标准化
- parent-child chunk 切分
- `chunk_hash` diff 更新
- embedding 生成
- Qdrant upsert
- PostgreSQL FTS `search_tsv` 回填
- 混合检索 / RRF / rerank
- answer generation / citation checker
- `/documents/{id}/replace`
- `/query/*` 相关接口
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
│  │  ├─ env.py
│  │  └─ versions/
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
│  │  │  └─ upload_service.py
│  │  ├─ utils/
│  │  │  └─ hash_utils.py
│  │  └─ workers/
│  │     ├─ celery_app.py
│  │     └─ ingest_worker.py
│  └─ tests/
│     ├─ test_health.py
│     ├─ test_models.py
│     ├─ test_crud.py
│     └─ test_upload.py
└─ Doc/
   ├─ 文档2.MD
   ├─ Phase0完成进度细节文档.md
   ├─ Phase0面试学习版.html
   └─ Phase1面试学习版.html
```

---

## 5. 上传链路当前是怎么工作的

### 5.1 接口职责

当前接口是：

```http
POST /api/v1/documents/upload
```

它的职责很明确：

1. 接收一个**新文档**上传
2. 做基础校验
3. 保存原始文件
4. 创建数据库记录
5. 创建异步任务记录
6. 投递 Celery worker 入口
7. 返回 `document_id`、`version_id`、`task_id`、`status`

### 5.2 为什么 upload 只允许“新文档”

根据规格，上传语义是：

- `upload` = 创建一个全新的 `document`
- `replace` = 给已有 document 创建新版本

所以当前实现里：

- `upload` **不允许传 `document_id`**
- 如果传了，会返回 `invalid_request`

这保证了 Phase 2 的接口语义保持单一，也避免提前把“版本替换逻辑”混进当前阶段。

### 5.3 上传成功后会创建哪些记录

成功上传后，会一次性创建：

- `documents`：逻辑文档主体
- `document_versions`：当前上传生成的第一个版本（`version_no = 1`）
- `ingest_tasks`：异步入库任务（初始为 `queued`）

### 5.4 当前事务边界

`upload_service.py` 里使用了一次事务提交来完成：

- `Document`
- `DocumentVersion`
- `IngestTask`

这样做的原因是：上传动作在业务上是一个整体，不能只成功一半。

当前顺序大致是：

1. 读取上传 bytes
2. 做校验
3. 计算 `file_hash`
4. 预生成 `document_id` / `version_id` / `task_id`
5. 保存原始文件到本地
6. 创建数据库记录并提交
7. 提交成功后再 dispatch Celery 任务
8. 如果 DB 失败，则尝试删除刚写入的文件

### 5.5 文件存储路径为什么按 document/version 分层

当前本地存储路径是 document/version aware 的，核心目的是：

- 避免只靠原始文件名造成冲突
- 让后续 replace / diff / 审计更容易追踪
- 让“某个 document 的某个 version 的原始文件在哪”这个问题可以直接回答

可理解为类似：

```text
storage/documents/<document_id>/<version_id>/<safe_filename>
```

---

## 6. 异步任务当前做到哪一步

当前 Celery 相关实现分为两层：

### 6.1 Celery app

`backend/app/workers/celery_app.py`：

- 从配置读取 Redis 作为 broker / backend
- 创建 Celery 应用对象

### 6.2 ingest worker

`backend/app/workers/ingest_worker.py` 当前只做 **Phase 2 安全边界内的占位行为**：

- 接收 `document_id` / `version_id` / `task_id` / `file_path`
- 从数据库读取 `IngestTask`
- 把任务状态更新为 `processing`
- 记录“后续 Phase 才会实现真实解析/索引”的占位说明

它**不会**在当前阶段做以下事：

- 解析 PDF / Markdown / TXT
- 切 chunk
- 写 `chunks`
- 生成 embedding
- 写入 Qdrant
- 回填 FTS

这不是功能缺失，而是**刻意遵守阶段边界**。

---

## 7. 环境与配置

### 7.1 基础设施

当前 `docker-compose.yml` 编排了：

- `postgres`
- `redis`
- `qdrant`
- `backend`
- `worker`

### 7.2 关键配置项

`.env.example` 中 Phase 2 新增 / 强化了这些配置：

- `STORAGE_ROOT=storage`
- `MAX_UPLOAD_SIZE_MB=20`
- `ALLOWED_UPLOAD_EXTENSIONS=.pdf,.md,.markdown,.txt`
- `ALLOWED_UPLOAD_MIME_TYPES=application/pdf,text/markdown,text/plain,text/x-markdown`

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

# 集成测试
pytest -m integration

# 只跑上传测试
pytest backend/tests/test_upload.py

# 只跑模型测试
pytest backend/tests/test_models.py

# 只跑 CRUD 测试
pytest backend/tests/test_crud.py
```

---

## 9. 当前最值得阅读的文件

如果你想快速理解现在的项目，建议按这个顺序读：

1. `Doc/文档2.MD`：权威规格
2. `backend/app/api/upload.py`：上传接口入口
3. `backend/app/services/upload_service.py`：Phase 2 核心业务编排
4. `backend/app/services/storage_service.py`：文件本地存储抽象
5. `backend/app/workers/ingest_worker.py`：异步入口边界
6. `backend/app/models/document.py`
7. `backend/app/models/document_version.py`
8. `backend/app/models/ingest_task.py`
9. `backend/tests/test_upload.py`

---

## 10. 下一步会进入什么阶段

按规格，后续阶段会逐步进入：

- Phase 3：解析与清洗
- Phase 4：chunk 切分
- Phase 5：embedding / 索引
- Phase 6：混合检索
- Phase 7：查询理解与安全边界
- Phase 8：答案生成与引用校验
- Phase 9：replace / 增量更新
- Phase 10：评测体系

所以当前 Phase 2 的本质，是把“上传一个新文档并形成可异步处理的入口”这个最小闭环搭起来，为后续真实 ingest pipeline 铺路。
