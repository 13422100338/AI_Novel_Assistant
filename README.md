# AI Novel Assistant

一个面向长篇小说创作的本地桌面 AI 辅助写作工具。项目基于 PyQt6，支持 OpenAI-compatible API，可用于章节管理、剧情商讨、正文生成、手动改稿、长篇记忆压缩、人物状态管理和已有稿件导入。

> 本项目基于 [XZQINSYSU/AI-Web-Novel-Assistant](https://github.com/XZQINSYSU/AI-Web-Novel-Assistant) 改造，保留原 MIT License 与版权声明。

## 主要功能

- 三栏创作界面
  - 左栏：章节管理、当前节点人物心理、设定/细纲/人物介绍
  - 中栏：正文编辑与 AI 生成输出
  - 右栏：类似 ChatGPT 的剧情聊天窗口
- 双模型配置
  - 剧情商讨模型
  - 正文创作模型
- 长篇记忆系统
  - 章节摘要
  - 人物状态库
  - 伏笔/正典账本
  - 章节历史版本
- 百万字上下文策略
  - 最近章节保留全文以维持文风
  - 较早章节使用压缩摘要
  - 动态加入人物状态、伏笔和重要事实
- 导入已有稿件
  - 支持 TXT / DOCX
  - 支持 `#第X章标题` / `（第X章 完）` 原稿格式
  - 可调用稿件整理 Agent 自动判断卷结构并归类章节
  - 自动分析情节点、人物状态和压缩摘要
- 导出
  - DOCX
  - Markdown
  - TXT
  - PDF
- 本地优先
  - 项目文件和正文默认保存在本地
  - 长篇记忆使用 SQLite 存储

## 运行方式

### 从源码运行

推荐 Python 3.10+。

```bash
pip install -r requirements.txt
python main.py
```

Windows 下也可以双击：

```text
Start_AI_Novel_Assistant.cmd
```

### 打包为 exe

先安装 PyInstaller：

```bash
pip install pyinstaller
```

然后运行：

```text
build_exe.bat
```

打包产物会生成在：

```text
dist/AI_Novel_Assistant/AI_Novel_Assistant.exe
```

注意：默认是 PyInstaller one-folder 模式，`AI_Novel_Assistant.exe` 旁边的 `_internal` 文件夹不能删除。

## 模型配置

首次启动时进入设置界面，配置 OpenAI-compatible API：

- API Key
- Base URL
- Model
- Temperature
- Max Tokens

你可以为剧情聊天和正文生成分别配置不同模型。

## 项目结构

```text
main.py                 应用入口
main_window.py          主窗口与主要工作流
context_builder.py      长篇上下文组装策略
import_agent.py         原稿章节识别、智能分卷提示与导入计划校验
novel_memory.py         SQLite 长篇记忆系统
model_profiles.py       双模型配置
ai_worker.py            后台 AI 调用与分析任务
data_manager.py         原项目文件/章节存储
ui_components.py        对话框和基础 UI 组件
ui_helpers.py           可折叠面板、聊天气泡渲染等 UI 辅助
styles.py               全局样式
ARCHITECTURE.md         架构说明
```

## 开发路线建议

下一步适合继续拆分：

- `chat_panel.py`：独立右侧剧情聊天面板
- `import_service.py`：独立 TXT/DOCX 导入和章节拆分
- `memory_panel.py`：独立人物状态、情节点、记忆面板

## 许可证

MIT License。详见 [LICENSE](LICENSE)。

本项目保留原项目作者 `XZQINSYSU` 的 MIT 版权声明。
