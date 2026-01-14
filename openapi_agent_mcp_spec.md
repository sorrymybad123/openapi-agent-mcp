# OpenAPI Agent MCP Spec（FastAPI `/openapi.json`）

## 1. 目标与边界

### 1.1 目标（给前端开发提速）

在前端开发阶段，引入一个“OpenAPI Agent”（通过 MCP 工具访问后端 OpenAPI 规范），让 agent 能自动：

1) 按 `tag / operationId / path / 描述` 列出/搜索接口  
2) 获取某个接口的完整参数 schema（`path/query/body/header/cookie`）  
3) 获取响应 schema（不同 status code 下的结构）

并输出给“业务层执行器”（业务层负责：实际 HTTP 请求、鉴权、重试、幂等等）：

```json
{
  "operationId": "string",
  "method": "GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD",
  "path": "/api/xxx/{id}",
  "params": {
    "path": {},
    "query": {},
    "headers": {},
    "body": null
  },
  "expectedResponses": {}
}
```

### 1.2 非目标

- 不在 agent 层执行真实 HTTP 请求（不做鉴权/重试/幂等等）。
- 不在本文档规定任何具体 UI 或前端框架用法（只定义协议与输出结构）。

## 2. OpenAPI 数据源（FastAPI）

### 2.1 服务端配置约定

后端 FastAPI 通过 `hr.py` 暴露：

- Swagger UI：`/info`
- OpenAPI JSON：`/openapi.json`

说明：`db/kingdee_session_middleware.py` 对 `/openapi.json` 做了排除（不需要 Cookie，即可读取规范），适合 agent 在开发期拉取。

### 2.2 OpenAPI 版本

MCP 工具应支持 OpenAPI 3.x（FastAPI 默认输出 3.0.x/3.1.x 之一）。如果遇到 3.1 的 JSON Schema 语义差异，工具需要兼容或在输出中显式标注。

## 3. 总体工作流（推荐）

1) 前端/开发者描述需求（自然语言）
2) agent 调用 `search_operations` 找到候选接口
3) agent 选定 `operationId` 后：
   - 调用 `get_request_schema(operationId)` 生成 `params` 的结构骨架
   - 调用 `get_response_schema(operationId)` 了解不同 `status_code` 下的返回结构
4) agent 输出最终“调用计划”（`operationId + method + path + params + expectedResponses`）
5) 业务层执行器拿到调用计划后，负责：
   - 拼接 URL、填充 path/query/header/body
   - 鉴权（Cookie / Authorization / 自定义 Header）
   - 网络重试、幂等 key、超时、错误兜底等

## 4. MCP 工具定义（3 个能力）

本 spec 只定义工具的输入输出结构；具体实现可以是：
- MCP server 直接拉取 `/openapi.json` 并解析
- 或 MCP server 通过配置拿到 OpenAPI 文件/缓存

### 4.1 通用约定

#### 4.1.1 OpenAPI 拉取（仅 `{baseUrl}/openapi.json`）

- 默认 OpenAPI 地址：`{baseUrl}/openapi.json`
- `baseUrl` 由业务层配置（例如 dev/qa/prod）
- 工具侧必须实现缓存（本仓库默认方案：hash 缓存）：
  - **每次拉取** `/openapi.json`，在下载过程中计算内容 hash（例如 `sha256`）
  - 若 hash 未变化：必须复用上一版解析结果/索引（避免重复解析与重建索引）
  - 若 hash 变化：刷新索引与解析缓存
  - 可选：实现 `cache_ttl_seconds`（TTL 期间不拉取，适合本地调试；默认关闭）

#### 4.1.2 schema 表达形式（关键约定）

为了让前端/agent “直接可用”，本 spec 约定：

- `get_request_schema` / `get_response_schema` 返回的 schema 应尽可能 **已展开（dereference）**：
  - 将 OpenAPI 的 `$ref` 展开为内联结构
  - 若无法完全展开（例如循环引用），允许保留 `$ref`，但必须同时返回 `components` 以便调用方解析

