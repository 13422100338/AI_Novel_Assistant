# ui_components.py
import json
import os
from openai import OpenAI
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QTextEdit, QPushButton, QDialog, QMessageBox, QFileDialog,
                             QListWidget, QFormLayout, QDialogButtonBox, QSpinBox,
                             QDoubleSpinBox, QCheckBox, QInputDialog, QGroupBox,
                             QTabWidget, QComboBox)
from PyQt6.QtCore import Qt, QSettings

class WelcomeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("欢迎来到 AI 网文创作台")
        self.setFixedSize(550, 400)
        self.selected_path = None
        self.settings = QSettings("AIWriter", "Settings")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title_lbl = QLabel("请选择或创建一部小说")
        title_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #202124;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)

        layout.addWidget(QLabel("最近打开的项目："))
        self.recent_list = QListWidget()
        recent_paths = self.settings.value("recent_novels", [])
        for p in recent_paths:
            if os.path.exists(p):
                self.recent_list.addItem(p)
        layout.addWidget(self.recent_list)

        btn_layout = QHBoxLayout()
        btn_open_recent = QPushButton("打开选中项目")
        btn_open_recent.setStyleSheet("background-color: #202124; color: white; border: none;")
        btn_open_recent.clicked.connect(self.open_selected_recent)

        btn_open_dir = QPushButton("打开本地文件夹")
        btn_open_dir.clicked.connect(self.open_directory)

        btn_create = QPushButton("创建新小说")
        btn_create.setStyleSheet("background-color: #202124; color: white; border: none; font-weight: bold;")
        btn_create.clicked.connect(self.create_new_project)

        btn_layout.addWidget(btn_open_recent)
        btn_layout.addWidget(btn_open_dir)
        btn_layout.addWidget(btn_create)
        layout.addLayout(btn_layout)

    def open_selected_recent(self):
        item = self.recent_list.currentItem()
        if item:
            self.selected_path = item.text()
            self.accept()
        else:
            QMessageBox.warning(self, "提示", "请先在列表中选中一个项目。")

    def open_directory(self):
        path = QFileDialog.getExistingDirectory(self, "选择小说根目录")
        if path:
            self.selected_path = path
            self.update_recent(path)
            self.accept()

    def create_new_project(self):
        path = QFileDialog.getExistingDirectory(self, "选择存放新小说的位置")
        if path:
            text, ok = QInputDialog.getText(self, "小说名称", "请输入新小说名称:")
            if ok and text:
                full_path = os.path.join(path, text)
                os.makedirs(full_path, exist_ok=True)
                self.selected_path = full_path
                self.update_recent(full_path)
                self.accept()

    def update_recent(self, path):
        recent_paths = self.settings.value("recent_novels", [])
        if path in recent_paths:
            recent_paths.remove(path)
        recent_paths.insert(0, path)
        self.settings.setValue("recent_novels", recent_paths[:])

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("全局设置 & 模型参数")
        self.setFixedSize(450, 320)
        self.settings = QSettings("AIWriter", "Settings")

        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.api_key_input = QLineEdit(self.settings.value("api_key", ""))
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.base_url_input = QLineEdit(self.settings.value("base_url", "https://api.deepseek.com"))
        self.model_input = QLineEdit(self.settings.value("model", "deepseek-reasoner"))

        self.temp_input = QDoubleSpinBox()
        self.temp_input.setRange(0.0, 1.99)
        self.temp_input.setSingleStep(0.1)
        self.temp_input.setValue(float(self.settings.value("temperature", 0.7)))

        self.tokens_input = QSpinBox()
        self.tokens_input.setRange(500, 128000)
        self.tokens_input.setSingleStep(500)
        self.tokens_input.setValue(int(self.settings.value("max_tokens", 4000)))

        self.confirm_delete_cb = QCheckBox("删除卷/章时进行二次确认")
        self.confirm_delete_cb.setChecked(self.settings.value("confirm_delete", True, type=bool))
        layout.addRow("删除确认:", self.confirm_delete_cb)
        layout.addRow("API Key:", self.api_key_input)
        layout.addRow("Base URL:", self.base_url_input)
        layout.addRow("模型名称:", self.model_input)
        layout.addRow("Temperature:", self.temp_input)
        layout.addRow("Max Tokens:", self.tokens_input)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def save_and_accept(self):
        self.settings.setValue("api_key", self.api_key_input.text().strip())
        self.settings.setValue("base_url", self.base_url_input.text().strip())
        self.settings.setValue("model", self.model_input.text().strip())
        self.settings.setValue("temperature", self.temp_input.value())
        self.settings.setValue("max_tokens", self.tokens_input.value())
        self.settings.setValue("confirm_delete", self.confirm_delete_cb.isChecked())
        self.accept()

