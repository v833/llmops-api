# LLMOps API

![LLMOps API](https://img.shields.io/badge/LLMOps-API-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)
![Flask](https://img.shields.io/badge/Flask-2.0+-red)
![LangGraph](https://img.shields.io/badge/LangGraph-latest-orange)
![LangChain](https://img.shields.io/badge/LangChain-latest-yellow)

LLMOps API 是一个基于 Flask 的 API 服务，用于构建、管理和部署基于大语言模型的智能体应用。该项目集成了 LangGraph 和 LangChain，提供了一套完整的工具链，用于创建具有状态、多角色的智能体应用程序。

前端仓库: https://github.com/v833/llmops-ui

## 功能特点

- **智能体管理**：创建、配置和管理基于 LLM 的智能体
- **知识库管理**：上传、索引和检索文档，支持语义搜索
- **工具集成**：
  - 内置工具：提供多种预设工具
  - API 工具：支持通过 OpenAPI 规范集成第三方 API
- **对话管理**：跟踪和管理用户与智能体的对话
- **工作流编排**：使用 LangGraph 构建复杂的智能体工作流，支持循环和条件分支
- **用户认证**：支持密码登录和 OAuth 认证
- **异步任务处理**：使用 Celery 处理长时间运行的任务

## 技术栈

- **后端框架**：Flask
- **数据库**：PostgreSQL
- **缓存**：Redis
- **任务队列**：Celery
- **LLM 集成**：支持多种大语言模型（OpenAI、Grok、DeepSeek 等）
- **向量数据库**：支持 Weaviate
- **对象存储**：支持腾讯云 COS

## 快速开始

### 环境要求

- Python 3.9+
- PostgreSQL
- Redis

### 安装

1. 克隆仓库

```bash
git clone https://github.com/yourusername/llmops-api.git
cd llmops-api
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 配置环境变量

复制 `.env.example` 文件为 `.env` 并根据需要修改配置：

```bash
cp .env.example .env
```

4. 初始化数据库

```bash
flask db upgrade
```

5. 启动服务

```bash
python app/http/app.py
```

## 项目结构

```
llmops-api/
├── app/                    # 应用入口
│   └── http/               # HTTP 服务
├── config/                 # 配置文件
├── internal/               # 内部模块
│   ├── core/               # 核心功能
│   │   ├── agent/          # 智能体相关
│   │   └── tools/          # 工具相关
│   ├── entity/             # 实体定义
│   ├── extension/          # 扩展模块
│   ├── handler/            # 请求处理器
│   ├── middleware/         # 中间件
│   ├── migration/          # 数据库迁移
│   ├── model/              # 数据模型
│   ├── router/             # 路由定义
│   ├── schema/             # 请求/响应模式
│   ├── server/             # 服务器配置
│   └── service/            # 业务服务
├── pkg/                    # 公共包
└── study/                  # 示例和学习资料
```

## API 接口

LLMOps API 提供了丰富的 RESTful API 接口，包括：

- 应用管理 API
- 工具管理 API
- 知识库管理 API
- 文档管理 API
- 对话管理 API
- 用户认证 API
- 账号管理 API

详细的 API 文档请参考 API 文档。

## LangGraph 集成

LLMOps API 深度集成了 LangGraph，支持构建具有状态、多角色的应用程序。LangGraph 提供了以下核心优势：

- **循环和分支**：在 LLM/Agent 应用程序中实现循环和条件语句
- **持久化**：自动保存状态，支持暂停和恢复执行
- **人机交互**：支持中断执行以进行人机交互
- **流支持**：支持流式输出（包括 token 流式输出）

## 贡献指南

欢迎贡献代码、报告问题或提出新功能建议。请遵循以下步骤：

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 [MIT 许可证](LICENSE)。

## 联系方式

如有任何问题或建议，请通过 [issues](https://github.com/v833/llmops-api/issues) 联系我们。
