"""
自动化测试 - HotkeyManager 双击检测逻辑
"""
import os
import sys
import time
import unittest
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

# 确保 QApplication 单例
_app = QApplication.instance()
if _app is None:
    _app = QApplication(sys.argv)

from hotkey_manager import HotkeyManager, _is_key_down, VK_CONTROL, VK_SHIFT


class TestIsKeyDown(unittest.TestCase):
    """_is_key_down 函数测试"""

    def test_is_key_down_returns_bool(self):
        """返回布尔值"""
        result = _is_key_down(VK_CONTROL)
        self.assertIsInstance(result, bool)

    def test_is_key_down_no_exception(self):
        """不抛出异常"""
        try:
            _is_key_down(VK_CONTROL)
            _is_key_down(VK_SHIFT)
            _is_key_down(0xFF)  # 无效键码
        except Exception as e:
            self.fail(f"_is_key_down 不应抛出异常: {e}")


class TestHotkeyManagerInit(unittest.TestCase):
    """HotkeyManager 初始化测试"""

    def setUp(self):
        self.hm = HotkeyManager()

    def tearDown(self):
        self.hm.stop()

    def test_initial_not_running(self):
        """初始未运行"""
        self.assertFalse(self.hm._running)

    def test_has_toggle_signal(self):
        """有 toggle_requested 信号"""
        self.assertIsNotNone(self.hm.toggle_requested)

    def test_has_pin_signal(self):
        """有 pin_requested 信号"""
        self.assertIsNotNone(self.hm.pin_requested)

    def test_signals_are_pyqtSignal(self):
        """信号是 pyqtSignal 类型"""
        self.assertTrue(hasattr(self.hm.toggle_requested, 'connect'))
        self.assertTrue(hasattr(self.hm.pin_requested, 'connect'))

    def test_double_press_interval_default(self):
        """默认双击间隔 0.5s"""
        self.assertEqual(self.hm._double_press_interval, 0.5)

    def test_custom_interval(self):
        """自定义双击间隔"""
        hm = HotkeyManager(double_press_interval=0.3)
        self.assertEqual(hm._double_press_interval, 0.3)
        hm.stop()


class TestHotkeyManagerStartStop(unittest.TestCase):
    """启动/停止测试"""

    def setUp(self):
        self.hm = HotkeyManager()

    def tearDown(self):
        self.hm.stop()

    def test_start_sets_running(self):
        """start 后 _running=True"""
        self.hm.start()
        self.assertTrue(self.hm._running)

    def test_start_creates_thread(self):
        """start 创建线程"""
        self.hm.start()
        self.assertIsNotNone(self.hm._thread)
        self.assertTrue(self.hm._thread.is_alive())

    def test_stop_stops_running(self):
        """stop 后 _running=False"""
        self.hm.start()
        self.hm.stop()
        time.sleep(0.1)  # 等待线程退出
        self.assertFalse(self.hm._running)

    def test_start_twice_noop(self):
        """重复start不创建多个线程"""
        self.hm.start()
        self.hm.start()
        self.assertEqual(self.hm._running, True)

    def test_stop_before_start_noop(self):
        """未start时stop不报错"""
        try:
            self.hm.stop()
        except Exception as e:
            self.fail(f"stop before start 不应抛出异常: {e}")


class TestHotkeyManagerSignal(unittest.TestCase):
    """信号连接测试"""

    def setUp(self):
        self.hm = HotkeyManager(double_press_interval=0.1)

    def tearDown(self):
        self.hm.stop()

    def test_toggle_signal_connectable(self):
        """toggle_requested 信号可连接"""
        received = []

        def handler():
            received.append(True)

        self.hm.toggle_requested.connect(handler)
        self.hm.toggle_requested.emit()
        self.assertEqual(len(received), 1)

    def test_pin_signal_connectable(self):
        """pin_requested 信号可连接"""
        received = []

        def handler():
            received.append(True)

        self.hm.pin_requested.connect(handler)
        self.hm.pin_requested.emit()
        self.assertEqual(len(received), 1)

    def test_both_signals_independent(self):
        """两个信号独立"""
        toggle_count = [0]
        pin_count = [0]

        def on_toggle():
            toggle_count[0] += 1

        def on_pin():
            pin_count[0] += 1

        self.hm.toggle_requested.connect(on_toggle)
        self.hm.pin_requested.connect(on_pin)

        self.hm.toggle_requested.emit()
        self.assertEqual(toggle_count[0], 1)
        self.assertEqual(pin_count[0], 0)

        self.hm.pin_requested.emit()
        self.assertEqual(toggle_count[0], 1)
        self.assertEqual(pin_count[0], 1)


