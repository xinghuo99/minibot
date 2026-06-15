# -*- coding: utf-8 -*-
"""
多格式文件编辑器 — 酒红色主题 · 无边框自定义标题栏 · 原生预览
支持：txt, py, json, md, html, pdf, png, jpg, docx, xlsx, pptx 等格式
"""

import sys
import os
import json
import tempfile
import shutil
import io
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTreeView, QFileSystemModel,
    QStackedWidget, QTextEdit, QPlainTextEdit, QScrollArea,
    QSplitter, QMessageBox, QMenu, QFileDialog, QShortcut,
    QComboBox, QFrame, QAction
)
from PyQt5.QtCore import Qt, QDir, QUrl, QPoint, QSize, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QKeySequence, QFont, QIcon, QPainter, QPen, QColor

# ---------- 可选依赖 ----------
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False

try:
    from docx import Document as DocxDocument
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    import mammoth
    HAS_MAMMOTH = True
except ImportError:
    HAS_MAMMOTH = False

try:
    import openpyxl
    from openpyxl.styles import Font as XlFont, PatternFill, Alignment, Border, Side
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

try:
    from pptx import Presentation
    from pptx.util import Inches
    HAS_PPTX = True
except ImportError:
    HAS_PPTX = False

try:
    from PIL import Image as PILImage
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ---------- LibreOffice 检测（用于 Office 文档转 HTML 预览） ----------
import subprocess as _subprocess

_LO_SOFFICE = None
_LO_AVAILABLE = False


def _find_libreoffice() -> str | None:
    """查找 LibreOffice soffice 可执行文件路径"""
    candidates = [
        # Windows
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        # Linux / macOS
        "/usr/bin/soffice",
        "/usr/local/bin/soffice",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "soffice",  # PATH 中查找
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
        # 也尝试在 PATH 中查找
        if p == "soffice" and shutil.which("soffice"):
            return shutil.which("soffice")
    return None


def _check_lo_available() -> bool:
    """检测 LibreOffice 是否可用"""
    global _LO_SOFFICE, _LO_AVAILABLE
    _LO_SOFFICE = _find_libreoffice()
    if not _LO_SOFFICE:
        _LO_AVAILABLE = False
        return False
    try:
        # 使用 STARTUPINFO 彻底隐藏窗口
        startupinfo = _subprocess.STARTUPINFO()
        startupinfo.dwFlags |= _subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = _subprocess.SW_HIDE
        proc = _subprocess.Popen(
            [_LO_SOFFICE, "--headless", "--norestore", "--nologo", "--version"],
            stdout=_subprocess.PIPE, stderr=_subprocess.PIPE,
            startupinfo=startupinfo,
            creationflags=_subprocess.CREATE_NO_WINDOW,
        )
        try:
            proc.communicate(timeout=15)
            _LO_AVAILABLE = proc.returncode == 0
        except _subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            _LO_AVAILABLE = os.path.exists(_LO_SOFFICE)
        return _LO_AVAILABLE
    except Exception:
        # 子进程异常，但文件存在则假定可用
        _LO_AVAILABLE = os.path.exists(_LO_SOFFICE)
        return _LO_AVAILABLE


def convert_with_libreoffice(input_path: str, out_dir: str, fmt: str = "html") -> str | None:
    """使用 LibreOffice headless 将文档转换为 HTML。
    返回输出文件路径，失败返回 None。"""
    _ensure_lo_checked()
    if not _LO_AVAILABLE or not _LO_SOFFICE:
        return None
    try:
        cmd = [
            _LO_SOFFICE,
            "--headless", "--norestore", "--nologo",
            "--convert-to", fmt,
            "--outdir", out_dir,
            input_path,
        ]
        startupinfo = _subprocess.STARTUPINFO()
        startupinfo.dwFlags |= _subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = _subprocess.SW_HIDE
        proc = _subprocess.Popen(
            cmd,
            stdout=_subprocess.PIPE, stderr=_subprocess.PIPE,
            startupinfo=startupinfo,
            creationflags=_subprocess.CREATE_NO_WINDOW,
        )
        try:
            proc.communicate(timeout=60)
        except _subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            return None
        if proc.returncode == 0:
            base = os.path.splitext(os.path.basename(input_path))[0]
            ext = f".{fmt}"
            output = os.path.join(out_dir, base + ext)
            if os.path.exists(output):
                return output
        return None
    except Exception:
        return None


# 延迟初始化（在 EditWorkbench.__init__ 中调用）
_LO_CHECKED = False

# 在模块导入时也尝试检测（避免 EditWorkbench.__init__ 阻塞 GUI）
def _ensure_lo_checked():
    global _LO_CHECKED, _LO_AVAILABLE, _LO_SOFFICE
    if not _LO_CHECKED:
        try:
            _check_lo_available()
        except Exception:
            pass
        _LO_CHECKED = True

# ===================== 颜色 / 样式 =====================
WINE_RED = "#722F37"
WINE_RED_DARK = "#5C1E26"
WINE_RED_LIGHT = "#8B3A44"
WINE_RED_HOVER = "#933F4A"
WINE_BG = "#6B2F37"
TEXT_COLOR = "#F0E6D0"
BORDER_COLOR = "#4A1E26"
MENU_BG = "#5A252E"
TREE_BG = "#5E2A33"
EDIT_BG = "#FDF5E6"
EDIT_TEXT = "#2C1810"
TITLE_BAR_BG = "#4A1E28"

# ---------- 全局字号 ----------
BASE_FONT_SIZE = 17
SMALL_FONT_SIZE = 16
LARGE_FONT_SIZE = 20
TITLE_FONT_SIZE = 18

# ---------- 最近项目存储路径 ----------
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".project_history.json")


def load_project_history() -> list:
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_project_history(history: list):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False)
    except Exception:
        pass


def add_to_history(folder: str):
    history = load_project_history()
    folder = os.path.abspath(folder)
    if folder in history:
        history.remove(folder)
    history.insert(0, folder)
    if len(history) > 20:
        history = history[:20]
    save_project_history(history)


def wine_style() -> str:
    return f"""
    QMainWindow {{
        background-color: {WINE_RED};
    }}
    QWidget {{
        background-color: {WINE_RED};
        color: {TEXT_COLOR};
        font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
        font-size: {BASE_FONT_SIZE}px;
    }}
    QMenu {{
        background-color: {MENU_BG};
        color: {TEXT_COLOR};
        border: 1px solid {BORDER_COLOR};
        font-size: {BASE_FONT_SIZE}px;
    }}
    QMenu::item {{
        padding: 8px 36px 8px 24px;
        font-size: {BASE_FONT_SIZE}px;
    }}
    QMenu::item:selected {{
        background-color: {WINE_RED_HOVER};
    }}
    QPushButton {{
        background-color: {WINE_RED_DARK};
        color: {TEXT_COLOR};
        border: 1px solid {BORDER_COLOR};
        padding: 6px 14px;
        border-radius: 4px;
        font-size: {BASE_FONT_SIZE}px;
    }}
    QPushButton:hover {{
        background-color: {WINE_RED_HOVER};
    }}
    QPushButton:pressed {{
        background-color: {WINE_RED};
    }}
    QPushButton:checked {{
        background-color: {WINE_RED_LIGHT};
    }}
    QLineEdit {{
        background-color: #FDF5E6;
        color: #2C1810;
        border: 1px solid {BORDER_COLOR};
        border-radius: 4px;
        padding: 6px 10px;
        font-size: {BASE_FONT_SIZE}px;
    }}
    QTreeView {{
        background-color: {TREE_BG};
        color: {TEXT_COLOR};
        border: 1px solid {BORDER_COLOR};
        alternate-background-color: {WINE_RED_DARK};
        selection-background-color: {WINE_RED_HOVER};
        selection-color: {TEXT_COLOR};
        outline: none;
        font-size: {SMALL_FONT_SIZE}px;
    }}
    QTreeView::item:hover {{
        background-color: {WINE_RED_HOVER};
    }}
    QSplitter::handle {{
        background-color: {BORDER_COLOR};
    }}
    QSplitter::handle:horizontal {{ width: 2px; }}
    QSplitter::handle:vertical {{ height: 2px; }}
    QScrollBar:vertical {{
        background: {WINE_RED_DARK}; width: 12px; border-radius: 6px;
    }}
    QScrollBar::handle:vertical {{
        background: {WINE_RED_LIGHT}; border-radius: 6px; min-height: 24px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
    QScrollBar:horizontal {{
        background: {WINE_RED_DARK}; height: 12px; border-radius: 6px;
    }}
    QScrollBar::handle:horizontal {{
        background: {WINE_RED_LIGHT}; border-radius: 6px; min-width: 24px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}
    QPlainTextEdit, QTextEdit {{
        background-color: {EDIT_BG};
        color: {EDIT_TEXT};
        border: none;
        font-family: "Consolas", "Courier New", monospace;
        font-size: {LARGE_FONT_SIZE}px;
        selection-background-color: {WINE_RED_LIGHT};
        selection-color: {TEXT_COLOR};
    }}
    QLabel {{ background-color: transparent; }}
    """

