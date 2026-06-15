# -*- coding: utf-8 -*-
"""图标选择框组件 —— QPushButton + 自定义弹出面板"""

from enum import Enum

from PyQt5.QtCore import pyqtSignal, QPoint, QRect, QSize, Qt
from PyQt5.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


# ---------------------------------------------------------------
#  颜色主题
# ---------------------------------------------------------------

class Theme(Enum):
    WINE_RED = "wine_red"     # 酒红色
    BRICK_RED = "brick_red"   # 砖红色
    PINK = "pink"              # 粉红色


THEME_COLORS = {
    Theme.WINE_RED: {
        "bg": "#8C1C1C",
        "hover": "#A52A2A",
        "border": "#6B1515",
        "text": "#FFFFFF",
        "btn_bg": "#A52A2A",
        "btn_hover": "#B84545",
        "arrow": "#FFFFFF",
    },
    Theme.BRICK_RED: {
        "bg": "#C73E3A",
        "hover": "#D9544A",
        "border": "#A8322E",
        "text": "#FFFFFF",
        "btn_bg": "#D9544A",
        "btn_hover": "#E06858",
        "arrow": "#FFFFFF",
    },
    Theme.PINK: {
        "bg": "#E88CA5",
        "hover": "#F0A0B8",
        "border": "#D07088",
        "text": "#FFFFFF",
        "btn_bg": "#F0A0B8",
        "btn_hover": "#F5B8C8",
        "arrow": "#FFFFFF",
    },
}


# ---------------------------------------------------------------
#  自定义弹出面板
# ---------------------------------------------------------------

class ChoosePopup(QFrame):
    """图标选择弹出面板 —— 图标网格 + 底部按钮"""

    itemClicked = pyqtSignal(int)      # 选中某个图标选项
    bottomClicked = pyqtSignal()       # 底部按钮被点击

    COLUMNS = 4          # 每行图标数
    ICON_SIZE = 32       # 图标尺寸
    PADDING = 10         # 内边距
    SPACING = 8          # 图标间距
    BOTTOM_BTN_H = 32    # 底部按钮高度

    def __init__(self, parent: QWidget, theme: Theme = Theme.WINE_RED) -> None:
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        self._theme: Theme = theme
        self._icons: list[QIcon] = []
        self._icon_widgets: list[QPushButton] = []
        self._current_index: int = -1

        self._build_ui()
        self._apply_theme()

    # ---- 公共接口 --------------------------------------------------

    def setIcons(self, icons: list[QIcon], current_index: int = -1) -> None:
        """设置图标列表及当前选中索引"""
        self._icons = icons
        self._current_index = current_index
        self._rebuild_icons()

    def setTheme(self, theme: Theme) -> None:
        """切换主题"""
        self._theme = theme
        self._apply_theme()

    # ---- 内部 ------------------------------------------------------

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(self.PADDING, self.PADDING, self.PADDING, 0)
        main_layout.setSpacing(0)

        # 图标网格容器
        self._grid = QGridLayout()
        self._grid.setSpacing(self.SPACING)
        main_layout.addLayout(self._grid)

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        main_layout.addWidget(sep)
        main_layout.addSpacing(4)

        # 底部按钮
        self._bottom_btn = QPushButton("按钮")
        self._bottom_btn.setFixedHeight(self.BOTTOM_BTN_H)
        self._bottom_btn.setCursor(Qt.PointingHandCursor)
        self._bottom_btn.clicked.connect(self._on_bottom_clicked)
        main_layout.addWidget(self._bottom_btn)
        main_layout.addSpacing(self.PADDING // 2)

    def _rebuild_icons(self) -> None:
        """根据图标列表重建网格"""
        # 清除旧组件
        for w in self._icon_widgets:
            w.deleteLater()
        self._icon_widgets.clear()

        # 清空网格
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        colors = THEME_COLORS[self._theme]

        for i, icon in enumerate(self._icons):
            btn = QPushButton()
            btn.setIcon(icon)
            btn.setIconSize(QSize(self.ICON_SIZE, self.ICON_SIZE))
            btn.setFixedSize(self.ICON_SIZE + 16, self.ICON_SIZE + 16)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setFlat(True)

            # 当前选中高亮
            if i == self._current_index:
                btn.setStyleSheet(
                    f"QPushButton {{ background: {colors['hover']}; "
                    f"border: 2px solid {colors['text']}; border-radius: 6px; }}"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ background: transparent; border: none; }}"
                    f"QPushButton:hover {{ background: {colors['hover']}; "
                    f"border-radius: 6px; }}"
                )

            btn.clicked.connect(lambda _, idx=i: self._on_item_clicked(idx))

            row = i // self.COLUMNS
            col = i % self.COLUMNS
            self._grid.addWidget(btn, row, col, Qt.AlignCenter)
            self._icon_widgets.append(btn)

    def _apply_theme(self) -> None:
        colors = THEME_COLORS[self._theme]

        # 面板背景 + 边框
        self.setStyleSheet(
            f"ChoosePopup {{ background: {colors['bg']}; border: 2px solid {colors['border']}; border-radius: 8px; }}"
        )

        # 底部按钮
        self._bottom_btn.setStyleSheet(
            f"QPushButton {{"
            f"  background: {colors['btn_bg']};"
            f"  color: {colors['text']};"
            f"  border: none;"
            f"  border-radius: 4px;"
            f"  font-size: 13px;"
            f"}}"
            f"QPushButton:hover {{ background: {colors['btn_hover']}; }}"
            f"QPushButton:pressed {{ background: {colors['border']}; }}"
        )

    def _on_item_clicked(self, index: int) -> None:
        self.itemClicked.emit(index)
        self.close()

    def _on_bottom_clicked(self) -> None:
        self.bottomClicked.emit()
        self.close()

    def sizeHint(self) -> QSize:
        rows = (len(self._icons) + self.COLUMNS - 1) // self.COLUMNS if self._icons else 1
        w = self.COLUMNS * (self.ICON_SIZE + 16) + (self.COLUMNS - 1) * self.SPACING + self.PADDING * 2
        h = rows * (self.ICON_SIZE + 16) + (rows - 1) * self.SPACING + 1 + 4 + self.BOTTOM_BTN_H + self.PADDING * 2
        return QSize(w, h)


