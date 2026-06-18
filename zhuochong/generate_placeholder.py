"""
生成线条小狗GIF素材 - 可爱的卡通小狗形象
包含：idle、hover、dance、shake、run、eat、sleep 等动作动画
"""
import os
import math

from PIL import Image, ImageDraw

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "resources", "skins", "line_puppy")
W, H = 200, 200
CENTER = (100, 100)

# 配色
FUR = (194, 150, 102)        # 金毛色
FUR_DARK = (140, 100, 60)    # 深色轮廓
INNER_EAR = (240, 180, 150)  # 耳内粉色
NOSE_COLOR = (50, 30, 20)    # 鼻子
EYE_COLOR = (40, 25, 15)     # 眼睛
CHEEK = (255, 170, 150, 140) # 腮红
COLLAR = (220, 60, 50)       # 红色项圈
TONGUE = (255, 120, 120)     # 舌头
PAW = (220, 190, 155)        # 爪垫
WHITE = (255, 255, 255)
LINE_WIDTH = 3


def create_frame(draw_func, frame_idx: int = 0):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_func(draw, frame_idx, img)
    return img


# ═══════════════════════════════════════════════════════════════
#  小狗绘制 - 核心
# ═══════════════════════════════════════════════════════════════

def draw_puppy(draw, cx, cy, **kwargs):
    """
    绘制一只可爱的小狗
    kwargs:
      ear_flop: 耳朵摆动偏移 (0=正常)
      tail_wag: 尾巴摆动偏移 (0=正常)
      eye_style: 'normal' | 'happy' | 'heart' | 'closed'
      mouth_open: 嘴巴张开程度 (0=闭合, 1=张开)
      head_tilt: 头部倾斜角度对应的偏移
      body_bob: 身体上下弹跳偏移
      leg_pose: 腿部姿势 'stand' | 'run1' | 'run2' | 'sit'
      zzz: 是否显示Zzz
      tongue_out: 是否吐舌头
    """
    ear_flop = kwargs.get("ear_flop", 0)
    tail_wag = kwargs.get("tail_wag", 0)
    eye_style = kwargs.get("eye_style", "normal")
    mouth_open = kwargs.get("mouth_open", 0)
    body_bob = kwargs.get("body_bob", 0)
    leg_pose = kwargs.get("leg_pose", "stand")
    zzz = kwargs.get("zzz", False)
    tongue_out = kwargs.get("tongue_out", False)

    cy += body_bob

    # ── 身体 ──
    bx, by = cx - 30, cy + 5
    draw.rounded_rectangle([bx, by, bx + 60, by + 50], radius=20,
                           fill=FUR, outline=FUR_DARK, width=LINE_WIDTH)

    # 肚皮白色
    draw.ellipse([cx - 18, cy + 20, cx + 18, cy + 52],
                 fill=(255, 245, 235, 255), outline=FUR_DARK, width=LINE_WIDTH)

    # ── 项圈 ──
    collar_y = cy + 8
    draw.arc([cx - 28, collar_y - 2, cx + 28, collar_y + 8],
             start=0, end=180, fill=COLLAR, width=4)
    # 项圈吊坠
    draw.ellipse([cx - 3, collar_y + 4, cx + 3, collar_y + 12],
                 fill=(255, 200, 40, 255), outline=FUR_DARK, width=1)

    # ── 头 ──
    head_top = cy - 32
    draw.ellipse([cx - 32, head_top, cx + 32, head_top + 60],
                 fill=FUR, outline=FUR_DARK, width=LINE_WIDTH)

    # ── 耳朵（下垂的软耳朵，不是尖耳朵！） ──
    # 左耳 - 下垂
    ear_lx = cx - 28
    ear_ly = head_top + 5
    draw.ellipse([ear_lx - 8, ear_ly - 5, ear_lx + 20, ear_ly + 35 + ear_flop],
                 fill=FUR, outline=FUR_DARK, width=LINE_WIDTH)
    draw.ellipse([ear_lx - 2, ear_ly + 2, ear_lx + 14, ear_ly + 28 + ear_flop],
                 fill=INNER_EAR, outline=None)

    # 右耳 - 下垂
    ear_rx = cx + 28
    draw.ellipse([ear_rx - 20, ear_ly - 5, ear_rx + 8, ear_ly + 35 - ear_flop],
                 fill=FUR, outline=FUR_DARK, width=LINE_WIDTH)
    draw.ellipse([ear_rx - 14, ear_ly + 2, ear_rx + 2, ear_ly + 28 - ear_flop],
                 fill=INNER_EAR, outline=None)

    # ── 脸部白色区域 ──
    draw.ellipse([cx - 20, head_top + 18, cx + 20, head_top + 52],
                 fill=(255, 245, 235, 255), outline=None)

    # ── 眼睛 ──
    eye_y = head_top + 20
    if eye_style == "happy":
        # 笑眼 (弯弯的弧线)
        for ex in [cx - 12, cx + 12]:
            draw.arc([ex - 6, eye_y - 4, ex + 6, eye_y + 10],
                     start=0, end=180, fill=EYE_COLOR, width=2)
    elif eye_style == "heart":
        # 爱心眼
        for ex in [cx - 12, cx + 12]:
            draw.ellipse([ex - 4, eye_y - 3, ex, eye_y + 3], fill=(255, 60, 60, 255))
            draw.ellipse([ex, eye_y - 3, ex + 4, eye_y + 3], fill=(255, 60, 60, 255))
    elif eye_style == "closed":
        # 闭眼 (睡觉)
        for ex in [cx - 12, cx + 12]:
            draw.arc([ex - 5, eye_y + 2, ex + 5, eye_y + 8],
                     start=0, end=180, fill=EYE_COLOR, width=2)
    else:
        # 正常圆眼 + 高光
        for ex in [cx - 12, cx + 12]:
            draw.ellipse([ex - 6, eye_y - 2, ex + 6, eye_y + 10],
                         fill=EYE_COLOR, outline=None)
            draw.ellipse([ex - 2, eye_y, ex + 2, eye_y + 4],
                         fill=WHITE, outline=None)

    # ── 眉毛 ──
    for ex in [cx - 12, cx + 12]:
        draw.arc([ex - 5, eye_y - 8, ex + 5, eye_y - 2],
                 start=20, end=160, fill=FUR_DARK, width=2)

    # ── 鼻子 ──
    nose_y = head_top + 32
    draw.ellipse([cx - 6, nose_y - 2, cx + 6, nose_y + 8],
                 fill=NOSE_COLOR, outline=None)
    # 鼻子高光
    draw.ellipse([cx - 1, nose_y, cx + 2, nose_y + 3],
                 fill=WHITE, outline=None)

    # ── 嘴/吻部 ──
    mouth_y = nose_y + 10
    if mouth_open > 0:
        # 张嘴
        draw.ellipse([cx - 7, mouth_y - 2, cx + 7, mouth_y + 8 * mouth_open],
                     fill=(60, 30, 20, 255), outline=FUR_DARK, width=1)
        if tongue_out:
            draw.ellipse([cx - 3, mouth_y + 3, cx + 3, mouth_y + 10],
                         fill=TONGUE, outline=None)
    else:
        # 微笑
        draw.arc([cx - 8, mouth_y - 4, cx, mouth_y + 6],
                 start=0, end=180, fill=FUR_DARK, width=2)
        draw.arc([cx, mouth_y - 4, cx + 8, mouth_y + 6],
                 start=0, end=180, fill=FUR_DARK, width=2)

    # 吻部中线
    draw.line([cx, nose_y + 8, cx, mouth_y - 2], fill=FUR_DARK, width=1)

    # ── 腮红 ──
    for sx, sy in [(cx - 22, nose_y), (cx + 14, nose_y)]:
        draw.ellipse([sx, sy, sx + 9, sy + 7], fill=CHEEK)

    # ── 腿 ──
    if leg_pose == "stand":
        _draw_legs_stand(draw, cx, cy)
    elif leg_pose == "run1":
        _draw_legs_run(draw, cx, cy, phase=0)
    elif leg_pose == "run2":
        _draw_legs_run(draw, cx, cy, phase=1)
    elif leg_pose == "sit":
        _draw_legs_sit(draw, cx, cy)

    # ── 尾巴（蓬松弯曲的尾巴，不是细尾巴！） ──
    tail_base_x = cx + 28
    tail_base_y = cy + 15
    wag = tail_wag

    # 用多个重叠椭圆画出蓬松尾巴
    points = [
        (tail_base_x, tail_base_y),
        (tail_base_x + 15 + wag, tail_base_y - 10),
        (tail_base_x + 25 + wag * 2, tail_base_y - 25),
        (tail_base_x + 20 + wag * 3, tail_base_y - 40),
        (tail_base_x + 10 + wag * 2, tail_base_y - 45),
    ]
    for px, py in points:
        draw.ellipse([px - 7, py - 5, px + 7, py + 5], fill=FUR, outline=FUR_DARK, width=2)

    # ── Zzz ──
    if zzz:
        zx = cx + 35
        zy = head_top - 15
        for i, size in enumerate([8, 10, 12]):
            draw.text((zx + i * 10, zy - i * 10), "z", fill=(100, 150, 255, 200),
                      font=None, font_size=size + 2)


