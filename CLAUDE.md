# Distiller（万物可蒸馏）— CLAUDE.md

## 项目概述

Distiller 是一款 Windows 桌面知识蒸馏工具。用户将人物/领域资料录入本地向量知识库，通过 DeepSeek v4 API 提炼出做事方法论、思维模式、话术风格等模式，并以聊天方式互动。详见 [需求文档](docs/requirements.md)。

## 标准文档路径

| 文档 | 路径 | 用途 |
|------|------|------|
| 需求文档 | [docs/requirements.md](docs/requirements.md) | 功能需求、非功能需求、使用场景 |
| 技术规范 | [docs/tech-spec.md](docs/tech-spec.md) | 技术选型、架构、数据库设计、关键实现 |
| 设计规范 | [docs/design-spec.md](docs/design-spec.md) | UI 风格、配色、布局、交互 |
| 执行计划 | [docs/execution-plan.md](docs/execution-plan.md) | 10 阶段实施步骤、进度追踪 |
| 开发日志 | [devlog/](devlog/) | 每日开发记录 |

## 工作约定

1. **逐阶段推进**：严格按 10 个阶段顺序开发，每个阶段完成后验证，确认无误再进入下一阶段
2. **可运行交付**：每个阶段的产出必须是可运行、可验证的
3. **每日记录**：每次开发结束后更新 `devlog/YYYY-MM-DD.md`，记录完成事项和待办
4. **代码简洁**：不引入未使用的抽象，不过度设计，不写多余注释
5. **验证优先**：每个阶段完成后运行 `python main.py` 验证功能正常
6. **先确认再动手**：修改已有代码前先 Read，不确定的地方先问
7. **不跨阶段开发**：不提前做后续阶段的准备工作

## 技术要点

- **运行命令**：`python main.py`
- **依赖安装**：`pip install -r requirements.txt`
- **Eel 通信**：Python `@eel.expose` → JS `eel.function_name()(callback)`
- **数据库**：SQLite（`data/distiller.db`）+ ChromaDB（`data/chroma/`）
- **嵌入模型**：sentence-transformers all-MiniLM-L6-v2，首次运行自动下载 (~80MB)
- **AI API**：DeepSeek v4，OpenAI 兼容协议，base_url 指向 DeepSeek 端点
- **API Key**：存储在 SQLite settings 表中，base64 编码

## 开发阶段速览

| 阶段 | 内容 | 核心产出 |
|------|------|----------|
| 1 | 项目骨架 | Eel 窗口启动 |
| 2 | 配置 & API | DeepSeek 对话通 |
| 3 | 知识库核心 | 文本录入 + RAG 问答 |
| 4 | 文档解析 | docx/pdf 上传录入 |
| 5 | 蒸馏引擎 | 结构化方法论报告 |
| 6 | 聊天界面 | 流式对话体验 |
| 7 | 全网搜索 | DuckDuckGo 搜索录入 |
| 8 | Skills 系统 | 模板 + 角色管理 |
| 9 | 风格生成 | 模仿风格创作 |
| 10 | 打包发布 | Distiller.exe |

## 不要做的事

- 不要引入新的依赖而不确认
- 不要跳过阶段开发
- 不要修改 docs/ 中的标准文档而不确认
- 不要在未经验证的情况下批量推进多个阶段
- 不要在阶段 1-3 完成前考虑 Skills 或风格生成的实现
