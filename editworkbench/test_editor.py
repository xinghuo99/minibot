# -*- coding: utf-8 -*-
"""
自动化测试 — 测试 sample_files 文件夹内所有格式文件的打开、编辑、搜索替换功能
运行方式: python test_editor.py
"""

import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

import main as editor_module

# ===================== 测试辅助 =====================
_passed = 0
_failed = 0
SAMPLE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_files")


def log(msg: str):
    print(f"  {msg}")


def ok(msg: str):
    global _passed
    _passed += 1
    print(f"  [PASS] {msg}")


def fail(msg: str):
    global _failed
    _failed += 1
    print(f"  [FAIL] {msg}")


def assert_true(condition, msg: str):
    if condition:
        ok(msg)
    else:
        fail(msg)


# ===================== 测试用例 =====================

def test_text_editor():
    """测试 TextEditor 打开 txt/py/json 文件"""
    print("\n--- 测试: TextEditor ---")
    editor = editor_module.TextEditor()

    for fname, keyword in [
        ("readme.txt", "Edit Workbench"),
        ("hello.py", "def greet"),
        ("config.json", "EditWorkbench"),
    ]:
        path = os.path.join(SAMPLE_DIR, fname)
        if not os.path.isfile(path):
            print(f"  [SKIP] {fname} 不存在")
            continue
        editor.load_file(path)
        content = editor.toPlainText()
        assert_true(keyword in content, f"{fname} 加载成功")
        assert_true(not editor.isReadOnly(), f"{fname} 编辑器可编辑")


def test_html_md_viewer():
    """测试 HtmlMdViewer 打开 md/html 文件，HTML默认预览模式"""
    print("\n--- 测试: HtmlMdViewer ---")
    viewer = editor_module.HtmlMdViewer()

    # 测试 MD 文件 - 默认源码模式
    path_md = os.path.join(SAMPLE_DIR, "guide.md")
    if os.path.isfile(path_md):
        viewer.load_file(path_md)
        content = viewer.source_editor.toPlainText()
        assert_true("使用指南" in content, "md 加载成功")
        assert_true(not viewer.source_editor.isReadOnly(), "md 源码编辑器可编辑")
        assert_true(viewer.stack.currentIndex() == 0, "md 默认源码模式")
        # 切换到预览模式
        viewer._switch_view("preview")
        assert_true(viewer.stack.currentIndex() == 1, "md 可切换到预览模式")

    # 测试 HTML 文件 - 默认预览模式（网页形式）
    path_html = os.path.join(SAMPLE_DIR, "demo.html")
    if os.path.isfile(path_html):
        viewer.load_file(path_html)
        content = viewer.source_editor.toPlainText()
        assert_true("<h1>" in content, "html 加载成功")
        assert_true(not viewer.source_editor.isReadOnly(), "html 源码编辑器可编辑")
        assert_true(viewer._is_html, "html 文件类型识别正确")
        assert_true(viewer.stack.currentIndex() == 1, "html 默认预览模式")
        # 可以切换到源码模式
        viewer._switch_view("source")
        assert_true(viewer.stack.currentIndex() == 0, "html 可切换到源码模式")


def test_docx_viewer():
    """测试 DocxViewer（LibreOffice HTML 预览）"""
    print("\n--- 测试: DocxViewer ---")
    path = os.path.join(SAMPLE_DIR, "sample.docx")
    if not os.path.isfile(path):
        print("  [SKIP] sample.docx 不存在")
        return
    if not editor_module.HAS_DOCX:
        print("  [SKIP] python-docx 未安装")
        return

    viewer = editor_module.DocxViewer()
    viewer.load_file(path)
    content = viewer.source_editor.toPlainText()
    assert_true("Word 示例文档" in content, "docx 文本加载成功")
    assert_true(not viewer.source_editor.isReadOnly(), "docx 源码编辑器可编辑")
    assert_true(hasattr(viewer, "_preview_html"), "docx 预览HTML属性存在")
    assert_true(hasattr(viewer, "source_editor"), "docx 有 source_editor 属性")
    assert_true(hasattr(viewer, "browser"), "docx 有 browser 属性")
    assert_true(hasattr(viewer, "btn_preview"), "docx 预览按钮存在")
    assert_true(hasattr(viewer, "btn_source"), "docx 源码按钮存在")

    # 测试保存
    backup = content
    viewer.source_editor.setPlainText("修改后的docx内容\n新段落")
    result = viewer.save_file()
    assert_true(result, "docx 保存成功")
    # 还原
    viewer.source_editor.setPlainText(backup)
    viewer.save_file()


