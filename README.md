# Data Analysis Deep Agent

🔍 **基于 LLM Agent 的自动化数据分析平台**  
上传 CSV/Excel 文件，由 AI Agent 在云端沙箱中完成探索性数据分析，自动生成分析报告与图表，并在 Web 界面展示。

---

## 📌 项目定位

这是一个 **个人学习项目**，旨在深入实践以下领域：
- **LLM Agent 应用开发**：基于 DeepAgents (LangChain/LangGraph) 构建可自主规划分析步骤的智能体
- **后端工程化**：FastAPI + 异步任务队列 + 云端沙箱 + 容器化 + CI/CD 全链路
- **可观测性与评估**：集成 LangSmith 追踪 Token 消耗与延迟，建立效率评估体系

适合对 AI Agent、后端工程化、DevOps 感兴趣的学习者参考。

---

## 🚀 核心功能

- ✅ **文件上传**：支持 CSV/Excel 文件，Web 界面一键上传
- ✅ **云端沙箱分析**：利用 Modal Sandbox 在隔离环境中执行代码，保证安全
- ✅ **LLM 智能分析**：DeepSeek 大模型自动生成分析策略、编写并执行代码
- ✅ **报告生成**：输出文本报告与 PNG 图表，可在页面直接查看/下载
- ✅ **异步任务队列**：Procrastinate + PostgreSQL 管理长时间分析任务
- ✅ **可观测性**：LangSmith 全链路追踪 Token 用量、延迟、Agent 轨迹
- ✅ **工程化部署**：Docker Compose 一键启动，GitHub Actions CI/CD 自动构建并推送镜像

---

## 🛠️ 技术栈

| 领域 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| 异步任务 | Procrastinate + PostgreSQL |
| LLM Agent | DeepAgents (LangChain/LangGraph) |
| 模型服务 | DeepSeek API |
| 沙箱执行 | Modal Sandbox |
| 可观测性 | LangSmith |
| 容器化 | Docker + Docker Compose |
| CI/CD | GitHub Actions (lint → test → build & push) |
| 静态检查 | ruff |
| 测试框架 | pytest |

---

## 🧱 工程化亮点

- **多环境配置**：通过 `ENVIRONMENT` 变量区分开发与容器环境，数据库连接串自动切换
- **容器化一键启动**：`docker compose up -d` 启动 PostgreSQL + Web + Worker 三服务
- **CI/CD 流水线**：每次 Push 自动完成代码风格检查 → 单元测试 → Docker 镜像构建并推送至 Docker Hub
- **效率评估体系**：内置评估脚本，对 Agent 的 Token 消耗与延迟进行量化分析
- **安全隔离**：用户文件仅在 Modal 沙箱内处理，避免直接在主机执行任意代码

---

## ⚡ 快速开始

### 环境要求
- Python 3.11+
- Docker & Docker Compose
- 一个 [DeepSeek API Key](https://platform.deepseek.com/)
- （可选）[Modal](https://modal.com/) 与 [LangSmith](https://www.langchain.com/langsmith) 账号

### 1. 克隆项目
```bash
git clone https://github.com/LambProgrammer/data_analysis_deep_agent.git
cd data_analysis_deep_agent
```

### 2. 配置环境变量
复制示例文件并填入你自己的 API Key：
```bash
cp .env.example .env
```
编辑 `.env` 文件，至少填写：
```
DEEPSEEK_API_KEY=你的key
MODAL_TOKEN=你的token
MODAL_ENVIRONMENT=你的环境名
LANGSMITH_API_KEY=你的key（可选）
```

### 3. 一键启动
```bash
docker compose up -d
```
首次启动会自动拉取 PostgreSQL 镜像并构建应用服务。  
启动后访问 `http://localhost:8000` 上传文件开始分析。

### 4. 停止服务
```bash
docker compose down
```

---

## 📁 项目结构

```
data_analysis_deep_agent/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── core/                # Modal、队列、依赖注入
│   ├── routes/              # API 端点
│   ├── services/            # 核心分析逻辑
│   ├── schemas/             # Pydantic 模型
│   └── utils/               # 数据库连接池等
├── data/                    # 挂载卷（上传文件、生成产物）
├── evaluation/              # 效率评估脚本与样本数据
├── static/                  # 前端测试页面
├── tests/                   # 单元测试
├── .github/workflows/       # CI/CD 工作流
├── config.py                # 多环境配置
├── llm_provider.py          # LLM 惰性单例工厂
├── docker-compose.yml       # 容器编排
├── Dockerfile               # 应用镜像
├── requirements.txt         # 依赖清单
├── pyproject.toml           # 项目元数据与工具配置
└── .env.example             # 环境变量模板
```

---

## 🧪 测试与评估

### 单元测试
```bash
pytest tests/ -v
```
单元测试覆盖核心逻辑（如配置解析），不调用外部服务，可在本地秒级运行。

### 集成测试与评估
集成测试依赖真实数据库、LLM、Modal 服务，**按需运行**：  
```bash
python test_async_conn.py          # 测试数据库异步连接
python test_modal_sandbox.py       # 测试 Modal 沙箱创建
python test_agent_sandbox.py       # 测试 Agent 完整分析流程
python evaluation/eval_efficiency.py  # 运行效率评估
```



---

## 🤝 贡献与参考

本项目为个人学习所用，欢迎 Star ⭐️ 或 Fork 参考。  
如果你对 Agent 工程化、Docker 部署、CI/CD 有任何疑问，欢迎提 Issue 交流。

---

## 📄 许可证

MIT
