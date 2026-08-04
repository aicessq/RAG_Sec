# RAG_Sec Project Learning Resources

## Knowledge

- [Repository spec: `Doc/文档2.MD`](../Doc/文档2.MD)
  项目的权威可执行规格。Use for: 判断阶段边界、功能取舍和实现是否符合设计。
- [Current implementation guide: `README.md`](../README.md)
  当前项目状态、运行方式和功能概览。Use for: 快速确认项目已经实现到哪些阶段。
- [Agent guidance: `CLAUDE.md`](../CLAUDE.md)
  项目给 Claude Code 的工作约束和架构提示。Use for: 学习代码分层、测试命令、非显而易见规则。
- [项目启动与使用指南](../Doc/项目启动与使用指南.md)
  基于真实代码的启动与验证路径。Use for: 第 2 课本地/Compose 启动。
- [Teach_Learn 课程总览](README.md)
  12 课完整路径与参考材料索引。Use for: 选择下一课、复习导航。
- [术语表](reference/glossary.html) · [四条主流程](reference/four-flows.html) · [数据模型](reference/data-model.html) · [检索参数](reference/retrieval-pipeline.html)
  课程压缩后的速查。Use for: 做练习时不翻长文档。
- [FastAPI documentation](https://fastapi.tiangolo.com/)
  后端 API 框架官方文档。Use for: 理解 `backend/app/api/` 路由、依赖注入和请求响应模型。
- [SQLAlchemy 2.x documentation](https://docs.sqlalchemy.org/)
  Python ORM 官方文档。Use for: 理解 `backend/app/models/`、会话与迁移。
- [Celery documentation](https://docs.celeryq.dev/)
  异步任务队列官方文档。Use for: ingest worker、broker、任务状态。
- [Qdrant documentation](https://qdrant.tech/documentation/)
  向量数据库官方文档。Use for: collection、payload、与软删除对齐。
- [PostgreSQL Full-Text Search](https://www.postgresql.org/docs/current/textsearch.html)
  FTS 官方文档。Use for: `search_tsv`、关键词检索与 fallback 设计背景。
- [Vite documentation](https://vite.dev/guide/)
  前端构建工具官方文档。Use for: `frontend/` 的 dev/build/preview。
- [React documentation](https://react.dev/learn)
  React 官方学习文档。Use for: 前端页面与状态（第 11 课）。

## Wisdom (Communities)

- [FastAPI GitHub Discussions](https://github.com/fastapi/fastapi/discussions)
  Use for: API 设计、框架行为问题。
- [Qdrant Community](https://qdrant.tech/documentation/community/)
  Use for: 向量检索与部署问题。
- [Celery GitHub Discussions](https://github.com/celery/celery/discussions)
  Use for: worker、broker、任务可靠性。

## Gaps

- 尚无独立“RRF / hybrid search”权威短文被钉死为唯一主读；课程内以规格 §2.15 / §14 与代码为准。
- 前端无测试脚本；前端课以 API 对照为主，不假装有前端测试体系。
