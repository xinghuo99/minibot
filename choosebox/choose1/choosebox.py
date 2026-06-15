# -*- coding: utf-8 -*-
"""下拉/上拉选择框组件 —— 基于 QPushButton + QMenu 实现"""

from PyQt5.QtCore import pyqtSignal, QPoint, QRect, QSize, Qt
from PyQt5.QtGui import QFontMetrics, QIcon, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QMenu,
    QPushButton,
    QStyle,
    QStyleOptionButton,
    QStyleOptionMenuItem,
    QWidget,
)


class ChooseBox(QPushButton):
    """自定义下拉/上拉选择框

    信号:
        currentIndexChanged(int):  当前选中索引变化时发射
        currentTextChanged(str):   当前选中文本变化时发射
        activated(int):            用户点击菜单项时发射（即使索引未变）
    """

    currentIndexChanged = pyqtSignal(int)
    currentTextChanged = pyqtSignal(str)
    activated = pyqtSignal(int)

    # 箭头图标宽度（含留白）
    ARROW_WIDTH = 20
    # 文字边距
    TEXT_MARGIN = 8
    # 默认图标尺寸
    ICON_SIZE = 16

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self._items: list[str] = []
        self._current_index: int = -1
        self._placeholder: str = ""
        self._drop_up: bool = False
        self._default_icon: QIcon | None = None

        self._menu = QMenu(self)
        self._menu.aboutToShow.connect(self._on_menu_about_to_show)
        self._menu.triggered.connect(self._on_action_triggered)

        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self._on_clicked)

        self._apply_default_icon()
        self._refresh_text()

    # ---- 图标 ----------------------------------------------------

    def setDefaultIcon(self, icon: QIcon) -> None:
        """设置按钮左侧的默认图标"""
        self._default_icon = icon
        self._apply_default_icon()

    def defaultIcon(self) -> QIcon | None:
        """返回当前默认图标"""
        return self._default_icon

    # ---- 公共接口 --------------------------------------------------

    def addItem(self, text: str) -> None:
        """添加一个选项"""
        self._items.append(text)

    def addItems(self, texts: list[str]) -> None:
        """批量添加选项"""
        self._items.extend(texts)

    def insertItem(self, index: int, text: str) -> None:
        """在指定位置插入选项"""
        self._items.insert(index, text)

    def removeItem(self, index: int) -> None:
        """移除指定位置的选项"""
        if 0 <= index < len(self._items):
            del self._items[index]
            if self._current_index == index:
                self._current_index = -1
                self._refresh_text()
                self.currentIndexChanged.emit(-1)
                self.currentTextChanged.emit("")
            elif self._current_index > index:
                self._current_index -= 1

    def clear(self) -> None:
        """清空所有选项"""
        self._items.clear()
        self._current_index = -1
        self._refresh_text()
        self.currentIndexChanged.emit(-1)
        self.currentTextChanged.emit("")

    def count(self) -> int:
        """返回选项总数"""
        return len(self._items)

    # ---- 当前选中 --------------------------------------------------

    def setCurrentIndex(self, index: int) -> None:
        """设置当前选中索引，-1 表示不选中任何项"""
        if index != self._current_index and -1 <= index < len(self._items):
            self._current_index = index
            self._refresh_text()
            self.currentIndexChanged.emit(self._current_index)
            self.currentTextChanged.emit(self.currentText())

    def currentIndex(self) -> int:
        """返回当前选中索引，无选中时返回 -1"""
        return self._current_index

    def setCurrentText(self, text: str) -> None:
        """根据文本设置选中项"""
        try:
            idx = self._items.index(text)
        except ValueError:
            return
        self.setCurrentIndex(idx)

    def currentText(self) -> str:
        """返回当前选中文本"""
        if 0 <= self._current_index < len(self._items):
            return self._items[self._current_index]
        return ""

    def itemText(self, index: int) -> str:
        """返回指定索引的文本"""
        if 0 <= index < len(self._items):
            return self._items[index]
        return ""

    def itemData(self, index: int) -> str:
        """与 itemText 相同，兼容 QComboBox 接口"""
        return self.itemText(index)

    # ---- 占位文本 --------------------------------------------------

    def setPlaceholderText(self, text: str) -> None:
        """设置占位文本（无选中项时显示）"""
        self._placeholder = text
        self._refresh_text()

    def placeholderText(self) -> str:
        return self._placeholder

    # ---- 方向 -----------------------------------------------------

    def autoDirection(self) -> None:
        """根据按钮在屏幕上的位置自动选择下拉或上拉"""
        btn_rect: QRect = self.rect()
        btn_bottom = self.mapToGlobal(QPoint(0, btn_rect.bottom())).y()
        btn_top = self.mapToGlobal(QPoint(0, 0)).y()
        screen_rect = QApplication.primaryScreen().availableGeometry()

        space_below = screen_rect.bottom() - btn_bottom
        space_above = btn_top - screen_rect.top()

        # 估算菜单高度
        menu_height = min(len(self._items) * 28, 400) if self._items else 100

        if space_below >= menu_height:
            self._drop_up = False
        elif space_above >= menu_height:
            self._drop_up = True
        else:
            self._drop_up = space_above > space_below

    # ---- 内部 ------------------------------------------------------

    def _apply_default_icon(self) -> None:
        """应用默认图标：若用户未设置，使用系统内置列表图标"""
        if self._default_icon is not None:
            self.setIcon(self._default_icon)
            self.setIconSize(QSize(self.ICON_SIZE, self.ICON_SIZE))
        else:
            # 使用系统主题的内置「列表」图标作为默认
            pixmap = self.style().standardIcon(
                QStyle.SP_FileDialogContentsView
            ).pixmap(self.ICON_SIZE, self.ICON_SIZE)
            self.setIcon(QIcon(pixmap))
            self.setIconSize(QSize(self.ICON_SIZE, self.ICON_SIZE))

    def _refresh_text(self) -> None:
        if self._current_index >= 0:
            self.setText(self._items[self._current_index])
        elif self._placeholder:
            self.setText(self._placeholder)
        else:
            self.setText("")

    def _on_clicked(self) -> None:
        self.autoDirection()
        self._build_menu()
        self._show_menu()

    def _on_menu_about_to_show(self) -> None:
        """菜单显示前标记当前选中项"""
        for i, action in enumerate(self._menu.actions()):
            if i == self._current_index:
                font = action.font()
                font.setBold(True)
                action.setFont(font)
                action.setIcon(self.style().standardIcon(QStyle.SP_DialogApplyButton))
            else:
                font = action.font()
                font.setBold(False)
                action.setFont(font)
                action.setIcon(self.style().standardIcon(QStyle.SP_DialogIgnoreButton))

    def _build_menu(self) -> None:
        """重建菜单项"""
        self._menu.clear()
        for i, text in enumerate(self._items):
            action = self._menu.addAction(text)
            action.setData(i)

    def _show_menu(self) -> None:
        btn_rect = self.rect()

        if self._drop_up:
            pos = self.mapToGlobal(QPoint(0, 0))
            menu_height = self._menu.sizeHint().height()
            pos.setY(pos.y() - menu_height)
        else:
            pos = self.mapToGlobal(QPoint(0, btn_rect.bottom()))

        self._menu.setFixedWidth(self.width())
        self._menu.popup(pos)

    def _on_action_triggered(self, action) -> None:
        idx = action.data()
        if isinstance(idx, int):
            self.activated.emit(idx)
            if idx != self._current_index:
                self._current_index = idx
                self._refresh_text()
                self.currentIndexChanged.emit(idx)
                self.currentTextChanged.emit(self._items[idx])

    # ---- 绘制 ------------------------------------------------------

    def paintEvent(self, event):
        # 1) 让 QPushButton 先绘制背景和边框
        super().paintEvent(event)

        # 2) 裁剪出右侧箭头区域，绘制菜单箭头
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        w = self.width()
        h = self.height()

        # 箭头颜色
        if self.isEnabled():
            arrow_color = self.palette().buttonText().color()
        else:
            arrow_color = self.palette().mid().color()

        painter.setPen(QPen(arrow_color, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))

        cx = w - self.ARROW_WIDTH // 2
        cy = h // 2
        r = 4  # 箭头半宽

        if self._drop_up:
            # 上箭头 ▼（表示点击会向上弹出）
            painter.drawLine(cx - r, cy + 2, cx, cy - 2)
            painter.drawLine(cx, cy - 2, cx + r, cy + 2)
        else:
            # 下箭头
            painter.drawLine(cx - r, cy - 2, cx, cy + 2)
            painter.drawLine(cx, cy + 2, cx + r, cy - 2)

        painter.end()
    def sizeHint(self):
        sh = super().sizeHint()
        fm = QFontMetrics(self.font())
        text_width = fm.horizontalAdvance(self.text()) if self.text() else fm.horizontalAdvance(self._placeholder or "    ")
        # 图标宽度 + 图标与文字间距 + 文字 + 箭头区域 + 左右边距
        icon_width = self.ICON_SIZE + 6 if self.icon() and not self.icon().isNull() else 0
        min_w = icon_width + text_width + self.ARROW_WIDTH + self.TEXT_MARGIN * 2 + 12
        return sh.expandedTo(sh.__class__(max(sh.width(), min_w), sh.height()))
