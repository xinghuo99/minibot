# -*- coding: utf-8 -*-
"""ChooseBox 测试 Demo —— 图标选择框 + 三色主题 + 事件处理示例"""

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMessageBox,
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
        self.setWindowTitle("ChooseBox Demo — 图标选择框 + 事件处理")
        self.resize(600, 550)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(20)

        # ============================================================
        #  酒红色主题 — 演示三种选项的点击事件处理
        # ============================================================
        layout.addWidget(QLabel("酒红色主题 — 三种选项的点击事件"))
        row1 = QHBoxLayout()
        row1.setSpacing(12)
        self.box1 = ChooseBox()
        self.box1.setTheme(Theme.WINE_RED)
        self.box1.addItem(make_shape_icon("#FFD700", "star"), "")
        self.box1.addItem(make_shape_icon("#FF6B6B", "circle"), "圆形")
        self.box1.addItem(make_shape_icon("#4ECDC4", "square"), "方形")
        self.box1.addItem(make_shape_icon("#FFE66D", "triangle"), "三角")
        self.box1.addItem(make_shape_icon("#A8E6CF", "heart"), "爱心")

        # 选中变化（纯图标 or 图标+文字 都会触发）
        self.box1.currentIndexChanged.connect(self._on_box1_changed)

        # 底部按钮点击
        self.box1.bottomButtonClicked.connect(self._on_box1_bottom_btn)

        row1.addWidget(self.box1)
        self._label1 = QLabel("状态：等待操作...")
        self._label1.setStyleSheet("color: #555; font-size: 12px;")
        row1.addWidget(self._label1)
        row1.addStretch()
        layout.addLayout(row1)

        # ============================================================
        #  砖红色主题 — 演示 activated 信号（不区分纯图标/文字）
        # ============================================================
        layout.addWidget(QLabel("砖红色主题 — 每次点击都触发 activated"))
        row2 = QHBoxLayout()
        row2.setSpacing(12)
        self.box2 = ChooseBox()
        self.box2.setTheme(Theme.BRICK_RED)
        self.box2.addItem(make_shape_icon("#FFD700", "star"), "")
        self.box2.addItem(make_shape_icon("#FF6B6B", "circle"), "圆形")
        self.box2.addItem(make_shape_icon("#4ECDC4", "star"), "星形")
        self.box2.addItem(make_shape_icon("#FFE66D", "heart"), "爱心")
        self.box2.setCurrentIndex(1)

        self.box2.activated.connect(self._on_box2_activated)
        self.box2.bottomButtonClicked.connect(self._on_box2_bottom_btn)

        row2.addWidget(self.box2)
        self._label2 = QLabel("状态：已选中「圆形」")
        self._label2.setStyleSheet("color: #555; font-size: 12px;")
        row2.addWidget(self._label2)
        row2.addStretch()
        layout.addLayout(row2)

        # ============================================================
        #  粉红色主题 — 演示更多选项 + 弹窗式事件处理
        # ============================================================
        layout.addWidget(QLabel("粉红色主题 — 弹窗式事件处理"))
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

        self.box3.activated.connect(self._on_box3_activated)
        self.box3.bottomButtonClicked.connect(self._on_box3_bottom_btn)

        row3.addWidget(self.box3)
        self._label3 = QLabel("状态：等待操作...")
        self._label3.setStyleSheet("color: #555; font-size: 12px;")
        row3.addWidget(self._label3)
        row3.addStretch()
        layout.addLayout(row3)

        layout.addStretch()

    # ---- box1 事件处理（酒红色）-------------------------------------

    def _on_box1_changed(self, index: int) -> None:
        """根据选项类型做不同处理"""
        if index < 0:
            self._label1.setText("状态：已恢复默认")
            return
        text = self.box1.itemText(index)
        if not text:
            # 纯图标选项被选中
            self._label1.setText(f"状态：选中了【纯图标选项】(index={index})")
        else:
            # 图标+文字选项被选中
            self._label1.setText(f"状态：选中了【{text}】(index={index})")

    def _on_box1_bottom_btn(self) -> None:
        self._label1.setText("状态：点击了底部「按钮」")
        QMessageBox.information(self, "底部按钮", "弹出面板底部的按钮被点击了！")

    # ---- box2 事件处理（砖红色）-------------------------------------

    def _on_box2_activated(self, index: int) -> None:
        text = self.box2.itemText(index)
        if not text:
            self._label2.setText(f"状态：点击了【纯图标选项】(index={index})")
        else:
            self._label2.setText(f"状态：点击了【{text}】(index={index})")

    def _on_box2_bottom_btn(self) -> None:
        self._label2.setText("状态：点击了底部「按钮」")
        QMessageBox.information(self, "底部按钮", "砖红色主题的底部按钮被点击了！")

    # ---- box3 事件处理（粉红色）-------------------------------------

    def _on_box3_activated(self, index: int) -> None:
        text = self.box3.itemText(index)
        if not text:
            self._label3.setText(f"状态：点击了【纯图标选项】(index={index})")
        else:
            self._label3.setText(f"状态：点击了【{text}】(index={index})")

    def _on_box3_bottom_btn(self) -> None:
        self._label3.setText("状态：点击了底部「按钮」")
        QMessageBox.information(self, "底部按钮", "粉红色主题的底部按钮被点击了！")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = DemoWindow()
    win.show()
    sys.exit(app.exec_())