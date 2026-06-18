"""将 gifs/gifs2 目录下的 GIF 文件内嵌为 base64 数据，生成新的 gifs.py 和 gifs2.py"""
import os
import base64

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _generate_gifs_module(gif_dir, output_path, var_prefix=""):
    gif_files = sorted(f for f in os.listdir(gif_dir) if f.endswith(".gif"))

    lines = []
    lines.append(f'"""GIF image data - embedded base64 bytes from {os.path.basename(gif_dir)} folder"""')
    lines.append("import base64")
    lines.append("")
    lines.append("")

    for fname in gif_files:
        var_name = var_prefix + fname.replace(".gif", "").upper() + "_GIF"
        with open(os.path.join(gif_dir, fname), "rb") as f:
            data = base64.b64encode(f.read()).decode("ascii")
        lines.append(f"{var_name} = base64.b64decode(")
        for i in range(0, len(data), 120):
            chunk = data[i : i + 120]
            lines.append(f'    b"{chunk}"')
        lines.append(")")
        lines.append("")

    return lines


def _generate_lists(gif_dir, var_prefix=""):
    """生成 _ALL_GIFS, _HAPPY_GIFS, _CLICK_GIFS, _HOVER_GIFS 列表"""
    gif_files = sorted(f for f in os.listdir(gif_dir) if f.endswith(".gif"))

    def _v(name):
        return var_prefix + name.replace(".gif", "").upper() + "_GIF"

    all_gifs = [_v(f) for f in gif_files]
    happy_gifs = [_v(f) for f in gif_files if f.startswith("happy")]
    click_gifs = [_v(f) for f in gif_files if f.startswith("click")]
    hover_gifs = [_v(f) for f in gif_files if f in ("left.gif", "right.gif")]

    # 列表名使用前缀（gifs2 用 G2_ALL_GIFS，gifs 用 _ALL_GIFS）
    prefix_upper = var_prefix.rstrip("_")  # "G2_" -> "G2", "" -> ""
    all_name = f"{prefix_upper}_ALL_GIFS" if prefix_upper else "_ALL_GIFS"
    happy_name = f"{prefix_upper}_HAPPY_GIFS" if prefix_upper else "_HAPPY_GIFS"
    click_name = f"{prefix_upper}_CLICK_GIFS" if prefix_upper else "_CLICK_GIFS"
    hover_name = f"{prefix_upper}_HOVER_GIFS" if prefix_upper else "_HOVER_GIFS"

    def _format_list(name, items):
        lines = [f"{name} = ["]
        for item in items:
            lines.append(f"    {item},")
        lines.append("]")
        return lines

    lines = []
    lines += _format_list(all_name, all_gifs)
    lines.append("")
    lines.append("")
    lines += _format_list(happy_name, happy_gifs)
    lines.append("")
    lines.append("")
    lines += _format_list(click_name, click_gifs)
    lines.append("")
    lines.append("")
    lines += _format_list(hover_name, hover_gifs)
    return lines


def main():
    for dir_name, out_name, prefix in [
        ("gifs", "gifs.py", ""),
        ("gifs2", "gifs2.py", "G2_"),
    ]:
        gif_dir = os.path.join(BASE_DIR, dir_name)
        out_path = os.path.join(BASE_DIR, out_name)

        body = _generate_gifs_module(gif_dir, out_path, prefix)
        lists = _generate_lists(gif_dir, prefix)
        all_lines = body + lists + [""]

        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(all_lines))

        print(f"Generated {out_name} ({len(body) - 3} variables)")


if __name__ == "__main__":
    main()