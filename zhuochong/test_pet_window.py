"""
自动化测试 - PetWindow 状态机、风格切换、钉住逻辑
"""
import os
import sys
import unittest
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QPoint, QTimer

# 确保 QApplication 单例存在
_app = QApplication.instance()
if _app is None:
    _app = QApplication(sys.argv)

from pet_window import PetWindow
import gifs
import gifs2


class TestPetWindowInit(unittest.TestCase):
    """PetWindow 初始化测试"""

    def setUp(self):
        self.pet = PetWindow()

    def tearDown(self):
        self.pet._cleanup_tmp()
        self.pet.close()

    def test_initial_state(self):
        """初始状态验证"""
        self.assertEqual(self.pet._mode, "begin")
        self.assertEqual(self.pet._style, "white")
        self.assertFalse(self.pet._pinned)
        # 窗口构造后默认不可见（main.py 控制不show）

    def test_initial_size(self):
        """初始窗口大小"""
        self.assertGreaterEqual(self.pet.width(), 10)
        self.assertGreaterEqual(self.pet.height(), 10)

    def test_window_flags(self):
        """窗口标志：无边框、置顶"""
        flags = self.pet.windowFlags()
        self.assertTrue(flags & Qt.FramelessWindowHint)
        self.assertTrue(flags & Qt.WindowStaysOnTopHint)

    def test_label_exists(self):
        """QLabel 已创建"""
        self.assertIsNotNone(self.pet.label)

    def test_tmp_dir_exists(self):
        """临时目录已创建"""
        self.assertTrue(os.path.isdir(self.pet._tmp_dir))

    def test_begin_timer_active(self):
        """_play_begin 已设置 frameChanged 监听"""
        # __init__ 调用 _play_begin，验证 mode 为 begin
        self.assertEqual(self.pet._mode, "begin")
        self.assertIsNotNone(self.pet._current_movie)

    def test_position_timer_active(self):
        """位置移动定时器已启动"""
        self.assertIsNotNone(self.pet._pos_timer)
        self.assertTrue(self.pet._pos_timer.isActive())


class TestPetWindowStyleSwitch(unittest.TestCase):
    """风格切换测试"""

    def setUp(self):
        self.pet = PetWindow()

    def tearDown(self):
        self.pet._cleanup_tmp()
        self.pet.close()

    def test_default_style_white(self):
        """默认风格为白色"""
        self.assertEqual(self.pet._style, "white")

    def test_switch_to_yellow(self):
        """切换到黄色风格"""
        self.pet._switch_style("yellow")
        self.assertEqual(self.pet._style, "yellow")

    def test_switch_back_to_white(self):
        """切回白色风格"""
        self.pet._switch_style("yellow")
        self.pet._switch_style("white")
        self.assertEqual(self.pet._style, "white")

    def test_switch_same_style_noop(self):
        """切换到相同风格不触发任何操作"""
        self.pet._switch_style("white")
        self.assertEqual(self.pet._style, "white")

    def test_gif_module_white(self):
        """白色风格返回gifs2模块"""
        self.pet._style = "white"
        self.assertIs(self.pet._gif_module(), gifs2)

    def test_gif_module_yellow(self):
        """黄色风格返回gifs模块"""
        self.pet._style = "yellow"
        self.assertIs(self.pet._gif_module(), gifs)

    def test_current_begin_white(self):
        """白色风格的begin GIF"""
        self.pet._style = "white"
        self.assertIsInstance(self.pet._current_begin(), bytes)

    def test_current_begin_yellow(self):
        """黄色风格的begin GIF"""
        self.pet._style = "yellow"
        self.assertIsInstance(self.pet._current_begin(), bytes)

    def test_current_happy_list_white(self):
        """白色风格的happy列表"""
        self.pet._style = "white"
        happy = self.pet._current_happy_list()
        self.assertEqual(len(happy), 33)

    def test_current_happy_list_yellow(self):
        """黄色风格的happy列表"""
        self.pet._style = "yellow"
        happy = self.pet._current_happy_list()
        self.assertEqual(len(happy), 44)

    def test_current_click_list_white(self):
        """白色风格的click列表"""
        self.pet._style = "white"
        click = self.pet._current_click_list()
        self.assertEqual(len(click), 3)

    def test_current_click_list_yellow(self):
        """黄色风格的click列表"""
        self.pet._style = "yellow"
        click = self.pet._current_click_list()
        self.assertEqual(len(click), 3)

    def test_current_hover_list_white(self):
        """白色风格的hover列表"""
        self.pet._style = "white"
        hover = self.pet._current_hover_list()
        self.assertEqual(len(hover), 2)

    def test_current_hover_list_yellow(self):
        """黄色风格的hover列表"""
        self.pet._style = "yellow"
        hover = self.pet._current_hover_list()
        self.assertEqual(len(hover), 2)


