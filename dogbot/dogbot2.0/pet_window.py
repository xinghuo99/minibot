"""
桌面宠物窗口 - 透明无边框的宠物显示窗口
启动播放 begin.gif，左键单击播放 click，悬停播放 left/right，空闲播放 happy*
支持拖拽、右键菜单、随机位置移动、风格切换（白色小狗/黄色小狗）
"""
import os
import random
import tempfile
import atexit

from PyQt5.QtWidgets import QWidget, QLabel, QMenu, QApplication, QAction
from PyQt5.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QMovie, QMouseEvent, QEnterEvent, QCursor

import gifs
import gifs2


class PetWindow(QWidget):
    """桌面宠物主窗口"""

    def __init__(self):
        super().__init__()
        self._drag_pos: QPoint | None = None
        self._scale = 0.3
        self._mode = "begin"  # 'begin' | 'idle' | 'click' | 'hover'
        self._style = "white"  # 'white' (gifs2) | 'yellow' (gifs)
        self._pinned = False  # 是否钉在右下角
        self._current_movie: QMovie | None = None
        self._click_timer: QTimer | None = None
        self._idle_timer: QTimer | None = None
        self._pos_timer: QTimer | None = None
        self._last_tmp_path: str | None = None    # 上一次临时文件路径，用于清理

        # 临时文件目录，用于写入GIF数据供QMovie播放
        self._tmp_dir = tempfile.mkdtemp(prefix="pet_gifs_")
        atexit.register(self._cleanup_tmp)

        print(f"[GIF] 黄色小狗: {len(gifs._ALL_GIFS)} 个GIF")
        print(f"[GIF] 白色小狗: {len(gifs2.G2_ALL_GIFS)} 个GIF")
        print(f"[GIF] 当前风格: 白色小狗")

        self._setup_window()
        self._setup_label()
        self._setup_menu()
        self._setup_position_timer()

        self._play_begin()

    # ── 窗口设置 ──────────────────────────────────────────────

    def _setup_window(self):
        """配置无边框透明置顶窗口"""
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.Tool
            | Qt.WindowStaysOnTopHint
            | Qt.SubWindow
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setAutoFillBackground(False)

        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.right() - 80, geo.bottom() - 80)

        self.resize(60, 60)

    def _setup_label(self):
        """创建用于播放GIF的QLabel"""
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("background: transparent;")
        self.label.setScaledContents(True)
        self.label.resize(self.size())
        self.label.installEventFilter(self)

        self.setMouseTracking(True)
        self.label.setMouseTracking(True)

    # ── 右键菜单 ───────────────────────────────────────────────

    def _setup_menu(self):
        """构建右键菜单"""
        menu_style = """
            QMenu {
                background-color: #8B2500;
                border: 1px solid #6B1C00;
                border-radius: 6px;
                padding: 4px;
                color: #00FF00;
            }
            QMenu::item {
                padding: 6px 24px;
                border-radius: 4px;
                color: #00FF00;
            }
            QMenu::item:selected {
                background-color: #A0522D;
                color: #00FF00;
            }
            QMenu::item:disabled {
                color: #556B2F;
            }
            QMenu::separator {
                height: 1px;
                background: #6B1C00;
                margin: 4px 8px;
            }
        """
        self.menu = QMenu(self)
        self.menu.setStyleSheet(menu_style)

        # 风格切换子菜单
        self.style_menu = QMenu("切换风格", self)
        self.style_menu.setStyleSheet(menu_style)

        self._white_action = QAction("白色小狗", self)
        self._white_action.triggered.connect(lambda: self._switch_style("white"))
        self.style_menu.addAction(self._white_action)

        self._yellow_action = QAction("黄色小狗", self)
        self._yellow_action.triggered.connect(lambda: self._switch_style("yellow"))
        self.style_menu.addAction(self._yellow_action)

        self.menu.addMenu(self.style_menu)

        self.menu.addSeparator()

        close_action = QAction("关闭宠物", self)
        close_action.triggered.connect(self._on_close)
        self.menu.addAction(close_action)

    def _switch_style(self, style: str):
        """切换风格：white(白色小狗=gifs2) 或 yellow(黄色小狗=gifs)"""
        if self._style == style:
            return
        self._style = style
        print(f"[GIF] 切换风格: {'白色小狗' if style == 'white' else '黄色小狗'}")
        # 重启当前动画
        if self._mode == "begin":
            self._play_begin()
        elif self._mode == "hover":
            self._enter_hover()
        elif self._mode == "click":
            self._play_click()
        else:
            self._start_idle()

    # ── 当前风格的GIF数据 ─────────────────────────────────────

    def _gif_module(self):
        """返回当前风格对应的gif模块"""
        return gifs2 if self._style == "white" else gifs

    def _current_begin(self):
        return self._gif_module().BEGIN_GIF if self._style == "yellow" else self._gif_module().G2_BEGIN_GIF

    def _current_happy_list(self):
        m = self._gif_module()
        return m.G2_HAPPY_GIFS if self._style == "white" else m._HAPPY_GIFS

    def _current_click_list(self):
        m = self._gif_module()
        return m.G2_CLICK_GIFS if self._style == "white" else m._CLICK_GIFS

    def _current_hover_list(self):
        m = self._gif_module()
        return m.G2_HOVER_GIFS if self._style == "white" else m._HOVER_GIFS

    # ── GIF 播放核心 ───────────────────────────────────────────

    def _play_movie(self, gif_data: bytes):
        """播放GIF数据：写入临时文件后用QMovie播放"""
        # 停止并释放旧Movie
        if self._current_movie:
            self._current_movie.stop()
            self._current_movie.setFileName("")  # 释放文件句柄
            self._current_movie.deleteLater()
            self._current_movie = None

        # 清理上一次的临时文件
        if self._last_tmp_path and os.path.exists(self._last_tmp_path):
            try:
                os.remove(self._last_tmp_path)
            except OSError:
                pass

        # 写入临时文件
        fd, path = tempfile.mkstemp(suffix=".gif", dir=self._tmp_dir)
        with os.fdopen(fd, "wb") as f:
            f.write(gif_data)
        self._last_tmp_path = path

        self._current_movie = QMovie(path)
        self._current_movie.setCacheMode(QMovie.CacheAll)
        self._current_movie.start()
        self.label.setMovie(self._current_movie)

        # 根据GIF大小调整窗口
        fw = int(self._current_movie.frameRect().width() * self._scale)
        fh = int(self._current_movie.frameRect().height() * self._scale)
        if fw > 0 and fh > 0:
            self.label.resize(fw, fh)
            self.resize(fw, fh)

    def _play_begin(self):
        """启动时播放 begin.gif，完整播放结束后进入 idle 模式"""
        self._mode = "begin"

        begin_data = self._current_begin()
        if begin_data:
            self._play_movie(begin_data)
            if self._current_movie:
                # 监听帧变化，播放完所有帧后切换到 idle
                self._current_movie.frameChanged.connect(self._on_begin_frame)
        else:
            # 没有 begin GIF，直接进入 idle
            self._start_idle()

    def _on_begin_frame(self, frame: int):
        """begin GIF 帧变化回调：播放完最后一帧后切换到 idle"""
        if self._mode != "begin" or self._current_movie is None:
            return
        total = self._current_movie.frameCount()
        if total > 0 and frame >= total - 1:
            # 断开信号避免重复触发
            try:
                self._current_movie.frameChanged.disconnect(self._on_begin_frame)
            except TypeError:
                pass
            self._start_idle()

    def _start_idle(self):
        """开始空闲模式：随机播放 happy*.gif"""
        self._mode = "idle"
        happy_list = self._current_happy_list()
        if happy_list:
            self._play_movie(random.choice(happy_list))
        self._schedule_next_idle()

    def timerEvent(self, event):
        """处理定时器事件（当前无自定义定时器，由 super 处理）"""
        super().timerEvent(event)

    def _schedule_next_idle(self):
        """安排下一次空闲GIF切换（4-8秒）"""
        if self._idle_timer:
            self._idle_timer.stop()
        self._idle_timer = QTimer(self)
        self._idle_timer.setSingleShot(True)
        self._idle_timer.timeout.connect(self._play_next_idle)
        interval = random.randint(4000, 8000)
        self._idle_timer.start(interval)

    def _play_next_idle(self):
        """切换到下一个随机 happy GIF"""
        if self._mode != "idle":
            return
        happy_list = self._current_happy_list()
        if happy_list:
            self._play_movie(random.choice(happy_list))
        self._schedule_next_idle()

    def _play_click(self):
        """左键单击：随机播放 click GIF"""
        click_list = self._current_click_list()
        if not click_list:
            return
        self._mode = "click"
        self._play_movie(random.choice(click_list))

        if self._click_timer:
            self._click_timer.stop()
        self._click_timer = QTimer(self)
        self._click_timer.setSingleShot(True)
        self._click_timer.timeout.connect(self._restore_from_click)
        self._click_timer.start(random.randint(2000, 3000))

    def _restore_from_click(self):
        """从单击动画恢复"""
        if self._mode == "click":
            pos = self.mapFromGlobal(QCursor.pos())
            if self.rect().contains(pos):
                self._enter_hover()
            else:
                self._start_idle()

    def _enter_hover(self):
        """进入悬停模式：随机播放 left/right"""
        hover_list = self._current_hover_list()
        if not hover_list:
            return
        self._mode = "hover"
        self._play_movie(random.choice(hover_list))

    def _leave_hover(self):
        """离开悬停：恢复 idle"""
        self._start_idle()

    # ── 随机位置移动 ───────────────────────────────────────────

    def _setup_position_timer(self):
        """启动随机位置移动定时器"""
        self._pos_timer = QTimer(self)
        self._pos_timer.setSingleShot(True)
        self._pos_timer.timeout.connect(self._move_to_random_position)
        self._schedule_next_position()

    def _schedule_next_position(self):
        """安排下一次位置移动（10-20秒）"""
        if self._pos_timer:
            interval = random.randint(10000, 20000)
            self._pos_timer.start(interval)

    def _move_to_random_position(self):
        """移动到目标位置：钉住时仅右下角区域，否则全屏8个位置之一"""
        if self._drag_pos is not None:
            self._schedule_next_position()
            return

        screen = QApplication.primaryScreen()
        if not screen:
            self._schedule_next_position()
            return

        geo = screen.availableGeometry()
        pw = self.width()
        ph = self.height()

        if self._pinned:
            # 钉住模式：仅右下角区域活动
            corner_w = 300
            corner_h = 300
            left = max(geo.left(), geo.right() - corner_w)
            top = max(geo.top(), geo.bottom() - corner_h)
            right = max(left, geo.right() - pw)
            bottom = max(top, geo.bottom() - ph)
            target_x = random.randint(left, right) if right > left else left
            target_y = random.randint(top, bottom) if bottom > top else top
        else:
            # 全屏模式：8个位置之一
            positions = [
                (geo.left(), geo.top()),
                (geo.right() - pw, geo.top()),
                (geo.left(), geo.bottom() - ph),
                (geo.right() - pw, geo.bottom() - ph),
                ((geo.left() + geo.right()) // 2 - pw // 2, geo.top()),
                ((geo.left() + geo.right()) // 2 - pw // 2, geo.bottom() - ph),
                (geo.left(), (geo.top() + geo.bottom()) // 2 - ph // 2),
                (geo.right() - pw, (geo.top() + geo.bottom()) // 2 - ph // 2),
            ]
            target_x, target_y = random.choice(positions)

        self._anim = QPropertyAnimation(self, b"pos")
        self._anim.setDuration(800)
        self._anim.setStartValue(self.pos())
        self._anim.setEndValue(QPoint(target_x, target_y))
        self._anim.setEasingCurve(QEasingCurve.InOutQuad)
        self._anim.start()

        self._schedule_next_position()

    # ── 钉住功能 ───────────────────────────────────────────────

    def toggle_pin(self):
        """切换钉住状态：仅在宠物可见时生效"""
        if not self.isVisible():
            return
        self._pinned = not self._pinned
        if self._pinned:
            print("[宠物] 已钉住 - 锁定在屏幕右下角")
            self._move_to_corner()
        else:
            print("[宠物] 已解除钉住 - 恢复全屏活动")
            self._move_to_random_position()

    def _move_to_corner(self):
        """立即移动到屏幕右下角"""
        screen = QApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()
        self.move(geo.right() - self.width() - 20,
                  geo.bottom() - self.height() - 20)

    # ── 鼠标事件 ───────────────────────────────────────────────

    def eventFilter(self, obj, event):
        """事件过滤器：将 label 上的鼠标事件转发到 PetWindow 处理"""
        from PyQt5.QtCore import QEvent
        if obj is self.label:
            etype = event.type()
            if etype == QEvent.MouseButtonPress:
                self.mousePressEvent(event)
                return True
            elif etype == QEvent.MouseMove:
                self.mouseMoveEvent(event)
                return True
            elif etype == QEvent.MouseButtonRelease:
                self.mouseReleaseEvent(event)
                return True
            elif etype == QEvent.MouseButtonDblClick:
                self.mouseDoubleClickEvent(event)
                return True
            elif etype == QEvent.Enter:
                self.enterEvent(event)
                return True
            elif etype == QEvent.Leave:
                self.leaveEvent(event)
                return True
        return super().eventFilter(obj, event)

    def enterEvent(self, event):
        """鼠标进入宠物区域 → 如果处于 idle 模式则切换到 hover"""
        if self._mode == "idle":
            self._enter_hover()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开宠物区域 → 恢复 idle"""
        if self._mode == "hover":
            self._leave_hover()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """鼠标按下：左键单击播放 click GIF，右键弹出菜单"""
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            if self._mode in ("idle", "hover"):
                self._play_click()
        elif event.button() == Qt.RightButton:
            self.menu.exec(event.globalPos())

    def mouseMoveEvent(self, event):
        """鼠标移动：拖拽宠物"""
        if self._drag_pos is not None and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        """鼠标释放：结束拖拽"""
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event):
        """双击宠物隐藏"""
        if event.button() == Qt.LeftButton:
            self.hide()

    # ── 辅助 ────────────────────────────────────────────────────

    def _on_close(self):
        """关闭宠物并退出程序"""
        self._stop_all_timers()
        if self._current_movie is not None:
            try:
                self._current_movie.stop()
            except RuntimeError:
                pass
        self._cleanup_tmp()
        QApplication.quit()

    def _stop_all_timers(self):
        """停止所有定时器"""
        for timer in [self._click_timer, self._idle_timer, self._pos_timer]:
            if timer:
                timer.stop()

    def _cleanup_tmp(self):
        """清理临时文件"""
        import shutil
        # 先释放当前Movie（C++对象可能已被Qt销毁）
        if self._current_movie is not None:
            try:
                self._current_movie.stop()
                self._current_movie.setFileName("")
            except RuntimeError:
                pass  # C++对象已被销毁
            self._current_movie = None
        if self._tmp_dir and os.path.isdir(self._tmp_dir):
            shutil.rmtree(self._tmp_dir, ignore_errors=True)

    def toggle_visibility(self):
        """切换显示/隐藏"""
        if self.isVisible():
            self.hide()
        else:
            self._play_begin()
            self.show()

    def closeEvent(self, event):
        """窗口关闭时清理"""
        self._stop_all_timers()
        if self._current_movie is not None:
            try:
                self._current_movie.stop()
            except RuntimeError:
                pass
        self._cleanup_tmp()
        super().closeEvent(event)