import html

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QToolButton, QVBoxLayout, QWidget


class CollapsibleSection(QWidget):
    """Reusable collapsible section used by dense side panels."""

    def __init__(self, title: str, content_widget: QWidget, expanded: bool = True, parent=None):
        super().__init__(parent)
        self.title = title
        self.content_widget = content_widget

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(4)

        self.toggle = QToolButton()
        self.toggle.setCheckable(True)
        self.toggle.setChecked(expanded)
        self.toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle.setStyleSheet(
            "QToolButton { text-align: left; font-weight: 700; color: #202124; "
            "background-color: #F4F4F5; border: 1px solid #E5E7EB; border-radius: 12px; padding: 8px 10px; }"
            "QToolButton:hover { background-color: #ECEDEF; border-color: #D1D5DB; }"
        )
        self.toggle.toggled.connect(self._set_expanded)

        layout.addWidget(self.toggle)
        layout.addWidget(content_widget)
        self._set_expanded(expanded)

    def _set_expanded(self, expanded: bool):
        self.content_widget.setVisible(expanded)
        self.toggle.setText(("▼ " if expanded else "▶ ") + self.title)


def render_chat_messages_html(messages: list[dict]) -> str:
    """Render a Codex-like chat transcript."""
    style = """
    <style>
      body {
        font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
        font-size: 14px;
        background: #FFFFFF;
        color: #202124;
        margin: 0;
        padding: 18px 14px 24px;
      }
      .chat-shell { max-width: 820px; margin: 0 auto; }
      .chat-empty { color:#6B7280; text-align:center; line-height:1.8; padding:72px 18px; }
      .chat-empty-title { font-size:22px; color:#202124; font-weight:700; margin-bottom:8px; }
      .chat-row { display:flex; margin:22px 0; }
      .chat-row.user { justify-content:flex-end; }
      .chat-row.assistant { justify-content:flex-start; }
      .chat-bubble {
        max-width: 78%;
        border-radius: 20px;
        padding: 12px 15px;
        line-height: 1.78;
        white-space: normal;
        overflow-wrap: anywhere;
      }
      .user-message-bubble {
        background:#F1F3F4;
        color:#202124;
        border:1px solid #ECEFF1;
        font-size:15px;
      }
      .assistant-message-card {
        max-width: 100%;
        background:#FFFFFF;
        color:#202124;
        border:1px solid transparent;
        padding:0 0 0 0;
        font-size:15px;
      }
      .assistant-wrap { display:flex; gap:14px; align-items:flex-start; max-width:100%; }
      .assistant-avatar {
        width:30px; height:30px; border-radius:15px;
        background:#202124; color:#FFFFFF;
        text-align:center; line-height:30px;
        font-size:12px; font-weight:700; flex:0 0 auto;
      }
      .assistant-content { padding-top:0; line-height:1.85; }
      .assistant-title {
        color:#6B7280; font-size:12px; font-weight:700;
        margin-bottom:4px; letter-spacing:.02em;
      }
      .chat-heading { color:#111827; font-weight:800; margin:18px 0 8px; line-height:1.35; }
      .chat-heading.h1 { font-size:24px; }
      .chat-heading.h2 { font-size:20px; }
      .chat-heading.h3 { font-size:17px; }
      .chat-paragraph { margin:8px 0; }
      .chat-list { margin:8px 0 8px 20px; padding:0; }
      .chat-list li { margin:5px 0; }
      .code-card {
        background:#F7F7F8;
        border:1px solid #ECEFF1;
        border-radius:16px;
        margin:12px 0;
        overflow:hidden;
      }
      .code-card-header {
        color:#374151;
        font-size:12px;
        font-weight:700;
        padding:9px 13px;
        border-bottom:1px solid #ECEFF1;
      }
      .code-card pre {
        margin:0;
        padding:13px;
        color:#4F46E5;
        font-family:Consolas, "Cascadia Mono", monospace;
        white-space:pre-wrap;
      }
      .message-action-bar {
        color:#6B7280;
        font-size:12px;
        margin-top:10px;
        letter-spacing:8px;
        user-select:none;
      }
      .typing { color:#9CA3AF; }
    </style>
    """
    if not messages:
        return (
            f"<html><head>{style}</head><body><div class='chat-shell chat-empty'>"
            "<div class='chat-empty-title'>剧情搭档</div>"
            "<div>像和 Codex 聊天一样讨论剧情、人物心理、伏笔回收和下一章节奏。</div>"
            "<div>它会读取当前正文编辑区、章节设定和长篇记忆。</div>"
            "</div></body></html>"
        )

    rows = []
    for msg in messages:
        role = msg.get("role", "assistant")
        raw_content = msg.get("content", "")
        content = _render_message_content(raw_content, compact=(role == "user"))
        if role == "user":
            rows.append(
                "<div class='chat-row user'>"
                f"<div class='chat-bubble user-message-bubble'>{content}</div>"
                "</div>"
            )
        else:
            if not raw_content:
                content = "<span class='typing'>正在思考……</span>"
            title = html.escape(msg.get("title", "AI"))
            rows.append(
                "<div class='chat-row assistant'>"
                "<div class='assistant-wrap'>"
                "<div class='assistant-avatar'>AI</div>"
                "<div class='chat-bubble assistant-message-card'>"
                f"<div class='assistant-title'>{title}</div>"
                f"<div class='assistant-content'>{content}</div>"
                "<div class='message-action-bar'>复制 赞 踩 重试</div>"
                "</div></div></div>"
            )

    return (
        f"<html><head>{style}</head><body><div class='chat-shell'>"
        + "".join(rows) +
        "</div>"
        "</body></html>"
    )


