# Phase 0 完成进度细节文档

> 项目：CyberSec RAG Agent  
> 当前阶段：**Phase 0：项目初始化**  
> 文档位置：`/Doc/`  
> 依据：当前仓库实际代码、`README.md`、`Doc/文档2.MD`

---

## 1. 文档目的

本文档用于说明**当前仓库在 Phase 0 已完成了什么、完成到了什么程度、对应到哪些代码文件、如何验证，以及哪些内容明确还未进入实现范围**。

它不是总体规格文档，也不是后续 Phase 的设计文档，而是一个面向当前状态的**阶段完成度说明**。

---

## 2. 当前阶段结论

当前仓库已经完成 **Phase 0 基础工程骨架搭建**，可以认为：

- 项目目录结构已建立；
- FastAPI 后端应用可启动；
- PostgreSQL / Redis / Qdrant 的 Docker Compose 编排已建立；
- 基础配置系统已建立；
- 健康检查接口已实现；
- 基础测试已建立；
- 后续各 Phase 所需模块骨架已预留；
- **RAG 业务逻辑尚未开始实现**。

换言之：

> **Phase 0 的目标是“工程能跑、基础设施能连、后续开发有骨架可挂”，这个目标已达成。**

---

## 3. Phase 0 已完成内容明细

## 3.1 项目基础结构已建立

已建立根目录及后端目录结构，包括：

- 根目录工程文件：
  - `pyproject.toml`
  - `docker-compose.yml`
  - `.env.example`
  - `README.md`
- 后端目录：
  - `backend/app/`
  - `backend/tests/`
- 预留模块目录：
  - `api/`
  - `db/`
  - `models/`
  - `schemas/`
  - `services/`
  - `workers/`
  - `prompts/`
  - `utils/`
- 本地模型目录：
  - `models/embedding/`
  - `models/reranker/`

说明：

这些目录中，只有与 Phase 0 直接相关的基础模块已实现；其余多数文件仍为 TODO 占位，用于与规格文档中的长期架构保持一致。

---

## 3.2 FastAPI 应用入口已实现

已完成文件：

- `backend/app/main.py`

已实现能力：

- 创建 FastAPI 应用实例；
- 初始化日志配置；
- 注册 API 聚合路由；
- 提供根路径健康检查接口：`GET /health`；
- 注册最小全局异常处理器，统一返回 `internal_error` 结构。

当前状态说明：

- 该文件保持“薄入口”设计；
- 不承载任何 RAG 业务逻辑；
- 符合“API 层不写主业务逻辑”的约束。

---

## 3.3 API 路由聚合已建立

已完成文件：

- `backend/app/api/__init__.py`
- `backend/app/api/health.py`

已实现能力：

- 通过统一的 `api_router` 管理业务前缀路由；
- 当前已挂载 `/api/v1` 前缀；
- 已实现：
  - `GET /health`
  - `GET /api/v1/health/ready`

当前状态说明：

- Phase 0 仅启用 health 相关路由；
- `upload.py`、`documents.py`、`query.py`、`admin.py`、`eval.py` 等文件虽已存在，但当前不应视为已实现功能。

---

## 3.4 配置系统已建立

已完成文件：

- `backend/app/config.py`
- `.env.example`

已实现能力：

- 使用 `pydantic-settings` 管理配置；
- 支持从 `.env` / 环境变量读取配置；
- 已覆盖基础设施连接配置：
  - PostgreSQL
  - Redis
  - Qdrant
- 提供派生连接属性：
  - `postgres_dsn`
  - `redis_url`
  - `qdrant_url`
- 通过 `get_settings()` 做缓存，避免重复解析配置。

当前状态说明：

- 当前配置只覆盖 Phase 0 所需内容；
- embedding/reranker/LLM 等后续配置尚未接入。

---

## 3.5 数据库连接层已建立

已完成文件：

- `backend/app/db/session.py`
- `backend/app/db/base.py`

已实现能力：

- 创建 SQLAlchemy 引擎；
- 创建 `SessionLocal` 会话工厂；
- 提供 PostgreSQL 连通性检查函数；
- 为后续 ORM 模型与请求级数据库会话预留基础设施。

当前状态说明：

- 目前仅用于健康检查和后续会话预留；
- 尚未定义业务 ORM 表结构；
- Alembic 迁移尚未进入实际可用状态。

---

## 3.6 Redis / Qdrant 依赖封装已建立

已完成文件：

- `backend/app/dependencies.py`

已实现能力：

