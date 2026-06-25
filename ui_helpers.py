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
            "QToolButton { text-align: left; font-weight: 700; color: #334155; "
            "background-color: #EEF2FF; border: 1px solid #DDE5FF; border-radius: 8px; padding: 7px; }"
        )
        self.toggle.toggled.connect(self._set_expanded)

        layout.addWidget(self.toggle)
        layout.addWidget(content_widget)
        self._set_expanded(expanded)

    def _set_expanded(self, expanded: bool):
        self.content_widget.setVisible(expanded)
        self.toggle.setText(("▼ " if expanded else "▶ ") + self.title)


def render_chat_messages_html(messages: list[dict]) -> str:
    """Render a ChatGPT-like transcript."""
    if not messages:
        return (
            "<div style='max-width:720px; margin:64px auto; color:#64748B; text-align:center; line-height:1.8;'>"
            "<div style='font-size:22px; color:#111827; font-weight:700; margin-bottom:8px;'>剧情搭档</div>"
            "<div>像和 ChatGPT 聊天一样讨论剧情、人物心理、伏笔回收和下一章节奏。</div>"
            "<div>它会读取当前正文编辑区、章节设定和长篇记忆。</div>"
            "</div>"
        )

    rows = []
    for msg in messages:
        role = msg.get("role", "assistant")
        content = html.escape(msg.get("content", "")).replace("\n", "<br>")
        if role == "user":
            rows.append(
                "<div style='max-width:760px; margin:18px auto; text-align:right;'>"
                "<div style='display:inline-block; max-width:78%; text-align:left; "
                "background:#F3F4F6; color:#111827; border-radius:20px; "
                "padding:12px 16px; line-height:1.72; font-size:14px;'>"
                f"{content}</div></div>"
            )
        else:
            if not content:
                content = "<span style='color:#94A3B8;'>正在思考……</span>"
            rows.append(
                "<div style='max-width:760px; margin:22px auto; text-align:left;'>"
                "<div style='display:flex; gap:10px; align-items:flex-start;'>"
                "<div style='width:26px; height:26px; border-radius:13px; background:#111827; "
                "color:white; text-align:center; line-height:26px; font-size:13px; font-weight:700;'>AI</div>"
                "<div style='flex:1; color:#111827; line-height:1.78; font-size:14px; padding-top:2px;'>"
                f"{content}</div></div></div>"
            )

    return (
        "<html><body style='font-family:Microsoft YaHei, Segoe UI, sans-serif; font-size:14px; "
        "background:#FFFFFF; padding:12px;'>"
        + "".join(rows) +
        "</body></html>"
    )