# ===================== 文本编辑器 =====================

class TextEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabStopDistance(32)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self._current_path = None

    def load_file(self, path: str):
        self._current_path = path
        self.clear()
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.setPlainText(f.read())
        except UnicodeDecodeError:
            try:
                with open(path, "r", encoding="latin-1") as f:
                    self.setPlainText(f.read())
            except Exception as e:
                self.setPlainText(f"[无法读取文件]\n{str(e)}")
        except Exception as e:
            self.setPlainText(f"[读取文件出错]\n{str(e)}")

    def save_file(self):
        if self._current_path:
            try:
                with open(self._current_path, "w", encoding="utf-8") as f:
                    f.write(self.toPlainText())
                return True
            except Exception:
                return False
        return False


# ===================== 图片查看器（原生显示 + 可编辑） =====================

class ImageViewer(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_path = None
        self._pixmap = None
        self._scale = 1.0
        self._rotation = 0

        self.setStyleSheet("QScrollArea { border: none; background-color: #2C1810; }")
        self.setWidgetResizable(True)

        container = QWidget()
        container.setStyleSheet("background-color: #2C1810;")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # 工具栏
        toolbar = QWidget()
        toolbar.setFixedHeight(40)
        toolbar.setStyleSheet(f"background-color: {WINE_RED_DARK}; border-bottom: 1px solid {BORDER_COLOR};")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(8, 4, 8, 4)
        tb_layout.setSpacing(6)

        self.img_path_label = QLabel("")
        self.img_path_label.setStyleSheet(f"color: {TEXT_COLOR}; background: transparent; font-size: {SMALL_FONT_SIZE}px;")
        tb_layout.addWidget(self.img_path_label)
        tb_layout.addStretch()

        for label, slot in [
            ("↺ 旋转", self._rotate_image),
            ("+ 放大", self._zoom_in),
            ("- 缩小", self._zoom_out),
            ("↺ 还原", self._reset_view),
            ("💾 另存为", self._save_as),
        ]:
            btn = QPushButton(label)
            btn.setFixedHeight(28)
            btn.setStyleSheet(f"""
                QPushButton {{ font-size: {SMALL_FONT_SIZE}px; padding: 2px 10px; }}
            """)
            btn.clicked.connect(slot)
            tb_layout.addWidget(btn)

        container_layout.addWidget(toolbar)

        # 图片显示
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("background-color: #2C1810; border: none;")
        scroll_inner = QScrollArea()
        scroll_inner.setWidget(self.label)
        scroll_inner.setWidgetResizable(False)
        scroll_inner.setAlignment(Qt.AlignCenter)
        scroll_inner.setStyleSheet("QScrollArea { border: none; background-color: #2C1810; }")
        self._scroll_inner = scroll_inner

        container_layout.addWidget(scroll_inner, 1)
        self.setWidget(container)

    def load_file(self, path: str):
        self._current_path = path
        pix = QPixmap(path)
        if pix.isNull():
            self.label.setText("  无法加载图片")
            self.img_path_label.setText("")
            return
        self._pixmap = pix
        self._scale = 1.0
        self._rotation = 0
        self.img_path_label.setText(f"  {os.path.basename(path)}  ({pix.width()}x{pix.height()})")
        self._apply_transform()

    def _apply_transform(self):
        if not self._pixmap or self._pixmap.isNull():
            return
        pix = self._pixmap
        if self._rotation:
            from PyQt5.QtGui import QTransform
            t = QTransform().rotate(self._rotation)
            pix = pix.transformed(t, Qt.SmoothTransformation)
        if self._scale != 1.0:
            w = int(pix.width() * self._scale)
            h = int(pix.height() * self._scale)
            pix = pix.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label.setPixmap(pix)
        self.label.resize(pix.size())

    def _rotate_image(self):
        self._rotation = (self._rotation + 90) % 360
        self._apply_transform()

    def _zoom_in(self):
        self._scale = min(5.0, self._scale * 1.25)
        self._apply_transform()

    def _zoom_out(self):
        self._scale = max(0.1, self._scale * 0.8)
        self._apply_transform()

    def _reset_view(self):
        self._scale = 1.0
        self._rotation = 0
        self._apply_transform()

    def _save_as(self):
        if not self._pixmap or not hasattr(self, '_current_path') or not self._current_path:
            QMessageBox.warning(self, "提示", "没有可保存的图片")
            return
        new_path, _ = QFileDialog.getSaveFileName(
            self, "另存为图片", self._current_path,
            "PNG (*.png);;JPG (*.jpg);;BMP (*.bmp)"
        )
        if new_path:
            pix = self._pixmap
            if self._rotation:
                from PyQt5.QtGui import QTransform
                t = QTransform().rotate(self._rotation)
                pix = pix.transformed(t, Qt.SmoothTransformation)
            pix.save(new_path)
            self._current_path = new_path
            self.img_path_label.setText(f"  {os.path.basename(new_path)}  (已保存)")

    def save_file(self):
        """直接覆盖保存原图"""
        if self._pixmap and hasattr(self, '_current_path') and self._current_path:
            pix = self._pixmap
            if self._rotation:
                from PyQt5.QtGui import QTransform
                t = QTransform().rotate(self._rotation)
                pix = pix.transformed(t, Qt.SmoothTransformation)
            pix.save(self._current_path)
            return True
        return False


# ===================== HTML / Markdown 原生预览（网页形式） =====================

def _simple_md_to_html(text: str) -> str:
    """简单的 Markdown 转 HTML"""
    import re
    lines = text.split("\n")
    html_lines = []
    in_code_block = False
    in_list = False

    for line in lines:
        # 代码块
        if line.strip().startswith("```"):
            if in_code_block:
                html_lines.append("</pre>")
                in_code_block = False
            else:
                html_lines.append('<pre style="background:#2C1810;color:#F0E6D0;padding:16px;border-radius:6px;overflow-x:auto;">')
                in_code_block = True
            continue
        if in_code_block:
            html_lines.append(line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
            continue

        stripped = line.strip()

        # 空行
        if not stripped:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append("")
            continue

        # 标题
        m = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if m:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            level = len(m.group(1))
            html_lines.append(f'<h{level}>{m.group(2)}</h{level}>')
            continue

        # 无序列表
        m = re.match(r'^[-*+]\s+(.+)$', stripped)
        if m:
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            html_lines.append(f'<li>{m.group(1)}</li>')
            continue

        # 引用
        m = re.match(r'^>\s*(.+)$', stripped)
        if m:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f'<blockquote>{m.group(1)}</blockquote>')
            continue

        # 水平线
        if stripped in ('---', '***', '___'):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append('<hr>')
            continue

        # 普通段落 - 内联样式
        if in_list:
            html_lines.append("</ul>")
            in_list = False
        # 粗体 **text**
        line = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', stripped)
        # 斜体 *text*
        line = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<em>\1</em>', line)
        # 行内代码 `code`
        line = re.sub(r'`(.+?)`', r'<code>\1</code>', line)
        # 链接 [text](url)
        line = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', line)
        # 图片 ![alt](url)
        line = re.sub(r'!\[(.+?)\]\((.+?)\)', r'<img src="\2" alt="\1" style="max-width:100%">', line)
        html_lines.append(f'<p>{line}</p>')

    if in_code_block:
        html_lines.append("</pre>")
    if in_list:
        html_lines.append("</ul>")

    return "\n".join(html_lines)


class HtmlMdViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_path = None
        self._is_html = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()

        self.source_editor = QPlainTextEdit()
        self.source_editor.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {EDIT_BG};
                color: {EDIT_TEXT};
                font-family: "Consolas", "Courier New", monospace;
                font-size: {LARGE_FONT_SIZE}px;
            }}
        """)
        self.stack.addWidget(self.source_editor)  # 0

        if HAS_WEBENGINE:
            self.browser = QWebEngineView()
            self.stack.addWidget(self.browser)     # 1
        else:
            self.browser = None
            fallback = QLabel("  (需要安装 PyQtWebEngine 以预览 HTML/MD)")
            fallback.setStyleSheet(f"color:{TEXT_COLOR}; background:{WINE_RED_DARK}; padding:20px; font-size:{BASE_FONT_SIZE}px;")
            fallback.setAlignment(Qt.AlignCenter)
            self.stack.addWidget(fallback)

        layout.addWidget(self.stack)

        btn_layout = QHBoxLayout()
        self.btn_preview = QPushButton("预览")
        self.btn_source = QPushButton("源码")
        for b in [self.btn_preview, self.btn_source]:
            b.setFixedHeight(30)
            b.setCheckable(True)
        self.btn_preview.clicked.connect(lambda: self._switch_view("preview"))
        self.btn_source.clicked.connect(lambda: self._switch_view("source"))
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_preview)
        btn_layout.addWidget(self.btn_source)
        layout.addLayout(btn_layout)

        # 默认源码模式（HTML 文件在 load_file 中改为预览模式）
        self.btn_source.setChecked(True)
        self.stack.setCurrentIndex(0)

    def load_file(self, path: str):
        self._current_path = path
        ext = os.path.splitext(path)[1].lower()
        self._is_html = (ext in {".html", ".htm"})

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            content = f"[无法读取文件]\n{str(e)}"

        self.source_editor.setPlainText(content)

        if self._is_html:
            # HTML 文件默认预览模式（网页形式）
            self._render_preview(content)
            self.btn_preview.setChecked(True)
            self.btn_source.setChecked(False)
            self.stack.setCurrentIndex(1)
        else:
            # MD 文件默认源码模式
            self._render_preview(content)
            self.btn_source.setChecked(True)
            self.btn_preview.setChecked(False)
            self.stack.setCurrentIndex(0)

    def _switch_view(self, mode: str):
        if mode == "preview":
            self._render_preview(self.source_editor.toPlainText())
            self.stack.setCurrentIndex(1)
            self.btn_preview.setChecked(True)
            self.btn_source.setChecked(False)
        else:
            self.stack.setCurrentIndex(0)
            self.btn_source.setChecked(True)
            self.btn_preview.setChecked(False)

    def _render_preview(self, content: str):
        if not self.browser:
            return
        if self._is_html:
            # HTML 文件直接用浏览器渲染
            self.browser.setHtml(content)
        else:
            # Markdown 转 HTML 后渲染
            md_html = _simple_md_to_html(content)
            html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body {{
    font-family: "Microsoft YaHei", "SimSun", sans-serif;
    padding: 30px 50px;
    color: #2C1810;
    background: #FDF5E6;
    max-width: 860px;
    margin: 0 auto;
    line-height: 1.8;
  }}
  h1 {{ border-bottom: 2px solid #722F37; padding-bottom: 10px; color: #4A1E28; }}
  h2 {{ border-bottom: 1px solid #8B3A44; padding-bottom: 6px; color: #5C1E26; }}
  h3, h4 {{ color: #722F37; }}
  code {{ background: #F5EDE0; padding: 2px 6px; border-radius: 3px; font-family: "Consolas", monospace; }}
  pre {{ background: #2C1810; color: #F0E6D0; padding: 16px; border-radius: 6px; overflow-x: auto; }}
  blockquote {{ border-left: 3px solid #722F37; padding: 10px 20px; margin: 12px 0; background: #F5EDE0; color: #5C1E26; }}
  a {{ color: #722F37; }}
  hr {{ border: none; border-top: 1px solid #8B3A44; margin: 24px 0; }}
  ul, ol {{ padding-left: 24px; }}
  table {{ border-collapse: collapse; width: 100%; }}
  td, th {{ border: 1px solid #999; padding: 8px 14px; }}
  th {{ background: #722F37; color: #F0E6D0; }}
</style></head>
<body>{md_html}</body></html>"""
            self.browser.setHtml(html)

    def save_file(self):
        if self._current_path:
            try:
                with open(self._current_path, "w", encoding="utf-8") as f:
                    f.write(self.source_editor.toPlainText())
                return True
            except Exception:
                return False
        return False


