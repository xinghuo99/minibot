# -*- coding: utf-8 -*-
"""ChooseBox 测试 Demo —— 图标选择框 + 三色主题"""

import sys

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from choosebox import ChooseBox, Theme


# ---- 工具函数：生成彩色图标 ----------------------------------------

def make_color_icon(color: str, size: int = 32) -> QIcon:
    """生成指定颜色的纯色方块图标"""
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(color))
    return QIcon(pixmap)


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
        self.resize(500, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)

        # ---- 酒红色主题 ----
        layout.addWidget(QLabel("酒红色主题 (WINE_RED)"))
        row1 = QHBoxLayout()
        row1.setSpacing(12)
        self.box1 = ChooseBox()
        self.box1.setTheme(Theme.WINE_RED)
        self.box1.addItems([
            make_shape_icon("#FF6B6B", "circle"),
            make_shape_icon("#4ECDC4", "square"),
            make_shape_icon("#FFE66D", "triangle"),
            make_shape_icon("#A8E6CF", "star"),
            make_shape_icon("#FF8A80", "heart"),
            make_shape_icon("#80D8FF", "circle"),
            make_shape_icon("#B388FF", "square"),
            make_shape_icon("#FFD54F", "triangle"),
        ])
        self.box1.currentIndexChanged.connect(
            lambda i: print(f"[酒红] 选中 index={i}")
        )
        row1.addWidget(self.box1)
        row1.addWidget(QLabel("← 点击选择图标\n底部有「按钮」"))
        row1.addStretch()
        layout.addLayout(row1)

        # ---- 砖红色主题 ----
        layout.addWidget(QLabel("砖红色主题 (BRICK_RED)"))
        row2 = QHBoxLayout()
        row2.setSpacing(12)
        self.box2 = ChooseBox()
        self.box2.setTheme(Theme.BRICK_RED)
        self.box2.addItems([
            make_shape_icon("#FF6B6B", "circle"),
            make_shape_icon("#4ECDC4", "star"),
            make_shape_icon("#FFE66D", "heart"),
            make_shape_icon("#A8E6CF", "square"),
        ])
        self.box2.setCurrentIndex(1)
        self.box2.activated.connect(
            lambda i: print(f"[砖红] activated index={i}")
        )
        row2.addWidget(self.box2)
        row2.addWidget(QLabel("← 已选中第2个图标"))
        row2.addStretch()
        layout.addLayout(row2)

        # ---- 粉红色主题 ----
        layout.addWidget(QLabel("粉红色主题 (PINK)"))
        row3 = QHBoxLayout()
        row3.setSpacing(12)
        self.box3 = ChooseBox()
        self.box3.setTheme(Theme.PINK)
        self.box3.addItems([
            make_shape_icon("#FF6B6B", "heart"),
            make_shape_icon("#4ECDC4", "circle"),
            make_shape_icon("#FFE66D", "star"),
            make_shape_icon("#A8E6CF", "triangle"),
            make_shape_icon("#FF8A80", "square"),
            make_shape_icon("#80D8FF", "heart"),
            make_shape_icon("#B388FF", "circle"),
            make_shape_icon("#FFD54F", "star"),
            make_shape_icon("#E57373", "triangle"),
            make_shape_icon("#64B5F6", "square"),
            make_shape_icon("#81C784", "heart"),
            make_shape_icon("#FFB74D", "circle"),
        ])
        self.box3.currentIndexChanged.connect(
            lambda i: print(f"[粉红] 选中 index={i}")
        )
        row3.addWidget(self.box3)
        row3.addWidget(QLabel("← 12个图标选项\n超过4个自动换行"))
        row3.addStretch()
        layout.addLayout(row3)

        layout.addStretch()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = DemoWindow()
    win.show()
    sys.exit(app.exec_())