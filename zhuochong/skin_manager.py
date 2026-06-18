"""
皮肤管理模块 - 管理桌面宠物的皮肤（GIF图片包）
"""
import os
import shutil
from typing import List, Dict, Optional

# 皮肤资源根目录
SKINS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "skins")

# 皮肤必需文件（idle是默认动画，hover是悬停动画）
REQUIRED_FILES = ["idle.gif", "hover.gif"]

# 所有支持的动画类型
ANIMATION_TYPES = ["idle", "hover", "dance", "shake", "run", "eat", "sleep"]


class SkinManager:
    """皮肤管理器：扫描、切换、管理皮肤包"""

    def __init__(self):
        os.makedirs(SKINS_DIR, exist_ok=True)

    def list_skins(self) -> List[str]:
        """列出所有可用皮肤名称"""
        if not os.path.exists(SKINS_DIR):
            return []
        skins = []
        for name in os.listdir(SKINS_DIR):
            skin_path = os.path.join(SKINS_DIR, name)
            if os.path.isdir(skin_path) and self._is_valid_skin(skin_path):
                skins.append(name)
        return sorted(skins)

    def _is_valid_skin(self, skin_path: str) -> bool:
        """检查皮肤目录是否包含必要文件"""
        for f in REQUIRED_FILES:
            if not os.path.isfile(os.path.join(skin_path, f)):
                return False
        return True

    def get_skin_path(self, skin_name: str) -> Optional[str]:
        """获取皮肤目录路径"""
        path = os.path.join(SKINS_DIR, skin_name)
        if os.path.isdir(path) and self._is_valid_skin(path):
            return path
        return None

    def get_gif_path(self, skin_name: str, gif_type: str) -> Optional[str]:
        """
        获取指定皮肤的GIF文件路径
        gif_type: 'idle' | 'hover' | 'dance' | 'shake' | 'run' | 'eat' | 'sleep'
        """
        skin_path = self.get_skin_path(skin_name)
        if skin_path is None:
            return None
        gif_path = os.path.join(skin_path, f"{gif_type}.gif")
        if os.path.isfile(gif_path):
            return gif_path
        return None

    def add_skin(self, skin_name: str, source_dir: str) -> bool:
        """
        从外部目录导入新皮肤
        source_dir 需包含 idle.gif 和 hover.gif
        """
        if not os.path.isdir(source_dir):
            return False
        for f in REQUIRED_FILES:
            if not os.path.isfile(os.path.join(source_dir, f)):
                return False
        dest = os.path.join(SKINS_DIR, skin_name)
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(source_dir, dest)
        return True

    def delete_skin(self, skin_name: str) -> bool:
        """删除指定皮肤"""
        skin_path = self.get_skin_path(skin_name)
        if skin_path is None:
            return False
        shutil.rmtree(skin_path)
        return True