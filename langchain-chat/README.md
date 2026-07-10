# LangChain Chat

基于 LangChain 风格架构的多轮会话教学项目。项目默认使用 `mock-local` 模型，因此即使没有 API Key，也可以完整验证用户管理、会话保存、搜索、导出和多环境切换流程。

## 快速开始

```powershell
uv run python scripts/init_db.py
uv run python src/main.py
```

如果没有安装依赖，也可以先执行：

```powershell
uv sync --dev
```

## 已实现功能

- TUI 主菜单：用户管理、会话管理、预设管理、开始对话、设置。
- 用户管理：创建、切换、删除、默认模型设置。
- 预设 Prompt：加载系统内置预设，支持个人预设 CRUD。
- 会话管理：新建、列表、重命名、删除、搜索、Markdown 导出。
- 对话引擎：支持 mock-local 流式输出；配置 API Key 后尝试调用 OpenAI 兼容接口。
- 存储后端：SQLite、File、MySQL 模拟后端，业务层通过工厂切换。
- 日志：支持 JSON 格式日志配置。
- 测试：覆盖存储、用户、会话、配置和对话引擎。
- 多环境：支持 `dev`、`test`、`prod` 三套环境覆盖配置。

## 环境切换

PowerShell：

```powershell
$env:APP_ENV="dev"; uv run python src/main.py
$env:APP_ENV="test"; uv run pytest
$env:APP_ENV="prod"; uv run python scripts/smoke.py prod
```

配置加载顺序：

```text
config.yaml + config.{APP_ENV}.yaml + .env + .env.{APP_ENV}
```

环境覆盖文件只需要写和基础配置不同的部分。

## 验证命令

```powershell
uv run python scripts/init_db.py
uv run python scripts/smoke.py dev test prod
uv run pytest
```

## 项目结构

```text
src/
  core/        业务逻辑：配置、用户、预设、会话、对话引擎
  models/      Pydantic 数据模型
  storage/     SQLite/File/MySQL 后端与工厂
  interface/   UI 协议和未来扩展接口
  ui/tui/      命令行交互界面
tests/         单元测试
scripts/       初始化和冒烟验证脚本
config/        预设和日志配置
docs/          架构文档
```

## Git 标签建议

按计划完成正式开发时，建议每个阶段验证后打标签：

```text
step-1-init
step-2-skeleton
step-3-sqlite
step-4-user-mgmt
step-5-presets
step-6-chat-engine
step-7-first-chat
step-8-session-mgmt
step-9-search
step-10-export-switch
step-11-mysql
step-12-logging-file
step-13-tests
step-14-docs-extend
step-15-envs
```
