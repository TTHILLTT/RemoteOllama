你是一名资深全栈架构师，同时也是Python、Qt(QML/PySide6)、Android、Linux、Windows桌面应用开发专家。

请设计并实现一个完整的跨平台GUI客户端。

一、项目目标

开发一个跨平台AI聊天客户端，可以连接服务器上的Ollama。

服务器已经部署好了Ollama。

客户端只负责调用HTTP API。

API调用方式参考：

test_ollama.py（里面已有Python调用示例）

官方API文档：[Ollama API Documentation](https://docs.ollama.com/api/introduction?utm_source=chatgpt.com)（重点使用 /api/chat、/api/tags 等接口）


要求不要重新发明API，而是严格按照官方API实现。


---

二、平台要求

必须支持：

Windows

Linux

Android


要求：

尽可能共用同一套代码。

推荐使用：

> Python + PySide6(Qt/QML)



原因：

Windows支持最好

Linux支持最好

Android官方支持

UI一致

后续方便打包


如果你认为有更优方案（例如Flutter），需要说明优缺点，并最终仍推荐一个最优方案。


---

三、整体架构

请先设计完整的软件架构。

要求至少包含：

UI层

↓

ViewModel

↓

业务层

↓

Ollama Client

↓

HTTP API

要求采用模块化设计。

例如：

app/

    main.py

    models/

    services/

    ui/

    viewmodels/

    database/

    utils/

    config/

    resources/

要求说明每个目录职责。


---

四、UI设计

整体风格参考：

ChatGPT客户端

或者OpenWebUI

布局：

┌────────────────────────────┐
│ 左侧                       │
│                            │
│ + 新建聊天                 │
│                            │
│ 会话1                      │
│ 会话2                      │
│ 会话3                      │
│                            │
├────────────────────────────┤
│ 设置                       │
└────────────────────────────┘


右侧

──────────────────────────────

标题

──────────────────────────────

聊天内容

User

Assistant

User

Assistant

......

──────────────────────────────

输入框

发送按钮

Android界面需要自适应。

要求支持：

深色主题

浅色主题

DPI自适应

高分屏



---

五、会话功能

必须支持：

多会话

例如：

Chat 1

Chat 2

Chat 3

...

点击即可切换。

每个会话：

保存：

标题

创建时间

更新时间

所属模型

消息记录


要求：

消息永久保存。

推荐SQLite。


---

六、多模型支持

支持：

服务器存在多个模型。

进入聊天前可以选择：

Qwen3

DeepSeek

Llama3

Gemma

...

模型列表来自：

GET /api/tags

而不是写死。

要求：

一个聊天固定一个模型。

也可以：

复制聊天并切换模型。


---

七、聊天功能

必须支持：

✓ 流式输出（Streaming）

不能等待全部回答完成。

要求逐字刷新。

必须使用：

/api/chat

Streaming模式。

支持：

停止生成

重新生成

复制回答

删除消息

编辑上一条用户消息

Markdown渲染

代码高亮

数学公式（LaTeX）

表格

引用块


聊天体验尽量接近ChatGPT。


---

八、上下文管理

Ollama不会自动保存聊天状态，客户端需要自行维护消息历史，并在每次 /api/chat 请求中携带完整 messages 数组，以实现连续对话。

要求：

每个聊天：

messages = [

system,

user,

assistant,

user,

assistant

]

自动管理。

支持：

System Prompt。


---

九、设置页面

支持：

服务器地址：

例如：

http://192.168.1.20:11434

或者：

http://example.com:11434

可修改。

支持：

连接测试。

支持：

默认模型。

支持：

超时时间。

支持：

是否启用Streaming。

支持：

主题切换。

支持：

字体大小。

所有配置保存在：

config.json


---

十、数据库设计

设计SQLite数据库。

至少包括：

conversation

id

title

model

create_time

update_time

message

id

conversation_id

role

content

create_time

config

key

value

要求给出完整ER设计。


---

十一、网络层

封装：

OllamaClient

例如：

list_models()

chat()

generate()

stop()

health()

version()

统一异常处理：

网络错误

超时

API错误

JSON错误

服务器不可达



---

十二、性能要求

要求：

不要阻塞UI。

网络全部异步。

Streaming使用：

Worker Thread 或 asyncio + Qt事件循环。

聊天记录分页加载。

图片资源缓存。

Markdown缓存。


---

十三、Android适配

需要说明：

如何打包APK。

如何处理：

权限

网络

DPI

返回键

横竖屏



---

十四、项目要求

要求代码：

高内聚

低耦合

类型注解完整

遵循PEP8

所有类都有Docstring

关键模块有单元测试

日志统一管理

配置统一管理

易于后续扩展（例如支持OpenAI兼容接口、MCP、插件等）



---

十五、输出要求

不要一次生成所有代码。

请按照真正的软件开发流程输出：

1. 技术方案选型（含 Flutter、PySide6 等方案对比并给出最终推荐）


2. 总体架构设计


3. 项目目录结构


4. 数据库设计


5. UI设计（页面流程、组件关系）


6. 类图（Mermaid）


7. 时序图（Mermaid）


8. 模块依赖关系


9. 核心API封装设计（基于Ollama官方API）


10. 状态管理设计


11. 多会话实现方案


12. 多模型实现方案


13. Streaming实现方案


14. Android打包方案


15. Windows/Linux发布方案


16. 开发计划（按阶段拆分）


17. 每个阶段完成后，再开始生成对应代码，不要跨阶段生成。



最终目标是产出一个可维护、可扩展、接近 ChatGPT 使用体验的跨平台客户端。