class SettingsDialog(QDialog):
    """升级版设置面板：支持剧情商讨 / 正文创作两套模型配置。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("全局设置 & 双模型参数")
        self.setFixedSize(760, 600)
        self.settings = QSettings("AIWriter", "Settings")
        self.profile_widgets = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.confirm_delete_cb = QCheckBox("删除卷/章时进行二次确认")
        self.confirm_delete_cb.setChecked(self.settings.value("confirm_delete", True, type=bool))
        layout.addWidget(self.confirm_delete_cb)

        self.auto_import_volume_cb = QCheckBox("智能导入原稿时自动分卷（由正文创作模型担任稿件整理 Agent）")
        self.auto_import_volume_cb.setChecked(self.settings.value("import/auto_volume", True, type=bool))
        layout.addWidget(self.auto_import_volume_cb)

        tabs = QTabWidget()
        tabs.addTab(self._build_profile_tab("chat", "剧情商讨模型", 0.7, 4000), "剧情商讨模型")
        tabs.addTab(self._build_profile_tab("draft", "正文创作模型", 1.2, 6000), "正文创作模型")
        layout.addWidget(tabs)

        hint = QLabel("两个窗口可以分别使用不同 OpenAI-compatible API。Base URL 可填写第三方中转站地址；点击“获取模型列表”可从兼容 /v1/models 的服务拉取可用模型。")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #606266;")
        layout.addWidget(hint)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _legacy(self, key, default):
        value = self.settings.value(key, default)
        return value if value not in (None, "") else default

    def _build_profile_tab(self, role, display_name, default_temp, default_tokens):
        widget = QWidget()
        form = QFormLayout(widget)
        form.setContentsMargins(10, 15, 10, 10)
        form.setSpacing(12)

        prefix = f"profiles/{role}/"
        name_input = QLineEdit(self.settings.value(prefix + "name", display_name))
        api_key_input = QLineEdit(self.settings.value(prefix + "api_key", self.settings.value("api_key", "")))
        api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        base_url_input = QComboBox()
        base_url_input.setEditable(True)
        base_url_presets = [
            self.settings.value(prefix + "base_url", self._legacy("base_url", "https://api.deepseek.com")),
            "https://api.deepseek.com",
            "https://api.openai.com/v1",
            "https://openrouter.ai/api/v1",
            "https://api.siliconflow.cn/v1",
            "https://api.moonshot.cn/v1",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        ]
        for url in dict.fromkeys([str(u).strip() for u in base_url_presets if str(u).strip()]):
            base_url_input.addItem(url)

        model_input = QComboBox()
        model_input.setEditable(True)
        current_model = self.settings.value(prefix + "model", self._legacy("model", "deepseek-reasoner"))
        for model in dict.fromkeys([str(current_model), "deepseek-reasoner", "deepseek-chat", "gpt-4o", "gpt-4o-mini"]):
            if model:
                model_input.addItem(model)
        model_input.setCurrentText(str(current_model))

        temp_input = QDoubleSpinBox()
        temp_input.setRange(0.0, 1.99)
        temp_input.setSingleStep(0.1)
        temp_input.setValue(float(self.settings.value(prefix + "temperature", self._legacy("temperature", default_temp))))

        tokens_input = QSpinBox()
        tokens_input.setRange(500, 128000)
        tokens_input.setSingleStep(500)
        tokens_input.setValue(int(self.settings.value(prefix + "max_tokens", self._legacy("max_tokens", default_tokens))))

        form.addRow("配置名称:", name_input)
        form.addRow("API Key:", api_key_input)
        form.addRow("Base URL / 中转站:", base_url_input)
        model_row = QHBoxLayout()
        model_row.addWidget(model_input, 1)
        btn_fetch_models = QPushButton("获取模型列表")
        btn_fetch_models.clicked.connect(lambda: self.fetch_models_for_profile(role))
        model_row.addWidget(btn_fetch_models)
        form.addRow("模型名称:", model_row)
        form.addRow("Temperature:", temp_input)
        form.addRow("Max Tokens:", tokens_input)

        self.profile_widgets[role] = {
            "name": name_input,
            "api_key": api_key_input,
            "base_url": base_url_input,
            "model": model_input,
            "fetch_button": btn_fetch_models,
            "temperature": temp_input,
            "max_tokens": tokens_input,
        }
        return widget

    def _combo_text(self, widget):
        return widget.currentText().strip() if hasattr(widget, "currentText") else widget.text().strip()

    def fetch_models_for_profile(self, role):
        widgets = self.profile_widgets[role]
        api_key = widgets["api_key"].text().strip()
        base_url = self._combo_text(widgets["base_url"])
        if not api_key or not base_url:
            QMessageBox.warning(self, "缺少配置", "请先填写 API Key 和 Base URL。")
            return

        btn = widgets.get("fetch_button")
        if btn:
            btn.setEnabled(False)
            btn.setText("获取中...")
        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            models = client.models.list()
            model_ids = sorted({m.id for m in models.data if getattr(m, "id", None)})
            if not model_ids:
                QMessageBox.information(self, "模型列表", "接口返回成功，但没有发现模型 ID。")
                return
            combo = widgets["model"]
            current = combo.currentText().strip()
            combo.clear()
            combo.addItems(model_ids)
            if current:
                combo.setCurrentText(current if current in model_ids else model_ids[0])
            QMessageBox.information(self, "模型列表", f"已获取 {len(model_ids)} 个模型。")
        except Exception as e:
            QMessageBox.warning(self, "获取失败", f"无法获取模型列表：\n{e}\n\n如果你的中转站不支持 /v1/models，可以继续手动填写模型名称。")
        finally:
            if btn:
                btn.setEnabled(True)
                btn.setText("获取模型列表")

    def save_and_accept(self):
        for role, widgets in self.profile_widgets.items():
            prefix = f"profiles/{role}/"
            self.settings.setValue(prefix + "name", widgets["name"].text().strip())
            self.settings.setValue(prefix + "api_key", widgets["api_key"].text().strip())
            self.settings.setValue(prefix + "base_url", self._combo_text(widgets["base_url"]))
            self.settings.setValue(prefix + "model", self._combo_text(widgets["model"]))
            self.settings.setValue(prefix + "temperature", widgets["temperature"].value())
            self.settings.setValue(prefix + "max_tokens", widgets["max_tokens"].value())

        draft = self.profile_widgets["draft"]
        self.settings.setValue("api_key", draft["api_key"].text().strip())
        self.settings.setValue("base_url", self._combo_text(draft["base_url"]))
        self.settings.setValue("model", self._combo_text(draft["model"]))
        self.settings.setValue("temperature", draft["temperature"].value())
        self.settings.setValue("max_tokens", draft["max_tokens"].value())
        self.settings.setValue("confirm_delete", self.confirm_delete_cb.isChecked())
        self.settings.setValue("import/auto_volume", self.auto_import_volume_cb.isChecked())
        self.accept()


class CharacterWidget(QGroupBox):
    def __init__(self, parent_remove_func, init_data=None):
        super().__init__("人物卡片")
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 20, 15, 15)

        row1 = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("姓名 (如: 萧炎)")
        self.gender_input = QLineEdit()
        self.gender_input.setPlaceholderText("性别")
        row1.addWidget(self.name_input)
        row1.addWidget(self.gender_input)

        self.personality_input = QLineEdit()
        self.personality_input.setPlaceholderText("性格特征 (如：腹黑、热血、杀伐果断)")

        self.experience_input = QTextEdit()
        self.experience_input.setPlaceholderText("人物背景与经历简介...")
        self.experience_input.setFixedHeight(60)

        btn_remove = QPushButton("删除此人物")
        btn_remove.setStyleSheet("color: #202124; border-color: #DADCE0; background-color: #F1F3F4;")
        btn_remove.clicked.connect(lambda: parent_remove_func(self))

        layout.addLayout(row1)
        layout.addWidget(self.personality_input)
        layout.addWidget(self.experience_input)
        layout.addWidget(btn_remove)
        self.setLayout(layout)

        if init_data:
            self.name_input.setText(init_data.get("name", ""))
            self.gender_input.setText(init_data.get("gender", ""))
            self.personality_input.setText(init_data.get("personality", ""))
            self.experience_input.setText(init_data.get("experience", ""))

    def get_data(self):
        return {
            "name": self.name_input.text().strip(),
            "gender": self.gender_input.text().strip(),
            "personality": self.personality_input.text().strip(),
            "experience": self.experience_input.toPlainText().strip()
        }


class MemoryLibraryDialog(QDialog):
    """Editable review window for the long-novel memory database."""

    def __init__(self, memory_store, parent=None):
        super().__init__(parent)
        self.memory = memory_store
        self.setWindowTitle("长篇记忆库")
        self.resize(980, 720)
        self.setStyleSheet("""
            QDialog { background:#FFFFFF; color:#202124; }
            QLabel { color:#202124; }
            QTextEdit, QListWidget, QLineEdit, QComboBox {
                border:1px solid #E5E7EB; border-radius:12px; background:#FAFAFA; padding:8px;
            }
            QPushButton {
                border:1px solid #DADCE0; border-radius:12px; background:#FFFFFF; padding:8px 12px;
            }
            QPushButton:hover { background:#F1F3F4; }
        """)

        layout = QVBoxLayout(self)
        header = QLabel("长篇记忆库用于给 AI 提供动态压缩过的前文、人物状态、伏笔、正典事实和章节要点。")
        header.setWordWrap(True)
        header.setStyleSheet("font-size:15px; font-weight:600; margin-bottom:4px;")
        layout.addWidget(header)

        detail = QLabel(
            "提示：这里修改的是 AI 以后会参考的“记忆层”，不会直接改正文。"
            "如果 AI 误解了人物心理、遗漏伏笔或压缩摘要不准，可以在这里手动修正。"
        )
        detail.setWordWrap(True)
        detail.setStyleSheet("color:#6B7280; line-height:1.6;")
        layout.addWidget(detail)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_context_tab(), "上下文预览")
        self.tabs.addTab(self._build_layered_tab(), "分层摘要")
        self.tabs.addTab(self._build_chapter_tab(), "章节记忆")
        self.tabs.addTab(self._build_canon_tab(), "伏笔正典")
        layout.addWidget(self.tabs, 1)

        close_row = QHBoxLayout()
        close_row.addStretch()
        btn_close = QPushButton("关闭")
        btn_close.clicked.connect(self.accept)
        close_row.addWidget(btn_close)
        layout.addLayout(close_row)

        self.refresh_all()

    def _build_context_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.addWidget(QLabel("这是正文生成前会拼入提示词的一部分动态上下文预览，便于检查 AI 正在参考什么。"))
        self.context_preview = QTextEdit()
        self.context_preview.setReadOnly(True)
        layout.addWidget(self.context_preview, 1)
        btn_refresh = QPushButton("刷新预览")
        btn_refresh.clicked.connect(self.refresh_context_preview)
        layout.addWidget(btn_refresh)
        return widget

    def _build_layered_tab(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        self.layered_list = QListWidget()
        self.layered_list.currentRowChanged.connect(self.load_selected_layered_summary)
        layout.addWidget(self.layered_list, 1)
        editor_layout = QVBoxLayout()
        self.layered_title = QLabel("选择左侧摘要")
        self.layered_editor = QTextEdit()
        btn_save = QPushButton("保存分层摘要")
        btn_save.clicked.connect(self.save_selected_layered_summary)
        editor_layout.addWidget(self.layered_title)
        editor_layout.addWidget(self.layered_editor, 1)
        editor_layout.addWidget(btn_save)
        layout.addLayout(editor_layout, 3)
        return widget

    def _build_chapter_tab(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        self.chapter_memory_list = QListWidget()
        self.chapter_memory_list.currentRowChanged.connect(self.load_selected_chapter_memory)
        layout.addWidget(self.chapter_memory_list, 1)

        editor_layout = QVBoxLayout()
        self.chapter_memory_title = QLabel("选择左侧章节记忆")
        self.chapter_summary_editor = QTextEdit()
        self.chapter_summary_editor.setPlaceholderText("本章压缩摘要")
        self.chapter_plot_points_editor = QTextEdit()
        self.chapter_plot_points_editor.setPlaceholderText("关键情节点 JSON 数组，例如：[\"节点1\", \"节点2\"]")
        self.chapter_foreshadows_editor = QTextEdit()
        self.chapter_foreshadows_editor.setPlaceholderText("伏笔 JSON 数组，例如：[{\"title\":\"钥匙\", \"detail\":\"来源不明\", \"status\":\"active\"}]")
        btn_save = QPushButton("保存章节记忆")
        btn_save.clicked.connect(self.save_selected_chapter_memory)
        editor_layout.addWidget(self.chapter_memory_title)
        editor_layout.addWidget(QLabel("压缩摘要"))
        editor_layout.addWidget(self.chapter_summary_editor, 2)
        editor_layout.addWidget(QLabel("关键情节点（JSON）"))
        editor_layout.addWidget(self.chapter_plot_points_editor, 1)
        editor_layout.addWidget(QLabel("伏笔 / 承诺（JSON）"))
        editor_layout.addWidget(self.chapter_foreshadows_editor, 1)
        editor_layout.addWidget(btn_save)
        layout.addLayout(editor_layout, 3)
        return widget

    def _build_canon_tab(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        self.canon_list = QListWidget()
        self.canon_list.currentRowChanged.connect(self.load_selected_canon_entry)
        layout.addWidget(self.canon_list, 1)

        editor_layout = QVBoxLayout()
        self.canon_title_label = QLabel("选择左侧伏笔/正典")
        self.canon_kind = QLineEdit()
        self.canon_kind.setPlaceholderText("类型：foreshadow / fact")
        self.canon_title = QLineEdit()
        self.canon_title.setPlaceholderText("标题")
        self.canon_status = QComboBox()
        self.canon_status.addItems(["active", "closed", "changed"])
        self.canon_source = QLineEdit()
        self.canon_source.setPlaceholderText("来源：卷/章")
        self.canon_detail = QTextEdit()
        self.canon_detail.setPlaceholderText("细节说明")
        btn_row = QHBoxLayout()
        btn_save = QPushButton("保存条目")
        btn_delete = QPushButton("删除条目")
        btn_save.clicked.connect(self.save_selected_canon_entry)
        btn_delete.clicked.connect(self.delete_selected_canon_entry)
        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_delete)
        editor_layout.addWidget(self.canon_title_label)
        editor_layout.addWidget(self.canon_kind)
        editor_layout.addWidget(self.canon_title)
        editor_layout.addWidget(self.canon_status)
        editor_layout.addWidget(self.canon_source)
        editor_layout.addWidget(self.canon_detail, 1)
        editor_layout.addLayout(btn_row)
        layout.addLayout(editor_layout, 3)
        return widget

    def refresh_all(self):
        self.refresh_context_preview()
        self.refresh_layered_list()
        self.refresh_chapter_memory_list()
        self.refresh_canon_list()

    def refresh_context_preview(self):
        self.context_preview.setPlainText(self.memory.build_context("", ""))

    def refresh_layered_list(self):
        self.layered_list.clear()
        for row in self.memory.list_layered_summaries():
            self.layered_list.addItem(f"{row['level']} / {row['scope_key']}")
            self.layered_list.item(self.layered_list.count() - 1).setData(Qt.ItemDataRole.UserRole, row)
        if self.layered_list.count():
            self.layered_list.setCurrentRow(0)

    def load_selected_layered_summary(self):
        item = self.layered_list.currentItem()
        row = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not row:
            return
        self.layered_title.setText(f"{row['level']} / {row['scope_key']}")
        self.layered_editor.setPlainText(row.get("summary", ""))

    def save_selected_layered_summary(self):
        item = self.layered_list.currentItem()
        row = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not row:
            return
        self.memory.update_layered_summary(row["id"], self.layered_editor.toPlainText())
        self.refresh_layered_list()
        self.refresh_context_preview()

    def refresh_chapter_memory_list(self):
        self.chapter_memory_list.clear()
        for row in self.memory.list_chapter_memories():
            self.chapter_memory_list.addItem(f"{row['volume_name']} / {row['chapter_name']}")
            self.chapter_memory_list.item(self.chapter_memory_list.count() - 1).setData(Qt.ItemDataRole.UserRole, row)
        if self.chapter_memory_list.count():
            self.chapter_memory_list.setCurrentRow(0)

    def load_selected_chapter_memory(self):
        item = self.chapter_memory_list.currentItem()
        row = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not row:
            return
        self.chapter_memory_title.setText(f"{row['volume_name']} / {row['chapter_name']}")
        self.chapter_summary_editor.setPlainText(row.get("summary", ""))
        self.chapter_plot_points_editor.setPlainText(self._pretty_json(row.get("plot_points", "[]")))
        self.chapter_foreshadows_editor.setPlainText(self._pretty_json(row.get("foreshadows", "[]")))

    def save_selected_chapter_memory(self):
        item = self.chapter_memory_list.currentItem()
        row = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not row:
            return
        try:
            plot_points = json.loads(self.chapter_plot_points_editor.toPlainText() or "[]")
            foreshadows = json.loads(self.chapter_foreshadows_editor.toPlainText() or "[]")
        except Exception as exc:
            QMessageBox.warning(self, "JSON 格式错误", f"关键情节点或伏笔不是合法 JSON：\n{exc}")
            return
        self.memory.update_chapter_memory(
            row["id"],
            {
                "summary": self.chapter_summary_editor.toPlainText(),
                "plot_points": plot_points,
                "foreshadows": foreshadows,
            },
        )
        self.refresh_chapter_memory_list()
        self.refresh_layered_list()
        self.refresh_context_preview()

    def refresh_canon_list(self):
        self.canon_list.clear()
        for row in self.memory.list_canon_entries(include_closed=True):
            self.canon_list.addItem(f"[{row['kind']}/{row['status']}] {row['title']}")
            self.canon_list.item(self.canon_list.count() - 1).setData(Qt.ItemDataRole.UserRole, row)
        if self.canon_list.count():
            self.canon_list.setCurrentRow(0)

    def load_selected_canon_entry(self):
        item = self.canon_list.currentItem()
        row = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not row:
            return
        self.canon_title_label.setText(f"#{row['id']} {row['title']}")
        self.canon_kind.setText(row.get("kind", ""))
        self.canon_title.setText(row.get("title", ""))
        self.canon_status.setCurrentText(row.get("status", "active"))
        self.canon_source.setText(f"{row.get('source_volume', '')}/{row.get('source_chapter', '')}".strip("/"))
        self.canon_detail.setPlainText(row.get("detail", ""))

    def save_selected_canon_entry(self):
        item = self.canon_list.currentItem()
        row = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not row:
            return
        source = self.canon_source.text().split("/", 1)
        self.memory.update_canon_entry(
            row["id"],
            {
                "kind": self.canon_kind.text().strip(),
                "title": self.canon_title.text().strip(),
                "status": self.canon_status.currentText().strip(),
                "detail": self.canon_detail.toPlainText().strip(),
                "source_volume": source[0].strip() if source else "",
                "source_chapter": source[1].strip() if len(source) > 1 else "",
            },
        )
        self.refresh_canon_list()
        self.refresh_context_preview()

    def delete_selected_canon_entry(self):
        item = self.canon_list.currentItem()
        row = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not row:
            return
        reply = QMessageBox.question(
            self,
            "删除记忆条目",
            f"确认删除“{row['title']}”吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.memory.delete_canon_entry(row["id"])
        self.refresh_canon_list()
        self.refresh_context_preview()

    def _pretty_json(self, raw: str) -> str:
        try:
            return json.dumps(json.loads(raw or "[]"), ensure_ascii=False, indent=2)
        except Exception:
            return raw or "[]"
