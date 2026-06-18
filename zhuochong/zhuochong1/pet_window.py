"""
桌面宠物窗口 - 透明无边框的宠物显示窗口
支持拖拽、鼠标悬停表情切换、右键菜单、多动作动画、随机GIF、随机位置
"""
import os
import random
import glob

from PyQt6.QtWidgets import QWidget, QLabel, QMenu, QApplication, QFileDialog
from PyQt6.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QMovie, QAction, QMouseEvent, QEnterEvent

from skin_manager import SkinManager, ANIMATION_TYPES

# 动作名称中文映射
ACTION_NAMES = {
    "idle": "发呆",
    "hover": "开心",
    "dance": "跳舞",
    "shake": "摇头",
    "run": "跑步",
    "eat": "吃饭",
    "sleep": "睡觉",
}


class PetWindow(QWidget):
    """桌面宠物主窗口"""

    def __init__(self, skin_manager: SkinManager, current_skin: str = "line_puppy"):
        super().__init__()
        self.skin_manager = skin_manager
        self.current_skin = current_skin
        self._drag_pos: QPoint | None = None
        self._scale = 0.3

        # 所有动画播放器
        self._movies: dict[str, QMovie] = {}
        self._current_anim = "idle"
        self._is_hover = False
        self._action_timer: QTimer | None = None  # 动作恢复定时器

        # 随机GIF相关
        self._gifs_dir = os.path.join(os.path.dirname(__file__), "gifs")
        self._gif_files: list[str] = []
        self._random_gif_movie: QMovie | None = None
        self._is_playing_random = False
        self._random_gif_timer: QTimer | None = None
        self._random_pos_timer: QTimer | None = None
        self._scan_gif_files()

        self._setup_window()
        self._setup_label()
        self._setup_menu()
        self._setup_random_behaviors()

        self._load_skin(self.current_skin)

    # ── 窗口设置 ──────────────────────────────────────────────

    def _setup_window(self):
        """配置无边框透明置顶窗口"""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAutoFillBackground(False)

        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.right() - 80, geo.bottom() - 80)

        self.resize(60, 60)

    # ── GIF 标签 ───────────────────────────────────────────────

    def _setup_label(self):
        """创建用于播放GIF的QLabel"""
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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

        # 宠物动作子菜单
        self.action_menu = QMenu("宠物动作", self)
        self.action_menu.setStyleSheet(menu_style)
        self.menu.addMenu(self.action_menu)

        self.menu.addSeparator()

        # 更换皮肤子菜单
        self.skin_menu = QMenu("更换皮肤", self)
        self.skin_menu.setStyleSheet(menu_style)
        self.menu.addMenu(self.skin_menu)

        self.menu.addSeparator()

        # 关闭宠物
        close_action = QAction("关闭宠物", self)
        close_action.triggered.connect(self._on_close)
        self.menu.addAction(close_action)

    def _refresh_action_menu(self):
        """刷新动作子菜单"""
        self.action_menu.clear()
        for anim_type in ANIMATION_TYPES:
            if anim_type == "hover":
                continue  # hover 是悬停自动触发，不显示在菜单中
            if anim_type not in self._movies:
                continue
            label = ACTION_NAMES.get(anim_type, anim_type)
            action = QAction(label, self)
            if anim_type == self._current_anim:
                action.setEnabled(False)
            action.triggered.connect(lambda checked, t=anim_type: self._play_action(t))
            self.action_menu.addAction(action)

    def _refresh_skin_menu(self):
        """刷新皮肤子菜单"""
        self.skin_menu.clear()
        skins = self.skin_manager.list_skins()
        for name in skins:
            action = QAction(name, self)
            if name == self.current_skin:
                action.setEnabled(False)
            action.triggered.connect(lambda checked, n=name: self._switch_skin(n))
            self.skin_menu.addAction(action)

        self.skin_menu.addSeparator()
        import_action = QAction("导入新皮肤...", self)
        import_action.triggered.connect(self._import_skin)
        self.skin_menu.addAction(import_action)

    # ── 皮肤加载与切换 ─────────────────────────────────────────

    def _load_skin(self, skin_name: str):
        """加载指定皮肤的所有动画"""
        # 停止所有旧动画
        for m in self._movies.values():
            m.stop()
        self._movies.clear()

        # 加载所有可用动画
        for anim_type in ANIMATION_TYPES:
            gif_path = self.skin_manager.get_gif_path(skin_name, anim_type)
            if gif_path is None:
                continue
            movie = QMovie(gif_path)
            movie.setCacheMode(QMovie.CacheMode.CacheAll)
            movie.start()
            self._movies[anim_type] = movie

        if "idle" not in self._movies:
            print(f"[警告] 皮肤 '{skin_name}' 缺少 idle.gif，无法加载")
            return

        # 根据首个GIF实际大小 × 缩放比例调整窗口
        first_movie = self._movies.get("idle")
        if first_movie and first_movie.frameRect().width() > 0:
            fw = int(first_movie.frameRect().width() * self._scale)
            fh = int(first_movie.frameRect().height() * self._scale)
            self.label.resize(fw, fh)
            self.resize(fw, fh)

        self._current_anim = "idle"
        self._is_hover = False
        self._update_movie()
        self._refresh_action_menu()
        self._refresh_skin_menu()

    def _switch_skin(self, skin_name: str):
        """切换到指定皮肤"""
        if skin_name == self.current_skin:
            return
        self.current_skin = skin_name
        self._load_skin(skin_name)

    def _import_skin(self):
        """从文件系统导入新皮肤"""
        folder = QFileDialog.getExistingDirectory(self, "选择皮肤文件夹（需包含 idle.gif 和 hover.gif）")
        if not folder:
            return
        skin_name = os.path.basename(folder.rstrip("/\\"))
        if not skin_name:
            skin_name = "imported_skin"
        ok = self.skin_manager.add_skin(skin_name, folder)
        if ok:
            self._refresh_skin_menu()
            self._switch_skin(skin_name)
        else:
            print(f"[错误] 导入皮肤失败，请确保文件夹包含 idle.gif 和 hover.gif")

    # ── 动作播放 ───────────────────────────────────────────────

    def _play_action(self, anim_type: str):
        """播放指定动作动画，结束后恢复 idle"""
        if anim_type not in self._movies:
            return
        self._current_anim = anim_type
        self._update_movie()
        self._refresh_action_menu()

        # 取消之前的定时器
        if self._action_timer:
            self._action_timer.stop()

        # 非 idle 动作播放 3 秒后自动恢复
        if anim_type != "idle":
            self._action_timer = QTimer(self)
            self._action_timer.setSingleShot(True)
            self._action_timer.timeout.connect(self._restore_idle)
            self._action_timer.start(3000)

    def _restore_idle(self):
        """恢复到 idle 动画"""
        self._current_anim = "idle"
        self._update_movie()
        self._refresh_action_menu()

    # ── 随机行为 ───────────────────────────────────────────────

    def _scan_gif_files(self):
        """扫描 gifs 文件夹中的 GIF 文件"""
        if os.path.isdir(self._gifs_dir):
            self._gif_files = glob.glob(os.path.join(self._gifs_dir, "*.gif"))
            print(f"[随机GIF] 扫描到 {len(self._gif_files)} 个GIF文件")

    def _setup_random_behaviors(self):
        """启动随机GIF和随机位置定时器"""
        if self._gif_files:
            self._random_gif_timer = QTimer(self)
            self._random_gif_timer.timeout.connect(self._play_random_gif)
            self._schedule_next_random_gif()

        self._random_pos_timer = QTimer(self)
        self._random_pos_timer.timeout.connect(self._move_to_random_position)
        self._schedule_next_random_pos()

    def _schedule_next_random_gif(self):
        """安排下一次随机GIF播放（间隔 6-12 秒）"""
        if self._random_gif_timer:
            interval = random.randint(6000, 12000)
            self._random_gif_timer.start(interval)

    def _schedule_next_random_pos(self):
        """安排下一次随机位置移动（间隔 10-20 秒）"""
        if self._random_pos_timer:
            interval = random.randint(10000, 20000)
            self._random_pos_timer.start(interval)

    def _play_random_gif(self):
        """从 gifs 文件夹随机选一个GIF播放"""
        if self._is_hover or self._drag_pos is not None:
            self._schedule_next_random_gif()
            return

        if not self._gif_files:
            self._schedule_next_random_gif()
            return

        gif_path = random.choice(self._gif_files)
        if not os.path.isfile(gif_path):
            self._schedule_next_random_gif()
            return

        # 停止之前的随机GIF
        if self._random_gif_movie:
            self._random_gif_movie.stop()

        self._random_gif_movie = QMovie(gif_path)
        self._random_gif_movie.setCacheMode(QMovie.CacheMode.CacheAll)
        self._random_gif_movie.start()

        # 根据GIF大小调整窗口
        fw = int(self._random_gif_movie.frameRect().width() * self._scale)
        fh = int(self._random_gif_movie.frameRect().height() * self._scale)
        if fw > 0 and fh > 0:
            self.label.resize(fw, fh)
            self.resize(fw, fh)

        self._is_playing_random = True
        self._update_movie()

        # 播放 3-5 秒后恢复
        play_duration = random.randint(3000, 5000)
        QTimer.singleShot(play_duration, self._restore_from_random_gif)

        # 安排下一次随机GIF
        self._schedule_next_random_gif()

    def _restore_from_random_gif(self):
        """从随机GIF恢复到皮肤的 idle 动画"""
        self._is_playing_random = False
        if self._random_gif_movie:
            self._random_gif_movie.stop()
            self._random_gif_movie = None

        # 恢复窗口大小为皮肤原始大小
        idle_movie = self._movies.get("idle")
        if idle_movie and idle_movie.frameRect().width() > 0:
            fw = int(idle_movie.frameRect().width() * self._scale)
            fh = int(idle_movie.frameRect().height() * self._scale)
            self.label.resize(fw, fh)
            self.resize(fw, fh)

        self._update_movie()

    def _move_to_random_position(self):
        """移动到桌面的随机位置（8个位置之一）"""
        if self._drag_pos is not None:
            self._schedule_next_random_pos()
            return

        screen = QApplication.primaryScreen()
        if not screen:
            self._schedule_next_random_pos()
            return

        geo = screen.availableGeometry()  # 不含任务栏
        pw = self.width()
        ph = self.height()

        # 8个位置: 4个角 + 4个边中点
        positions = [
            (geo.left(), geo.top()),                              # 左上角
            (geo.right() - pw, geo.top()),                        # 右上角
            (geo.left(), geo.bottom() - ph),                      # 左下角
            (geo.right() - pw, geo.bottom() - ph),                # 右下角
            ((geo.left() + geo.right()) // 2 - pw // 2, geo.top()),           # 上边中点
            ((geo.left() + geo.right()) // 2 - pw // 2, geo.bottom() - ph),   # 下边中点
            (geo.left(), (geo.top() + geo.bottom()) // 2 - ph // 2),          # 左边中点
            (geo.right() - pw, (geo.top() + geo.bottom()) // 2 - ph // 2),    # 右边中点
        ]

        target_x, target_y = random.choice(positions)

        # 使用动画平滑移动
        self._anim = QPropertyAnimation(self, b"pos")
        self._anim.setDuration(800)
        self._anim.setStartValue(self.pos())
        self._anim.setEndValue(QPoint(target_x, target_y))
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._anim.start()

        self._schedule_next_random_pos()

    # ── 鼠标事件 ───────────────────────────────────────────────

    def eventFilter(self, obj, event):
        """事件过滤器：将 label 上的鼠标事件转发到 PetWindow 处理"""
        from PyQt6.QtCore import QEvent
        if obj is self.label:
            etype = event.type()
            if etype == QEvent.Type.MouseButtonPress:
                self.mousePressEvent(event)
                return True
            elif etype == QEvent.Type.MouseMove:
                self.mouseMoveEvent(event)
                return True
            elif etype == QEvent.Type.MouseButtonRelease:
                self.mouseReleaseEvent(event)
                return True
            elif etype == QEvent.Type.MouseButtonDblClick:
                self.mouseDoubleClickEvent(event)
                return True
            elif etype == QEvent.Type.Enter:
                self.enterEvent(event)
                return True
            elif etype == QEvent.Type.Leave:
                self.leaveEvent(event)
                return True
        return super().eventFilter(obj, event)

    def enterEvent(self, event: QEnterEvent):
        """鼠标进入宠物区域 → 切换到 hover 表情"""
        self._is_hover = True
        self._update_movie()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开宠物区域 → 恢复当前动画"""
        self._is_hover = False
        self._update_movie()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下：记录拖拽起点 或 弹出右键菜单"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        elif event.button() == Qt.MouseButton.RightButton:
            self._refresh_action_menu()
            self._refresh_skin_menu()
            self.menu.exec(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动：拖拽宠物"""
        if self._drag_pos is not None and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放：结束拖拽"""
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """双击宠物隐藏"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.hide()

    # ── 辅助 ────────────────────────────────────────────────────

    def _update_movie(self):
        """根据当前悬停状态和动作更新GIF"""
        if self._is_hover and "hover" in self._movies:
            self.label.setMovie(self._movies["hover"])
        elif self._is_playing_random and self._random_gif_movie is not None:
            self.label.setMovie(self._random_gif_movie)
        elif self._current_anim in self._movies:
            self.label.setMovie(self._movies[self._current_anim])
        elif "idle" in self._movies:
            self.label.setMovie(self._movies["idle"])

    def _on_close(self):
        """关闭宠物并退出程序"""
        self._stop_all_timers()
        for m in self._movies.values():
            m.stop()
        if self._random_gif_movie:
            self._random_gif_movie.stop()
        QApplication.quit()

    def _stop_all_timers(self):
        """停止所有定时器"""
        if self._action_timer:
            self._action_timer.stop()
        if self._random_gif_timer:
            self._random_gif_timer.stop()
        if self._random_pos_timer:
            self._random_pos_timer.stop()

    def toggle_visibility(self):
        """切换显示/隐藏"""
        if self.isVisible():
            self.hide()
        else:
            self._load_skin(self.current_skin)
            self.show()

    def closeEvent(self, event):
        """窗口关闭时停止GIF"""
        self._stop_all_timers()
        for m in self._movies.values():
            m.stop()
        if self._random_gif_movie:
            self._random_gif_movie.stop()
        super().closeEvent(event)