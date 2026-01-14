# OpenAPI Agent MCP（用途说明）

这个项目提供一个 **MCP Server + CLI**，用于从 FastAPI 暴露的 `/{baseUrl}/openapi.json` 读取 OpenAPI 规范，并把“接口可调用信息”结构化输出给 Agent / 工具链使用。

核心价值是：让 Agent 不需要“猜接口”，而是通过 MCP tools **检索接口 → 获取请求参数 schema → 获取响应 schema**，再把结果交给业务层执行器去发真实 HTTP 请求（鉴权、重试、幂等等仍由业务层负责）。

## 提供的 3 个 MCP Tools

- `search_operations`：按 `tag / operationId / path / summary / description` 搜索接口
- `get_request_schema(operationId)`：返回 path/query/header/cookie 参数的 JSON Schema 骨架 + requestBody schema（优先 `application/json`）
- `get_response_schema(operationId)`：返回不同 status code 下的响应 schema（优先 `application/json`）

## 关键约定（对 Agent 友好）

- **hash 缓存**：每次拉取 `/openapi.json`，内容不变则复用索引/解析结果，避免重复解析。
- **deref**：尽可能展开 `$ref`；遇到循环/超阈值时保留 `$ref`，并在输出里携带 `components`，确保调用方仍可解析引用。
- **不做真实请求**：本项目只产出“调用计划”所需的结构化信息，不负责网络调用与鉴权。

## 快速验证（CLI）

```bash
poetry run openapi-agent-mcp --base-url http://localhost:5052 fetch
poetry run openapi-agent-mcp --base-url http://localhost:5052 search --query "" --limit 20
```

更完整的输入输出结构与错误约定，见 `openapi_agent_mcp_spec.md`。

