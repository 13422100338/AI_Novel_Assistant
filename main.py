# main.py
import os
import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox, QDialog
from PyQt6.QtCore import QSettings
from styles import MODERN_QSS
from ui_components import WelcomeDialog, SettingsDialog
from main_window import MainWindow
from model_profiles import has_any_api_key


def show_startup_error(exc):
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "startup_error.log")
    details = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(details)
    try:
        QMessageBox.critical(None, "启动失败", f"程序启动时发生错误：\n{exc}\n\n详细日志：\n{log_path}")
    except Exception:
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    try:
        app.setStyleSheet(MODERN_QSS)

        settings = QSettings("AIWriter", "Settings")
        if not has_any_api_key(settings):
            QMessageBox.information(None, "初始化", "检测到您首次使用或未配置 API Key，请先进行全局设置。")
            SettingsDialog().exec()

        while True:
            welcome = WelcomeDialog()
            welcome.show()
            welcome.raise_()
            welcome.activateWindow()
            if welcome.exec() == QDialog.DialogCode.Accepted and welcome.selected_path:
                project_path = welcome.selected_path
                window = MainWindow(project_path)
                window.show()
                window.raise_()
                window.activateWindow()
                app.exec()

                if getattr(window, 'switch_project', False):
                    continue
                else:
                    break
            else:
                break
    except Exception as exc:
        show_startup_error(exc)
        sys.exit(1)

    sys.exit(0)