# ===================== Word 预览（LibreOffice HTML + WebEngine，效果与 Word 一致） =====================

class DocxViewer(QWidget):
    """使用 LibreOffice 将 docx 转换为 HTML，通过 QWebEngineView 渲染，预览效果与 Word 高度一致"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_path = None
        self._preview_html = None
        self._temp_dir = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()

        # 源码编辑
        self.source_editor = QPlainTextEdit()
        self.source_editor.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {EDIT_BG}; color: {EDIT_TEXT};
                font-family: "Consolas", "Courier New", monospace; font-size: {LARGE_FONT_SIZE}px;
            }}
        """)
        self.stack.addWidget(self.source_editor)   # 0

        # HTML 预览
        if HAS_WEBENGINE:
            self.browser = QWebEngineView()
            self.stack.addWidget(self.browser)      # 1
        else:
            self.browser = None
            fallback = QLabel("  (需要 PyQtWebEngine 以预览)")
            fallback.setStyleSheet(f"color:{TEXT_COLOR}; background:{WINE_RED_DARK}; padding:20px; font-size:{BASE_FONT_SIZE}px;")
            fallback.setAlignment(Qt.AlignCenter)
            self.stack.addWidget(fallback)

        layout.addWidget(self.stack)

        # 切换按钮
        btn_layout = QHBoxLayout()
        self.btn_preview = QPushButton("LibreOffice 预览")
        self.btn_source = QPushButton("文本编辑")
        for b in [self.btn_preview, self.btn_source]:
            b.setFixedHeight(30)
            b.setCheckable(True)
        self.btn_preview.clicked.connect(lambda: self._switch("preview"))
        self.btn_source.clicked.connect(lambda: self._switch("source"))
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_preview)
        btn_layout.addWidget(self.btn_source)
        layout.addLayout(btn_layout)

        self.btn_source.setChecked(True)
        self.stack.setCurrentIndex(0)

    def load_file(self, path: str):
        self._current_path = path
        self._preview_html = None

        # 清理旧临时目录
        if self._temp_dir and os.path.isdir(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir, ignore_errors=True)
            except Exception:
                pass
        self._temp_dir = None

        # 提取文本用于源码编辑
        if HAS_DOCX:
            try:
                doc = DocxDocument(path)
                text_lines = []
                for para in doc.paragraphs:
                    text = para.text
                    if text.strip():
                        text_lines.append(text)
                for table in doc.tables:
                    text_lines.append("--- [表格] ---")
                    for row in table.rows:
                        cells = [cell.text for cell in row.cells]
                        text_lines.append("\t".join(cells))
                self.source_editor.setPlainText("\n".join(text_lines))
            except Exception as e:
                self.source_editor.setPlainText(f"[无法读取 Word 文件]\n{str(e)}")
        else:
            self.source_editor.setPlainText("[需要安装 python-docx]\npip install python-docx")

        # LibreOffice 转换 HTML
        _ensure_lo_checked()
        if _LO_AVAILABLE and self.browser:
            self._preview_html = self._lo_convert_to_html(path)
        elif HAS_MAMMOTH and self.browser:
            self._preview_html = self._mammoth_convert(path)

        self.btn_source.setChecked(False)
        self.btn_preview.setChecked(True)
        self.stack.setCurrentIndex(1)  # 默认预览模式
        if self._preview_html and self.browser:
            self.browser.setHtml(self._preview_html)
        elif self.browser:
            self.browser.setHtml(
                "<p style='color:#888;padding:40px;'>"
                "(需要 LibreOffice 或 mammoth 库以支持原生预览)</p>")

    def _lo_convert_to_html(self, path: str) -> str | None:
        """使用 LibreOffice 将 docx 转换为 HTML"""
        self._temp_dir = tempfile.mkdtemp(prefix="ew_docx_")
        output = convert_with_libreoffice(path, self._temp_dir, "html")
        if output and os.path.exists(output):
            try:
                with open(output, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
            except Exception:
                pass
        return None

    def _mammoth_convert(self, path: str) -> str | None:
        """使用 mammoth 转换（回退方案）"""
        try:
            with open(path, "rb") as f:
                result = mammoth.convert_to_html(f)
            html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body {{ font-family: "Microsoft YaHei", "SimSun", sans-serif; padding: 40px 60px;
         color: #2C1810; background: #FDF5E6; max-width: 900px; margin: 0 auto; line-height: 1.8; }}
  h1 {{ border-bottom: 2px solid #722F37; padding-bottom: 10px; color: #4A1E28; }}
  h2 {{ border-bottom: 1px solid #8B3A44; padding-bottom: 6px; color: #5C1E26; }}
  h3 {{ color: #722F37; }}
  table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
  td, th {{ border: 1px solid #999; padding: 8px 14px; }}
  th {{ background: #722F37; color: #F0E6D0; }}
  tr:nth-child(even) {{ background: #F5EDE0; }}
  img {{ max-width: 100%; height: auto; margin: 8px 0; }}
  p {{ margin: 8px 0; }}
  ul, ol {{ margin: 8px 0; padding-left: 24px; }}
  blockquote {{ border-left: 3px solid #722F37; padding-left: 16px; margin: 12px 0; color: #5C1E26; background: #F5EDE0; }}
  pre {{ background: #2C1810; color: #F0E6D0; padding: 16px; border-radius: 6px; overflow-x: auto; }}
  code {{ background: #F5EDE0; padding: 2px 6px; border-radius: 3px; font-family: "Consolas", monospace; }}
</style></head>
<body>{result.value}</body></html>"""
            return html
        except Exception:
            return None

    def _switch(self, mode: str):
        if mode == "preview":
            if self._preview_html and self.browser:
                self.browser.setHtml(self._preview_html)
            elif self.browser:
                self.browser.setHtml(
                    "<p style='color:#888;padding:40px;'>"
                    "(需要 LibreOffice 或 mammoth 库以支持原生预览)</p>")
            self.stack.setCurrentIndex(1)
            self.btn_preview.setChecked(True)
            self.btn_source.setChecked(False)
        else:
            self.stack.setCurrentIndex(0)
            self.btn_source.setChecked(True)
            self.btn_preview.setChecked(False)

    def save_file(self):
        if self._current_path and HAS_DOCX:
            try:
                doc = DocxDocument(self._current_path)
                new_text = self.source_editor.toPlainText().split("\n")
                existing_paras = doc.paragraphs
                for i, para in enumerate(existing_paras):
                    para.text = new_text[i] if i < len(new_text) else ""
                for i in range(len(existing_paras), len(new_text)):
                    doc.add_paragraph(new_text[i])
                for i in range(len(existing_paras) - 1, len(new_text) - 1, -1):
                    if i >= 0 and i < len(existing_paras):
                        p = existing_paras[i]._element
                        p.getparent().remove(p)
                doc.save(self._current_path)
                return True
            except Exception:
                return False
        return False

    def closeEvent(self, event):
        if self._temp_dir and os.path.isdir(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir, ignore_errors=True)
            except Exception:
                pass
        self._temp_dir = None
        super().closeEvent(event)


# ===================== Excel 原生预览（HTML表格渲染，保留样式：颜色/字体/边框/对齐） =====================

def _xl_color_to_css(color_obj):
    """将 openpyxl 颜色对象转为 CSS 颜色字符串"""
    if color_obj is None:
        return None
    if hasattr(color_obj, 'rgb') and color_obj.rgb:
        rgb = str(color_obj.rgb)
        if len(rgb) == 8 and rgb.startswith('FF'):
            return f"#{rgb[2:]}"
        elif len(rgb) == 6:
            return f"#{rgb}"
    if hasattr(color_obj, 'theme') and color_obj.theme is not None:
        return None  # 主题色无法直接映射
    return None


def _xl_font_to_css(font) -> str:
    """将 openpyxl Font 转为 CSS 样式字符串"""
    styles = []
    if font.bold:
        styles.append("font-weight:bold")
    if font.italic:
        styles.append("font-style:italic")
    if font.underline:
        styles.append("text-decoration:underline")
    if font.size:
        styles.append(f"font-size:{font.size}pt")
    if font.name:
        styles.append(f"font-family:'{font.name}', sans-serif")
    color = _xl_color_to_css(font.color)
    if color:
        styles.append(f"color:{color}")
    return "; ".join(styles)


def _xl_fill_to_css(fill) -> str:
    """将 openpyxl Fill 转为 CSS background-color"""
    if fill and fill.fgColor:
        color = _xl_color_to_css(fill.fgColor)
        if color:
            return f"background-color:{color}"
    return ""


def _xl_alignment_to_css(align) -> str:
    """将 openpyxl Alignment 转为 CSS 样式"""
    styles = []
    if align:
        h_map = {"left": "left", "center": "center", "right": "right",
                 "justify": "justify", "distributed": "justify"}
        if align.horizontal and align.horizontal in h_map:
            styles.append(f"text-align:{h_map[align.horizontal]}")
        v_map = {"top": "top", "center": "middle", "bottom": "bottom"}
        if align.vertical and align.vertical in v_map:
            styles.append(f"vertical-align:{v_map[align.vertical]}")
        if align.wrap_text:
            styles.append("white-space:pre-wrap")
    return "; ".join(styles)


def _xl_border_to_css(border) -> str:
    """将 openpyxl Border 转为 CSS border 样式"""
    if not border:
        return ""
    parts = []
    for side_name, side in [("top", border.top), ("bottom", border.bottom),
                             ("left", border.left), ("right", border.right)]:
        if side and side.style:
            color = _xl_color_to_css(side.color) if side.color else "#ccc"
            parts.append(f"border-{side_name}:1px solid {color}")
    return "; ".join(parts)


def _xl_sheet_to_html(path: str) -> str:
    """openpyxl 回退方案：将 xlsx 转换为带样式的 HTML"""
    if not HAS_OPENPYXL:
        return None
    try:
        wb_styled = openpyxl.load_workbook(path)
        html_parts = []
        for sheet_name in wb_styled.sheetnames:
            ws = wb_styled[sheet_name]
            max_row = ws.max_row or 0
            max_col = ws.max_column or 0
            if max_row == 0:
                continue
            html_parts.append(f'<h2 style="color:#722F37;">Sheet: {sheet_name}</h2>')
            html_parts.append('<table>')
            for row_idx in range(1, max_row + 1):
                is_header = (row_idx == 1)
                tag = "th" if is_header else "td"
                html_parts.append("<tr>")
                for col_idx in range(1, max_col + 1):
                    cell = ws.cell(row=row_idx, column=col_idx)
                    cell_styles = []
                    font_css = _xl_font_to_css(cell.font)
                    if font_css:
                        cell_styles.append(font_css)
                    fill_css = _xl_fill_to_css(cell.fill)
                    if fill_css:
                        cell_styles.append(fill_css)
                    align_css = _xl_alignment_to_css(cell.alignment)
                    if align_css:
                        cell_styles.append(align_css)
                    border_css = _xl_border_to_css(cell.border)
                    if border_css:
                        cell_styles.append(border_css)
                    if is_header and not fill_css:
                        cell_styles.append("background:#722F37; color:#F0E6D0; font-weight:bold")
                    style_str = "; ".join(cell_styles)
                    val = str(cell.value) if cell.value is not None else ""
                    val = val.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    if not val.strip():
                        val = "&nbsp;"
                    html_parts.append(f'<{tag} style="{style_str}">{val}</{tag}>')
                html_parts.append("</tr>")
            html_parts.append("</table><br>")
        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body {{ font-family: "Microsoft YaHei", sans-serif; padding: 20px 30px;
         color: #2C1810; background: #FDF5E6; }}
  h2 {{ border-bottom: 2px solid #722F37; padding-bottom: 6px; color: #4A1E28; }}
  table {{ border-collapse: collapse; width: auto; margin-bottom: 24px; }}
  th {{ padding: 10px 16px; border: 1px solid #999; }}
  td {{ padding: 8px 14px; border: 1px solid #ccc; }}
  tr:nth-child(even) td {{ background: #FDF5E6; }}
  tr:nth-child(odd) td {{ background: #FFF; }}
</style></head>
<body>{"".join(html_parts)}</body></html>"""
    except Exception:
        return None


class XlsxViewer(QWidget):
    """使用 LibreOffice 将 xlsx 转换为 HTML，通过 QWebEngineView 渲染，预览效果与 Excel 高度一致"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_path = None
        self._preview_html = None
        self._temp_dir = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()

        self.source_editor = QPlainTextEdit()
        self.source_editor.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {EDIT_BG}; color: {EDIT_TEXT};
                font-family: "Consolas", "Courier New", monospace; font-size: {LARGE_FONT_SIZE}px;
            }}
        """)
        self.stack.addWidget(self.source_editor)   # 0

        if HAS_WEBENGINE:
            self.browser = QWebEngineView()
            self.stack.addWidget(self.browser)      # 1
        else:
            self.browser = None
            fallback = QLabel("  (需要 PyQtWebEngine 以预览)")
            fallback.setStyleSheet(f"color:{TEXT_COLOR}; background:{WINE_RED_DARK}; padding:20px;")
            fallback.setAlignment(Qt.AlignCenter)
            self.stack.addWidget(fallback)

        layout.addWidget(self.stack)

        btn_layout = QHBoxLayout()
        self.btn_preview = QPushButton("LibreOffice 预览")
        self.btn_source = QPushButton("文本编辑")
        for b in [self.btn_preview, self.btn_source]:
            b.setFixedHeight(30)
            b.setCheckable(True)
        self.btn_preview.clicked.connect(lambda: self._switch("preview"))
        self.btn_source.clicked.connect(lambda: self._switch("source"))
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_preview)
        btn_layout.addWidget(self.btn_source)
        layout.addLayout(btn_layout)

        self.btn_source.setChecked(True)
        self.stack.setCurrentIndex(0)

    def load_file(self, path: str):
        self._current_path = path
        self._preview_html = None

        if self._temp_dir and os.path.isdir(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir, ignore_errors=True)
            except Exception:
                pass
        self._temp_dir = None

        # 提取文本用于源码编辑
        if HAS_OPENPYXL:
            try:
                wb_styled = openpyxl.load_workbook(path)
                lines = []
                for sheet_name in wb_styled.sheetnames:
                    ws = wb_styled[sheet_name]
                    lines.append(f"=== Sheet: {sheet_name} ===")
                    max_row = ws.max_row or 0
                    max_col = ws.max_column or 0
                    if max_row == 0:
                        continue
                    for row_idx in range(1, max_row + 1):
                        row_values = []
                        for col_idx in range(1, max_col + 1):
                            cell = ws.cell(row=row_idx, column=col_idx)
                            val = str(cell.value) if cell.value is not None else ""
                            row_values.append(val)
                        row_str = "\t".join(row_values)
                        if row_str.strip():
                            lines.append(row_str)
                    lines.append("")
                self.source_editor.setPlainText("\n".join(lines))
            except Exception as e:
                self.source_editor.setPlainText(f"[无法读取 Excel 文件]\n{str(e)}")
        else:
            self.source_editor.setPlainText("[需要安装 openpyxl]\npip install openpyxl")

        # LibreOffice 转换 HTML
        _ensure_lo_checked()
        if _LO_AVAILABLE and self.browser:
            self._preview_html = self._lo_convert_to_html(path)
        elif HAS_OPENPYXL and self.browser:
            self._preview_html = _xl_sheet_to_html(path)

        self.btn_source.setChecked(False)
        self.btn_preview.setChecked(True)
        self.stack.setCurrentIndex(1)  # 默认预览模式
        if self._preview_html and self.browser:
            self.browser.setHtml(self._preview_html)
        elif self.browser:
            self.browser.setHtml(
                "<p style='color:#888;padding:40px;'>"
                "(需要 LibreOffice 或 openpyxl 以支持 Excel 预览)</p>")

    def _lo_convert_to_html(self, path: str) -> str | None:
        """使用 LibreOffice 将 xlsx 转换为 HTML"""
        self._temp_dir = tempfile.mkdtemp(prefix="ew_xlsx_")
        output = convert_with_libreoffice(path, self._temp_dir, "html")
        if output and os.path.exists(output):
            try:
                with open(output, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
            except Exception:
                pass
        return None

    def _switch(self, mode: str):
        if mode == "preview":
            if self._preview_html and self.browser:
                self.browser.setHtml(self._preview_html)
            elif self.browser:
                self.browser.setHtml(
                    "<p style='color:#888;padding:40px;'>"
                    "(需要 LibreOffice 或 openpyxl 以支持预览)</p>")
            self.stack.setCurrentIndex(1)
            self.btn_preview.setChecked(True)
            self.btn_source.setChecked(False)
        else:
            self.stack.setCurrentIndex(0)
            self.btn_source.setChecked(True)
            self.btn_preview.setChecked(False)

    def save_file(self):
        if self._current_path and HAS_OPENPYXL:
            try:
                wb = openpyxl.load_workbook(self._current_path)
                lines = self.source_editor.toPlainText().split("\n")

                # 按 sheet 分组数据
                sheets = {}
                current_sheet = wb.active.title if wb.sheetnames else "Sheet1"
                for line in lines:
                    if line.startswith("=== Sheet:") and "===" in line:
                        current_sheet = line.replace("=== Sheet:", "").replace("===", "").strip()
                        if current_sheet not in sheets:
                            sheets[current_sheet] = []
                        continue
                    if not line.strip():
                        continue
                    sheets.setdefault(current_sheet, []).append(line.split("\t"))

                # 写入各 sheet
                for sheet_name, rows in sheets.items():
                    if sheet_name not in wb.sheetnames:
                        wb.create_sheet(sheet_name)
                    ws = wb[sheet_name]
                    # 清空旧数据
                    for row in ws.iter_rows():
                        for cell in row:
                            cell.value = None
                    # 写入新数据
                    for ri, cells in enumerate(rows, 1):
                        for ci, val in enumerate(cells, 1):
                            ws.cell(row=ri, column=ci, value=val)

                wb.save(self._current_path)
                return True
            except Exception:
                return False
        return False

    def closeEvent(self, event):
        if self._temp_dir and os.path.isdir(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir, ignore_errors=True)
            except Exception:
                pass
        self._temp_dir = None
        super().closeEvent(event)


# ===================== PPT 预览（LibreOffice HTML + WebEngine，效果与 PowerPoint 高度一致） =====================

class PptxViewer(QWidget):
    """使用 LibreOffice 将 pptx 转换为 HTML，通过 QWebEngineView 渲染，预览效果与 PowerPoint 高度一致"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_path = None
        self._preview_html = None
        self._temp_dir = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()

        # 源码编辑
        self.source_editor = QPlainTextEdit()
        self.source_editor.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {EDIT_BG}; color: {EDIT_TEXT};
                font-family: "Consolas", "Courier New", monospace; font-size: {LARGE_FONT_SIZE}px;
            }}
        """)
        self.stack.addWidget(self.source_editor)   # 0

        # HTML 预览
        if HAS_WEBENGINE:
            self.browser = QWebEngineView()
            self.stack.addWidget(self.browser)      # 1
        else:
            self.browser = None
            fallback = QLabel("  (需要 PyQtWebEngine 以预览)")
            fallback.setStyleSheet(f"color:{TEXT_COLOR}; background:{WINE_RED_DARK}; padding:20px; font-size:{BASE_FONT_SIZE}px;")
            fallback.setAlignment(Qt.AlignCenter)
            self.stack.addWidget(fallback)

        layout.addWidget(self.stack)

        # 切换按钮
        btn_layout = QHBoxLayout()
        self.btn_preview = QPushButton("LibreOffice 预览")
        self.btn_source = QPushButton("文本编辑")
        for b in [self.btn_preview, self.btn_source]:
            b.setFixedHeight(30)
            b.setCheckable(True)
        self.btn_preview.clicked.connect(lambda: self._switch("preview"))
        self.btn_source.clicked.connect(lambda: self._switch("source"))
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_preview)
        btn_layout.addWidget(self.btn_source)
        layout.addLayout(btn_layout)

        self.btn_source.setChecked(True)
        self.stack.setCurrentIndex(0)

    def load_file(self, path: str):
        self._current_path = path
        self._preview_html = None

        if self._temp_dir and os.path.isdir(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir, ignore_errors=True)
            except Exception:
                pass
        self._temp_dir = None

        # 提取文本用于源码编辑
        if HAS_PPTX:
            try:
                prs = Presentation(path)
                lines = []
                for i, slide in enumerate(prs.slides, 1):
                    lines.append(f"=== Slide {i} ===")
                    for shape in slide.shapes:
                        if shape.has_text_frame:
                            for para in shape.text_frame.paragraphs:
                                if para.text.strip():
                                    lines.append(para.text)
                    lines.append("")
                self.source_editor.setPlainText("\n".join(lines))
            except Exception as e:
                self.source_editor.setPlainText(f"[无法读取 PPT 文件]\n{str(e)}")
        else:
            self.source_editor.setPlainText("[需要安装 python-pptx]\npip install python-pptx")

        # LibreOffice 转换 HTML
        _ensure_lo_checked()
        if _LO_AVAILABLE and self.browser:
            self._preview_html = self._lo_convert_to_html(path)

        self.btn_source.setChecked(False)
        self.btn_preview.setChecked(True)
        self.stack.setCurrentIndex(1)  # 默认预览模式
        if self._preview_html and self.browser:
            self.browser.setHtml(self._preview_html)
        elif self.browser:
            self.browser.setHtml(
                "<p style='color:#888;padding:40px;'>"
                "(需要 LibreOffice 以支持幻灯片预览)</p>")

    def _lo_convert_to_html(self, path: str) -> str | None:
        """使用 LibreOffice 将 pptx 转换为 HTML"""
        self._temp_dir = tempfile.mkdtemp(prefix="ew_pptx_")
        output = convert_with_libreoffice(path, self._temp_dir, "html")
        if output and os.path.exists(output):
            try:
                with open(output, "r", encoding="utf-8", errors="replace") as f:
                    return f.read()
            except Exception:
                pass
        return None

    def _switch(self, mode: str):
        if mode == "preview":
            if self._preview_html and self.browser:
                self.browser.setHtml(self._preview_html)
            elif self.browser:
                self.browser.setHtml(
                    "<p style='color:#888;padding:40px;'>"
                    "(需要 LibreOffice 以支持幻灯片预览)</p>")
            self.stack.setCurrentIndex(1)
            self.btn_preview.setChecked(True)
            self.btn_source.setChecked(False)
        else:
            self.stack.setCurrentIndex(0)
            self.btn_source.setChecked(True)
            self.btn_preview.setChecked(False)

    def save_file(self):
        if self._current_path and HAS_PPTX:
            try:
                prs = Presentation(self._current_path)
                new_text = self.source_editor.toPlainText().split("\n")
                pure_text = [l for l in new_text if l.strip() and not l.startswith("=== Slide")]
                text_idx = 0
                for slide in prs.slides:
                    for shape in slide.shapes:
                        if shape.has_text_frame:
                            for para in shape.text_frame.paragraphs:
                                if text_idx < len(pure_text):
                                    para.text = pure_text[text_idx]
                                    text_idx += 1
                                else:
                                    para.text = ""
                prs.save(self._current_path)
                return True
            except Exception:
                return False
        return False

    def closeEvent(self, event):
        if self._temp_dir and os.path.isdir(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir, ignore_errors=True)
            except Exception:
                pass
        self._temp_dir = None
        super().closeEvent(event)


# ===================== PDF 查看器（原生渲染） =====================

class PdfViewer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        if HAS_WEBENGINE:
            self.browser = QWebEngineView()
            layout.addWidget(self.browser)
        else:
            fallback = QLabel("  (需要安装 PyQtWebEngine 以预览 PDF)")
            fallback.setStyleSheet(f"color:{TEXT_COLOR}; background:{WINE_RED_DARK}; padding:20px; font-size:{BASE_FONT_SIZE}px;")
            fallback.setAlignment(Qt.AlignCenter)
            layout.addWidget(fallback)

    def load_file(self, path: str):
        if HAS_WEBENGINE:
            self.browser.load(QUrl.fromLocalFile(path))


# ===================== 欢迎页 =====================

class WelcomeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        title = QLabel("Edit Workbench")
        title.setStyleSheet(f"font-size:36px; color:{TEXT_COLOR}; font-weight:bold;")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("酒红色主题 · 多格式文件编辑器")
        subtitle.setStyleSheet(f"font-size:18px; color:{TEXT_COLOR};")
        subtitle.setAlignment(Qt.AlignCenter)

        hint = QLabel("从左侧资源管理器中选择文件进行预览和编辑")
        hint.setStyleSheet(f"font-size:15px; color:#C0A890; margin-top:10px;")
        hint.setAlignment(Qt.AlignCenter)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(hint)


# ===================== 搜索替换面板 =====================

class SearchReplacePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._editor_ref = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        self.setStyleSheet(f"background-color: {WINE_RED_DARK}; border-left: 1px solid {BORDER_COLOR};")

        title = QLabel("  查找与替换")
        title.setStyleSheet(f"font-weight:bold; font-size:{LARGE_FONT_SIZE}px; color:{TEXT_COLOR}; background:transparent;")
        layout.addWidget(title)

        layout.addWidget(QLabel("查找："))
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("输入查找内容...")
        self.find_input.textChanged.connect(self._highlight_find)
        layout.addWidget(self.find_input)

        layout.addWidget(QLabel("替换为："))
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("输入替换内容...")
        layout.addWidget(self.replace_input)

        btn_row = QHBoxLayout()
        self.btn_find_next = QPushButton("查找下一个")
        self.btn_replace = QPushButton("替换")
        self.btn_replace_all = QPushButton("全部替换")
        for b in [self.btn_find_next, self.btn_replace, self.btn_replace_all]:
            b.setFixedHeight(32)
        self.btn_find_next.clicked.connect(self._find_next)
        self.btn_replace.clicked.connect(self._replace_one)
        self.btn_replace_all.clicked.connect(self._replace_all)
        btn_row.addWidget(self.btn_find_next)
        btn_row.addWidget(self.btn_replace)
        btn_row.addWidget(self.btn_replace_all)
        layout.addLayout(btn_row)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color:#C0A890; background:transparent; font-size:{SMALL_FONT_SIZE}px;")
        layout.addWidget(self.status_label)

        layout.addStretch()
        self.setFixedWidth(260)
        self.hide()

    def set_editor(self, editor):
        self._editor_ref = editor

    def _get_text_edit_widget(self):
        if self._editor_ref:
            if isinstance(self._editor_ref, HtmlMdViewer):
                return self._editor_ref.source_editor
            if isinstance(self._editor_ref, DocxViewer):
                return self._editor_ref.source_editor
            if isinstance(self._editor_ref, XlsxViewer):
                return self._editor_ref.source_editor
            if isinstance(self._editor_ref, PptxViewer):
                return self._editor_ref.source_editor
            return self._editor_ref
        return None

    def _highlight_find(self):
        editor = self._get_text_edit_widget()
        if not editor or not self.find_input.text():
            self.status_label.setText("")
            return
        count = editor.toPlainText().count(self.find_input.text())
        self.status_label.setText(f"找到 {count} 处匹配" if count > 0 else "未找到")

    def _find_next(self):
        editor = self._get_text_edit_widget()
        if not editor or not self.find_input.text():
            return
        if not editor.find(self.find_input.text()):
            cursor = editor.textCursor()
            cursor.movePosition(cursor.Start)
            editor.setTextCursor(cursor)
            editor.find(self.find_input.text())

    def _replace_one(self):
        editor = self._get_text_edit_widget()
        if not editor or not self.find_input.text():
            return
        cursor = editor.textCursor()
        if cursor.hasSelection() and cursor.selectedText() == self.find_input.text():
            cursor.insertText(self.replace_input.text())
        self._find_next()

    def _replace_all(self):
        editor = self._get_text_edit_widget()
        if not editor or not self.find_input.text():
            return
        keyword = self.find_input.text()
        replacement = self.replace_input.text()
        text = editor.toPlainText()
        count = text.count(keyword)
        editor.setPlainText(text.replace(keyword, replacement))
        self.status_label.setText(f"已替换 {count} 处")


# ===================== 主窗口 =====================

class EditWorkbench(QMainWindow):

    TEXT_EXTS = {".txt", ".py", ".json", ".xml", ".yaml", ".yml", ".ini",
                 ".cfg", ".log", ".csv", ".c", ".cpp", ".h", ".java",
                 ".js", ".ts", ".css", ".scss", ".sql", ".sh", ".bat",
                 ".cmd", ".ps1", ".rb", ".go", ".rs"}
    IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp", ".svg"}
    HTML_EXTS = {".html", ".htm", ".md", ".markdown"}
    DOCX_EXTS = {".docx", ".doc"}
    XLSX_EXTS = {".xlsx", ".xls"}
    PPTX_EXTS = {".pptx", ".ppt"}
    PDF_EXTS = {".pdf"}

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Edit Workbench — 多格式编辑器")
        self.resize(1400, 900)
        self.setMinimumSize(1000, 600)

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)

        self.current_file = None
        self._drag_pos = None

        # 初始化 LibreOffice 检测
        _ensure_lo_checked()

        self._init_ui()
        self._init_menu()

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.title_bar = self._create_title_bar()
        root_layout.addWidget(self.title_bar)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)

        self.activity_bar = self._create_activity_bar()
        self.file_tree = self._create_file_tree()
        self.editor_stack = self._create_editor_area()

        splitter.addWidget(self.activity_bar)
        splitter.addWidget(self.file_tree)
        splitter.addWidget(self.editor_stack)

        splitter.setSizes([50, 280, 1070])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 0)
        splitter.setStretchFactor(2, 1)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        splitter.setCollapsible(2, False)

        root_layout.addWidget(splitter, 1)
        self.btn_explorer.setChecked(True)

    # ========== 自定义标题栏（项目名称在中间，下拉切换） ==========

    def _create_title_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(52)
        bar.setStyleSheet(f"background-color: {TITLE_BAR_BG}; border-bottom: 1px solid {BORDER_COLOR};")
        bar.mousePressEvent = self._title_bar_mouse_press
        bar.mouseMoveEvent = self._title_bar_mouse_move
        bar.mouseDoubleClickEvent = self._title_bar_double_click

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ===== 左侧区域：图标 + 菜单按钮 =====
        left_widget = QWidget()
        left_widget.setStyleSheet("background: transparent;")
        left_layout = QHBoxLayout(left_widget)
        left_layout.setContentsMargins(8, 0, 0, 0)
        left_layout.setSpacing(2)

        self.win_title = QLabel("  Edit Workbench")
        self.win_title.setStyleSheet(f"font-size:{TITLE_FONT_SIZE}px; font-weight:bold; color:{TEXT_COLOR}; background:transparent;")

        self.menu_btns = []
        menu_data = [
            ("文件", self._show_file_menu),
            ("编辑", self._show_edit_menu),
            ("选择", self._show_select_menu),
            ("查看", self._show_view_menu),
        ]
        for text, slot in menu_data:
            btn = QPushButton(text)
            btn.setFixedHeight(32)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; border: none;
                    font-size: {BASE_FONT_SIZE}px; padding: 4px 14px; color: {TEXT_COLOR};
                }}
                QPushButton:hover {{ background-color: {WINE_RED_HOVER}; border-radius: 4px; }}
            """)
            btn.clicked.connect(slot)
            self.menu_btns.append(btn)

        left_layout.addWidget(self.win_title)
        for btn in self.menu_btns:
            left_layout.addWidget(btn)

        # ===== 中间区域：项目名称（真正居中） =====
        center_widget = QWidget()
        center_widget.setStyleSheet("background: transparent;")
        center_layout = QHBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        self.project_btn = QPushButton("MyProject  ▼")
        self.project_btn.setFixedHeight(34)
        self.project_btn.setMinimumWidth(160)
        self.project_btn.setCursor(Qt.PointingHandCursor)
        self.project_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; border: none;
                font-size: {TITLE_FONT_SIZE}px; font-weight: bold; color: {TEXT_COLOR};
                padding: 0 20px;
            }}
            QPushButton:hover {{ background-color: {WINE_RED_HOVER}; border-radius: 4px; }}
            QPushButton::menu-indicator {{ image: none; }}
        """)
        self.project_btn.clicked.connect(self._show_project_menu)

        self.project_menu = QMenu(self)
        self.project_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {MENU_BG};
                color: {TEXT_COLOR};
                border: 2px solid {WINE_RED_LIGHT};
                border-radius: 6px;
                padding: 4px;
                font-size: {BASE_FONT_SIZE}px;
            }}
            QMenu::item {{
                padding: 10px 40px 10px 20px;
                border-radius: 4px;
                margin: 2px 4px;
            }}
            QMenu::item:selected {{
                background-color: {WINE_RED_HOVER};
            }}
            QMenu::separator {{
                height: 1px;
                background: {BORDER_COLOR};
                margin: 4px 8px;
            }}
        """)
        self.project_menu.aboutToShow.connect(self._build_project_menu)

        center_layout.addStretch()
        center_layout.addWidget(self.project_btn)
        center_layout.addStretch()

        # ===== 右侧区域：搜索框 + 工具按钮 + 窗口控制 =====
        right_widget = QWidget()
        right_widget.setStyleSheet("background: transparent;")
        right_layout = QHBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 4, 0)
        right_layout.setSpacing(4)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索文件...")
        self.search_box.setFixedWidth(220)
        self.search_box.setFixedHeight(32)
        self.search_box.setStyleSheet(f"""
            QLineEdit {{
                background-color: #FDF5E6;
                color: #2C1810;
                border: 1px solid {BORDER_COLOR};
                border-radius: 4px;
                padding: 6px 10px 6px 30px;
                font-size: {BASE_FONT_SIZE}px;
            }}
            QLineEdit::placeholder {{
                color: #FFFFFF;
            }}
        """)
        # 搜索图标
        icon_pixmap = QPixmap(16, 16)
        icon_pixmap.fill(Qt.transparent)
        painter = QPainter(icon_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor("#CCCCCC"), 2))
        painter.drawEllipse(1, 1, 11, 11)
        painter.drawLine(10, 10, 14, 14)
        painter.end()
        search_action = QAction(QIcon(icon_pixmap), "", self.search_box)
        self.search_box.addAction(search_action, QLineEdit.LeadingPosition)
        self.search_box.textChanged.connect(self._on_search)

        self.btn_open_folder = QPushButton("打开文件夹")
        self.btn_open_folder.setFixedHeight(32)
        self.btn_open_folder.clicked.connect(self._open_folder)

        self.btn_save = QPushButton("保存")
        self.btn_save.setFixedHeight(32)
        self.btn_save.clicked.connect(self._save_current_file)

        self.btn_min = QPushButton("─")
        self.btn_max = QPushButton("□")
        self.btn_close = QPushButton("✕")
        for btn_data in [
            (self.btn_min, self.showMinimized),
            (self.btn_max, self._toggle_maximize),
            (self.btn_close, self.close),
        ]:
            btn, slot = btn_data
            btn.setFixedSize(40, 32)
            btn.clicked.connect(slot)
            btn.setStyleSheet(f"""
                QPushButton {{ background: transparent; border: none; font-size:{LARGE_FONT_SIZE}px; color:{TEXT_COLOR}; }}
                QPushButton:hover {{ background-color: {WINE_RED_HOVER}; border-radius: 3px; }}
            """)
        self.btn_close.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: none; font-size:{LARGE_FONT_SIZE}px; color:{TEXT_COLOR}; }}
            QPushButton:hover {{ background-color: #D93636; border-radius: 3px; color: white; }}
        """)

        right_layout.addWidget(self.search_box)
        right_layout.addWidget(self.btn_open_folder)
        right_layout.addWidget(self.btn_save)
        right_layout.addSpacing(8)
        right_layout.addWidget(self.btn_min)
        right_layout.addWidget(self.btn_max)
        right_layout.addWidget(self.btn_close)

        # 主布局：左 | 中（真正居中） | 右
        layout.addWidget(left_widget)
        layout.addWidget(center_widget, 1)  # stretch=1 让中间区域占满剩余空间
        layout.addWidget(right_widget)

        return bar

    def _show_project_menu(self):
        """点击项目名称弹出下拉菜单"""
        self.project_menu.exec_(self.project_btn.mapToGlobal(QPoint(0, self.project_btn.height())))

    def _build_project_menu(self):
        """构建历史项目下拉菜单"""
        self.project_menu.clear()

        # 当前项目标题
        current_name = self.project_btn.text().replace("  ▼", "").strip()
        title_action = self.project_menu.addAction(f"  当前项目：{current_name}")
        title_action.setEnabled(False)
        font = title_action.font()
        font.setBold(True)
        title_action.setFont(font)

        self.project_menu.addSeparator()

        # 历史项目列表
        history = load_project_history()
        current_root = self.model.filePath(self.tree.rootIndex())
        if history:
            for folder in history:
                name = os.path.basename(folder)
                is_current = os.path.abspath(folder) == os.path.abspath(current_root)
                label = f"  {name}" + ("  ✓" if is_current else "")
                a = self.project_menu.addAction(label)
                a.setData(folder)
                if is_current:
                    a.setEnabled(False)
                    font = a.font()
                    font.setBold(True)
                    a.setFont(font)
            self.project_menu.addSeparator()

        # 操作按钮
        self.project_menu.addAction("  + 打开其他文件夹...", self._open_folder)
        if history:
            clear_action = self.project_menu.addAction("  ✕ 清除历史记录")
            clear_action.triggered.connect(self._clear_project_history)

        self.project_menu.triggered.connect(self._on_project_selected)

    def _on_project_selected(self, action):
        folder = action.data()
        if folder and os.path.isdir(folder) and folder != self.model.filePath(self.tree.rootIndex()):
            self._switch_project(folder)

    def _switch_project(self, folder: str):
        self.tree.setRootIndex(self.model.index(folder))
        self.project_btn.setText(f"{os.path.basename(folder)}  ▼")
        self.setWindowTitle(f"{os.path.basename(folder)} — Edit Workbench")
        add_to_history(folder)

    def _clear_project_history(self):
        save_project_history([])
        self.project_btn.setText("MyProject  ▼")
        self.setWindowTitle("Edit Workbench")
        self.tree.setRootIndex(self.model.index(QDir.homePath()))

    # ========== 标题栏拖拽 ==========

    def _title_bar_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos()

    def _title_bar_mouse_move(self, event):
        if self._drag_pos is not None and event.buttons() == Qt.LeftButton:
            delta = event.globalPos() - self._drag_pos
            self.move(self.pos() + delta)
            self._drag_pos = event.globalPos()

    def _title_bar_double_click(self, event):
        if event.button() == Qt.LeftButton:
            self._toggle_maximize()

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            self.btn_max.setText("□")
        else:
            self.showMaximized()
            self.btn_max.setText("❐")

    # ========== 菜单 ==========

    def _init_menu(self):
        self.menu_file = QMenu(self)
        self.menu_file.addAction("打开文件夹...", self._open_folder)
        self.menu_file.addAction("打开文件...", self._open_file_dialog)
        self.menu_file.addSeparator()
        self.menu_file.addAction("保存 Ctrl+S", self._save_current_file)
        self.menu_file.addSeparator()
        self.menu_file.addAction("退出 Alt+F4", self.close)

        self.menu_edit = QMenu(self)
        self.menu_edit.addAction("撤销 Ctrl+Z", lambda: self._editor_action("undo"))
        self.menu_edit.addAction("重做 Ctrl+Y", lambda: self._editor_action("redo"))
        self.menu_edit.addSeparator()
        self.menu_edit.addAction("剪切 Ctrl+X", lambda: self._editor_action("cut"))
        self.menu_edit.addAction("复制 Ctrl+C", lambda: self._editor_action("copy"))
        self.menu_edit.addAction("粘贴 Ctrl+V", lambda: self._editor_action("paste"))
        self.menu_edit.addAction("全选 Ctrl+A", lambda: self._editor_action("selectAll"))

        self.menu_select = QMenu(self)
        self.menu_select.addAction("刷新文件树", self._refresh_tree)

        self.menu_view = QMenu(self)
        self.menu_view.addAction("切换文件树", self._toggle_file_tree)
        self.menu_view.addAction("查找替换 Ctrl+F", self._toggle_search_panel)

        QShortcut(QKeySequence("Ctrl+S"), self, self._save_current_file)
        QShortcut(QKeySequence("Ctrl+F"), self, self._toggle_search_panel)

    def _show_file_menu(self):
        self.menu_file.exec_(self.menu_btns[0].mapToGlobal(QPoint(0, self.menu_btns[0].height())))

    def _show_edit_menu(self):
        self.menu_edit.exec_(self.menu_btns[1].mapToGlobal(QPoint(0, self.menu_btns[1].height())))

    def _show_select_menu(self):
        self.menu_select.exec_(self.menu_btns[2].mapToGlobal(QPoint(0, self.menu_btns[2].height())))

    def _show_view_menu(self):
        self.menu_view.exec_(self.menu_btns[3].mapToGlobal(QPoint(0, self.menu_btns[3].height())))

    # ========== 活动栏 ==========

    def _create_activity_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedWidth(50)
        bar.setStyleSheet(f"background-color: {WINE_RED_DARK};")
        layout = QVBoxLayout(bar)
        layout.setContentsMargins(4, 8, 4, 8)
        layout.setSpacing(6)

        self.btn_explorer = QPushButton("\U0001F4C1\n资源")
        self.btn_search_toggle = QPushButton("\U0001F50D\n搜索")

        for btn in [self.btn_explorer, self.btn_search_toggle]:
            btn.setCheckable(True)
            btn.setFixedSize(42, 42)
            btn.setStyleSheet(f"""
                QPushButton {{ background: transparent; border: none; color: {TEXT_COLOR}; font-size: 11px; }}
                QPushButton:hover {{ background-color: {WINE_RED_HOVER}; border-radius: 4px; }}
                QPushButton:checked {{ background-color: {WINE_RED_LIGHT}; border-radius: 4px; }}
            """)

        self.btn_explorer.clicked.connect(lambda: self._show_panel("explorer"))
        self.btn_search_toggle.clicked.connect(lambda: self._show_panel("search"))

        layout.addWidget(self.btn_explorer)
        layout.addWidget(self.btn_search_toggle)
        layout.addStretch(1)
        return bar

    # ========== 文件树 ==========

    def _create_file_tree(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.file_tree_title = QLabel("  资源管理器")
        self.file_tree_title.setFixedHeight(38)
        self.file_tree_title.setStyleSheet(f"""
            font-weight: bold; font-size: {BASE_FONT_SIZE}px; color: {TEXT_COLOR};
            background: {MENU_BG}; padding-left: 8px;
        """)
        layout.addWidget(self.file_tree_title)

        self.file_stack = QStackedWidget()
        self.file_stack.setStyleSheet(f"background-color: {WINE_RED};")

        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.rootPath())
        self.model.setFilter(QDir.NoDotAndDotDot | QDir.AllEntries | QDir.Dirs | QDir.Files)
        self.model.setNameFilters(["*.*"])
        self.model.setNameFilterDisables(False)

        self.tree = QTreeView()
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(QDir.homePath()))
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(18)
        self.tree.setAnimated(True)
        self.tree.hideColumn(1)
        self.tree.hideColumn(2)
        self.tree.hideColumn(3)
        self.tree.clicked.connect(self._on_tree_clicked)

        self.file_stack.addWidget(self.tree)             # 0

        self.search_panel = SearchReplacePanel()
        self.file_stack.addWidget(self.search_panel)     # 1

        self.file_stack.setCurrentIndex(0)
        layout.addWidget(self.file_stack, 1)
        return container

    # ========== 编辑器区域 ==========

    def _create_editor_area(self) -> QStackedWidget:
        stack = QStackedWidget()

        self.welcome = WelcomeWidget()           # 0
        stack.addWidget(self.welcome)

        self.text_editor = TextEditor()          # 1
        stack.addWidget(self.text_editor)

        self.image_viewer = ImageViewer()        # 2
        stack.addWidget(self.image_viewer)

        self.html_viewer = HtmlMdViewer()        # 3
        stack.addWidget(self.html_viewer)

        self.docx_viewer = DocxViewer()    # 4
        stack.addWidget(self.docx_viewer)

        self.xlsx_viewer = XlsxViewer()    # 5
        stack.addWidget(self.xlsx_viewer)

        self.pptx_viewer = PptxViewer()    # 6
        stack.addWidget(self.pptx_viewer)

        self.pdf_viewer = PdfViewer()            # 7
        stack.addWidget(self.pdf_viewer)

        stack.setCurrentIndex(0)
        return stack

    # ========== 文件打开 ==========

    def _open_file(self, path: str):
        ext = os.path.splitext(path)[1].lower()
        self.current_file = path

        if ext in self.TEXT_EXTS:
            self.text_editor.load_file(path)
            self.editor_stack.setCurrentIndex(1)
            self.search_panel.set_editor(self.text_editor)
        elif ext in self.IMAGE_EXTS:
            self.image_viewer.load_file(path)
            self.editor_stack.setCurrentIndex(2)
        elif ext in self.HTML_EXTS:
            self.html_viewer.load_file(path)
            self.editor_stack.setCurrentIndex(3)
            self.search_panel.set_editor(self.html_viewer)
        elif ext in self.DOCX_EXTS:
            self.docx_viewer.load_file(path)
            self.editor_stack.setCurrentIndex(4)
            self.search_panel.set_editor(self.docx_viewer)
        elif ext in self.XLSX_EXTS:
            self.xlsx_viewer.load_file(path)
            self.editor_stack.setCurrentIndex(5)
            self.search_panel.set_editor(self.xlsx_viewer)
        elif ext in self.PPTX_EXTS:
            self.pptx_viewer.load_file(path)
            self.editor_stack.setCurrentIndex(6)
            self.search_panel.set_editor(self.pptx_viewer)
        elif ext in self.PDF_EXTS:
            self.pdf_viewer.load_file(path)
            self.editor_stack.setCurrentIndex(7)
        else:
            self.text_editor.load_file(path)
            self.editor_stack.setCurrentIndex(1)
            self.search_panel.set_editor(self.text_editor)

        self.setWindowTitle(f"{os.path.basename(path)} — Edit Workbench")

    def _get_current_editor(self):
        w = self.editor_stack.currentWidget()
        if w and hasattr(w, "save_file"):
            return w
        return None

    def _save_current_file(self):
        editor = self._get_current_editor()
        if editor and editor.save_file():
            QMessageBox.information(self, "保存", "文件已保存。")
        elif editor:
            QMessageBox.warning(self, "保存失败", "无法保存文件。")

    def _editor_action(self, action: str):
        w = self.editor_stack.currentWidget()
        if isinstance(w, HtmlMdViewer):
            w = w.source_editor
        if isinstance(w, DocxViewer):
            w = w.source_editor
        if isinstance(w, XlsxViewer):
            w = w.source_editor
        if isinstance(w, PptxViewer):
            w = w.source_editor
        if hasattr(w, action):
            getattr(w, action)()

    # ========== 事件处理 ==========

    def _on_tree_clicked(self, index):
        path = self.model.filePath(index)
        if os.path.isfile(path):
            self._open_file(path)

    def _on_search(self, text: str):
        if text.strip():
            self.model.setNameFilters([f"*{text}*"])
        else:
            self.model.setNameFilters(["*.*"])

    def _show_panel(self, panel: str):
        if panel == "explorer":
            self.file_stack.setCurrentIndex(0)
            self.file_tree_title.setText("  资源管理器")
            self.btn_explorer.setChecked(True)
            self.btn_search_toggle.setChecked(False)
        elif panel == "search":
            self.btn_explorer.setChecked(False)
            self.btn_search_toggle.setChecked(True)
            self._toggle_search_panel()

    def _toggle_search_panel(self):
        if self.file_stack.currentIndex() == 1:
            self.file_stack.setCurrentIndex(0)
            self.file_tree_title.setText("  资源管理器")
            self.btn_search_toggle.setChecked(False)
        else:
            self.file_stack.setCurrentIndex(1)
            self.file_tree_title.setText("  查找与替换")
            self.btn_search_toggle.setChecked(True)
            self.search_panel.find_input.setFocus()

    def _open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹", QDir.homePath())
        if folder:
            self._switch_project(folder)

    def _open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "打开文件", QDir.homePath())
        if path:
            self._open_file(path)
            parent_dir = os.path.dirname(path)
            self.tree.setRootIndex(self.model.index(parent_dir))

    def _refresh_tree(self):
        folder = self.model.filePath(self.tree.rootIndex())
        self.model.setRootPath("")
        self.model.setRootPath(folder)
        self.tree.setRootIndex(self.model.index(folder))

    def _toggle_file_tree(self):
        self.file_tree.setVisible(not self.file_tree.isVisible())


# ===================== 入口 =====================

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(wine_style())
    window = EditWorkbench()
    sample_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_files")
    if os.path.isdir(sample_dir):
        window._switch_project(sample_dir)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()