建议优先实现“尽可能展开 + 兜底保留 `$ref` + 透出 `components`”。

#### 4.1.3 content-type 选择

当一个 request/response 有多个 `content-type`：

- 默认优先：`application/json`
- 若不存在 `application/json`：选择第一个可用的 `content-type`
- 工具输出需把最终选择写进结果（避免调用方猜测）

#### 4.1.4 `$ref` 展开（deref）默认策略（本仓库约定）

- 默认：**尽可能展开（dereference）**，将 `$ref` 指向的 schema 内联到输出。
- 循环引用/超阈值：**保留 `$ref`**，同时在 tool 输出中携带 `components`，确保调用方仍能解析引用。
  - “`components`”指 OpenAPI 根对象中的 `components`（如 `#/components/schemas/*`）。
  - 推荐实现安全阈值：`max_depth` / `max_nodes`（防止恶意或异常文档导致无限展开或爆炸增长）。
- 不可解析的 `$ref`：不得静默丢字段；应返回错误对象（见 6.1）。

### 4.2 Tool: `search_operations`

#### 4.2.1 输入

```json
{
  "query": "string (可为空)",
  "match": {
    "tag": true,
    "operationId": true,
    "path": true,
    "summary": true,
    "description": true
  },
  "method": "GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD|null",
  "limit": 50
}
```

约定：

- `query` 为空：返回所有接口（受 `limit` 限制）
- 默认 `match` 全部为 `true`
- `method=null` 表示不限方法

#### 4.2.2 输出

```json
[
  {
    "operationId": "string",
    "method": "GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD",
    "path": "/api/example/{id}",
    "tags": ["string"],
    "summary": "string|null",
    "description": "string|null"
  }
]
```

### 4.3 Tool: `get_request_schema`

#### 4.3.1 输入

```json
{
  "operationId": "string"
}
```

#### 4.3.2 输出

```json
{
  "operationId": "string",
  "method": "GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD",
  "path": "/api/example/{id}",
  "params": {
    "path": {
      "type": "object",
      "properties": {},
      "required": []
    },
    "query": {
      "type": "object",
      "properties": {},
      "required": []
    },
    "header": {
      "type": "object",
      "properties": {},
      "required": []
    },
    "cookie": {
      "type": "object",
      "properties": {},
      "required": []
    }
  },
  "body": {
    "selectedContentType": "application/json|null",
    "required": false,
    "schema": {}
  },
  "components": {}
}
```

约定：

- `params.path/query/header/cookie` 都输出为 JSON Schema（`type=object`），并包含：
  - `properties`：每个参数名对应的 schema
  - `required`：必填参数名列表
- header 参数规范化：
  - 以 OpenAPI parameter `name` 为 key
  - 不在这里做大小写改写（业务层可以按 HTTP 需要处理）
- `body`：
  - 如果无 requestBody：`body.selectedContentType=null` 且 `body.schema={}` 且 `body.required=false`
  - 若有 requestBody：按 `content-type` 选择策略决定 `selectedContentType`，输出对应 `schema`
- `components`：当输出 schema 中仍包含 `$ref` 时必须提供；若已完全展开，可返回空对象

### 4.4 Tool: `get_response_schema`

#### 4.4.1 输入

```json
{
  "operationId": "string"
}
```

#### 4.4.2 输出

```json
{
  "operationId": "string",
  "method": "GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD",
  "path": "/api/example/{id}",
  "responses": {
    "200": {
      "selectedContentType": "application/json|null",
      "schema": {}
    },
    "400": {
      "selectedContentType": "application/json|null",
      "schema": {}
    },
    "default": {
      "selectedContentType": "application/json|null",
      "schema": {}
    }
  },
  "components": {}
}
```

约定：

- key 为 status code（字符串），包含 `default`
- 若某个 status code 没有 `content`（例如空响应/纯文本）：`selectedContentType=null` 且 `schema={}`
- `components` 同 `get_request_schema` 约定

## 5. Agent 最终产出（给业务层执行器）

