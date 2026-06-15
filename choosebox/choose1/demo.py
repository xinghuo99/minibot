# -*- coding: utf-8 -*-
"""ChooseBox 测试 Demo"""

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from choosebox import ChooseBox


class DemoWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChooseBox Demo")
        self.resize(450, 350)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(16)

        # ---- 上方组件演示上拉效果 -----------------------------------
        layout.addWidget(QLabel("▼ 上方（靠近顶部，易触发上拉）"))
        top_layout = QHBoxLayout()
        box1 = ChooseBox()
        box1.setPlaceholderText("选择一个城市")
        box1.addItems(["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "南京"])
        box1.currentIndexChanged.connect(lambda i: print(f"[box1] index={i}, text={box1.currentText()}"))
        box1.activated.connect(lambda i: print(f"[box1] activated index={i}"))
        top_layout.addWidget(box1)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        # ---- 中间组件正常下拉 ----------------------------------------
        layout.addStretch()
        layout.addWidget(QLabel("▼ 中间（正常下拉）"))
        mid_layout = QHBoxLayout()
        box2 = ChooseBox()
        box2.setPlaceholderText("选择一个水果")
        box2.addItems(["苹果", "香蕉", "橘子", "葡萄", "西瓜", "草莓", "芒果"])
        box2.setCurrentIndex(0)
        box2.currentTextChanged.connect(lambda t: print(f"[box2] text={t}"))

        # 动态增删按钮
        from PyQt5.QtWidgets import QPushButton

        btn_add = QPushButton("添加「菠萝」")
        btn_add.clicked.connect(lambda: box2.addItem("菠萝"))
        btn_remove = QPushButton("移除最后一项")
        btn_remove.clicked.connect(lambda: box2.removeItem(box2.count() - 1))

        mid_layout.addWidget(box2)
        mid_layout.addWidget(btn_add)
        mid_layout.addWidget(btn_remove)
        mid_layout.addStretch()
        layout.addLayout(mid_layout)

        # ---- 底部组件演示上拉效果 ------------------------------------
        layout.addStretch()
        layout.addWidget(QLabel("▼ 底部（靠近屏幕底部，自动上拉）"))
        bot_layout = QHBoxLayout()
        box3 = ChooseBox()
        box3.setPlaceholderText("请选择版本")
        box3.addItems(["v1.0", "v2.0", "v3.0-beta", "v3.0-stable", "v4.0-preview"])
        box3.setCurrentText("v3.0-stable")
        box3.activated.connect(lambda i: print(f"[box3] activated {i}"))
        bot_layout.addWidget(box3)
        bot_layout.addStretch()
        layout.addLayout(bot_layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = DemoWindow()
    win.show()
    sys.exit(app.exec_())