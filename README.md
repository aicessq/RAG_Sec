# CyberSec RAG Agent — 网络安全领域 RAG 知识库系统

> 本仓库当前进度：**Phase 0：项目初始化**（仅完成基础工程骨架，不含任何 RAG 业务逻辑）。
> 权威实现规格见 [`Doc/文档2.MD`](Doc/文档2.MD)，执行纪律与默认决策见 [`Doc/CLAUDE.md`](Doc/CLAUDE.md)。

本文件既是 README，也是 **Phase 0 的中文实现说明文档**，面向初学者讲解：做了什么、为什么这么设计、如何启动、如何测试、如何验证环境联通，以及后续 Phase 将如何在此骨架上扩展。

---

## 一、Phase 0 做了什么

Phase 0 的唯一目标是“让基础工程能跑起来”，对应规格 §21 / Phase 0 验收标准：

1. 创建项目目录结构（与规格 §5 一致）。
2. 创建 FastAPI 应用（`backend/app/main.py`）。
3. 创建 `docker-compose.yml`，编排后端 + 基础设施。
4. 集成 **PostgreSQL**（持久化）。
5. 集成 **Redis**（任务状态缓存）。
6. 集成 **Qdrant**（向量检索）。
7. 创建 `.env.example`（配置模板）。
8. 创建 `.gitignore`，并忽略 `models/`（本地模型文件不进仓库）。
9. 创建本 README（兼中文实现文档）。
10. 实现 `GET /health`（返回 `{"status":"ok"}`），并额外提供 `GET /health/ready` 用于联通性验收。

### 为什么 Phase 0 只做这些

RAG 系统的复杂度集中在“入库链路”和“检索链路”（规格 §4）。如果一上来就写业务逻辑，
一旦基础设施（数据库、缓存、向量库）没接通，调试会非常痛苦。
Phase 0 先把“地基”打通：服务能起、能连、能探活，后续每个 Phase 才能在稳定的地基上逐层叠加。
因此本阶段**故意不实现**任何上传 / 解析 / 切分 / embedding / 检索 / 答案 / 评测逻辑。

---

## 二、目录结构

```text
RAG_Sec/
├─ README.md                 # 本文件（兼实现文档）
├─ pyproject.toml            # 依赖与构建配置
├─ docker-compose.yml        # 编排 PG / Redis / Qdrant / backend
├─ .env.example              # 环境变量模板
├─ .gitignore                # 含 models/
├─ models/                   # 本地模型文件目录（已 gitignore）
│  ├─ embedding/             # Qwen Embedding 模型（Phase 5 用）
│  └─ reranker/              # Qwen3 Reranker 模型（Phase 5 用）
└─ backend/
   ├─ Dockerfile             # 后端镜像
   ├─ alembic.ini            # Alembic 占位（Phase 1 配置）
   ├─ app/
   │  ├─ main.py             # FastAPI 入口（★核心）
   │  ├─ config.py           # 配置（从 .env 读，Pydantic v2）（★核心）
   │  ├─ logging_config.py   # 统一日志配置
   │  ├─ dependencies.py     # Redis/Qdrant 客户端 + 连接检查 + get_db（★核心）
   │  ├─ api/                # 路由层（health 已实现，其余 TODO 占位）
   │  │  ├─ __init__.py      # 路由聚合
   │  │  └─ health.py        # /health 与 /health/ready（★核心）
   │  ├─ db/                 # 数据库会话
   │  │  ├─ session.py       # SQLAlchemy 引擎 + 连接检查（★核心）
   │  │  └─ base.py          # DeclarativeBase
   │  ├─ models/             # ORM 模型（Phase 1，TODO 占位）
   │  ├─ schemas/            # Pydantic schema（后续 Phase，TODO 占位）
   │  ├─ services/           # 服务层（后续 Phase，TODO 占位）
   │  ├─ workers/            # Celery worker（后续 Phase，TODO 占位）
   │  ├─ prompts/            # Prompt 文件（后续 Phase，TODO 占位）
   │  └─ utils/              # 工具函数（后续 Phase，TODO 占位）
   └─ tests/                 # 测试
      ├─ conftest.py         # 公共夹具（TestClient）
      ├─ test_health.py      # 健康检查接口测试
      ├─ test_config.py      # 配置/启动层基本验证
      └─ test_integration.py # PG/Redis/Qdrant 连通性集成测试（默认跳过）
```