# ---------------------------------------------------------------
#  ChooseBox 主体
# ---------------------------------------------------------------

class ChooseBox(QPushButton):
    """图标选择框

    信号:
        currentIndexChanged(int):  当前选中索引变化
        activated(int):            用户点击菜单项时发射（即使索引未变）
    """

    currentIndexChanged = pyqtSignal(int)
    activated = pyqtSignal(int)

    # 主按钮图标尺寸
    MAIN_ICON_SIZE = 32
    # 按钮最小尺寸
    BUTTON_SIZE = 56
    # 箭头宽度
    ARROW_WIDTH = 16

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self._icons: list[QIcon] = []
        self._current_index: int = -1
        self._theme: Theme = Theme.WINE_RED
        self._default_icon: QIcon | None = None
        self._popup: ChoosePopup | None = None

        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(self.BUTTON_SIZE, self.BUTTON_SIZE)
        self.clicked.connect(self._on_clicked)

        self._apply_default_icon()
        self._apply_theme()

    # ---- 主题 ----------------------------------------------------

    def setTheme(self, theme: Theme) -> None:
        """设置颜色主题：WINE_RED / BRICK_RED / PINK"""
        self._theme = theme
        self._apply_theme()

    def theme(self) -> Theme:
        return self._theme

    # ---- 图标 ----------------------------------------------------

    def setDefaultIcon(self, icon: QIcon) -> None:
        """设置按钮默认图标（未选中任何项时显示）"""
        self._default_icon = icon
        if self._current_index < 0:
            self._apply_default_icon()

    def defaultIcon(self) -> QIcon | None:
        return self._default_icon

    # ---- 选项 ----------------------------------------------------

    def addItem(self, icon: QIcon) -> None:
        """添加一个图标选项"""
        self._icons.append(icon)

    def addItems(self, icons: list[QIcon]) -> None:
        """批量添加图标选项"""
        self._icons.extend(icons)

    def removeItem(self, index: int) -> None:
        """移除指定位置的选项"""
        if 0 <= index < len(self._icons):
            del self._icons[index]
            if self._current_index == index:
                self._current_index = -1
                self._restore_default_icon()
                self.currentIndexChanged.emit(-1)
            elif self._current_index > index:
                self._current_index -= 1

    def clear(self) -> None:
        """清空所有选项"""
        self._icons.clear()
        self._current_index = -1
        self._restore_default_icon()
        self.currentIndexChanged.emit(-1)

    def count(self) -> int:
        """返回选项总数"""
        return len(self._icons)

    # ---- 当前选中 --------------------------------------------------

    def setCurrentIndex(self, index: int) -> None:
        """设置当前选中索引，-1 恢复默认图标"""
        if index != self._current_index and -1 <= index < len(self._icons):
            self._current_index = index
            if index >= 0:
                self.setIcon(self._icons[index])
                self.setIconSize(QSize(self.MAIN_ICON_SIZE, self.MAIN_ICON_SIZE))
            else:
                self._restore_default_icon()
            self.currentIndexChanged.emit(self._current_index)

    def currentIndex(self) -> int:
        """返回当前选中索引，无选中时返回 -1"""
        return self._current_index

    # ---- 内部 ------------------------------------------------------

    def _apply_default_icon(self) -> None:
        if self._default_icon is not None:
            self.setIcon(self._default_icon)
        else:
            pixmap = QPixmap(self.MAIN_ICON_SIZE, self.MAIN_ICON_SIZE)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setPen(QPen(QColor("#CCCCCC"), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(4, 4, self.MAIN_ICON_SIZE - 8, self.MAIN_ICON_SIZE - 8, 4, 4)
            painter.setPen(QPen(QColor("#CCCCCC"), 2))
            cx, cy = self.MAIN_ICON_SIZE // 2, self.MAIN_ICON_SIZE // 2
            painter.drawLine(cx - 6, cy, cx + 6, cy)
            painter.drawLine(cx, cy - 6, cx, cy + 6)
            painter.end()
            self.setIcon(QIcon(pixmap))
        self.setIconSize(QSize(self.MAIN_ICON_SIZE, self.MAIN_ICON_SIZE))

    def _restore_default_icon(self) -> None:
        if self._default_icon is not None:
            self.setIcon(self._default_icon)
        else:
            self._apply_default_icon()

    def _apply_theme(self) -> None:
        colors = THEME_COLORS[self._theme]
        self.setStyleSheet(
            f"ChooseBox {{"
            f"  background: {colors['bg']};"
            f"  border: 2px solid {colors['border']};"
            f"  border-radius: 10px;"
            f"}}"
            f"ChooseBox:hover {{ background: {colors['hover']}; }}"
            f"ChooseBox:pressed {{ background: {colors['border']}; }}"
        )

    def _on_clicked(self) -> None:
        if self._popup is not None:
            self._popup.close()
            self._popup = None

        popup = ChoosePopup(self, self._theme)
        popup.setIcons(self._icons, self._current_index)
        popup.itemClicked.connect(self._on_item_selected)
        popup.bottomClicked.connect(self._on_bottom_button)

        # 计算弹出位置
        btn_rect = self.rect()
        popup_w = popup.sizeHint().width()
        popup_h = popup.sizeHint().height()

        # 水平：面板中心对齐按钮中心
        btn_global = self.mapToGlobal(QPoint(btn_rect.center().x(), 0))
        popup_x = btn_global.x() - popup_w // 2

        # 垂直：优先向下，空间不够则向上
        btn_bottom = self.mapToGlobal(QPoint(0, btn_rect.bottom())).y()
        btn_top = self.mapToGlobal(QPoint(0, 0)).y()
        screen_rect = QApplication.primaryScreen().availableGeometry()

        if btn_bottom + popup_h + 4 <= screen_rect.bottom():
            popup_y = btn_bottom + 4
        elif btn_top - popup_h - 4 >= screen_rect.top():
            popup_y = btn_top - popup_h - 4
        else:
            popup_y = btn_bottom + 4

        # 水平边界修正
        if popup_x < screen_rect.left():
            popup_x = screen_rect.left() + 4
        elif popup_x + popup_w > screen_rect.right():
            popup_x = screen_rect.right() - popup_w - 4

        popup.move(popup_x, popup_y)
        popup.show()
        self._popup = popup

    def _on_item_selected(self, index: int) -> None:
        self._popup = None
        self.activated.emit(index)
        if index != self._current_index:
            self._current_index = index
            self.setIcon(self._icons[index])
            self.setIconSize(QSize(self.MAIN_ICON_SIZE, self.MAIN_ICON_SIZE))
            self.currentIndexChanged.emit(index)

    def _on_bottom_button(self) -> None:
        self._popup = None
        msg = QMessageBox(self)
        msg.setWindowTitle("提示")
        msg.setText("这是一个按钮")
        msg.setIcon(QMessageBox.Information)
        msg.exec_()

    # ---- 绘制 ------------------------------------------------------

    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        colors = THEME_COLORS[self._theme]

        w, h = self.width(), self.height()
        cx = w - self.ARROW_WIDTH // 2 - 2
        cy = h // 2
        r = 4

        painter.setPen(QPen(QColor(colors["arrow"]), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(cx - r, cy - 2, cx, cy + 2)
        painter.drawLine(cx, cy + 2, cx + r, cy - 2)

        painter.end()