def test_xlsx_viewer():
    """测试 XlsxViewer（LibreOffice HTML 预览）"""
    print("\n--- 测试: XlsxViewer ---")
    path = os.path.join(SAMPLE_DIR, "sample.xlsx")
    if not os.path.isfile(path):
        print("  [SKIP] sample.xlsx 不存在")
        return
    if not editor_module.HAS_OPENPYXL:
        print("  [SKIP] openpyxl 未安装")
        return

    viewer = editor_module.XlsxViewer()
    viewer.load_file(path)
    content = viewer.source_editor.toPlainText()
    assert_true("员工信息" in content, "xlsx Sheet 加载成功")
    assert_true("张三" in content, "xlsx 数据加载成功")
    assert_true(not viewer.source_editor.isReadOnly(), "xlsx 源码编辑器可编辑")
    assert_true(hasattr(viewer, "source_editor"), "xlsx 有 source_editor 属性")
    assert_true(hasattr(viewer, "browser"), "xlsx 有 browser 属性")
    assert_true(hasattr(viewer, "btn_preview"), "xlsx 预览按钮存在")
    assert_true(hasattr(viewer, "btn_source"), "xlsx 源码按钮存在")

    # 测试保存
    backup = content
    viewer.source_editor.setPlainText("员工信息\t年龄\t职位\n张三\t30\t工程师")
    result = viewer.save_file()
    assert_true(result, "xlsx 保存成功")
    # 还原
    viewer.source_editor.setPlainText(backup)
    viewer.save_file()


def test_pptx_viewer():
    """测试 PptxViewer（LibreOffice HTML 预览）"""
    print("\n--- 测试: PptxViewer ---")
    path = os.path.join(SAMPLE_DIR, "sample.pptx")
    if not os.path.isfile(path):
        print("  [SKIP] sample.pptx 不存在")
        return
    if not editor_module.HAS_PPTX:
        print("  [SKIP] python-pptx 未安装")
        return

    viewer = editor_module.PptxViewer()
    viewer.load_file(path)
    content = viewer.source_editor.toPlainText()
    assert_true("Edit Workbench" in content, "pptx 标题加载成功")
    assert_true("Slide 1" in content, "pptx 幻灯片加载成功")
    assert_true(not viewer.source_editor.isReadOnly(), "pptx 源码编辑器可编辑")
    assert_true(hasattr(viewer, "btn_preview"), "pptx 预览按钮存在")
    assert_true(hasattr(viewer, "btn_source"), "pptx 源码按钮存在")
    assert_true(hasattr(viewer, "browser"), "pptx 有 browser 属性")

    # 测试保存
    backup = content
    viewer.source_editor.setPlainText("Slide 1\n新标题\n新内容")
    result = viewer.save_file()
    assert_true(result, "pptx 保存成功")
    # 还原
    viewer.source_editor.setPlainText(backup)
    viewer.save_file()


def test_libreoffice_available():
    """测试 LibreOffice 检测与转换功能"""
    print("\n--- 测试: LibreOffice 检测 ---")
    # 触发懒加载检测
    editor_module._ensure_lo_checked()
    lo_available = editor_module._LO_AVAILABLE
    if lo_available:
        ok("LibreOffice 可用")
        assert_true(editor_module._LO_SOFFICE is not None, "LibreOffice soffice 路径已找到")
        assert_true(callable(editor_module.convert_with_libreoffice), "convert_with_libreoffice 函数存在")
        assert_true(hasattr(editor_module, "_check_lo_available"), "_check_lo_available 函数存在")
        assert_true(hasattr(editor_module, "_find_libreoffice"), "_find_libreoffice 函数存在")
    else:
        print("  [SKIP] LibreOffice 未安装或不可用（降级到 mammoth/openpyxl 渲染）")

    # 测试 DocxViewer 有 _lo_convert_to_html 方法
    viewer = editor_module.DocxViewer()
    assert_true(hasattr(viewer, "_lo_convert_to_html"), "DocxViewer 有 _lo_convert_to_html 方法")
    assert_true(hasattr(viewer, "_mammoth_convert"), "DocxViewer 有 _mammoth_convert 回退方法")

    # 测试 XlsxViewer 有 _lo_convert_to_html 方法
    viewer = editor_module.XlsxViewer()
    assert_true(hasattr(viewer, "_lo_convert_to_html"), "XlsxViewer 有 _lo_convert_to_html 方法")

    # 测试 PptxViewer 有 _lo_convert_to_html 方法
    viewer = editor_module.PptxViewer()
    assert_true(hasattr(viewer, "_lo_convert_to_html"), "PptxViewer 有 _lo_convert_to_html 方法")