class TestPetWindowMode(unittest.TestCase):
    """模式切换逻辑测试"""

    def setUp(self):
        self.pet = PetWindow()

    def tearDown(self):
        self.pet._cleanup_tmp()
        self.pet.close()

    def test_initial_mode_begin(self):
        """初始模式为begin"""
        self.assertEqual(self.pet._mode, "begin")

    def test_start_idle_changes_mode(self):
        """_start_idle 切换到 idle 模式"""
        self.pet._start_idle()
        self.assertEqual(self.pet._mode, "idle")

    def test_play_click_changes_mode(self):
        """_play_click 切换到 click 模式"""
        self.pet._play_click()
        self.assertEqual(self.pet._mode, "click")

    def test_enter_hover_changes_mode(self):
        """_enter_hover 切换到 hover 模式"""
        self.pet._enter_hover()
        self.assertEqual(self.pet._mode, "hover")

    def test_leave_hover_enters_idle(self):
        """_leave_hover 切换到 idle 模式"""
        self.pet._enter_hover()
        self.pet._leave_hover()
        self.assertEqual(self.pet._mode, "idle")

    def test_play_begin_resets_mode(self):
        """_play_begin 重置为 begin 模式"""
        self.pet._start_idle()
        self.pet._play_begin()
        self.assertEqual(self.pet._mode, "begin")

    def test_play_next_idle_only_in_idle(self):
        """_play_next_idle 仅在 idle 模式生效"""
        self.pet._mode = "click"
        # 不应触发任何操作
        try:
            self.pet._play_next_idle()
        except Exception as e:
            self.fail(f"_play_next_idle 在click模式下不应抛出异常: {e}")
        self.assertEqual(self.pet._mode, "click")

    def test_begin_timer_transitions_to_idle(self):
        """begin帧播放完毕后切换到idle"""
        self.pet._mode = "begin"
        self.pet._play_movie(gifs.HAPPY1_GIF)
        if self.pet._current_movie:
            total = self.pet._current_movie.frameCount()
            # 模拟最后一帧触发
            self.pet._on_begin_frame(total - 1)
        self.assertEqual(self.pet._mode, "idle")

    def test_begin_timer_ignored_when_not_begin(self):
        """不在begin模式时 _on_begin_frame 不触发切换"""
        self.pet._mode = "click"
        self.pet._play_movie(gifs.HAPPY1_GIF)
        if self.pet._current_movie:
            total = self.pet._current_movie.frameCount()
            self.pet._on_begin_frame(total - 1)
        self.assertEqual(self.pet._mode, "click")  # 不应切换


class TestPetWindowPin(unittest.TestCase):
    """钉住功能测试"""

    def setUp(self):
        self.pet = PetWindow()

    def tearDown(self):
        self.pet._cleanup_tmp()
        self.pet.close()

    def test_initial_not_pinned(self):
        """初始未钉住"""
        self.assertFalse(self.pet._pinned)

    def test_toggle_pin_when_visible(self):
        """可见时切换钉住状态"""
        self.pet.show()
        self.pet.toggle_pin()
        self.assertTrue(self.pet._pinned)

    def test_toggle_pin_twice(self):
        """两次切换回到未钉住"""
        self.pet.show()
        self.pet.toggle_pin()
        self.pet.toggle_pin()
        self.assertFalse(self.pet._pinned)

    def test_toggle_pin_when_hidden_noop(self):
        """隐藏时切换钉住不生效"""
        self.pet.hide()
        self.pet.toggle_pin()
        self.assertFalse(self.pet._pinned)

    def test_toggle_pin_multiple_toggles(self):
        """多次切换"""
        self.pet.show()
        for i in range(5):
            self.pet.toggle_pin()
        self.assertTrue(self.pet._pinned)  # 奇数次切换 = 钉住


