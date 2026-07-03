# RAG_Sec Project Learning Resources

## Knowledge

- [Repository spec: `Doc/文档2.MD`](../Doc/文档2.MD)
  项目的权威可执行规格。Use for: 判断阶段边界、功能取舍和实现是否符合设计。
- [Current implementation guide: `README.md`](../README.md)
  当前项目状态、运行方式和功能概览。Use for: 快速确认项目已经实现到哪些阶段。
- [Agent guidance: `CLAUDE.md`](../CLAUDE.md)
  项目给 Claude Code 的工作约束和架构提示。Use for: 学习代码分层、测试命令、非显而易见规则。
- [FastAPI documentation](https://fastapi.tiangolo.com/)
  后端 API 框架官方文档。Use for: 理解 `backend/app/api/` 路由、依赖注入和请求响应模型。
- [SQLAlchemy ORM documentation](https://docs.sqlalchemy.org/)
  Python ORM 官方文档。Use for: 理解 `backend/app/models/`、数据库会话和持久化层。
- [Celery documentation](https://docs.celeryq.dev/)
  异步任务队列官方文档。Use for: 理解 ingest worker、任务分发和后台处理。
- [Qdrant documentation](https://qdrant.tech/documentation/)
  向量数据库官方文档。Use for: 理解向量检索、collection、point payload 与软删除对齐。
- [Vite documentation](https://vite.dev/guide/)
  前端构建工具官方文档。Use for: 理解 `frontend/` 的开发、构建和预览命令。
- [React documentation](https://react.dev/learn)
  React 官方学习文档。Use for: 理解前端组件、状态和用户交互。

## Wisdom (Communities)

- [FastAPI GitHub Discussions](https://github.com/fastapi/fastapi/discussions)
  Use for: API 设计、FastAPI 行为和框架问题。
- [Qdrant Discord / Community](https://qdrant.tech/documentation/community/)
  Use for: 向量检索、索引设计和 Qdrant 部署问题。
- [Celery GitHub Discussions](https://github.com/celery/celery/discussions)
  Use for: worker、broker、任务可靠性问题。

## Gaps

- 需要后续补充一份“本项目文件地图”参考文档，压缩记录每个目录的职责。
- 需要后续补充一份“RAG 查询链路术语表”，统一学习中的中文/英文术语。
