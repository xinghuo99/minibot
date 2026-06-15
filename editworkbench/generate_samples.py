"""生成 sample_files 样本文件夹"""
import os

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_files")
os.makedirs(SAMPLE_DIR, exist_ok=True)

# ---- txt ----
with open(os.path.join(SAMPLE_DIR, "readme.txt"), "w", encoding="utf-8") as f:
    f.write("Edit Workbench 示例文件\n\n这是一个纯文本文件。\n支持多格式编辑。\n")

# ---- py ----
with open(os.path.join(SAMPLE_DIR, "hello.py"), "w", encoding="utf-8") as f:
    f.write('"""示例 Python 文件"""\n\n')
    f.write("def greet(name):\n")
    f.write('    return f"你好, {name}!"\n')
    f.write("\n\n")
    f.write('if __name__ == "__main__":\n')
    f.write('    print(greet("世界"))\n')
    f.write("    print(\"求和:\", sum([1, 2, 3, 4, 5]))\n")

# ---- json ----
with open(os.path.join(SAMPLE_DIR, "config.json"), "w", encoding="utf-8") as f:
    f.write('{\n')
    f.write('  "app": "EditWorkbench",\n')
    f.write('  "version": "2.0",\n')
    f.write('  "theme": "wine-red",\n')
    f.write('  "features": ["editor", "preview", "search"]\n')
    f.write('}\n')

# ---- md ----
with open(os.path.join(SAMPLE_DIR, "guide.md"), "w", encoding="utf-8") as f:
    f.write("# Edit Workbench 使用指南\n\n")
    f.write("## 功能\n\n")
    f.write("- 支持多种文件格式\n")
    f.write("- 搜索与替换\n")
    f.write("- 酒红色主题\n\n")
    f.write("## 快捷键\n\n")
    f.write("| 按键 | 功能 |\n")
    f.write("|------|------|\n")
    f.write("| Ctrl+S | 保存 |\n")
    f.write("| Ctrl+F | 查找替换 |\n")

# ---- html ----
with open(os.path.join(SAMPLE_DIR, "demo.html"), "w", encoding="utf-8") as f:
    f.write('<!DOCTYPE html>\n')
    f.write('<html lang="zh-CN">\n')
    f.write('<head>\n')
    f.write('<meta charset="UTF-8">\n')
    f.write('<title>示例页面</title>\n')
    f.write("<style>\n")
    f.write("body { font-family: sans-serif; background: #fdf5e6; color: #2c1810; padding: 40px; }\n")
    f.write("h1 { color: #722F37; }\n")
    f.write("</style>\n")
    f.write("</head>\n")
    f.write("<body>\n")
    f.write("<h1>欢迎使用 Edit Workbench</h1>\n")
    f.write("<p>这是一个<strong>HTML</strong>示例页面。</p>\n")
    f.write("</body>\n")
    f.write("</html>\n")

# ---- docx ----
try:
    from docx import Document
    doc = Document()
    doc.add_heading("Word 示例文档", 0)
    doc.add_paragraph("这是一个 Word 文档示例。")
    doc.add_paragraph("包含多段文字内容。")
    doc.add_paragraph("酒红色主题编辑器。")
    doc.save(os.path.join(SAMPLE_DIR, "sample.docx"))
    print("  [OK] sample.docx")
except ImportError:
    print("  [SKIP] python-docx 未安装")

# ---- xlsx ----
try:
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "员工信息"
    ws["A1"] = "姓名"
    ws["B1"] = "部门"
    ws["C1"] = "职位"
    ws["A2"] = "张三"
    ws["B2"] = "技术部"
    ws["C2"] = "工程师"
    ws["A3"] = "李四"
    ws["B3"] = "设计部"
    ws["C3"] = "设计师"
    ws["A4"] = "王五"
    ws["B4"] = "市场部"
    ws["C4"] = "经理"
    wb.save(os.path.join(SAMPLE_DIR, "sample.xlsx"))
    print("  [OK] sample.xlsx")
except ImportError:
    print("  [SKIP] openpyxl 未安装")

# ---- pptx ----
try:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    prs = Presentation()
    # Slide 1
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "Edit Workbench"
    slide.placeholders[1].text = "多格式文件编辑器\n\n酒红色主题"
    # Slide 2
    slide2 = prs.slides.add_slide(prs.slide_layouts[1])
    slide2.shapes.title.text = "支持的格式"
    slide2.placeholders[1].text = "TXT · PY · JSON · MD · HTML\nDOCX · XLSX · PPTX · PDF\nPNG · JPG"
    prs.save(os.path.join(SAMPLE_DIR, "sample.pptx"))
    print("  [OK] sample.pptx")
except ImportError:
    print("  [SKIP] python-pptx 未安装")

# ---- pdf (简单文本PDF) ----
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(os.path.join(SAMPLE_DIR, "sample.pdf"), pagesize=A4)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(100, 750, "Edit Workbench")
    c.setFont("Helvetica", 14)
    c.drawString(100, 700, "PDF 示例文档")
    c.drawString(100, 670, "这是一个酒红色主题的多格式编辑器。")
    c.drawString(100, 640, "支持多种文件格式的打开与编辑。")
    c.save()
    print("  [OK] sample.pdf")
except ImportError:
    # fallback: 创建最小合法 PDF
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n"
        b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n190\n%%EOF"
    )
    with open(os.path.join(SAMPLE_DIR, "sample.pdf"), "wb") as f:
        f.write(pdf_content)
    print("  [OK] sample.pdf (minimal)")

# ---- png ----
try:
    from PIL import Image, ImageDraw, ImageFont
    img = Image.new("RGB", (400, 300), color="#722F37")
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 350, 250], fill="#FDF5E6", outline="#8B3A44", width=3)
    draw.text((120, 130), "PNG Sample", fill="#722F37")
    img.save(os.path.join(SAMPLE_DIR, "sample.png"))
    print("  [OK] sample.png")
except ImportError:
    print("  [SKIP] Pillow 未安装")

# ---- jpg ----
try:
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (400, 300), color="#5C1E26")
    draw = ImageDraw.Draw(img)
    draw.ellipse([100, 50, 300, 250], fill="#FDF5E6", outline="#8B3A44", width=3)
    draw.text((155, 135), "JPG Sample", fill="#5C1E26")
    img.save(os.path.join(SAMPLE_DIR, "sample.jpg"), quality=90)
    print("  [OK] sample.jpg")
except ImportError:
    print("  [SKIP] Pillow 未安装")

print(f"\n样本文件已生成: {SAMPLE_DIR}")
print("文件列表:")
for f in sorted(os.listdir(SAMPLE_DIR)):
    print(f"  - {f}")