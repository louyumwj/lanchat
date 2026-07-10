# LangChain Chat

一个用于学习和实践的多轮会话命令行项目。项目采用分层架构，支持用户管理、预设 Prompt、会话保存、历史搜索、Markdown 导出、多存储后端和 dev/test/prod 多环境配置。

项目默认使用 `mock-local` 本地模拟模型，所以即使没有 API Key，也可以完整跑通核心流程。

## 功能特性

- 多轮对话：支持流式输出、上下文历史、Token 用量统计。
- 用户管理：创建用户、切换用户、删除用户，用户数据相互隔离。
- 会话管理：新建、加载、重命名、删除、搜索历史消息。
- 预设 Prompt：内置系统预设，支持个人预设新增、编辑、删除。
- Markdown 导出：将指定会话导出为 Markdown 文件。
- 模型切换：支持默认模型设置和会话内模型切换。
- 存储后端：支持 SQLite、File、MySQL 配置入口。
- 多环境：支持 `dev`、`test`、`prod` 三套配置隔离。
- 测试与文档：包含单元测试、冒烟测试和架构说明。

## 技术栈

| 类型 | 技术 |
|---|---|
| 语言 | Python 3.10+ |
| 依赖管理 | uv |
| LLM 框架 | LangChain / langchain-openai |
| 数据模型 | Pydantic |
| 存储 | SQLite / File / MySQL |
| TUI | Rich / prompt_toolkit |
| 配置 | YAML / python-dotenv |
| 测试 | pytest |

## 快速开始

进入项目目录：

```powershell
cd C:\Users\17267\Documents\Codex\2026-07-09\files-mentioned-by-the-user-md\outputs\langchain-chat
```

### 方式一：使用 Anaconda 环境

创建名为 `lanchat` 的环境：

```powershell
conda env create -f environment.yml
```

激活环境：

```powershell
conda activate lanchat
```

初始化数据库和内置预设：

```powershell
python scripts/init_db.py
```

启动程序：

```powershell
python src/main.py
```

### 方式二：使用 uv

安装依赖：

```powershell
uv sync --dev
```

初始化数据库和内置预设：

```powershell
uv run python scripts/init_db.py
```

启动程序：

```powershell
uv run python src/main.py
```

如果本机已经有相关依赖，也可以直接使用：

```powershell
python scripts/init_db.py
python src/main.py
```

## 配置 API Key

项目默认使用 `mock-local`，不需要 API Key。若要连接 OpenAI 兼容接口，可以复制 `.env.example` 为 `.env`，然后填写：

```env
APP_ENV=dev
API_BASE_URL=https://api.openai.com/v1
API_KEY=your-api-key
MODEL_NAME=gpt-4o-mini
```

随后在 `config.yaml` 或环境配置中把默认模型改为真实模型名。

## 多环境切换

配置加载顺序：

```text
config.yaml + config.{APP_ENV}.yaml + .env + .env.{APP_ENV}
```

PowerShell 示例：

```powershell
$env:APP_ENV="dev"; uv run python src/main.py
$env:APP_ENV="test"; uv run pytest
$env:APP_ENV="prod"; uv run python scripts/smoke.py prod
```

当前环境文件：

| 环境 | 配置文件 | 默认用途 |
|---|---|---|
| dev | `config.dev.yaml` | 本地开发，SQLite |
| test | `config.test.yaml` | 自动测试，独立测试数据 |
| prod | `config.prod.yaml` | 生产配置入口，MySQL |

## 常用命令

初始化数据库：

```powershell
python scripts/init_db.py
```

或使用 uv：

```powershell
uv run python scripts/init_db.py
```

运行 TUI：

```powershell
python src/main.py
```

或使用 uv：

```powershell
uv run python src/main.py
```

运行测试：

```powershell
python -m pytest -p no:cacheprovider
```

或使用 uv：

```powershell
uv run pytest
```

运行三环境冒烟测试：

```powershell
uv run python scripts/smoke.py dev test prod
```

代码检查：

```powershell
uv run ruff check .
```

## 项目结构

```text
langchain-chat/
├── config/                  # 预设 Prompt 和日志配置
├── docs/                    # 架构文档
├── scripts/                 # 初始化、冒烟测试脚本
├── src/
│   ├── core/                # 核心业务逻辑
│   ├── interface/           # UI 协议与扩展接口
│   ├── models/              # Pydantic 数据模型
│   ├── storage/             # 存储后端
│   └── ui/tui/              # 命令行交互界面
├── tests/                   # 单元测试
├── config.yaml              # 基础配置
├── config.dev.yaml          # dev 环境覆盖配置
├── config.test.yaml         # test 环境覆盖配置
├── config.prod.yaml         # prod 环境覆盖配置
├── pyproject.toml           # 项目依赖与工具配置
└── README.md
```

## 核心流程

1. 用户在 TUI 输入消息。
2. `SessionManager` 保存用户消息。
3. `ChatEngine` 调用模型并流式返回回复。
4. TUI 实时展示回复内容。
5. `SessionManager` 保存 AI 回复和 Token 用量。
6. `StorageBackend` 将数据持久化到当前环境的数据源。

## 数据与导出

- 运行时数据默认写入 `data/`，该目录不提交到 Git。
- 导出的 Markdown 文件默认位于 `data/users/{username}/exports/`。
- test 环境使用独立数据路径，避免污染 dev 数据。

## Git 标签

项目计划中的阶段标签如下：

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

## 说明

`MySQLBackend` 当前保留了生产配置入口，并使用本地模拟方式保证无数据库环境也能完成流程验证。接入真实 MySQL 时，只需要替换该后端内部实现，业务层无需调整。