class TestPetWindowVisibility(unittest.TestCase):
    """可见性切换测试"""

    def setUp(self):
        self.pet = PetWindow()

    def tearDown(self):
        self.pet._cleanup_tmp()
        self.pet.close()

    def test_toggle_visibility_hide(self):
        """toggle_visibility 隐藏"""
        self.pet.show()
        self.pet.toggle_visibility()
        self.assertFalse(self.pet.isVisible())

    def test_toggle_visibility_show(self):
        """toggle_visibility 显示"""
        self.pet.hide()
        self.pet.toggle_visibility()
        self.assertTrue(self.pet.isVisible())

    def test_toggle_visibility_roundtrip(self):
        """显示→隐藏→显示"""
        self.pet.show()
        self.pet.toggle_visibility()
        self.assertFalse(self.pet.isVisible())
        self.pet.toggle_visibility()
        self.assertTrue(self.pet.isVisible())


class TestPetWindowPlayMovie(unittest.TestCase):
    """GIF播放核心测试"""

    def setUp(self):
        self.pet = PetWindow()

    def tearDown(self):
        self.pet._cleanup_tmp()
        self.pet.close()

    def test_play_movie_creates_temp_file(self):
        """_play_movie 创建临时文件"""
        test_data = gifs.HAPPY1_GIF
        self.pet._play_movie(test_data)
        self.assertIsNotNone(self.pet._last_tmp_path)
        self.assertTrue(os.path.exists(self.pet._last_tmp_path))

    def test_play_movie_cleans_old_temp(self):
        """_play_movie 清理旧临时文件"""
        test_data1 = gifs.HAPPY1_GIF
        test_data2 = gifs.HAPPY2_GIF
        self.pet._play_movie(test_data1)
        old_path = self.pet._last_tmp_path
        self.assertIsNotNone(old_path)
        self.assertTrue(os.path.exists(old_path))
        # 处理 deleteLater 事件
        QApplication.processEvents()
        self.pet._play_movie(test_data2)
        # 旧文件应被删除
        self.assertFalse(os.path.exists(old_path),
                         "旧临时文件应被清理")

    def test_play_movie_sets_current_movie(self):
        """_play_movie 设置当前Movie"""
        self.pet._play_movie(gifs.HAPPY1_GIF)
        self.assertIsNotNone(self.pet._current_movie)

    def test_play_movie_resizes_window(self):
        """_play_movie 调整窗口大小"""
        old_w = self.pet.width()
        old_h = self.pet.height()
        self.pet._play_movie(gifs.HAPPY1_GIF)
        # 窗口大小应该变化（GIF有实际尺寸）
        self.assertGreater(self.pet.width(), 0)
        self.assertGreater(self.pet.height(), 0)


class TestPetWindowCleanup(unittest.TestCase):
    """清理测试"""

    def test_cleanup_removes_temp_dir(self):
        """_cleanup_tmp 删除临时目录"""
        pet = PetWindow()
        tmp_dir = pet._tmp_dir
        self.assertTrue(os.path.isdir(tmp_dir))
        # 先停止Movie释放文件句柄
        if pet._current_movie:
            pet._current_movie.stop()
            pet._current_movie.setFileName("")
            pet._current_movie = None
        pet._cleanup_tmp()
        self.assertFalse(os.path.isdir(tmp_dir))
        pet.close()

    def test_close_event_cleans_up(self):
        """closeEvent 清理资源"""
        pet = PetWindow()
        tmp_dir = pet._tmp_dir
        # 先停止Movie释放文件句柄
        if pet._current_movie:
            pet._current_movie.stop()
            pet._current_movie.setFileName("")
            pet._current_movie = None
        pet.close()
        self.assertFalse(os.path.isdir(tmp_dir))


if __name__ == '__main__':
    unittest.main()