def _draw_legs_stand(draw, cx, cy):
    """站立姿势的腿"""
    # 前腿
    for lx, ofs in [(cx - 20, -3), (cx + 8, 3)]:
        draw.line([lx, cy + 50, lx + ofs, cy + 72], fill=FUR_DARK, width=LINE_WIDTH + 1)
        draw.ellipse([lx + ofs - 4, cy + 68, lx + ofs + 4, cy + 76],
                     fill=PAW, outline=FUR_DARK, width=1)
    # 后腿
    for lx, ofs in [(cx - 8, -2), (cx + 20, 2)]:
        draw.line([lx, cy + 50, lx + ofs, cy + 74], fill=FUR_DARK, width=LINE_WIDTH + 1)
        draw.ellipse([lx + ofs - 4, cy + 70, lx + ofs + 4, cy + 78],
                     fill=PAW, outline=FUR_DARK, width=1)


def _draw_legs_run(draw, cx, cy, phase=0):
    """跑步姿势的腿"""
    if phase == 0:
        # 前腿一前一后
        draw.line([cx - 18, cy + 48, cx - 28, cy + 60], fill=FUR_DARK, width=LINE_WIDTH + 1)
        draw.ellipse([cx - 32, cy + 56, cx - 24, cy + 64], fill=PAW, outline=FUR_DARK, width=1)
        draw.line([cx + 10, cy + 48, cx + 20, cy + 62], fill=FUR_DARK, width=LINE_WIDTH + 1)
        draw.ellipse([cx + 16, cy + 58, cx + 24, cy + 66], fill=PAW, outline=FUR_DARK, width=1)
        # 后腿一前一后
        draw.line([cx - 6, cy + 48, cx + 2, cy + 64], fill=FUR_DARK, width=LINE_WIDTH + 1)
        draw.ellipse([cx - 2, cy + 60, cx + 6, cy + 68], fill=PAW, outline=FUR_DARK, width=1)
        draw.line([cx + 22, cy + 48, cx + 30, cy + 58], fill=FUR_DARK, width=LINE_WIDTH + 1)
        draw.ellipse([cx + 26, cy + 54, cx + 34, cy + 62], fill=PAW, outline=FUR_DARK, width=1)
    else:
        draw.line([cx - 18, cy + 48, cx - 10, cy + 62], fill=FUR_DARK, width=LINE_WIDTH + 1)
        draw.ellipse([cx - 14, cy + 58, cx - 6, cy + 66], fill=PAW, outline=FUR_DARK, width=1)
        draw.line([cx + 10, cy + 48, cx + 18, cy + 58], fill=FUR_DARK, width=LINE_WIDTH + 1)
        draw.ellipse([cx + 14, cy + 54, cx + 22, cy + 62], fill=PAW, outline=FUR_DARK, width=1)
        draw.line([cx - 6, cy + 48, cx - 16, cy + 60], fill=FUR_DARK, width=LINE_WIDTH + 1)
        draw.ellipse([cx - 20, cy + 56, cx - 12, cy + 64], fill=PAW, outline=FUR_DARK, width=1)
        draw.line([cx + 22, cy + 48, cx + 32, cy + 62], fill=FUR_DARK, width=LINE_WIDTH + 1)
        draw.ellipse([cx + 28, cy + 58, cx + 36, cy + 66], fill=PAW, outline=FUR_DARK, width=1)


