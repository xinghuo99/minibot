# -*- coding: utf-8 -*-
"""ChooseBox 测试 Demo —— 图标选择框 + 三色主题"""

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from choosebox import ChooseBox, Theme


# ---- 工具函数：生成形状图标 ----------------------------------------

def make_shape_icon(color: str, shape: str, size: int = 32) -> QIcon:
    """生成带形状的图标：circle / square / triangle / star / heart"""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(color))

    m = 4
    r = size // 2 - m

    if shape == "circle":
        painter.drawEllipse(m, m, size - 2 * m, size - 2 * m)
    elif shape == "square":
        painter.drawRoundedRect(m, m, size - 2 * m, size - 2 * m, 3, 3)
    elif shape == "triangle":
        from PyQt5.QtCore import QPointF
        from PyQt5.QtGui import QPolygonF
        poly = QPolygonF([
            QPointF(size / 2, m),
            QPointF(size - m, size - m),
            QPointF(m, size - m),
        ])
        painter.drawPolygon(poly)
    elif shape == "star":
        from math import cos, pi, sin
        from PyQt5.QtCore import QPointF
        from PyQt5.QtGui import QPolygonF
        points = []
        cx, cy = size / 2, size / 2
        outer = r
        inner = r * 0.4
        for i in range(10):
            angle = -pi / 2 + i * pi / 5
            rad = outer if i % 2 == 0 else inner
            points.append(QPointF(cx + rad * cos(angle), cy + rad * sin(angle)))
        poly = QPolygonF(points)
        painter.drawPolygon(poly)
    elif shape == "heart":
        from PyQt5.QtGui import QPainterPath
        path = QPainterPath()
        cx, cy = size / 2, size / 2 + 4
        path.moveTo(cx, cy + r * 0.7)
        path.cubicTo(cx - r * 1.3, cy - r * 0.3, cx - r * 0.5, cy - r * 1.1, cx, cy - r * 0.5)
        path.cubicTo(cx + r * 0.5, cy - r * 1.1, cx + r * 1.3, cy - r * 0.3, cx, cy + r * 0.7)
        painter.drawPath(path)

    painter.end()
    return QIcon(pixmap)


# ---- Demo 主窗口 --------------------------------------------------

class DemoWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChooseBox Demo — 图标选择框")
        self.resize(550, 450)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)

        # ---- 酒红色主题 ----
        layout.addWidget(QLabel("酒红色主题 (WINE_RED)"))
        row1 = QHBoxLayout()
        row1.setSpacing(12)
        self.box1 = ChooseBox()
        self.box1.setTheme(Theme.WINE_RED)
        # 第一个：纯图标选项（text=""）
        self.box1.addItem(make_shape_icon("#FFD700", "star"), "")
        # 其余：图标+文字选项
        self.box1.addItem(make_shape_icon("#FF6B6B", "circle"), "圆形")
        self.box1.addItem(make_shape_icon("#4ECDC4", "square"), "方形")
        self.box1.addItem(make_shape_icon("#FFE66D", "triangle"), "三角")
        self.box1.addItem(make_shape_icon("#A8E6CF", "heart"), "爱心")
        self.box1.currentIndexChanged.connect(
            lambda i: print(f"[酒红] 选中 index={i}, text={self.box1.currentText()}")
        )
        row1.addWidget(self.box1)
        row1.addWidget(QLabel("← 第1个是纯图标\n其余是图标+文字\n底部有「按钮」"))
        row1.addStretch()
        layout.addLayout(row1)

        # ---- 砖红色主题 ----
        layout.addWidget(QLabel("砖红色主题 (BRICK_RED)"))
        row2 = QHBoxLayout()
        row2.setSpacing(12)
        self.box2 = ChooseBox()
        self.box2.setTheme(Theme.BRICK_RED)
        self.box2.addItem(make_shape_icon("#FFD700", "star"), "")
        self.box2.addItem(make_shape_icon("#FF6B6B", "circle"), "圆形")
        self.box2.addItem(make_shape_icon("#4ECDC4", "star"), "星形")
        self.box2.addItem(make_shape_icon("#FFE66D", "heart"), "爱心")
        self.box2.setCurrentIndex(1)
        self.box2.activated.connect(
            lambda i: print(f"[砖红] activated index={i}")
        )
        row2.addWidget(self.box2)
        row2.addWidget(QLabel("← 已选中「圆形」"))
        row2.addStretch()
        layout.addLayout(row2)

        # ---- 粉红色主题 ----
        layout.addWidget(QLabel("粉红色主题 (PINK)"))
        row3 = QHBoxLayout()
        row3.setSpacing(12)
        self.box3 = ChooseBox()
        self.box3.setTheme(Theme.PINK)
        self.box3.addItem(make_shape_icon("#FFD700", "star"), "")
        self.box3.addItem(make_shape_icon("#FF6B6B", "heart"), "爱心")
        self.box3.addItem(make_shape_icon("#4ECDC4", "circle"), "圆形")
        self.box3.addItem(make_shape_icon("#FFE66D", "star"), "星形")
        self.box3.addItem(make_shape_icon("#A8E6CF", "triangle"), "三角")
        self.box3.addItem(make_shape_icon("#FF8A80", "square"), "方形")
        self.box3.currentIndexChanged.connect(
            lambda i: print(f"[粉红] 选中 index={i}, text={self.box3.currentText()}")
        )
        row3.addWidget(self.box3)
        row3.addWidget(QLabel("← 6个选项"))
        row3.addStretch()
        layout.addLayout(row3)

        layout.addStretch()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = DemoWindow()
    win.show()
    sys.exit(app.exec_())