def test_libreoffice_conversion():
    """测试 LibreOffice 实际转换（如果可用）"""
    print("\n--- 测试: LibreOffice 转换 ---")
    editor_module._ensure_lo_checked()
    if not editor_module._LO_AVAILABLE:
        print("  [SKIP] LibreOffice 不可用")
        return

    import tempfile

    # 测试 docx 转换
    path_docx = os.path.join(SAMPLE_DIR, "sample.docx")
    if os.path.isfile(path_docx):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = editor_module.convert_with_libreoffice(path_docx, tmpdir, "html")
            if result and os.path.exists(result):
                ok("docx LibreOffice 转换成功")
                with open(result, "r", encoding="utf-8", errors="replace") as f:
                    html = f.read()
                assert_true(len(html) > 100, "docx 转换HTML内容非空")
                assert_true("html" in html.lower(), "docx 转换包含HTML结构")
            else:
                fail("docx LibreOffice 转换失败")

    # 测试 xlsx 转换
    path_xlsx = os.path.join(SAMPLE_DIR, "sample.xlsx")
    if os.path.isfile(path_xlsx):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = editor_module.convert_with_libreoffice(path_xlsx, tmpdir, "html")
            if result and os.path.exists(result):
                ok("xlsx LibreOffice 转换成功")
                with open(result, "r", encoding="utf-8", errors="replace") as f:
                    html = f.read()
                assert_true(len(html) > 100, "xlsx 转换HTML内容非空")
            else:
                fail("xlsx LibreOffice 转换失败")

    # 测试 pptx 转换
    path_pptx = os.path.join(SAMPLE_DIR, "sample.pptx")
    if os.path.isfile(path_pptx):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = editor_module.convert_with_libreoffice(path_pptx, tmpdir, "html")
            if result and os.path.exists(result):
                ok("pptx LibreOffice 转换成功")
                with open(result, "r", encoding="utf-8", errors="replace") as f:
                    html = f.read()
                assert_true(len(html) > 100, "pptx 转换HTML内容非空")
            else:
                fail("pptx LibreOffice 转换失败")


def test_pdf_viewer():
    """测试 PdfViewer"""
    print("\n--- 测试: PdfViewer ---")
    path = os.path.join(SAMPLE_DIR, "sample.pdf")
    if not os.path.isfile(path):
        print("  [SKIP] sample.pdf 不存在")
        return

    viewer = editor_module.PdfViewer()
    try:
        viewer.load_file(path)
        if editor_module.HAS_WEBENGINE:
            ok("pdf 加载成功 (WebEngine)")
        else:
            ok("pdf 查看器已创建 (无WebEngine)")
    except Exception as e:
        fail(f"pdf 加载失败: {e}")


def test_image_viewer():
    """测试 ImageViewer 打开 png/jpg 并测试编辑功能"""
    print("\n--- 测试: ImageViewer ---")
    viewer = editor_module.ImageViewer()

    for fname in ["sample.png", "sample.jpg"]:
        path = os.path.join(SAMPLE_DIR, fname)
        if not os.path.isfile(path):
            print(f"  [SKIP] {fname} 不存在")
            continue
        viewer.load_file(path)
        # 检查是否有 pixmap
        if hasattr(viewer, "_pixmap") and viewer._pixmap and not viewer._pixmap.isNull():
            ok(f"{fname} 图片加载成功")
        else:
            fail(f"{fname} 图片加载失败或为空")

        # 测试缩放
        viewer._zoom_in()
        assert_true(viewer._scale > 1.0, f"{fname} 放大成功")
        viewer._zoom_out()
        assert_true(viewer._scale < 1.25, f"{fname} 缩小成功")

        # 测试旋转
        viewer._rotate_image()
        assert_true(viewer._rotation == 90, f"{fname} 旋转90度成功")
        viewer._reset_view()
        assert_true(viewer._rotation == 0 and viewer._scale == 1.0, f"{fname} 还原视图成功")

        # 测试保存
        result = viewer.save_file()
        assert_true(result, f"{fname} 保存成功")