def _draw_legs_sit(draw, cx, cy):
    """坐姿"""
    # 前腿伸直
    draw.line([cx - 18, cy + 48, cx - 16, cy + 66], fill=FUR_DARK, width=LINE_WIDTH + 1)
    draw.ellipse([cx - 20, cy + 62, cx - 12, cy + 70], fill=PAW, outline=FUR_DARK, width=1)
    draw.line([cx + 10, cy + 48, cx + 12, cy + 66], fill=FUR_DARK, width=LINE_WIDTH + 1)
    draw.ellipse([cx + 8, cy + 62, cx + 16, cy + 70], fill=PAW, outline=FUR_DARK, width=1)
    # 后腿折叠
    draw.ellipse([cx - 8, cy + 40, cx + 8, cy + 52], fill=FUR, outline=FUR_DARK, width=LINE_WIDTH)


# ═══════════════════════════════════════════════════════════════
#  动画生成函数
# ═══════════════════════════════════════════════════════════════

def generate_idle():
    """idle.gif: 呼吸 + 尾巴轻轻摇摆"""
    frames = []
    for i in range(16):
        breath = int(math.sin(i * math.pi / 8) * 2)
        wag = int(math.sin(i * math.pi / 6) * 5)
        eye = "happy" if i == 8 else "normal"  # 眨眼
        frame = create_frame(lambda d, fi, im: draw_puppy(d, 100, 100,
            tail_wag=wag, body_bob=breath, eye_style=eye, leg_pose="stand"), i)
        frames.append(frame)
    _save_gif("idle.gif", frames, duration=150)


