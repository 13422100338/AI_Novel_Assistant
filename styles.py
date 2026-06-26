# styles.py

MODERN_QSS = """
* {
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
    font-size: 14px;
}
QMainWindow, QDialog {
    background-color: #F7F7F8;
}
QWidget {
    color: #202124;
}
QPushButton {
    background-color: #FFFFFF;
    border: 1px solid #DADCE0;
    border-radius: 12px;
    padding: 8px 16px;
    color: #202124;
    font-weight: 500;
}
QPushButton:hover {
    color: #202124;
    border-color: #BDC1C6;
    background-color: #F1F3F4;
}
QPushButton:pressed {
    color: #111111;
    border-color: #9AA0A6;
    background-color: #E8EAED;
}
QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {
    border: 1px solid #DADCE0;
    border-radius: 12px;
    padding: 8px;
    background-color: #FFFFFF;
    selection-background-color: #DADCE0;
}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #202124;
}
QTreeWidget {
    border: 1px solid #E5E7EB;
    border-radius: 14px;
    background-color: #FAFAFA;
    padding: 6px;
}
QTreeWidget::item {
    padding: 7px;
    border-radius: 10px;
}
QTreeWidget::item:selected {
    background-color: #E8EAED;
    color: #202124;
}
QGroupBox {
    border: 1px solid #E5E7EB;
    border-radius: 14px;
    margin-top: 20px;
    background-color: #FFFFFF;
    padding-top: 15px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 5px;
    color: #5F6368;
    font-weight: bold;
    left: 10px;
}
QSplitter::handle {
    background-color: #EEF0F2;
    width: 3px;
    margin: 0 5px;
    border-radius: 1px;
}
QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 12px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #C7C9CC;
    min-height: 36px;
    border-radius: 6px;
}
QScrollBar::handle:vertical:hover {
    background: #9AA0A6;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
    border: none;
    height: 0px;
}
QScrollBar:horizontal {
    border: none;
    background: transparent;
    height: 12px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background: #C7C9CC;
    min-width: 36px;
    border-radius: 6px;
}
QScrollBar::handle:horizontal:hover {
    background: #9AA0A6;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: transparent;
    border: none;
    width: 0px;
}
QListWidget {
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    background-color: #FFFFFF;
}
QListWidget::item {
    padding: 10px;
    border-bottom: 1px solid #F2F4F8;
}
QListWidget::item:selected {
    background-color: #E8EAED;
    color: #202124;
    border-radius: 10px;
}
"""
