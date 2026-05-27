import sys

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QStyle

from widgets.overlay import Overlay


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    overlay = Overlay()
    overlay.show()

    tray = QSystemTrayIcon(
        app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon), app
    )
    menu = QMenu()
    menu.addAction("Show / Hide", overlay.toggle)
    menu.addSeparator()
    menu.addAction("Quit", app.quit)
    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda r: overlay.toggle()
        if r == QSystemTrayIcon.ActivationReason.Trigger else None
    )
    tray.setToolTip("AI Assistant — right-click for menu")
    tray.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
