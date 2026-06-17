import sys
import random
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QWidget,
                             QVBoxLayout, QHBoxLayout, QTextBrowser)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QBrush


class HeartParticle:
    """单个爱心粒子"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = random.uniform(16, 66)
        self.speed_y = random.uniform(1.5, 4.0)
        self.speed_x = random.uniform(-1.0, 1.0)
        self.opacity = 2.0 # old value 1.0
        self.wobble_phase = random.uniform(0, math.pi * 2)
        self.wobble_amp = random.uniform(0.3, 1.2)

    def update(self):
        self.y -= self.speed_y
        self.wobble_phase += 0.05
        self.x += self.speed_x + math.sin(self.wobble_phase) * self.wobble_amp * 0.3
        self.opacity -= 0.008
        self.size *= 0.997

    def is_alive(self):
        return self.y > -50 and self.opacity > 0


class _HeartOverlay(QWidget):
    """透明爱心动画覆盖层"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.particles = []
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.hide()

    def showEvent(self, event):
        super().showEvent(event)
        if not self._timer.isActive():
            self._timer.start(16)

    def hideEvent(self, event):
        self._timer.stop()
        super().hideEvent(event)

    def _animate(self):
        self.particles = [p for p in self.particles if p.is_alive()]
        for p in self.particles:
            p.update()
        if not self.particles:
            self.hide()
        self.update()

    def paintEvent(self, event):
        if not self.particles:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        for p in self.particles:
            a = max(0, min(255, int(p.opacity * 255)))
            painter.setBrush(QBrush(QColor(255, 0, 0, 255)))
            painter.drawPath(self._heart_path(p.x, p.y, p.size))
        painter.end()

    @staticmethod
    def _heart_path(cx, cy, size):
        s = size * 0.5
        path = QPainterPath()
        path.moveTo(cx, cy + s * 0.6)
        path.cubicTo(cx - s * 1.2, cy + s * 0.1,
                     cx - s * 1.2, cy - s * 0.5,
                     cx, cy - s * 0.2)
        path.cubicTo(cx + s * 1.2, cy - s * 0.5,
                     cx + s * 1.2, cy + s * 0.1,
                     cx, cy + s * 0.6)
        return path


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("爱心雨")
        self.resize(450, 650)

        # ---- 中央组件：聊天框 + 按钮 ----
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # 聊天框
        self.chat = QTextBrowser()
        self.chat.setStyleSheet("""
            QTextBrowser {
                background-color: #f5f0eb;
                border: 1px solid #ddd;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
            }
        """)
        self._init_chat_content()
        layout.addWidget(self.chat)

        # 底部区域：输入框 + 按钮
        bottom = QHBoxLayout()
        bottom.setSpacing(10)

        self.btn = QPushButton("点我")
        self.btn.setFixedSize(80, 80)
        self.btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4081;
                color: white;
                border-radius: 40px;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #ff79b0;
            }
            QPushButton:pressed {
                background-color: #c60055;
            }
        """)
        self.btn.clicked.connect(self._on_click)
        bottom.addStretch()
        bottom.addWidget(self.btn)
        bottom.addStretch()
        layout.addLayout(bottom)

        # ---- 透明覆盖层（覆盖整个窗口） ----
        self.overlay = _HeartOverlay(self)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.overlay.setGeometry(self.centralWidget().geometry())

    def _on_click(self):
        # 按钮顶部中心在 overlay 坐标系中的位置
        btn_pos = self.btn.mapTo(self, self.btn.rect().topLeft())
        bx = btn_pos.x() + self.btn.width() // 2 - self.overlay.x()
        by = btn_pos.y() - self.overlay.y()

        for _ in range(30):
            self.overlay.particles.append(HeartParticle(bx, by))
        self.overlay.show()
        self.overlay.raise_()

    def _init_chat_content(self):
        messages = [
            ("我", "你好呀！今天天气真好 ☀️"),
            ("TA", "是呀，要不要出去走走？"),
            ("我", "好啊，去哪里呢？"),
            ("TA", "去公园吧，樱花开了 🌸"),
            ("我", "太棒了！几点出发？"),
            ("TA", "下午两点，老地方见～"),
        ]
        html = '<div style="line-height: 2;">'
        for who, msg in messages:
            align = "right" if who == "我" else "left"
            color = "#4a90d9" if who == "我" else "#e8875b"
            bg = "#e8f0fe" if who == "我" else "#fef0e8"
            html += (
                f'<div style="text-align:{align};margin:6px 0;">'
                f'<span style="display:inline-block;max-width:70%;'
                f'background:{bg};color:{color};padding:8px 14px;'
                f'border-radius:16px;">{msg}</span>'
                f'</div>'
            )
        html += '</div>'
        self.chat.setHtml(html)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())