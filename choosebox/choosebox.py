# -*- coding: utf-8 -*-
"""图标选择框组件 —— QPushButton + 自定义弹出面板"""

from enum import Enum

from PyQt5.QtCore import pyqtSignal, QPoint, QRect, QSize, Qt
from PyQt5.QtGui import QColor, QFont, QFontMetrics, QIcon, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
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
        "sep": "#9B3A3A",
    },
    Theme.BRICK_RED: {
        "bg": "#C73E3A",
        "hover": "#D9544A",
        "border": "#A8322E",
        "text": "#FFFFFF",
        "btn_bg": "#D9544A",
        "btn_hover": "#E06858",
        "arrow": "#FFFFFF",
        "sep": "#D06060",
    },
    Theme.PINK: {
        "bg": "#E88CA5",
        "hover": "#F0A0B8",
        "border": "#D07088",
        "text": "#FFFFFF",
        "btn_bg": "#F0A0B8",
        "btn_hover": "#F5B8C8",
        "arrow": "#FFFFFF",
        "sep": "#F0B0C0",
    },
}


# ---------------------------------------------------------------
#  自定义弹出面板
# ---------------------------------------------------------------

class ChoosePopup(QFrame):
    """图标选择弹出面板 —— 图标选项列表 + 底部按钮"""

    itemClicked = pyqtSignal(int)      # 选中某个选项
    bottomClicked = pyqtSignal()       # 底部按钮被点击

    PADDING = 10
    BOTTOM_BTN_H = 32
    ICON_ONLY_SIZE = 48       # 纯图标选项的图标尺寸
    ICON_TEXT_SIZE = 20       # 图标+文字选项的图标尺寸
    ITEM_H = 36               # 图标+文字选项的高度

    def __init__(self, parent: QWidget, theme: Theme = Theme.WINE_RED) -> None:
        super().__init__(parent, Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        self._theme: Theme = theme
        self._items: list[dict] = []          # [{"icon": QIcon, "text": str}, ...]
        self._item_widgets: list[QWidget] = []
        self._current_index: int = -1

        self._build_ui()
        self._apply_theme()

    # ---- 公共接口 --------------------------------------------------

    def setItems(self, items: list[dict], current_index: int = -1) -> None:
        """设置选项列表: [{"icon": QIcon, "text": "..."}, ...]"""
        self._items = items
        self._current_index = current_index
        self._rebuild_items()

    def setTheme(self, theme: Theme) -> None:
        self._theme = theme
        self._apply_theme()

    # ---- 内部 ------------------------------------------------------

    def _build_ui(self) -> None:
        self._outer_layout = QVBoxLayout(self)
        self._outer_layout.setContentsMargins(self.PADDING, self.PADDING, self.PADDING, 0)
        self._outer_layout.setSpacing(0)

        # 选项列表容器
        self._items_layout = QVBoxLayout()
        self._items_layout.setContentsMargins(0, 0, 0, 0)
        self._items_layout.setSpacing(2)
        self._outer_layout.addLayout(self._items_layout)

        # 分隔线
        self._sep = QFrame()
        self._sep.setFrameShape(QFrame.HLine)
        self._sep.setFixedHeight(1)
        self._outer_layout.addWidget(self._sep)
        self._outer_layout.addSpacing(4)

        # 底部按钮
        self._bottom_btn = QPushButton("按钮")
        self._bottom_btn.setFixedHeight(self.BOTTOM_BTN_H)
        self._bottom_btn.setCursor(Qt.PointingHandCursor)
        self._bottom_btn.clicked.connect(self._on_bottom_clicked)
        self._outer_layout.addWidget(self._bottom_btn)
        self._outer_layout.addSpacing(self.PADDING // 2)

    def _rebuild_items(self) -> None:
        """根据选项列表重建所有选项组件"""
        for w in self._item_widgets:
            w.deleteLater()
        self._item_widgets.clear()

        # 清空 items_layout
        while self._items_layout.count():
            item = self._items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

        colors = THEME_COLORS[self._theme]

        for i, data in enumerate(self._items):
            icon = data.get("icon")
            text = data.get("text", "")
            is_icon_only = (not text)

            if is_icon_only:
                # ---- 纯图标选项：大图标居中 ----
                btn = QPushButton()
                btn.setIcon(icon)
                btn.setIconSize(QSize(self.ICON_ONLY_SIZE, self.ICON_ONLY_SIZE))
                btn.setFixedHeight(self.ICON_ONLY_SIZE + 16)
                btn.setCursor(Qt.PointingHandCursor)
                btn.setFlat(True)

                if i == self._current_index:
                    btn.setStyleSheet(
                        f"QPushButton {{ background: {colors['hover']}; "
                        f"border: 2px solid {colors['text']}; border-radius: 6px; }}"
                    )
                else:
                    btn.setStyleSheet(
                        f"QPushButton {{ background: transparent; border: none; }}"
                        f"QPushButton:hover {{ background: {colors['hover']}; border-radius: 6px; }}"
                    )

                btn.clicked.connect(lambda _, idx=i: self._on_item_clicked(idx))
                self._items_layout.addWidget(btn, 0, Qt.AlignHCenter)
                self._item_widgets.append(btn)

            else:
                # ---- 图标+文字选项：左图标 + 右文字 ----
                row = QWidget()
                row.setFixedHeight(self.ITEM_H)
                row.setCursor(Qt.PointingHandCursor)

                # 背景高亮
                if i == self._current_index:
                    row.setStyleSheet(
                        f"QWidget {{ background: {colors['hover']}; border-radius: 4px; }}"
                    )
                else:
                    row.setStyleSheet(
                        f"QWidget {{ background: transparent; }}"
                        f"QWidget:hover {{ background: {colors['hover']}; border-radius: 4px; }}"
                    )

                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(8, 4, 12, 4)
                row_layout.setSpacing(8)

                icon_btn = QPushButton()
                icon_btn.setIcon(icon)
                icon_btn.setIconSize(QSize(self.ICON_TEXT_SIZE, self.ICON_TEXT_SIZE))
                icon_btn.setFixedSize(self.ICON_TEXT_SIZE + 8, self.ICON_TEXT_SIZE + 8)
                icon_btn.setFlat(True)
                icon_btn.setStyleSheet("QPushButton { background: transparent; border: none; }")
                icon_btn.setAttribute(Qt.WA_TransparentForMouseEvents, True)
                row_layout.addWidget(icon_btn)

                label = QLabel(text)
                label.setStyleSheet(f"QLabel {{ color: {colors['text']}; font-size: 13px; background: transparent; }}")
                row_layout.addWidget(label)
                row_layout.addStretch()

                # 点击事件
                row.mousePressEvent = lambda e, idx=i: self._on_item_clicked(idx)
                self._items_layout.addWidget(row)
                self._item_widgets.append(row)

    def _clear_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _apply_theme(self) -> None:
        colors = THEME_COLORS[self._theme]
        self.setStyleSheet(
            f"ChoosePopup {{ background: {colors['bg']}; border: 2px solid {colors['border']}; border-radius: 8px; }}"
        )
        self._sep.setStyleSheet(f"QFrame {{ color: {colors['sep']}; }}")
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
        h = 0
        for data in self._items:
            if not data.get("text"):
                h += self.ICON_ONLY_SIZE + 16 + 2   # 纯图标项高度
            else:
                h += self.ITEM_H + 2                # 图标+文字项高度
        # 分隔线 + 底部按钮 + 边距
        h += 1 + 4 + self.BOTTOM_BTN_H + self.PADDING * 2
        # 宽度：取最宽项
        w = 180
        return QSize(w, max(h, 100))


# ---------------------------------------------------------------
#  ChooseBox 主体
# ---------------------------------------------------------------

class ChooseBox(QPushButton):
    """图标选择框

    信号:
        currentIndexChanged(int):  当前选中索引变化
        activated(int):            用户点击菜单项时发射（即使索引未变）
        bottomButtonClicked():     弹出面板底部按钮被点击
    """

    currentIndexChanged = pyqtSignal(int)
    activated = pyqtSignal(int)
    bottomButtonClicked = pyqtSignal()

    # 主按钮图标尺寸
    MAIN_ICON_SIZE = 32
    # 箭头宽度
    ARROW_WIDTH = 16
    # 最小高度
    MIN_HEIGHT = 56
    # 最小宽度（纯图标时）
    MIN_WIDTH = 56

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self._items: list[dict] = []     # [{"icon": QIcon, "text": str}, ...]
        self._current_index: int = -1
        self._theme: Theme = Theme.WINE_RED
        self._default_icon: QIcon | None = None
        self._popup: ChoosePopup | None = None

        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(self.MIN_HEIGHT)
        self.clicked.connect(self._on_clicked)

        self._apply_default_icon()
        self._update_button_content()
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
            self._update_button_content()

    def defaultIcon(self) -> QIcon | None:
        return self._default_icon

    # ---- 选项 ----------------------------------------------------

    def addItem(self, icon: QIcon, text: str = "") -> None:
        """添加一个选项。text 为空时为纯图标选项，否则为图标+文字选项"""
        self._items.append({"icon": icon, "text": text})

    def addItems(self, items: list[dict]) -> None:
        """批量添加选项: [{"icon": QIcon, "text": "..."}, ...]"""
        self._items.extend(items)

    def removeItem(self, index: int) -> None:
        """移除指定位置的选项"""
        if 0 <= index < len(self._items):
            del self._items[index]
            if self._current_index == index:
                self._current_index = -1
                self._update_button_content()
                self.currentIndexChanged.emit(-1)
            elif self._current_index > index:
                self._current_index -= 1

    def clear(self) -> None:
        """清空所有选项"""
        self._items.clear()
        self._current_index = -1
        self._update_button_content()
        self.currentIndexChanged.emit(-1)

    def count(self) -> int:
        return len(self._items)

    def itemText(self, index: int) -> str:
        """返回指定索引的文本"""
        if 0 <= index < len(self._items):
            return self._items[index].get("text", "")
        return ""

    def itemIcon(self, index: int) -> QIcon | None:
        """返回指定索引的图标"""
        if 0 <= index < len(self._items):
            return self._items[index].get("icon")
        return None

    # ---- 当前选中 --------------------------------------------------

    def setCurrentIndex(self, index: int) -> None:
        """设置当前选中索引，-1 恢复默认图标"""
        if index != self._current_index and -1 <= index < len(self._items):
            self._current_index = index
            self._update_button_content()
            self.currentIndexChanged.emit(self._current_index)

    def currentIndex(self) -> int:
        return self._current_index

    def currentText(self) -> str:
        if 0 <= self._current_index < len(self._items):
            return self._items[self._current_index].get("text", "")
        return ""

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

    def _update_button_content(self) -> None:
        """根据当前选中项刷新按钮的图标和文字"""
        colors = THEME_COLORS[self._theme]

        if self._current_index >= 0:
            item = self._items[self._current_index]
            self.setIcon(item["icon"])
            self.setIconSize(QSize(self.MAIN_ICON_SIZE, self.MAIN_ICON_SIZE))
            if item["text"]:
                self.setText(item["text"])
                self.setStyleSheet(
                    f"ChooseBox {{"
                    f"  background: {colors['bg']};"
                    f"  border: 2px solid {colors['border']};"
                    f"  border-radius: 10px;"
                    f"  color: {colors['text']};"
                    f"  font-size: 13px;"
                    f"}}"
                    f"ChooseBox:hover {{ background: {colors['hover']}; }}"
                    f"ChooseBox:pressed {{ background: {colors['border']}; }}"
                )
            else:
                self.setText("")
                self._apply_theme()
        else:
            self.setText("")
            self._apply_default_icon()
            self._apply_theme()

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
        popup.setItems(self._items, self._current_index)
        popup.itemClicked.connect(self._on_item_selected)
        popup.bottomClicked.connect(self._on_bottom_button)

        btn_rect = self.rect()
        popup_w = popup.sizeHint().width()
        popup_h = popup.sizeHint().height()

        btn_global = self.mapToGlobal(QPoint(btn_rect.center().x(), 0))
        popup_x = btn_global.x() - popup_w // 2

        btn_bottom = self.mapToGlobal(QPoint(0, btn_rect.bottom())).y()
        btn_top = self.mapToGlobal(QPoint(0, 0)).y()
        screen_rect = QApplication.primaryScreen().availableGeometry()

        if btn_bottom + popup_h + 4 <= screen_rect.bottom():
            popup_y = btn_bottom + 4
        elif btn_top - popup_h - 4 >= screen_rect.top():
            popup_y = btn_top - popup_h - 4
        else:
            popup_y = btn_bottom + 4

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
            self._update_button_content()
            self.currentIndexChanged.emit(index)

    def _on_bottom_button(self) -> None:
        self._popup = None
        self.bottomButtonClicked.emit()

    # ---- 大小 ------------------------------------------------------

    def sizeHint(self) -> QSize:
        return self._calc_size()

    def minimumSizeHint(self) -> QSize:
        return self._calc_size()

    def _calc_size(self) -> QSize:
        """根据当前内容计算按钮尺寸"""
        fm = QFontMetrics(self.font())
        h = self.MIN_HEIGHT

        text = self.text()
        if text:
            text_w = fm.horizontalAdvance(text)
            # 图标 + 间距 + 文字 + 内边距
            w = self.MAIN_ICON_SIZE + 8 + text_w + 24
        else:
            w = self.MIN_WIDTH

        return QSize(w, h)

    # ---- 绘制 ------------------------------------------------------

    # 箭头已移除，直接使用 QPushButton 默认绘制