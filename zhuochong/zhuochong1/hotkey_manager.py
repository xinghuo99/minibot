"""
全局快捷键管理器 - 使用 keyboard 库实现 CTRL+CTRL 双击唤醒
"""
import time
import threading

from PyQt6.QtCore import QObject, pyqtSignal


try:
    import keyboard
    HAS_KEYBOARD = True
except ImportError:
    HAS_KEYBOARD = False
    print("[警告] 未安装 keyboard 库，全局快捷键不可用。请执行: pip install keyboard")


class HotkeyManager(QObject):
    """
    CTRL+CTRL 双击热键管理器
    在单独的线程中监听键盘事件，检测到双击Ctrl后触发信号
    """
    # 信号：通知主线程切换宠物可见性
    toggle_requested = pyqtSignal()

    def __init__(self, double_press_interval: float = 0.5):
        """
        double_press_interval: 双击检测间隔（秒），默认500ms
        """
        super().__init__()
        self._double_press_interval = double_press_interval
        self._last_ctrl_time = 0.0
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    def start(self):
        """启动热键监听线程"""
        if not HAS_KEYBOARD:
            print("[错误] keyboard 库未安装，无法启动快捷键监听")
            return
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()
        print("[热键] CTRL+CTRL 全局快捷键已就绪")

    def stop(self):
        """停止热键监听"""
        self._running = False
        if HAS_KEYBOARD:
            try:
                keyboard.unhook_all()
            except Exception:
                pass

    def _listen_loop(self):
        """后台监听循环：检测CTRL键按下"""
        def on_ctrl_press(event):
            if not self._running:
                return
            with self._lock:
                now = time.time()
                if now - self._last_ctrl_time <= self._double_press_interval:
                    # 双击Ctrl → 触发信号
                    self.toggle_requested.emit()
                    self._last_ctrl_time = 0.0  # 重置，防止三连触发
                else:
                    self._last_ctrl_time = now

        keyboard.on_press_key("ctrl", on_ctrl_press)

        # 保持线程存活
        while self._running:
            time.sleep(0.1)