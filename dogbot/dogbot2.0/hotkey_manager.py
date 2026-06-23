"""
全局快捷键管理器 - 使用 Windows 低层键盘钩子实现事件驱动
支持 CTRL 单击（唤醒/隐藏）和 SHIFT 单击（钉住/解除）
纯事件驱动，零轮询，CPU消耗极低
"""
import ctypes
from ctypes import wintypes, CFUNCTYPE

from PyQt5.QtCore import QObject, pyqtSignal


# ── Windows API 常量 ──────────────────────────────────────
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105

VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_LSHIFT = 0xA0
VK_RSHIFT = 0xA1

# ── KBDLLHOOKSTRUCT 结构体 ─────────────────────────────────

class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


# 钩子回调函数类型
HOOKPROC = CFUNCTYPE(ctypes.c_long, ctypes.c_int, wintypes.WPARAM, ctypes.POINTER(KBDLLHOOKSTRUCT))

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# 修复 64 位指针截断：显式声明返回值和参数类型
user32.SetWindowsHookExW.restype = ctypes.c_void_p
user32.SetWindowsHookExW.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD]

user32.UnhookWindowsHookEx.restype = wintypes.BOOL
user32.UnhookWindowsHookEx.argtypes = [ctypes.c_void_p]

user32.CallNextHookEx.restype = ctypes.c_long
user32.CallNextHookEx.argtypes = [ctypes.c_void_p, ctypes.c_int, wintypes.WPARAM, ctypes.c_void_p]

kernel32.GetModuleHandleW.restype = ctypes.c_void_p
kernel32.GetModuleHandleW.argtypes = [ctypes.c_void_p]


class HotkeyManager(QObject):
    """
    事件驱动热键管理器
    使用 SetWindowsHookEx(WH_KEYBOARD_LL) 注册低层键盘钩子，
    按键事件由系统回调触发，无需轮询线程。
    """
    toggle_requested = pyqtSignal()   # CTRL 单击 → 唤醒/隐藏
    pin_requested = pyqtSignal()      # SHIFT 单击 → 钉住/解除

    def __init__(self):
        super().__init__()
        self._hook_id: int | None = None
        self._hook_proc = None  # 保持CFUNCTYPE引用，防止被GC
        self._running = False

        # 按键状态追踪：确保"单独按下后松开"才触发
        self._ctrl_down = False
        self._ctrl_alone = True   # CTRL按下期间无其他键
        self._shift_down = False
        self._shift_alone = True

    # ── 公开接口 ──────────────────────────────────────────

    def start(self):
        """安装键盘钩子，开始监听"""
        if self._running:
            return
        self._running = True
        self._hook_proc = HOOKPROC(self._hook_callback)
        self._hook_id = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL,
            self._hook_proc,
            kernel32.GetModuleHandleW(None),
            0,
        )
        if not self._hook_id:
            self._running = False
            raise OSError("SetWindowsHookExW 失败")
        print("[热键] CTRL / SHIFT 全局快捷键已就绪（事件驱动，零轮询）")

    def stop(self):
        """卸载键盘钩子"""
        self._running = False
        if self._hook_id:
            user32.UnhookWindowsHookEx(self._hook_id)
            self._hook_id = None
        self._hook_proc = None

    # ── 钩子回调 ──────────────────────────────────────────

    def _hook_callback(self, nCode: int, wParam: int, lParam) -> int:
        """低层键盘钩子回调（由系统在消息循环中调用）"""
        if nCode < 0:
            return user32.CallNextHookEx(self._hook_id, nCode, wParam, lParam)

        try:
            kb = lParam.contents
            vk = kb.vkCode
            is_down = wParam in (WM_KEYDOWN, WM_SYSKEYDOWN)
            is_up = wParam in (WM_KEYUP, WM_SYSKEYUP)

            # ── CTRL 处理 ──
            if vk in (VK_LCONTROL, VK_RCONTROL):
                if is_down:
                    self._ctrl_down = True
                    self._ctrl_alone = True
                    # 如果 SHIFT 已按下，则互相标记为非单独
                    if self._shift_down:
                        self._shift_alone = False
                        self._ctrl_alone = False
                elif is_up:
                    if self._ctrl_down and self._ctrl_alone:
                        self.toggle_requested.emit()
                    self._ctrl_down = False

            # ── SHIFT 处理 ──
            elif vk in (VK_LSHIFT, VK_RSHIFT):
                if is_down:
                    self._shift_down = True
                    self._shift_alone = True
                    # 如果 CTRL 已按下，则 CTRL 也不是"单独"的
                    if self._ctrl_down:
                        self._ctrl_alone = False
                        self._shift_alone = False
                elif is_up:
                    if self._shift_down and self._shift_alone:
                        self.pin_requested.emit()
                    self._shift_down = False

            # ── 其他键：标记"非单独按下" ──
            else:
                if is_down:
                    if self._ctrl_down:
                        self._ctrl_alone = False
                    if self._shift_down:
                        self._shift_alone = False

        except Exception:
            pass  # 钩子回调中不能抛出异常

        return user32.CallNextHookEx(self._hook_id, nCode, wParam, lParam)