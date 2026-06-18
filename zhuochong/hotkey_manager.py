"""
全局快捷键管理器 - 使用 GetAsyncKeyState 轮询实现双击热键
支持 CTRL+CTRL（唤醒/隐藏）和 SHIFT+SHIFT（钉住/解除）
无需管理员权限，不与IDE冲突
"""
import time
import threading
import ctypes
from ctypes import wintypes

from PyQt5.QtCore import QObject, pyqtSignal


# Windows API
user32 = ctypes.windll.user32
VK_CONTROL = 0x11
VK_SHIFT = 0x10


def _is_key_down(vk_code: int) -> bool:
    """检测按键是否当前被按下"""
    return bool(user32.GetAsyncKeyState(vk_code) & 0x8000)


class HotkeyManager(QObject):
    """
    双击热键管理器
    通过轮询 GetAsyncKeyState 检测按键双击，无需全局钩子
    """
    # 信号：通知主线程切换宠物可见性
    toggle_requested = pyqtSignal()
    # 信号：通知主线程切换钉住状态
    pin_requested = pyqtSignal()

    def __init__(self, double_press_interval: float = 0.5):
        """
        double_press_interval: 双击检测间隔（秒），默认500ms
        """
        super().__init__()
        self._double_press_interval = double_press_interval
        self._running = False
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

        # 各按键状态追踪
        self._last_ctrl_time = 0.0
        self._ctrl_was_up = True  # 上一次检测时Ctrl是否松开
        self._last_shift_time = 0.0
        self._shift_was_up = True

    def start(self):
        """启动热键监听线程"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        print("[热键] CTRL+CTRL / SHIFT+SHIFT 全局快捷键已就绪")

    def stop(self):
        """停止热键监听"""
        self._running = False

    def _poll_loop(self):
        """后台轮询循环：检测 CTRL 和 SHIFT 双击"""
        while self._running:
            time.sleep(0.02)  # 50Hz 轮询，足够检测快速双击

            with self._lock:
                now = time.time()

                # ── CTRL 双击检测 ──
                ctrl_down = _is_key_down(VK_CONTROL)
                if ctrl_down and self._ctrl_was_up:
                    # Ctrl 刚按下
                    if now - self._last_ctrl_time <= self._double_press_interval:
                        self.toggle_requested.emit()
                        self._last_ctrl_time = 0.0
                    else:
                        self._last_ctrl_time = now
                self._ctrl_was_up = not ctrl_down

                # ── SHIFT 双击检测 ──
                shift_down = _is_key_down(VK_SHIFT)
                if shift_down and self._shift_was_up:
                    # Shift 刚按下
                    if now - self._last_shift_time <= self._double_press_interval:
                        self.pin_requested.emit()
                        self._last_shift_time = 0.0
                    else:
                        self._last_shift_time = now
                self._shift_was_up = not shift_down