- 创建 Redis 客户端；
- 提供 Redis 连通性检查；
- 懒加载 Qdrant 客户端；
- 提供 Qdrant 连通性检查；
- 提供未来路由可复用的 `get_db()` 依赖。

当前状态说明：

- 当前仅实现“连通性探活”；
- 未实现任务状态读写、向量写入、集合管理等真实业务逻辑。

---

## 3.7 日志初始化已建立

已完成文件：

- `backend/app/logging_config.py`

已实现能力：

- 统一日志配置入口；
- 为应用启动与基础设施探活提供统一日志输出基础。

当前状态说明：

- 当前日志主要服务于基础启动与健康检查；
- 后续需要随业务扩展补充更细粒度日志策略。

---

## 3.8 Docker Compose 基础设施编排已完成

已完成文件：

- `docker-compose.yml`
- `backend/Dockerfile`

已实现能力：

- 可一键启动以下服务：
  - `postgres`
  - `redis`
  - `qdrant`
  - `backend`
- 为 PostgreSQL / Redis / Qdrant 配置了健康检查；
- `backend` 依赖三项服务健康后再启动；
- 配置了基础端口映射；
- 配置了持久化卷：
  - `postgres_data`
  - `redis_data`
  - `qdrant_data`

当前状态说明：

- 该编排已经满足 Phase 0 的“基础服务可启动并互联”目标；
- 尚未包含 Celery worker、异步任务消费等后续组件。

---

## 3.9 健康检查能力已实现

已完成接口：

### 1）存活探针

- `GET /health`

返回：

```json
{"status": "ok"}
```

作用：

- 只验证进程本身可响应；
- 不依赖外部基础设施；
- 用于最小存活检查。

### 2）就绪探针

- `GET /api/v1/health/ready`

作用：

- 检查 PostgreSQL / Redis / Qdrant 是否可连接；
- 返回每个组件的 `connected` 状态与耗时；
- 当部分组件不可用时返回 `degraded`，而不是直接抛 500。

当前状态说明：

- 这是 Phase 0 中最核心的“可验证功能”之一；
- 可直接用于本地环境验收和 Docker 启动后的联通性验证。

---

## 3.10 测试基础已建立

已完成文件：

- `backend/tests/conftest.py`
- `backend/tests/test_health.py`
- `backend/tests/test_config.py`
- `backend/tests/test_integration.py`

已实现测试分层：

### 默认测试

通过 `pytest` 执行，默认排除 integration：

- 验证 `/health` 返回结构；
- 验证 `/health/ready` 返回字段结构；
- 验证配置默认值；
- 验证 FastAPI 路由已正确注册。

### 集成测试

通过 `pytest -m integration` 显式执行：

- 验证 PostgreSQL 连接；
- 验证 Redis 连接；
- 验证 Qdrant 连接；
- 验证 `/health/ready` 在基础设施齐全时返回 `ok`。

当前状态说明：

- 测试体系已具备基本雏形；
- 当前测试重点是“工程启动正确、基础设施连接正确”；
- 还没有覆盖任何 RAG 业务逻辑，因为当前阶段尚未实现这些逻辑。

---

## 3.11 后续 Phase 所需模块骨架已预留

当前仓库已经存在以下后续模块文件：

- `services/` 下：
  - `parser_service.py`
  - `cleaner_service.py`
  - `chunk_service.py`
  - `embedding_service.py`
  - `vector_store.py`
  - `keyword_store.py`
  - `retriever.py`
  - `fusion.py`
  - `answer_generator.py`
  - `citation_checker.py`
  - `safety_guard.py`
  - `eval_service.py`
  - 等
- `workers/` 下：
  - `celery_app.py`
  - `ingest_worker.py`
  - `reindex_worker.py`
- `models/` / `schemas/` 下各类领域对象文件
- `prompts/` 下各类提示词文件

当前状态说明：

- 这些文件的存在表示架构方向已经铺好；
- 但绝大部分尚处于占位状态；
- 在 Phase 0 里，**它们不应被误认为已具备业务能力**。

---

## 4. Phase 0 当前完成度判断

从当前代码状态看，Phase 0 可以分成以下几个维度评估：