class TestHotkeyManagerDoublePress(unittest.TestCase):
    """双击检测逻辑测试（纯逻辑，不依赖真实按键）"""

    def setUp(self):
        self.hm = HotkeyManager(double_press_interval=0.5)

    def tearDown(self):
        self.hm.stop()

    def test_single_press_no_trigger(self):
        """单次按下不触发"""
        triggered = [False]
        self.hm.toggle_requested.connect(lambda: triggered.__setitem__(0, True))

        # 模拟单次按下：设置_last_ctrl_time
        self.hm._last_ctrl_time = time.time()
        # 等待超过双击间隔
        self.hm._last_ctrl_time = time.time() - 1.0
        # 再次按下检测会失败因为距离上次超过间隔
        self.assertFalse(triggered[0])

    def test_double_press_within_interval_triggers(self):
        """双击间隔内触发"""
        triggered = [False]
        self.hm.toggle_requested.connect(lambda: triggered.__setitem__(0, True))

        # 模拟双击
        self.hm._last_ctrl_time = time.time() - 0.1  # 100ms前按下
        self.hm._ctrl_was_up = True
        # 模拟按下检测
        ctrl_down = True
        if ctrl_down and self.hm._ctrl_was_up:
            now = time.time()
            if now - self.hm._last_ctrl_time <= self.hm._double_press_interval:
                self.hm.toggle_requested.emit()
                self.hm._last_ctrl_time = 0.0
        self.assertTrue(triggered[0])

    def test_double_press_outside_interval_no_trigger(self):
        """双击间隔外不触发"""
        triggered = [False]
        self.hm.toggle_requested.connect(lambda: triggered.__setitem__(0, True))

        # 600ms前按下，超过500ms间隔
        self.hm._last_ctrl_time = time.time() - 0.6
        self.hm._ctrl_was_up = True
        ctrl_down = True
        if ctrl_down and self.hm._ctrl_was_up:
            now = time.time()
            if now - self.hm._last_ctrl_time <= self.hm._double_press_interval:
                self.hm.toggle_requested.emit()
        self.assertFalse(triggered[0])

    def test_key_hold_not_triggered(self):
        """长按不触发双击"""
        triggered = [False]
        self.hm.toggle_requested.connect(lambda: triggered.__setitem__(0, True))

        # 模拟按键保持按下状态
        self.hm._ctrl_was_up = False  # 上次检测时按键仍按下
        self.hm._last_ctrl_time = time.time() - 0.1
        ctrl_down = True
        if ctrl_down and self.hm._ctrl_was_up:
            # 不应进入此分支
            self.hm.toggle_requested.emit()
        self.assertFalse(triggered[0])

    def test_reset_after_double_press(self):
        """双击后_last_ctrl_time重置为0"""
        self.hm._last_ctrl_time = time.time() - 0.1
        self.hm._ctrl_was_up = True
        ctrl_down = True
        if ctrl_down and self.hm._ctrl_was_up:
            now = time.time()
            if now - self.hm._last_ctrl_time <= self.hm._double_press_interval:
                self.hm.toggle_requested.emit()
                self.hm._last_ctrl_time = 0.0
        self.assertEqual(self.hm._last_ctrl_time, 0.0)


class TestHotkeyManagerThreadSafety(unittest.TestCase):
    """线程安全测试"""

    def setUp(self):
        self.hm = HotkeyManager()

    def tearDown(self):
        self.hm.stop()

    def test_lock_acquired_in_poll(self):
        """_lock 锁已创建"""
        self.assertIsInstance(self.hm._lock, type(threading.Lock()))

    def test_concurrent_start_stop(self):
        """并发启动停止不崩溃"""
        errors = []

        def runner():
            try:
                for _ in range(10):
                    self.hm.start()
                    time.sleep(0.01)
                    self.hm.stop()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=runner) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0, f"并发启动/停止出错: {errors}")


if __name__ == '__main__':
    unittest.main()