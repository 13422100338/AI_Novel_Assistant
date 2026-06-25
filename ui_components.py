# ui_components.py
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QTextEdit, QPushButton, QDialog, QMessageBox, QFileDialog,
                             QListWidget, QFormLayout, QDialogButtonBox, QSpinBox,
                             QDoubleSpinBox, QCheckBox, QInputDialog, QGroupBox,
                             QTabWidget)
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

        title_lbl = QLabel("📖 请选择或创建一部小说")
        title_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #303133;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_lbl)

        layout.addWidget(QLabel("📂 最近打开的项目："))
        self.recent_list = QListWidget()
        recent_paths = self.settings.value("recent_novels", [])
        for p in recent_paths:
            if os.path.exists(p):
                self.recent_list.addItem(p)
        layout.addWidget(self.recent_list)

        btn_layout = QHBoxLayout()
        btn_open_recent = QPushButton("打开选中项目")
        btn_open_recent.setStyleSheet("background-color: #E6A23C; color: white; border: none;")
        btn_open_recent.clicked.connect(self.open_selected_recent)

        btn_open_dir = QPushButton("打开本地文件夹")
        btn_open_dir.clicked.connect(self.open_directory)

        btn_create = QPushButton("✨ 创建新小说")
        btn_create.setStyleSheet("background-color: #409EFF; color: white; border: none; font-weight: bold;")
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
        self.setWindowTitle("⚙️ 全局设置 & 模型参数")
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
        layout.addRow("🗑️ 删除确认:", self.confirm_delete_cb)
        layout.addRow("🔑 API Key:", self.api_key_input)
        layout.addRow("🌐 Base URL:", self.base_url_input)
        layout.addRow("🤖 模型名称:", self.model_input)
        layout.addRow("🌡️ Temperature:", self.temp_input)
        layout.addRow("📝 Max Tokens:", self.tokens_input)

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
        self.setWindowTitle("⚙️ 全局设置 & 双模型参数")
        self.setFixedSize(620, 520)
        self.settings = QSettings("AIWriter", "Settings")
        self.profile_widgets = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        self.confirm_delete_cb = QCheckBox("删除卷/章时进行二次确认")
        self.confirm_delete_cb.setChecked(self.settings.value("confirm_delete", True, type=bool))
        layout.addWidget(self.confirm_delete_cb)

        tabs = QTabWidget()
        tabs.addTab(self._build_profile_tab("chat", "剧情商讨模型", 0.7, 4000), "剧情商讨模型")
        tabs.addTab(self._build_profile_tab("draft", "正文创作模型", 1.2, 6000), "正文创作模型")
        layout.addWidget(tabs)

        hint = QLabel("两个窗口可以分别使用不同 OpenAI-compatible API。旧版单模型配置会自动作为默认值带入。")
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
        base_url_input = QLineEdit(self.settings.value(prefix + "base_url", self._legacy("base_url", "https://api.deepseek.com")))
        model_input = QLineEdit(self.settings.value(prefix + "model", self._legacy("model", "deepseek-reasoner")))

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
        form.addRow("Base URL:", base_url_input)
        form.addRow("模型名称:", model_input)
        form.addRow("Temperature:", temp_input)
        form.addRow("Max Tokens:", tokens_input)

        self.profile_widgets[role] = {
            "name": name_input,
            "api_key": api_key_input,
            "base_url": base_url_input,
            "model": model_input,
            "temperature": temp_input,
            "max_tokens": tokens_input,
        }
        return widget

    def save_and_accept(self):
        for role, widgets in self.profile_widgets.items():
            prefix = f"profiles/{role}/"
            self.settings.setValue(prefix + "name", widgets["name"].text().strip())
            self.settings.setValue(prefix + "api_key", widgets["api_key"].text().strip())
            self.settings.setValue(prefix + "base_url", widgets["base_url"].text().strip())
            self.settings.setValue(prefix + "model", widgets["model"].text().strip())
            self.settings.setValue(prefix + "temperature", widgets["temperature"].value())
            self.settings.setValue(prefix + "max_tokens", widgets["max_tokens"].value())

        draft = self.profile_widgets["draft"]
        self.settings.setValue("api_key", draft["api_key"].text().strip())
        self.settings.setValue("base_url", draft["base_url"].text().strip())
        self.settings.setValue("model", draft["model"].text().strip())
        self.settings.setValue("temperature", draft["temperature"].value())
        self.settings.setValue("max_tokens", draft["max_tokens"].value())
        self.settings.setValue("confirm_delete", self.confirm_delete_cb.isChecked())
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

        btn_remove = QPushButton("🗑️ 删除此人物")
        btn_remove.setStyleSheet("color: #F56C6C; border-color: #FBC4C4; background-color: #FEF0F0;")
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