def generate_hover():
    """hover.gif: 兴奋 + 爱心眼 + 快速摇尾 + 吐舌头"""
    frames = []
    for i in range(12):
        wag = int(math.sin(i * math.pi / 3) * 10)
        ear = int(math.sin(i * math.pi / 3) * 6)
        eye = "heart" if i % 3 != 0 else "happy"
        frame = create_frame(lambda d, fi, im: draw_puppy(d, 100, 100,
            tail_wag=wag, ear_flop=ear, eye_style=eye, tongue_out=True, leg_pose="stand"), i)
        frames.append(frame)
    _save_gif("hover.gif", frames, duration=100)


def generate_dance():
    """dance.gif: 跳舞 - 上下弹跳 + 耳朵摆动 + 开心"""
    frames = []
    for i in range(16):
        bob = int(math.sin(i * math.pi / 4) * 8)
        ear = int(math.sin(i * math.pi / 4) * 10)
        wag = int(math.sin(i * math.pi / 3) * 8)
        eye = "heart"
        frame = create_frame(lambda d, fi, im: draw_puppy(d, 100, 100,
            body_bob=bob, ear_flop=ear, tail_wag=wag, eye_style=eye,
            tongue_out=True, leg_pose="stand"), i)
        frames.append(frame)
    _save_gif("dance.gif", frames, duration=100)


def generate_shake():
    """shake.gif: 摇头 - 头部左右晃动"""
    frames = []
    for i in range(16):
        head_tilt = int(math.sin(i * math.pi / 4) * 8)
        wag = int(math.sin(i * math.pi / 2) * 12)
        ear = int(math.sin(i * math.pi / 3) * 12)
        eye = "happy" if i % 2 == 0 else "normal"
        frame = create_frame(lambda d, fi, im: draw_puppy(d, 100 + head_tilt, 100,
            tail_wag=wag, ear_flop=ear, eye_style=eye, leg_pose="stand"), i)
        frames.append(frame)
    _save_gif("shake.gif", frames, duration=80)


def generate_run():
    """run.gif: 跑步 - 原地跑步 + 耳朵摆动"""
    frames = []
    for i in range(16):
        bob = int(math.sin(i * math.pi / 4) * 4)
        ear = int(math.sin(i * math.pi / 4) * 8)
        wag = int(math.sin(i * math.pi / 3) * 6)
        pose = "run1" if i % 2 == 0 else "run2"
        frame = create_frame(lambda d, fi, im: draw_puppy(d, 100, 100,
            body_bob=bob, ear_flop=ear, tail_wag=wag, leg_pose=pose,
            tongue_out=True), i)
        frames.append(frame)
    _save_gif("run.gif", frames, duration=80)


def generate_eat():
    """eat.gif: 吃饭 - 嘴巴一张一合 + 前爪捧着"""
    frames = []
    for i in range(16):
        mouth = abs(math.sin(i * math.pi / 4))  # 0~1 张嘴
        wag = int(math.sin(i * math.pi / 6) * 4)
        eye = "happy"
        frame = create_frame(lambda d, fi, im: draw_puppy(d, 100, 100,
            mouth_open=mouth, tail_wag=wag, eye_style=eye,
            tongue_out=True, leg_pose="sit"), i)
        frames.append(frame)
    _save_gif("eat.gif", frames, duration=150)


def generate_sleep():
    """sleep.gif: 睡觉 - 闭眼 + 呼吸 + Zzz"""
    frames = []
    for i in range(24):
        breath = int(math.sin(i * math.pi / 8) * 3)
        zzz = i % 12 < 8  # Zzz时隐时现
        frame = create_frame(lambda d, fi, im: draw_puppy(d, 100, 100,
            body_bob=breath, eye_style="closed", zzz=zzz, leg_pose="sit"), i)
        frames.append(frame)
    _save_gif("sleep.gif", frames, duration=200)


# ═══════════════════════════════════════════════════════════════
#  工具函数
# ═══════════════════════════════════════════════════════════════

def _save_gif(name, frames, duration=120):
    path = os.path.join(OUTPUT_DIR, name)
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        duration=duration,
        loop=0,
        disposal=2,
        transparency=0,
    )
    print(f"  [生成] {name} ({len(frames)}帧)")


# ═══════════════════════════════════════════════════════════════
#  主流程
# ═══════════════════════════════════════════════════════════════

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("正在生成线条小狗动画素材...")
    generate_idle()
    generate_hover()
    generate_dance()
    generate_shake()
    generate_run()
    generate_eat()
    generate_sleep()
    print(f"\n[完成] 所有素材已生成到: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()