"""
桌面宠物 - 主入口
全局快捷键 CTRL+CTRL 唤醒/隐藏宠物
"""
import sys
import os

from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt

from pet_window import PetWindow
from skin_manager import SkinManager
from hotkey_manager import HotkeyManager

# 解决 Windows 任务栏图标问题
try:
    from ctypes import windll
    APP_ID = "zhuochong.desktop.pet.v1"
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
except Exception:
    pass


def main():
    # 高DPI支持
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # ── 皮肤管理器 ──────────────────────────────────────────
    skin_manager = SkinManager()

    # 检查默认皮肤是否存在
    default_skin = "line_puppy"
    available = skin_manager.list_skins()
    if available:
        default_skin = available[0] if default_skin not in available else default_skin
    else:
        print("=" * 50)
        print("  未找到任何皮肤！")
        print(f"  请将GIF素材放入: resources/skins/<皮肤名>/")
        print("  每个皮肤需要: idle.gif 和 hover.gif")
        print("=" * 50)

    # ── 宠物窗口 ────────────────────────────────────────────
    pet = PetWindow(skin_manager, default_skin)

    # 初始显示
    if available:
        pet.show()

    # ── 系统托盘 ────────────────────────────────────────────
    tray = QSystemTrayIcon()
    # 尝试使用图标
    icon_path = os.path.join(os.path.dirname(__file__), "resources", "icon.png")
    if os.path.exists(icon_path):
        tray.setIcon(QIcon(icon_path))
    else:
        tray.setIcon(app.style().standardIcon(app.style().StandardPixmap.SP_ComputerIcon))

    tray_menu = QMenu()
    show_action = QAction("显示宠物", tray_menu)
    show_action.triggered.connect(lambda: pet.toggle_visibility() if not pet.isVisible() else None)
    tray_menu.addAction(show_action)

    quit_action = QAction("退出", tray_menu)
    quit_action.triggered.connect(app.quit)
    tray_menu.addAction(quit_action)

    tray.setContextMenu(tray_menu)
    tray.setToolTip("桌面宠物 - CTRL+CTRL 唤醒")
    tray.show()

    tray.activated.connect(lambda reason: pet.show() if reason == QSystemTrayIcon.ActivationReason.DoubleClick else None)

    # ── 全局快捷键 ──────────────────────────────────────────
    hotkey = HotkeyManager(double_press_interval=0.5)
    hotkey.toggle_requested.connect(pet.toggle_visibility)
    hotkey.start()

    # ── 运行 ────────────────────────────────────────────────
    print("[桌面宠物] 已启动！")
    print("[桌面宠物] 按 CTRL+CTRL 唤醒/隐藏宠物")
    print("[桌面宠物] 右键宠物 → 更换皮肤 / 关闭")
    print("[桌面宠物] 鼠标悬停宠物可看到表情变化")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()