import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import QTimer, Qt, QMetaObject

try:
    import shiboken2
    _has_shiboken = True
except ImportError:
    _has_shiboken = False

COLORS = [
    "#FF0000", "#FF4500", "#FF8C00", "#FFD700",
    "#32CD32", "#00CED1", "#1E90FF", "#8A2BE2",
    "#FF1493",
]


class ColorfulProgress(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(700, 280)

        self.dot_count = 1
        self._drag_pos = None

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        font = self.font()
        font.setPointSize(36)

        self.label_center = QLabel(self)
        self.label_center.setAlignment(Qt.AlignCenter)
        self.label_center.setFont(font)
        layout.addWidget(self.label_center)

        self.label_left = QLabel(self)
        self.label_left.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.label_left.setFont(font)
        layout.addWidget(self.label_left)

        self.label_right = QLabel(self)
        self.label_right.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.label_right.setFont(font)
        layout.addWidget(self.label_right)

        self.setLayout(layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)

    # ---- 线程安全的 show / hide ----
    def safe_show(self):
        """任意线程调用，安全地在主线程显示窗口。"""
        QMetaObject.invokeMethod(
            self, "show", Qt.QueuedConnection)

    def safe_hide(self):
        """任意线程调用，安全地在主线程隐藏窗口。"""
        QMetaObject.invokeMethod(
            self, "hide", Qt.QueuedConnection)

    # ---- 生命周期事件 ----
    def showEvent(self, event):
        """显示窗口时启动定时器，重置计数。"""
        self.dot_count = 1
        self._update_labels()
        if not self.timer.isActive():
            self.timer.start(200)
        super().showEvent(event)

    def hideEvent(self, event):
        """隐藏窗口时停止定时器，防止后台无意义刷新。"""
        if self.timer.isActive():
            self.timer.stop()
        super().hideEvent(event)

    def closeEvent(self, event):
        """关闭时确保定时器停止，再销毁。"""
        if self.timer.isActive():
            self.timer.stop()
        super().closeEvent(event)

    # ---- 拖拽 ----
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)

    def mouseDoubleClickEvent(self, event):
        self.close()

    # ---- 进度更新 ----
    def _build_dots(self):
        dots = ""
        for i in range(self.dot_count):
            color = COLORS[i % len(COLORS)]
            dots += f'<span style="color:{color};">●</span>'
        return dots

    def _update_labels(self):
        dots = self._build_dots()
        self.label_center.setText(dots)
        self.label_left.setText(dots)
        self.label_right.setText(dots)

    def update_progress(self):
        """兜底保护：widget不可见或被销毁时直接跳过。"""
        if _has_shiboken:
            try:
                if not shiboken2.isValid(self):
                    return
            except RuntimeError:
                return

        if not self.isVisible():
            return

        try:
            self._update_labels()
            self.dot_count += 1
            if self.dot_count > 9:
                self.dot_count = 1
        except RuntimeError:
            pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ColorfulProgress()
    window.show()
    sys.exit(app.exec_())