> 标 ★ 的文件是 Phase 0 真正实现的核心文件，建议优先阅读。
> 其余 `services/`、`models/`、`schemas/`、`workers/`、`prompts/` 下的文件均为**一行 TODO 占位**，
> 只是为了让目录骨架与规格 §5 一致，里面没有任何业务实现。

---

## 三、Docker 中每个服务的职责

| 服务 | 镜像 | 端口 | 职责 | 在哪个 Phase 真正使用 |
|------|------|------|------|----------------------|
| `postgres` | postgres:16 | 5432 | 关系型持久化：文档、版本、chunk、任务、评测等所有业务表 | Phase 1 起建表 |
| `redis` | redis:7 | 6379 | 实时任务状态缓存（与 PostgreSQL 双写，规格 §2.4） | Phase 2 入库任务 |
| `qdrant` | qdrant/qdrant | 6333 | 向量检索，**只索引 child chunk**（规格 §2.3） | Phase 5 索引 |
| `backend` | 本仓库 Dockerfile | 8000 | FastAPI 应用，对外提供 API | 本阶段已提供 /health |

编排要点：
- 后端 `depends_on` 三个基础设施的 `service_healthy`，确保 PG/Redis/Qdrant 就绪后再起后端。
- 三个基础设施都配了 `healthcheck`，编排据此判断是否就绪。
- `postgres_data` / `redis_data` / `qdrant_data` 三个命名卷做数据持久化。

---

## 四、关键设计原因（学习向）

### 1. 配置全部从 `.env` 读取（`config.py`）
用 `pydantic-settings` 把环境变量映射成带类型校验的 `Settings` 对象。
好处：同一份代码在本地（localhost）和 Docker（服务名 postgres/redis/qdrant）下只需换环境变量即可切换，
且类型错误在启动时就暴露。连接串用 `@property` 派生，避免子字段改了连接串没同步。

### 2. 健康检查分两层（`api/health.py`）
- `GET /health`：**存活探针**，进程能响应就返回 `ok`，不依赖外部服务。规格 §17.1 要求的就是这个。
- `GET /health/ready`：**就绪探针**，探活 PG/Redis/Qdrant 并返回各组件 `connected` 与耗时。
  Phase 0 验收“三服务连接正常”用这个接口可复现验证。

### 3. API 层不写业务逻辑
`main.py` 只创建应用、配日志、注册路由、做最小异常兜底；`health.py` 只调用 `dependencies` 里的检查函数并组装结果，
不直接拼连接串或发 SQL。这是规格 §3.2 的硬要求，也为后续 Phase 的服务层留出空间。

### 4. 连接检查失败返回 False 而非抛异常
`/health/ready` 需要能返回“部分不可用”，而不是某个组件挂了就让接口 500。检查函数吞掉异常并记日志。

### 5. 测试分层
- 默认 `pytest` 只跑**不需要基础设施**的测试（/health 结构、配置默认值、app 路由）；
- 集成测试带 `integration` 标记且默认被 `addopts` 排除，需 `pytest -m integration` 显式运行，
  这样在没起 docker 时 CI 不会红。

---

## 五、如何启动

### 方式 A：Docker Compose 一键启动（推荐，验收用）

```bash
# 1. 准备环境变量
cp .env.example .env

# 2. 构建并启动所有服务
docker compose up -d --build

# 3. 查看后端日志
docker compose logs -f backend
```

启动后：
- 后端：http://localhost:8000
- Qdrant 控制台：http://localhost:6333/dashboard
- API 文档（Swagger）：http://localhost:8000/docs

### 方式 B：本地直接跑（用于开发/跑单元测试）

```bash
# 在 backend/ 下创建虚拟环境并安装依赖
python -m venv .venv
# Windows: .venv\Scripts\activate   | Linux/Mac: source .venv/bin/activate
pip install -e ".[test]"

# 启动（需要 PG/Redis/Qdrant 可达，或仅测 /health）
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> 注意：本地直接跑时，`config.py` 默认用 `localhost` 连基础设施。
> 若此时没有起 docker compose，`/health` 仍返回 `ok`，但 `/health/ready` 会显示各组件 `connected=false`。这是预期行为。

---

## 六、如何测试

```bash
# 安装测试依赖（已含在 [test] extra 中）
pip install -e ".[test]"

