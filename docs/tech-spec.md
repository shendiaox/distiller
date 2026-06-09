# Distiller（万物可蒸馏）— 技术规范

> 版本：v1.0 | 日期：2026-05-30

---

## 一、技术选型

| 层面 | 技术 | 版本 | 选型理由 |
|------|------|------|----------|
| 后端 | Python | 3.10+ | 易维护，AI/ML 库丰富 |
| 前端 | HTML/CSS/JS | — | 聊天 UI 最适合 Web 渲染 |
| 桥接框架 | Eel | ≥0.16.0 | Python 与前端轻量通信，与 GameHub/MemoFlow 一致 |
| AI 对话 | DeepSeek v4 API | — | 用户已有 API Key，OpenAI 兼容协议 |
| 嵌入模型 | sentence-transformers (all-MiniLM-L6-v2) | ≥2.7.0 | 本地运行，免费，CPU 友好，中文支持 |
| 向量数据库 | ChromaDB | ≥0.5.0 | Python 原生，本地持久化，轻量零配置 |
| 元数据存储 | SQLite | 3（内置） | 零配置，适合单机应用 |
| HTTP 客户端 | openai (SDK) | ≥1.0.0 | 调用 DeepSeek API（兼容 OpenAI 协议） |
| 网页搜索 | duckduckgo-search | ≥6.0.0 | 免费，无需 API Key |
| 文档解析 | python-docx + PyPDF2 | — | docx / pdf 文本提取 |
| 打包 | PyInstaller | ≥6.0 | 单目录 .exe 分发 |

## 二、项目结构

```
Distiller/
├── main.py                    # 应用入口，Eel 启动
├── requirements.txt           # Python 依赖
├── backend/
│   ├── __init__.py
│   ├── config.py              # 配置文件读写（API Key、设置）
│   ├── database.py            # SQLite 连接、建表
│   ├── knowledge_base.py     # ChromaDB 管理（增删查）
│   ├── document_parser.py    # 文档解析（txt/docx/pdf）
│   ├── llm_client.py          # DeepSeek API 调用封装
│   ├── web_search.py          # DuckDuckGo 搜索
│   ├── distillation.py        # 蒸馏引擎（Prompt Chain）
│   ├── skill_manager.py       # Skills 模板/角色 CRUD
│   └── embedding.py           # 本地嵌入模型管理
├── frontend/
│   ├── index.html             # SPA 入口
│   ├── css/
│   │   ├── style.css          # 全局样式/变量
│   │   ├── chat.css           # 聊天界面样式
│   │   └── sidebar.css        # 侧边栏样式
│   ├── js/
│   │   ├── app.js             # 应用入口、状态管理
│   │   ├── bridge.js          # Eel 后端调用封装
│   │   ├── chat.js            # 聊天消息渲染与发送
│   │   ├── knowledge.js       # 知识库管理界面
│   │   ├── skills.js          # Skills 管理界面
│   │   └── markdown.js        # Markdown 渲染
│   └── assets/
│       └── logo.png           # 应用图标
├── data/                      # 运行时生成
│   ├── distiller.db           # SQLite 数据库（配置、元数据）
│   └── chroma/                # ChromaDB 持久化目录
├── docs/                      # 项目文档
└── devlog/                    # 开发日志
```

## 三、数据库设计

### SQLite（元数据 & 配置）

```sql
-- 知识库表
CREATE TABLE knowledge_bases (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    description TEXT DEFAULT '',
    created_at  TEXT DEFAULT (datetime('now','localtime')),
    updated_at  TEXT DEFAULT (datetime('now','localtime'))
);

-- 文档来源表
CREATE TABLE documents (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    kb_id             INTEGER NOT NULL,
    title             TEXT NOT NULL,
    source_type       TEXT NOT NULL,   -- 'paste', 'file', 'web_search'
    source_path       TEXT DEFAULT NULL,
    chunk_count       INTEGER DEFAULT 0,
    created_at        TEXT DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id)
);

-- Skills 表
CREATE TABLE skills (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    type            TEXT NOT NULL,     -- 'template', 'persona'
    system_prompt   TEXT NOT NULL,
    description     TEXT DEFAULT '',
    is_default      INTEGER DEFAULT 0,
    created_at      TEXT DEFAULT (datetime('now','localtime')),
    updated_at      TEXT DEFAULT (datetime('now','localtime'))
);

-- 设置表（Key-Value）
CREATE TABLE settings (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  TEXT DEFAULT (datetime('now','localtime'))
);
```

### ChromaDB（向量存储）

- 每个知识库对应一个 ChromaDB Collection
- Collection 命名：`kb_{kb_id}`
- 元数据字段：`document_id`, `chunk_index`, `source_type`

## 四、通信机制

- 前端通过 `eel.function_name(args)(callback)` 调用 Python 函数
- Python 通过 `@eel.expose` 装饰器暴露函数
- 聊天消息通过回调函数流式返回（逐 token 推送）

## 五、关键实现要点

### 5.1 文本分块策略
- 块大小：512 tokens（约 1000 中文字符）
- 重叠：50 tokens
- 按段落边界优先切分，避免截断句子
- 使用 langchain 的 RecursiveCharacterTextSplitter

### 5.2 RAG 流程
1. 用户提问 → 本地嵌入模型向量化
2. ChromaDB 检索 top-k 相关块（默认 k=5）
3. 拼接上下文 → 发送给 DeepSeek API
4. 流式返回回答

### 5.3 蒸馏 Prompt 设计
- 蒸馏不等同于问答，需要专门的 Prompt Chain
- 第一步：从素材中提取行为模式
- 第二步：归纳分类（决策 / 沟通 / 执行 / 思维框架）
- 第三步：生成结构化方法论报告
- 可插入用户选择的 Skill 模板作为分析视角

### 5.4 Skills 系统
- 模板类 Skill：预设的 `system_prompt` 片段，注入蒸馏/对话流程
- 角色类 Skill：完整的 system prompt，定义 AI 的行为模式
- Skills 以 JSON 形式加载，支持用户创建/编辑/删除

### 5.5 API Key 安全
- 存储在 SQLite settings 表中
- 使用 base64 简单编码（非明文）
- 仅在内存中解密使用

## 六、依赖清单

```txt
eel>=0.16.0
chromadb>=0.5.0
sentence-transformers>=2.7.0
openai>=1.0.0
duckduckgo-search>=6.0.0
python-docx>=1.0.0
PyPDF2>=3.0.0
```
