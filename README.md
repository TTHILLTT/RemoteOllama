# RemoteOllama

> 跨平台 AI 聊天客户端 — 连接远程 Ollama 服务器

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行

```bash
python -m app.main
```

### 运行测试

```bash
pytest tests/ -v
```

## 项目结构

```
RemoteOllama/
├── app/                    # 应用代码
│   ├── main.py             # 入口
│   ├── models/             # 数据模型
│   ├── database/           # SQLite 数据库层
│   ├── services/           # 业务服务层
│   ├── viewmodels/         # Qt ViewModel 层
│   ├── ui/                 # QML 加载 + 桥接
│   ├── utils/              # 工具（日志/常量）
│   ├── config/             # 配置管理
│   └── resources/qml/      # QML UI 文件
├── tests/                  # 单元测试
├── DESIGN.md               # 完整设计文档
├── requirements.txt        # Python 依赖
└── pyproject.toml          # 项目配置
```

## 打包

### Windows / Linux

```bash
pip install pyinstaller
pyinstaller RemoteOllama.spec
```

### Android

```bash
pip install buildozer
buildozer android debug
```

## 技术栈

- **UI**: Qt 6 + QML (PySide6)
- **HTTP**: httpx (streaming)
- **Database**: SQLite (WAL mode)
- **Markdown**: markdown + Pygments
- **测试**: pytest