# 1. 默认单元测试：不需要任何基础设施
pytest

# 2. 集成测试：需要先 docker compose up 起好 PG/Redis/Qdrant
pytest -m integration

# 3. 跑全部测试
pytest -m ""
```

### 预期结果

- `pytest`（默认）：
  - `test_health.py::test_health_returns_ok` ✅
  - `test_health.py::test_health_ready_shape` ✅（只校验结构）
  - `test_config.py::test_settings_defaults` ✅
  - `test_config.py::test_app_object_has_health_route` ✅
- `pytest -m integration`（基础设施已起时）：
  - `test_postgres_connection` ✅
  - `test_redis_connection` ✅
  - `test_qdrant_connection` ✅
  - `test_health_ready_all_ok` ✅

---

## 七、如何验证环境联通（验收步骤）

```bash
# 1. 启动全部服务
docker compose up -d --build

# 2. 存活探针：必须返回 {"status":"ok"}
curl http://localhost:8000/health

# 3. 就绪探针：三组件 connected 全部为 true
curl http://localhost:8000/api/v1/health/ready

# 4.（可选）直接验证三个基础设施端口
#    PostgreSQL
docker compose exec postgres pg_isready -U cybersec -d cybersec_rag
#    Redis
docker compose exec redis redis-cli ping
#    Qdrant
curl http://localhost:6333/

# 5. 跑集成测试复现验收
pytest -m integration

# 6. 收尾
docker compose down        # 停服务（保留数据卷）
docker compose down -v     # 停服务并删除数据卷
```

**预期结果**：
- `/health` → `{"status":"ok"}`
- `/health/ready` → `{"status":"ok","components":{"postgres":{"connected":true,...},"redis":{...},"qdrant":{...}}}`
- 集成测试全部通过。

---

## 八、哪些是 Phase 0 占位，后续 Phase 才实现

| 占位内容 | 何时实现 |
|---------|---------|
| `app/models/*` ORM 表模型 + Alembic 迁移 | Phase 1 |
| `app/api/upload.py`、`documents.py`、`query.py`、`admin.py`、`eval.py` | Phase 2 / 6 / 8 / 10 |
| `app/services/parser_service.py`、`cleaner_service.py` | Phase 3 |
| `app/services/chunk_service.py` | Phase 4 |
| `app/services/embedding_service.py`、`vector_store.py`、`keyword_store.py`、`reranker.py` | Phase 5 |
| `app/services/retriever.py`、`fusion.py` | Phase 6 |
| `app/services/safety_guard.py`、`intent_classifier.py`、`query_rewriter.py` 等 + `app/prompts/*` | Phase 7 |
| `app/services/answer_generator.py`、`citation_checker.py` | Phase 8 |
| `app/services/update_service.py`（chunk diff 增量更新） | Phase 9 |
| `app/services/eval_service.py` | Phase 10 |
| `app/workers/*` Celery 任务 | Phase 2+ |

---

## 九、后续 Phase 如何在当前骨架上扩展

1. **加表（Phase 1）**：在 `app/models/` 下新建 ORM 类继承 `app/db/base.py:Base`，配置 Alembic 后 `alembic upgrade head`。
2. **加接口**：在 `app/api/` 下新建 router，在 `app/api/__init__.py` 中 `include_router`，
   业务逻辑放 `app/services/`，路由层只做参数解析与调用（依赖 `dependencies.get_db` 取会话）。
3. **加基础设施客户端**：参照 `dependencies.py` 中 Redis/Qdrant 的写法，集中创建、懒加载、暴露连接检查。
4. **加配置项**：在 `config.py:Settings` 加字段，并在 `.env.example` 同步补占位，避免配置散落。

---

## 十、技术栈

Python 3.11+ · FastAPI · Pydantic v2 · SQLAlchemy 2.x · PostgreSQL · Redis · Qdrant · Docker Compose · pytest · `pyproject.toml` 管理依赖。