| 维度 | 状态 | 说明 |
|------|------|------|
| 项目骨架 | 已完成 | 目录结构与模块分层已建立 |
| 后端入口 | 已完成 | FastAPI 可启动，路由可注册 |
| 配置系统 | 已完成 | `.env` + `pydantic-settings` 已接通 |
| 基础设施编排 | 已完成 | Docker Compose 已可启动四个核心服务 |
| 健康检查 | 已完成 | `/health` 与 `/health/ready` 已实现 |
| 基础测试 | 已完成 | 单元/集成测试骨架已建立 |
| 数据模型 | 未开始业务实现 | 当前仅目录与文件占位 |
| 入库链路 | 未实现 | 上传、解析、切分、索引均未落地 |
| 检索链路 | 未实现 | 检索、融合、重排、答案生成均未落地 |
| 任务系统 | 未实现 | Celery/异步任务仅占位 |
| 评测系统 | 未实现 | 仅文件占位 |

综合判断：

> **Phase 0 的“基础工程目标”已完成；Phase 1 及之后的“业务系统目标”尚未开始。**

---

## 5. 当前可执行的验证方式

## 5.1 本地开发安装

在仓库根目录执行：

```bash
python -m venv .venv
pip install -e ".[test]"
```

---

## 5.2 本地运行后端

在 `backend/` 目录下执行：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 5.3 Docker Compose 启动

在仓库根目录执行：

```bash
cp .env.example .env
docker compose up -d --build
```

查看日志：

```bash
docker compose logs -f backend
```

---

## 5.4 接口验证

### 验证 1：存活探针

```bash
curl http://localhost:8000/health
```

预期：

```json
{"status":"ok"}
```

### 验证 2：就绪探针

```bash
curl http://localhost:8000/api/v1/health/ready
```

预期：

- PostgreSQL / Redis / Qdrant 全部可连时，返回 `status=ok`；
- 若某组件未启动，返回 `status=degraded`，同时 body 中显示对应组件状态。

---

## 5.5 测试验证

默认测试：

```bash
pytest
```

集成测试：

```bash
pytest -m integration
```

全部测试：

```bash
pytest -m ""
```

单测示例：

```bash
pytest backend/tests/test_health.py::test_health_returns_ok
```

---

## 6. 当前明确未完成内容

以下内容虽然在规格中已有规划，但**当前不属于已完成内容**：

### 6.1 数据层

- `documents` / `document_versions` / `chunks` / `ingest_tasks` 等业务 ORM 模型
- 实际数据库建表
- Alembic 迁移环境启用

### 6.2 入库链路

- 文档上传
- 原始文件保存
- 文本解析
- 文本清洗
- Parent-Child Chunk 切分
- `chunk_hash` 生成
- 索引写入

### 6.3 检索链路

- Query Rewrite
- Metadata Filter
- Qdrant 向量检索
- PostgreSQL FTS 关键词检索
- RRF 融合
- Reranker
- Parent 上下文回填
- 答案生成
- 引用校验

### 6.4 安全与治理

- `safety_guard` 实际逻辑
- 拒答 / 重定向策略落地
- `query_logs` 真实记录

### 6.5 异步任务系统

- Celery 应用配置
- 入库 worker
- 重建索引 worker
- Redis + PostgreSQL 双写任务状态

### 6.6 评测系统

- 评测数据集
- 评测执行逻辑
- 评测 API

---

## 7. 对当前阶段的准确定位

为了避免误判仓库状态，必须明确以下几点：

1. 当前仓库**已经不是空仓库**；
2. 当前仓库**也不是 RAG MVP 已完成状态**；
3. 当前仓库处于“Phase 0 已落地、后续 Phase 待继续实现”的状态；
4. 现在最可靠的事实来源是：
   - 当前代码文件；
   - `README.md`；
   - `Doc/文档2.MD`。

---

## 8. 建议作为 Phase 0 验收结论的表述

可将当前阶段总结为：

> 已完成 Phase 0 基础工程搭建：建立了符合规格的后端目录结构、FastAPI 应用入口、统一配置系统、PostgreSQL/Redis/Qdrant 基础依赖封装、Docker Compose 编排、健康检查接口与基础测试体系。当前仓库已具备“可启动、可联通、可验证”的工程基础，但尚未实现上传、解析、切分、检索、生成、增量更新、评测等 RAG 业务能力。

---

## 9. 后续衔接说明

Phase 0 之后，代码应继续按规格文档顺序推进：

- Phase 1：数据模型与 Alembic
- Phase 2：上传接口与异步入库任务框架
- Phase 3：解析与清洗
- Phase 4：切分
- Phase 5：Embedding / 索引
- Phase 6：检索
- Phase 7：安全与查询改写
- Phase 8：答案生成与引用
- Phase 9：增量更新
- Phase 10：评测

注意：

> 后续实现必须遵循 `Doc/文档2.MD` 的 Phase 边界，不应因为目录已存在就提前实现超出当前阶段范围的功能。
