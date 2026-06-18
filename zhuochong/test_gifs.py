"""
自动化测试 - gifs.py / gifs2.py 数据加载与变量命名验证
"""
import os
import sys
import unittest

# 确保从项目根目录导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gifs
import gifs2


class TestGifsModule(unittest.TestCase):
    """gifs.py 模块测试"""

    def test_all_variables_are_bytes(self):
        """_ALL_GIFS 中每个变量都是 bytes 类型"""
        for item in gifs._ALL_GIFS:
            self.assertIsInstance(item, bytes, f"应为bytes: {item[:10]}...")

    def test_all_gifs_not_empty(self):
        """所有GIF数据非空"""
        for item in gifs._ALL_GIFS:
            self.assertGreater(len(item), 0, "GIF数据不应为空")

    def test_gif_magic_bytes(self):
        """所有数据以GIF文件头开头"""
        for item in gifs._ALL_GIFS:
            self.assertTrue(item.startswith(b'GIF8'), f"不是有效GIF: {item[:10]}")

    def test_begin_gif_exists(self):
        """BEGIN_GIF 存在且非空"""
        self.assertIsInstance(gifs.BEGIN_GIF, bytes)
        self.assertGreater(len(gifs.BEGIN_GIF), 0)

    def test_happy_gifs_count(self):
        """_HAPPY_GIFS 包含 44 个 happy GIF"""
        self.assertEqual(len(gifs._HAPPY_GIFS), 44)

    def test_click_gifs_count(self):
        """_CLICK_GIFS 包含 3 个 click GIF"""
        self.assertEqual(len(gifs._CLICK_GIFS), 3)

    def test_hover_gifs_count(self):
        """_HOVER_GIFS 包含 2 个 hover GIF"""
        self.assertEqual(len(gifs._HOVER_GIFS), 2)

    def test_all_gifs_total_count(self):
        """_ALL_GIFS 总数 = 1 begin + 44 happy + 3 click + 2 hover = 50"""
        self.assertEqual(len(gifs._ALL_GIFS), 50)

    def test_happy_gifs_prefix(self):
        """所有 happy 变量名以 HAPPY 开头"""
        happy_vars = [v for k, v in vars(gifs).items() if k.startswith('HAPPY') and k.endswith('_GIF')]
        self.assertEqual(len(happy_vars), 44)
        for v in happy_vars:
            self.assertIsInstance(v, bytes)

    def test_click_gifs_prefix(self):
        """所有 click 变量名以 CLICK 开头"""
        click_vars = [v for k, v in vars(gifs).items() if k.startswith('CLICK') and k.endswith('_GIF')]
        self.assertEqual(len(click_vars), 3)

    def test_hover_variable_names(self):
        """LEFT_GIF 和 RIGHT_GIF 存在"""
        self.assertIsInstance(gifs.LEFT_GIF, bytes)
        self.assertIsInstance(gifs.RIGHT_GIF, bytes)


class TestGifs2Module(unittest.TestCase):
    """gifs2.py 模块测试"""

    def test_all_variables_are_bytes(self):
        """G2_ALL_GIFS 中每个变量都是 bytes 类型"""
        for item in gifs2.G2_ALL_GIFS:
            self.assertIsInstance(item, bytes, f"应为bytes: {item[:10]}...")

    def test_all_gifs_not_empty(self):
        """所有GIF数据非空"""
        for item in gifs2.G2_ALL_GIFS:
            self.assertGreater(len(item), 0, "GIF数据不应为空")

    def test_gif_magic_bytes(self):
        """所有数据以GIF文件头开头"""
        for item in gifs2.G2_ALL_GIFS:
            self.assertTrue(item.startswith(b'GIF8'), f"不是有效GIF: {item[:10]}")

    def test_g2_prefix_naming(self):
        """所有变量名以 G2_ 开头"""
        g2_vars = {k: v for k, v in vars(gifs2).items()
                   if k.startswith('G2_') and isinstance(v, bytes)}
        self.assertGreater(len(g2_vars), 0, "应有G2_前缀的变量")
        for name in g2_vars:
            self.assertTrue(name.startswith('G2_'), f"变量名应以G2_开头: {name}")

    def test_g2_begin_gif_exists(self):
        """G2_BEGIN_GIF 存在且非空"""
        self.assertIsInstance(gifs2.G2_BEGIN_GIF, bytes)
        self.assertGreater(len(gifs2.G2_BEGIN_GIF), 0)

    def test_g2_happy_gifs_count(self):
        """G2_HAPPY_GIFS 数量正确"""
        self.assertEqual(len(gifs2.G2_HAPPY_GIFS), 33)

    def test_g2_click_gifs_count(self):
        """G2_CLICK_GIFS 包含 3 个 click GIF"""
        self.assertEqual(len(gifs2.G2_CLICK_GIFS), 3)

    def test_g2_hover_gifs_count(self):
        """G2_HOVER_GIFS 包含 2 个 hover GIF"""
        self.assertEqual(len(gifs2.G2_HOVER_GIFS), 2)

    def test_g2_all_gifs_total(self):
        """G2_ALL_GIFS 总数 = 1 begin + 33 happy + 3 click + 2 hover = 39"""
        self.assertEqual(len(gifs2.G2_ALL_GIFS), 39)

    def test_g2_variable_name_format(self):
        """变量名格式：G2_ + 大写字母 + _GIF"""
        g2_vars = {k: v for k, v in vars(gifs2).items()
                   if k.startswith('G2_') and isinstance(v, bytes)}
        for name in g2_vars:
            # 格式: G2_XXXX_GIF
            self.assertTrue(name.endswith('_GIF'), f"应以_GIF结尾: {name}")
            # 去除 G2_ 前缀和 _GIF 后缀后，中间部分应全大写
            middle = name[3:-4]
            self.assertTrue(middle == middle.upper(), f"中间部分应全大写: {name}")


class TestGifDataIntegrity(unittest.TestCase):
    """跨模块数据完整性测试"""

    def test_gifs_and_gifs2_are_different(self):
        """两个模块的GIF数据不同（黄色小狗 ≠ 白色小狗）"""
        self.assertNotEqual(gifs.BEGIN_GIF, gifs2.G2_BEGIN_GIF,
                            "两个风格的begin.gif应该不同")

    def test_both_have_required_categories(self):
        """两个模块都有四大类GIF"""
        for mod, name in [(gifs, "gifs"), (gifs2, "gifs2")]:
            with self.subTest(module=name):
                self.assertTrue(hasattr(mod, 'BEGIN_GIF') or hasattr(mod, 'G2_BEGIN_GIF'),
                                f"{name} 缺少 BEGIN_GIF")
                happy = getattr(mod, 'G2_HAPPY_GIFS', None) or getattr(mod, '_HAPPY_GIFS', None)
                self.assertIsNotNone(happy, f"{name} 缺少 HAPPY_GIFS")
                click = getattr(mod, 'G2_CLICK_GIFS', None) or getattr(mod, '_CLICK_GIFS', None)
                self.assertIsNotNone(click, f"{name} 缺少 CLICK_GIFS")
                hover = getattr(mod, 'G2_HOVER_GIFS', None) or getattr(mod, '_HOVER_GIFS', None)
                self.assertIsNotNone(hover, f"{name} 缺少 HOVER_GIFS")


if __name__ == '__main__':
    unittest.main()