def test_search_replace_panel():
    """测试搜索替换面板"""
    print("\n--- 测试: SearchReplacePanel ---")
    panel = editor_module.SearchReplacePanel()
    editor = editor_module.TextEditor()
    editor.setPlainText("Hello World\n搜索目标在这里\nHello again\n找到目标文字")

    panel.set_editor(editor)

    # 查找计数
    panel.find_input.setText("Hello")
    assert_true("2" in panel.status_label.text(), "搜索 'Hello' 找到 2 处")

    panel.find_input.setText("目标")
    assert_true("2" in panel.status_label.text(), "搜索 '目标' 找到 2 处")

    panel.find_input.setText("不存在")
    assert_true("未找到" in panel.status_label.text(), "搜索不存在的词返回未找到")

    # 全部替换
    panel.find_input.setText("Hello")
    panel.replace_input.setText("你好")
    panel._replace_all()
    content = editor.toPlainText()
    assert_true("你好" in content, "全部替换成功")
    assert_true("Hello" not in content, "原文已全部替换")


def test_switch_search_panel():
    """测试搜索面板与资源管理器切换"""
    print("\n--- 测试: 搜索面板切换 ---")
    # 模拟切换逻辑
    stack = editor_module.QStackedWidget()
    tree = editor_module.QTreeView()
    panel = editor_module.SearchReplacePanel()
    stack.addWidget(tree)   # 0
    stack.addWidget(panel)  # 1

    assert_true(stack.currentIndex() == 0, "初始显示文件树")
    stack.setCurrentIndex(1)
    assert_true(stack.currentIndex() == 1, "切换到搜索面板")
    stack.setCurrentIndex(0)
    assert_true(stack.currentIndex() == 0, "切回文件树")


def test_file_type_mapping():
    """测试所有必需的格式都被正确映射"""
    print("\n--- 测试: 文件类型映射 ---")
    required = {".txt", ".py", ".json", ".md", ".html", ".png", ".jpg",
                ".docx", ".xlsx", ".pptx", ".pdf"}
    all_supported = (editor_module.EditWorkbench.TEXT_EXTS |
                     editor_module.EditWorkbench.IMAGE_EXTS |
                     editor_module.EditWorkbench.HTML_EXTS |
                     editor_module.EditWorkbench.DOCX_EXTS |
                     editor_module.EditWorkbench.XLSX_EXTS |
                     editor_module.EditWorkbench.PPTX_EXTS |
                     editor_module.EditWorkbench.PDF_EXTS)

    for ext in required:
        assert_true(ext in all_supported, f"格式 {ext} 已映射")

    # 检查 sample_files 中每个文件都能找到对应类型
    real_files = {
        "readme.txt": ".txt", "hello.py": ".py", "config.json": ".json",
        "guide.md": ".md", "demo.html": ".html", "sample.png": ".png",
        "sample.jpg": ".jpg", "sample.docx": ".docx", "sample.xlsx": ".xlsx",
        "sample.pptx": ".pptx", "sample.pdf": ".pdf",
    }
    for fname, ext in real_files.items():
        assert_true(ext in all_supported, f"sample_files/{fname} 格式 {ext} 已支持")


# ===================== 主入口 =====================

def main():
    global _passed, _failed

    print("=" * 60)
    print("  Edit Workbench — 自动化测试 (sample_files)")
    print("=" * 60)

    if not os.path.isdir(SAMPLE_DIR):
        print(f"\n[ERROR] sample_files 目录不存在: {SAMPLE_DIR}")
        print("请先运行: python generate_samples.py")
        sys.exit(1)

    print(f"\n测试目录: {SAMPLE_DIR}")
    files = os.listdir(SAMPLE_DIR)
    print(f"文件数: {len(files)}")
    for f in sorted(files):
        print(f"  - {f}")

    # PyQt 需要 QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    try:
        test_text_editor()
        test_html_md_viewer()
        test_docx_viewer()
        test_xlsx_viewer()
        test_pptx_viewer()
        test_libreoffice_available()
        test_libreoffice_conversion()
        test_pdf_viewer()
        test_image_viewer()
        test_search_replace_panel()
        test_switch_search_panel()
        test_file_type_mapping()
    except Exception as e:
        print(f"\n[ERROR] 测试异常: {e}")
        traceback.print_exc()
        _failed += 1

    total = _passed + _failed
    print("\n" + "=" * 60)
    print(f"  测试结果: {_passed}/{total} 通过, {_failed} 失败")
    print("=" * 60)

    if _failed > 0:
        sys.exit(1)
    else:
        print("  全部测试通过!")
        sys.exit(0)


if __name__ == "__main__":
    main()