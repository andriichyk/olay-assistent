LIGHT_CSS = """
QWidget {
    background: #f4f5fa;
    color: #1d1d2c;
    font-family: 'Segoe UI', 'Inter', 'SF Pro Display', system-ui, sans-serif;
    font-size: 13px;
}
QScrollArea {
    border: none;
    background: transparent;
}
QTextEdit, QLineEdit {
    background: #fafbfd;
    border: 1px solid #d8dae3;
    border-radius: 8px;
    padding: 7px 10px;
    color: #1d1d2c;
    selection-background-color: #c4d0ff;
}
QTextEdit:focus, QLineEdit:focus {
    border-color: #4e63d4;
}
QPushButton {
    background: #e6e7f0;
    border: none;
    border-radius: 7px;
    padding: 6px 14px;
    color: #3b3d52;
}
QPushButton:hover {
    background: #dbdce9;
}
QPushButton:pressed {
    background: #ced0e0;
}
QPushButton#send_btn {
    background: #4e63d4;
    font-weight: 600;
    color: #fff;
}
QPushButton#send_btn:hover {
    background: #3d52c7;
}
QPushButton#send_btn:pressed {
    background: #3548b0;
}
QPushButton#send_btn:disabled {
    background: #d8dae3;
    color: #a0a3b8;
}
QComboBox {
    background: #fafbfd;
    border: 1px solid #d8dae3;
    border-radius: 8px;
    padding: 5px 10px;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background: #fafbfd;
    border: 1px solid #d8dae3;
    border-radius: 6px;
    selection-background-color: #e6e7f0;
    outline: none;
}
QScrollBar:vertical {
    background: transparent;
    width: 4px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #c4c7d4;
    border-radius: 2px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #4e63d4;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
"""