agent 的最终产出必须满足：

```json
{
  "operationId": "string",
  "method": "GET|POST|PUT|PATCH|DELETE|OPTIONS|HEAD",
  "path": "/api/example/{id}",
  "params": {
    "path": {},
    "query": {},
    "headers": {},
    "body": null
  },
  "expectedResponses": {
    "200": {
      "contentType": "application/json|null",
      "schema": {}
    }
  }
}
```

映射规则：

- `params.path/query/body` 的结构来自 `get_request_schema`
- `params.headers` 来源于 `get_request_schema.params.header`（字段名从 `header` 统一改为 `headers`，避免与单个 header 混淆）
- `expectedResponses` 来自 `get_response_schema.responses`
- 业务层执行器负责把 `params.headers` 写进 HTTP Header，把 `params.body` 按 `contentType` 序列化

## 6. 错误与边界情况（工具侧输出约定）

为避免“猜测”，工具遇到以下情况必须显式返回错误（或结构化错误对象）：

### 6.1 错误对象（推荐）

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {}
  }
}
```

- `operationId` 不存在或不唯一
- OpenAPI 文档缺失 `paths` 或结构异常
- requestBody/response `schema` 缺失且无法推断
- `$ref` 无法解析（返回错误，或保留 `$ref` 并返回 `components`，但不得静默丢字段）

## 7. 示例（最小可用）

### 7.1 搜索接口

输入：

```json
{
  "query": "purchase requisition",
  "match": { "tag": true, "operationId": true, "path": true, "summary": true, "description": true },
  "method": null,
  "limit": 5
}
```

输出（示意）：

```json
[
  {
    "operationId": "purchase_requisition_list",
    "method": "GET",
    "path": "/purchase-requisition",
    "tags": ["purchase-requisition"],
    "summary": "采购申请列表",
    "description": null
  }
]
```

### 7.2 生成“调用计划”（给业务层执行器）

当 agent 选择了 `operationId="purchase_requisition_list"` 后：

1) `get_request_schema` 告诉 agent：
   - `query` 里有哪些字段、哪些必填、类型是什么
   - 是否存在 `body`，以及默认 `content-type`
2) `get_response_schema` 告诉 agent：
   - `200/400/422/...` 下返回结构分别是什么

agent 最终产出（示意）：

```json
{
  "operationId": "purchase_requisition_list",
  "method": "GET",
  "path": "/purchase-requisition",
  "params": {
    "path": {},
    "query": { "status": "APPROVED", "page": 1, "pageSize": 20 },
    "headers": { "X-User-Id": "123" },
    "body": null
  },
  "expectedResponses": {
    "200": { "contentType": "application/json", "schema": {} },
    "422": { "contentType": "application/json", "schema": {} }
  }
}
```

## 8. 备注（仓库现状）

本 spec 依赖服务端可正常提供 `/openapi.json`。若本地导入 `hr.py` 生成 OpenAPI 失败，优先检查代码是否存在语法错误或冲突标记（例如 `<<<<<<<`）。

## 9. 本仓库实现约定（工程化落地）

本 spec 的默认实现形态：

- 语言：Python
- MCP 框架：FastMCP
- 数据源：仅 `{baseUrl}/openapi.json`
- 缓存：hash（每次下载，hash 不变则复用索引/解析结果；可选 TTL）
- deref：尽可能展开；循环/超阈值保留 `$ref` + 返回 `components`
- 提供 CLI：用于本地调试与生成索引（不替代 MCP tools）

CLI（建议）：

- `openapi-agent-mcp fetch --base-url http://localhost:8000`
- `openapi-agent-mcp index --base-url http://localhost:8000 --out .cache/index.json`
- `openapi-agent-mcp search --base-url http://localhost:8000 --query purchase --limit 5`
- `openapi-agent-mcp schema request --base-url http://localhost:8000 --operation-id purchase_requisition_list`
- `openapi-agent-mcp schema response --base-url http://localhost:8000 --operation-id purchase_requisition_list`