def _render_message_content(text: str, compact: bool = False) -> str:
    """Small Markdown-ish renderer that works inside QTextEdit HTML."""
    if not text:
        return ""
    if compact:
        return html.escape(text).replace("\n", "<br>")

    lines = text.splitlines()
    chunks = []
    paragraph = []
    list_items = []
    in_code = False
    code_lang = ""
    code_lines = []

    def flush_paragraph():
        nonlocal paragraph
        if paragraph:
            escaped = html.escape(" ".join(p.strip() for p in paragraph)).replace("**", "")
            chunks.append(f"<div class='chat-paragraph'>{escaped}</div>")
            paragraph = []

    def flush_list():
        nonlocal list_items
        if list_items:
            items = "".join(f"<li>{html.escape(item)}</li>" for item in list_items)
            chunks.append(f"<ul class='chat-list'>{items}</ul>")
            list_items = []

    def flush_code():
        nonlocal code_lines, code_lang
        if code_lines or code_lang:
            code = html.escape("\n".join(code_lines))
            lang = html.escape(code_lang or "代码")
            chunks.append(
                "<div class='code-card'>"
                f"<div class='code-card-header'>{lang}</div>"
                f"<pre>{code}</pre>"
                "</div>"
            )
            code_lines = []
            code_lang = ""

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                flush_paragraph()
                flush_list()
                in_code = True
                code_lang = stripped[3:].strip() or "代码"
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not stripped:
            flush_paragraph()
            flush_list()
            continue
        if stripped.startswith("### "):
            flush_paragraph()
            flush_list()
            chunks.append(f"<div class='chat-heading h3'>{html.escape(stripped[4:])}</div>")
        elif stripped.startswith("## "):
            flush_paragraph()
            flush_list()
            chunks.append(f"<div class='chat-heading h2'>{html.escape(stripped[3:])}</div>")
        elif stripped.startswith("# "):
            flush_paragraph()
            flush_list()
            chunks.append(f"<div class='chat-heading h1'>{html.escape(stripped[2:])}</div>")
        elif stripped.startswith(("- ", "* ")):
            flush_paragraph()
            list_items.append(stripped[2:].strip())
        else:
            paragraph.append(stripped)

    flush_paragraph()
    flush_list()
    if in_code:
        flush_code()
    return "".join(chunks)


def build_plot_chat_prompt(
    *,
    global_synopsis: str,
    memory_context: str,
    editor_content: str,
    question: str,
    chat_history: str = "",
) -> tuple[str, str]:
    """Build prompts for plot discussion, including recent chat history."""
    system_prompt = (
        "你是长篇小说剧情策划搭档，负责和作者讨论剧情走向、人物动机、伏笔回收、节奏与冲突。"
        "你可以提出清晰、可执行的创作建议；除非作者明确要求，不要直接替作者改写整章正文。"
    )
    user_prompt = f"""
【小说全局设定】
{global_synopsis or "暂无"}

【当前章节与长篇记忆】
{memory_context or "暂无"}

【当前正文编辑区内容】
{editor_content or "当前正文编辑区为空。"}

【最近剧情商讨记录】
{chat_history or "暂无"}

【作者当前问题】
{question}
""".strip()
    return system_prompt, user_prompt


def build_chapter_requirement_prompt(
    *,
    global_synopsis: str,
    volume_name: str,
    chapter_name: str,
    chapter_synopsis: str,
    memory_context: str,
    editor_content: str,
    chat_context: str,
) -> tuple[str, str]:
    """Build prompts for converting plot discussion into formal chapter requirements."""
    system_prompt = (
        "你是长篇小说章节要求生成器。你的任务是把作者与剧情商讨模型形成的方向，"
        "整理成可直接交给正文创作模型使用的正式当前章写作要求。"
    )
    user_prompt = f"""
请只输出正式的当前章写作要求，不要寒暄，不要解释你如何思考，不要输出对话式建议。

输出建议结构：
1. 本章核心目标
2. 必须出现的关键情节点
3. 出场人物与当前心理/动机
4. 冲突推进与情绪节奏
5. 伏笔、正典事实与禁忌
6. 文风与镜头要求
7. 本章结尾钩子

【小说全局设定】
{global_synopsis or "暂无"}

【当前卷】
{volume_name or "未选择卷"}

【当前章】
{chapter_name or "未选择章节"}

【原当前章要求】
{chapter_synopsis or "暂无"}

【长篇记忆与人物状态】
{memory_context or "暂无"}

【当前正文编辑区内容】
{editor_content or "当前正文编辑区为空。"}

【最近剧情商讨上下文】
{chat_context or "暂无"}
""".strip()
    return system_prompt, user_prompt
