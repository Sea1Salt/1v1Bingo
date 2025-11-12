import pygame
import random
import sys
import traceback
import os

pygame.init()

# ------------------- CONFIG -------------------

# ==== TEXT HELPER ====
NAME = {"player": "ผู้เล่น", "bot": "T - T"}
def say(actor, action, target=None):
    left = NAME.get(actor, str(actor))
    if target is None:
        return f"{left} : {action}"
    right = NAME.get(target, str(target))
    return f"{left} → {right} : {action}"
# ================================================

# ------------------- BACKGROUND MUSIC -------------------
try:
    pygame.mixer.init()
    pygame.mixer.music.load("sounds/pirates-action-loop-368853.mp3")  # ใส่ path ของเพลง
    pygame.mixer.music.set_volume(0.3)         # ระดับเสียง (0.0 - 1.0)
    pygame.mixer.music.play(-1)                # เล่นวนลูปตลอดเกม

    win_sound  = pygame.mixer.Sound("sounds/you-win-sequence-1-183948.mp3")
    lose_sound = pygame.mixer.Sound("sounds/game-over-417465.mp3")
    win_sound.set_volume(0.6)
    lose_sound.set_volume(0.6)
    print("🎵 Background music started")
except Exception as e:
    print("⚠️ โหลดเพลงไม่สำเร็จ:", e)
# ===========================================================

# ------------------- SFX (Skill Sounds) -------------------
try:
    if not pygame.mixer.get_init():
        pygame.mixer.init()

    SFX = {}

    def load_sfx(name, path, volume=0.65):
        try:
            s = pygame.mixer.Sound(path)
            s.set_volume(volume)
            SFX[name] = s
        except Exception as e:
            print(f"⚠️ โหลดเสียง {name} ไม่สำเร็จ:", e)

    # โหลดไฟล์ (แก้พาธตามที่คุณวางไฟล์)
    load_sfx("block",    "sounds/game-bonus-144751.mp3")
    load_sfx("fire",     "sounds/single-gunshot-62-hp-37188.mp3")
    load_sfx("heal",     "sounds/coin-clatter-6-87110.mp3")
    load_sfx("remove",   "sounds/vd1h39gep6-pirate-sfx-2.mp3")
    load_sfx("lateup",   "sounds/game-bonus-144751.mp3")
    load_sfx("latedown", "sounds/game-bonus-144751.mp3")
    load_sfx("skill_any","sounds/game-bonus-144751.mp3") 

    def play_sfx(name):
        s = SFX.get(name) or SFX.get("skill_any")
        if s:
            s.play()
except Exception as e:
    print("⚠️ ตั้งค่าเสียงไม่สำเร็จ:", e)

# =========================================================

# ตำแหน่ง recent box
Box_recent_number_x = +173
Box_recent_number_y = +131.7

# ขนาดหัวใจ (สเกล) แยกผู้เล่น/บอท
PLAYER_HEART_SCALE = 1.5
BOT_HEART_SCALE    = 1.0

# ขยับกริดตัวเลข (เฉพาะกล่องสี) ทั้งชุด ภายในพาเน
PLAYER_GRID_OFFSET = [0, -65]     # [dx, dy] ของฝั่งผู้เล่น
BOT_GRID_OFFSET    = [0, -75]    # [dx, dy] ของฝั่งบอท

PLAYER_HEART_OFFSET = [5, -50]
BOT_HEART_OFFSET    = [5, -70]

PLAYER_POS_OFFSET = [-10, 160]
BOT_POS_OFFSET    = [100, 120]
SHOW_CENTER_STATUS = False

SIZE = 5
CELL_SIZE = 50
GRID_GAP = 6
PLAYER_CELL_SIZE = 70
BOT_CELL_SIZE    = 50

# สี/ธีม
WHITE  = (255, 255, 255)
BLACK  = (0, 0, 0)
YELLOW = (255, 255, 150)

PANEL_BG     = (250, 250, 250)
PANEL_BORDER = (235, 210, 160)
PANEL_SHADOW = (0, 0, 0, 60)

PASTEL_FIRE     = (255,179,186)
PASTEL_BLOCK    = (255,223,186)
PASTEL_HEAL     = (186,255,201)
PASTEL_REMOVE   = (186,225,255)
PASTEL_LATEUP   = (255,255,186)
PASTEL_LATEDOWN = (215,186,255)
PASTEL_NORMAL   = (152, 193, 218)

# ปู + แบนเนอร์ (ล็อกขนาดจากจอเริ่มต้น)
CRAB_USER_SCALE = 2.5
MAX_H_FRAC = 0.60
MAX_W_FRAC = 0.45

# ------------------- หน้าต่าง RESIZABLE -------------------
info = pygame.display.Info()
SCREEN_WIDTH, SCREEN_HEIGHT = int(info.current_w * 0.9), int(info.current_h * 0.9)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)

pygame.display.set_caption("1v1 Bingo Skill System")
clock = pygame.time.Clock()

# ⛳ ขนาดจอ "เริ่มต้น" (ใช้ล็อก UI)
INIT_SCREEN_WIDTH  = SCREEN_WIDTH
INIT_SCREEN_HEIGHT = SCREEN_HEIGHT

# ------------------- โหลดรูป -------------------
background_original     = pygame.image.load("images/BG.png").convert()
crab_original           = pygame.image.load("images/crab.png").convert_alpha()
banner_original         = pygame.image.load("images/banner.png").convert_alpha()
heart_player_original   = pygame.image.load("images/heart_play.png").convert_alpha()
heart_bot_original      = pygame.image.load("images/heart_bot.png").convert_alpha()
background_scaled       = pygame.transform.smoothscale(background_original, (SCREEN_WIDTH, SCREEN_HEIGHT))

# =================== FONTS ===================
FONT_DIR = "fonts"

def _safe_font(path_or_none, size, fallback=None):
    try:
        if path_or_none and os.path.isfile(path_or_none):
            return pygame.font.Font(path_or_none, size)
    except Exception:
        pass
    return pygame.font.SysFont(fallback or None, size)

def load_font(file_name, size, fallback=None):
    return _safe_font(os.path.join(FONT_DIR, file_name), size, fallback=fallback)

# ไทย/อังกฤษ
FONT_TH_BODY   = load_font("Mitr-Bold.ttf", 22, fallback="kanit")
FONT_TH_TITLE  = load_font("Mitr-Bold.ttf", 36, fallback="kanit")
FONT_EN_BODY   = load_font("Kitora-Demo.otf", 22, fallback="arial")
FONT_EN_TITLE  = load_font("Kitora-Demo.otf", 50, fallback="arial")


# ฟอนต์เลขในเซล
PREFERRED_NUM_FONT_FILE = "SuperAdorable-MAvyp.ttf"
def get_num_font(size):
    return load_font(PREFERRED_NUM_FONT_FILE, size, fallback="arial")

def is_thai(s: str) -> bool:
    return any('\u0E00' <= ch <= '\u0E7F' for ch in s)

def pick_font(kind: str, text: str):
    if kind == "num":
        return get_num_font(40)
    if is_thai(text):
        return FONT_TH_TITLE if kind == "title" else FONT_TH_BODY
    else:
        return FONT_EN_TITLE if kind == "title" else FONT_EN_BODY

# ===================== TITLE STYLE =====================
TITLE_STYLE = {
    "PLAYER": {"font_file_en":"Kitora-Demo.otf","font_file_th":"Kanit-ExtraBold.ttf",
               "size":70,"offset_x":0,"offset_y":30,"spacing":20,"color":(36,34,44)},
    "T - T":  {"font_file_en":"Kitora-Demo.otf","font_file_th":"Kanit-ExtraBold.ttf",
               "size":50,"offset_x":30,"offset_y":20,"spacing":25,"color":(36,34,44)}
}
DEFAULT_TITLE_STYLE = {"font_file_en":"Kitora-Demo.otf","font_file_th":"Kanit-ExtraBold.ttf",
                       "size":72,"offset_x":30,"offset_y":40,"spacing":18,"color":(36,34,44)}

# =====================================================
# ------------------- Layout (คงที่ตั้งแต่เริ่ม) -------------------
def compute_layout_initial():
    margin_x = int(INIT_SCREEN_WIDTH * 0.08)
    top_y    = int(INIT_SCREEN_HEIGHT * 0.12)

    grid_w = SIZE * CELL_SIZE + (SIZE - 1) * GRID_GAP
    panel_pad_x = 50

    left_grid_x  = margin_x + panel_pad_x
    right_grid_x = INIT_SCREEN_WIDTH - margin_x - panel_pad_x - grid_w

    player_pos = (left_grid_x  + PLAYER_POS_OFFSET[0],
                  top_y        + PLAYER_POS_OFFSET[1])
    bot_pos    = (right_grid_x + BOT_POS_OFFSET[0],
                  top_y        + BOT_POS_OFFSET[1])
    return player_pos, bot_pos

# 🧷 ตำแหน่งบอร์ด "คงที่" ตลอดอายุโปรแกรม
player_grid_pos, bot_grid_pos = compute_layout_initial()

# =====================================================
# ------------------- Helper วาดกรอบ/พาเนล -------------------
def draw_rounded_rect(surface, rect, color, radius=22, border_color=None, border_width=0):
    x, y, w, h = rect
    pygame.draw.rect(surface, color, (x+radius, y, w-2*radius, h))
    pygame.draw.rect(surface, color, (x, y+radius, w, h-2*radius))
    pygame.draw.circle(surface, color, (x+radius, y+radius), radius)
    pygame.draw.circle(surface, color, (x+w-radius-1, y+radius), radius)
    pygame.draw.circle(surface, color, (x+radius, y+h-radius-1), radius)
    pygame.draw.circle(surface, color, (x+w-radius-1, y+h-radius-1), radius)
    if border_color and border_width > 0:
        pygame.draw.rect(surface, border_color, (x+radius, y, w-2*radius, h), border_width)
        pygame.draw.rect(surface, border_color, (x, y+radius, w, h-2*radius), border_width)
        pygame.draw.circle(surface, border_color, (x+radius, y+radius), radius, border_width)
        pygame.draw.circle(surface, border_color, (x+w-radius-1, y+radius), radius, border_width)
        pygame.draw.circle(surface, border_color, (x+radius, y+h-radius-1), radius, border_width)
        pygame.draw.circle(surface, border_color, (x+w-radius-1, y+h-radius-1), radius, border_width)

def draw_board_panel(surface, board_grid_pos, title_text="PLAYER"):
    grid_x, grid_y = board_grid_pos

    # ใช้ขนาดเซลตามฝั่ง (คงที่)
    if title_text.upper() == "PLAYER":
        cell_size = PLAYER_CELL_SIZE
        pad_x, pad_y = 60, 40
        title_gap = 180
        extra_width, extra_height = 0, 120
    else:
        cell_size = BOT_CELL_SIZE
        pad_x, pad_y = 45, 30
        title_gap = 150
        extra_width, extra_height = 0, 0

    grid_w = SIZE * cell_size + (SIZE - 1) * GRID_GAP
    grid_h = SIZE * cell_size + (SIZE - 1) * GRID_GAP

    panel_x = grid_x - pad_x
    panel_y = grid_y - pad_y - title_gap
    panel_w = grid_w + pad_x * 2 + extra_width
    panel_h = grid_h + pad_y * 2 + title_gap + extra_height

    shadow = pygame.Surface((panel_w + 8, panel_h + 8), pygame.SRCALPHA)
    pygame.draw.rect(shadow, PANEL_SHADOW, shadow.get_rect(), border_radius=24)
    surface.blit(shadow, (panel_x - 2, panel_y + 4))

    draw_rounded_rect(surface, pygame.Rect(panel_x, panel_y, panel_w, panel_h),
                      PANEL_BG, radius=22, border_color=PANEL_BORDER, border_width=6)

    key = title_text.upper()
    style = TITLE_STYLE.get(key, DEFAULT_TITLE_STYLE)
    TITLE_OFFSET_X = style["offset_x"]
    TITLE_OFFSET_Y = style["offset_y"]
    LETTER_SPACING = style["spacing"]
    TITLE_COLOR    = style["color"]
    font_file = style.get("font_file_en") or DEFAULT_TITLE_STYLE["font_file_en"]
    custom_font = _safe_font(os.path.join(FONT_DIR, font_file), style["size"], fallback="arial")

    cursor_x   = panel_x + pad_x + TITLE_OFFSET_X
    baseline_y = panel_y + 18 + TITLE_OFFSET_Y
    for ch in title_text.upper():
        glyph = custom_font.render(ch, True, TITLE_COLOR)
        surface.blit(glyph, (cursor_x, baseline_y))
        cursor_x += glyph.get_width() + LETTER_SPACING

# =====================================================
# ------------------- Skill Panel (เหลือง) -------------------
skill_descriptions = []
skill_timer = []

def push_skill_desc(msg, sec=4.0):
    skill_descriptions.append(msg)
    skill_timer.append(int(sec*60))

def wrap_text(text, width, font):
    words = text.split()
    lines, line = [], ""
    for w in words:
        test = (line + w + " ").strip() + " "
        if font.size(test)[0] < width:
            line = test
        else:
            if line:
                lines.append(line.rstrip())
            line = w + " "
    if line:
        lines.append(line.rstrip())
    return lines

def update_skill_timer(clear_all=False):
    """ถ้า clear_all=True จะลบข้อความทั้งหมดทันที"""
    global skill_descriptions, skill_timer
    if clear_all:
        skill_descriptions.clear()
        skill_timer.clear()

# กล่องเหลือง "คงขนาด/ตำแหน่ง" จากจอเริ่มต้น
SKILL_FIXED_W = 300
SKILL_FIXED_H = 275
SKILL_PANEL_RECT = [INIT_SCREEN_WIDTH - SKILL_FIXED_W - 395, 530, SKILL_FIXED_W, SKILL_FIXED_H]

def draw_skill_descriptions():
    x, y, w, h = SKILL_PANEL_RECT

    shadow = pygame.Surface((w + 6, h + 6), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 60), shadow.get_rect(), border_radius=18)
    screen.blit(shadow, (x + 3, y + 4))
    
    pygame.draw.rect(screen, (255, 242, 189), (x, y, w, h), border_radius=18)
    pygame.draw.rect(screen, (214, 164, 84), (x, y, w, h), width=6, border_radius=18)

    title_font = pick_font("title", "Skill")
    title = title_font.render("Skill", True, BLACK)
    screen.blit(title, (x + 18, y + 5))

    body_font = pick_font("body", "ตัวอย่าง")
    yy = y + 54
    usable_w = w - 36
    for text in skill_descriptions:
        for line in wrap_text(text, usable_w, body_font):
            line_surf = body_font.render(line, True, BLACK)
            screen.blit(line_surf, (x + 18, yy))
            yy += line_surf.get_height() + 4
            if yy > y + h - 28:
                return

# ===== Buttons & Help =====
RESET_BTN_RECT = pygame.Rect(20, 20, 140, 48)
HELP_BTN_RECT  = pygame.Rect(20, 80, 180, 48)
show_help = False

def layout_update_buttons():
    global RESET_BTN_RECT, HELP_BTN_RECT
    reset_w, reset_h = 130, 48
    help_w, help_h   = 130, 48
    margin_x, margin_y = 5, 40

    reset_x = SCREEN_WIDTH - reset_w - margin_x
    reset_y = margin_y
    RESET_BTN_RECT = pygame.Rect(reset_x, reset_y, reset_w, reset_h)

    help_x = SCREEN_WIDTH - help_w - margin_x
    help_y = reset_y + reset_h + 10
    HELP_BTN_RECT = pygame.Rect(help_x, help_y, help_w, help_h)

def draw_button(surface, rect, label, hovered=False):
    bg = (255, 230, 160) if hovered else (255, 240, 180)
    pygame.draw.rect(surface, bg, rect, border_radius=12)
    pygame.draw.rect(surface, (214, 164, 84), rect, width=3, border_radius=12)
    f = pick_font("body", label)
    txt = f.render(label, True, (30, 30, 30))
    surface.blit(txt, txt.get_rect(center=rect.center))

HELP_TEXT = [
    "วิธีเล่น:",
    "• กด SPACE เพื่อสุ่มเลข",
    "• กดที่ตัวเลขของกระดาน player ถ้ามีเลขสุ่มตรง เพื่อทำเครื่องหมาย",
    "• สกิล:",
    "   - block: บล็อกช่องฝั่งตรงข้าม",
    "   - fire: โจมตี -1 (หัวใจ)",
    "   - heal: ฟื้น +1(หัวใจ) ",
    "   - remove: ลบเครื่องหมายของอีกฝั่ง",
    "   - lateup/latedown: ดัน/ถ่วงเลขในคิว",
    "• ปุ่มลัด: R รีเซ็ต, H คู่มือ, +/- ย่อ/ขยายปู",
    "• ปิดคู่มือ: คลิกที่ฉาก/กด ESC"
]

def draw_help_panel(surface):
    w, h = 520, 560
    x = (SCREEN_WIDTH - w)//2
    y = (SCREEN_HEIGHT - h)//2

    dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    dim.fill((0, 0, 0, 120))
    surface.blit(dim, (0, 0))

    pygame.draw.rect(surface, (255, 242, 189), (x, y, w, h), border_radius=18)
    pygame.draw.rect(surface, (214, 164, 84), (x, y, w, h), width=6, border_radius=18)

    title_surf = pick_font("title", "วิธีเล่น").render("วิธีเล่น", True, BLACK)
    surface.blit(title_surf, (x + 18, y + 16))

    body_font = pick_font("body", "ไทย")
    yy = y + 16 + title_surf.get_height() + 8
    usable_w = w - 36
    for line in HELP_TEXT:
        for part in wrap_text(line, usable_w, body_font):
            surface.blit(body_font.render(part, True, BLACK), (x + 18, yy))
            yy += body_font.get_height() + 4

def draw_result_popup(surface, winner_text):
    """วาดหน้าต่างแจ้งผลกลางจอ พร้อมคืน rect ของปุ่มรีเซ็ต (ไม่ตรวจคลิกที่นี่)"""
    w, h = 480, 240
    x = (SCREEN_WIDTH - w)//2
    y = (SCREEN_HEIGHT - h)//2

    # พื้นมืดครึ่งโปร่ง
    dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    dim.fill((0, 0, 0, 160))
    surface.blit(dim, (0, 0))

    # กล่องข้อความ
    pygame.draw.rect(surface, (255, 255, 210), (x, y, w, h), border_radius=18)
    pygame.draw.rect(surface, (230, 210, 150), (x, y, w, h), width=4, border_radius=18)

    # ข้อความผู้ชนะ/ผู้แพ้
    f_title = pick_font("title", "จบเกม")
    text = " " + winner_text + " "
    title_surf = f_title.render(text, True, (30, 30, 30))
    surface.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH//2, y + 80)))

    # ปุ่มรีเซ็ต
    btn_w, btn_h = 170, 50
    btn_x = (SCREEN_WIDTH - btn_w)//2
    btn_y = y + h - btn_h - 30
    btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)

    mouse_over = btn_rect.collidepoint(pygame.mouse.get_pos())
    draw_button(surface, btn_rect, "รีเซ็ตเกมใหม่ (R)", hovered=mouse_over)

    return btn_rect



def draw_number_panel(surface, x, y, w, h, number, title="เลขปัจจุบัน"):
    pygame.draw.rect(surface, YELLOW, (x, y, w, h), border_radius=18)
    pygame.draw.rect(surface, PANEL_BORDER, (x, y, w, h), width=4, border_radius=18)
    if number is not None:
        num_font = get_num_font(80)
        num_text = num_font.render(str(number), True, BLACK)
        num_rect = num_text.get_rect(center=(x + w // 2, y + h // 2 + 20))
        surface.blit(num_text, num_rect)

def draw_history_panel(surface, x, y, w, h, numbers, title="เลขที่ออกแล้ว", cols=7, pad=16, gap=10):

    shadow = pygame.Surface((w + 6, h + 6), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 60), shadow.get_rect(), border_radius=18)
    screen.blit(shadow, (x + 2, y + 3))

    pygame.draw.rect(surface, (255, 242, 189), (x, y, w, h), border_radius=18)
    pygame.draw.rect(surface, (214, 164, 84), (x, y, w, h), width=6, border_radius=18)

    title_font = pick_font("title", title)
    title_surf = title_font.render(title, True, BLACK)
    surface.blit(title_surf, (x + pad, y + pad-10))

    top = y + pad + title_surf.get_height() + 6
    left = x + pad
    usable_w = w - pad*2
    usable_h = h - (top - y) - pad

    cols = max(1, cols)
    cell_w = (usable_w - (cols - 1) * gap) // cols
    cell_h = max(36, int(cell_w * 0.65))
    rows   = max(1, (usable_h + gap) // (cell_h + gap))

    show = list(reversed(numbers))[: rows * cols]

    def fit_num_font(max_px):
        size = min(48, int(cell_h * 0.8))
        while size > 10:
            f = get_num_font(size)
            if f.size("88")[0] <= max_px:
                return f
            size -= 1
        return get_num_font(10)

    num_font = fit_num_font(int(cell_w * 0.8))

    for i, n in enumerate(show):
        r = i // cols
        c = i % cols
        cx = left + c * (cell_w + gap)
        cy = top  + r * (cell_h + gap)

        rect = pygame.Rect(cx, cy, cell_w, cell_h)
        pygame.draw.rect(surface, (255, 248, 200), rect, border_radius=10)
        pygame.draw.rect(surface, (230, 220, 160), rect, width=2, border_radius=10)

        txt = num_font.render(str(n), True, BLACK)
        surface.blit(txt, txt.get_rect(center=rect.center))

# =====================================================
# ------------------- CLASSES: Cell / Board -------------------
class Cell:
    def __init__(self, number, rect, skill="normal"):
        self.number = number
        self.skill = skill
        self.marked = False
        self.rect = rect
        self.blocked = False

    def draw(self, surface, num_font, base_size):
        color_map = {
            "fire": PASTEL_FIRE, "block": PASTEL_BLOCK, "heal": PASTEL_HEAL,
            "remove": PASTEL_REMOVE, "lateup": PASTEL_LATEUP, "latedown": PASTEL_LATEDOWN,
            "normal": PASTEL_NORMAL
        }
        color = (150,150,150) if self.blocked else color_map.get(self.skill, PASTEL_NORMAL)
        r = self.rect
        pygame.draw.rect(surface, color, r, border_radius=10)
        pygame.draw.rect(surface, (220,230,240), r, width=3, border_radius=10)

        text = "B" if self.blocked else str(self.number)
        text_surface = num_font.render(text, True, BLACK)
        surface.blit(text_surface, text_surface.get_rect(center=r.center))

        if self.marked:
            pygame.draw.circle(surface, (255,100,100), r.center, max(6, base_size//3), 5)

class Board:
    def __init__(self, size, position, numbers_skills, cell_size=50, grid_offset=(0, 0)):
        self.size = size
        self.position = position  # (grid_x, grid_y)
        self.cell_size = cell_size
        self.grid_offset = grid_offset
        self.cells = []
        self.generate_cells(numbers_skills)

    def generate_cells(self, numbers_skills):
        x0, y0 = self.position
        ox, oy = self.grid_offset
        self.cells = []
        for i in range(self.size):
            row = []
            for j in range(self.size):
                idx = i*self.size + j
                number, skill = numbers_skills[idx]
                rect = pygame.Rect(
                    x0 + ox + j*(self.cell_size + GRID_GAP),
                    y0 + oy + i*(self.cell_size + GRID_GAP),
                    self.cell_size,
                    self.cell_size
                )
                row.append(Cell(number, rect, skill))
            self.cells.append(row)

    def set_position(self, position):
        self.position = position
        self.generate_cells([(cell.number, cell.skill) for row in self.cells for cell in row])

    def draw(self, surface, is_bot=False):
        auto_num_size = max(16, int(self.cell_size * 0.58))
        num_size = auto_num_size if not is_bot else int(auto_num_size * 0.9)
        num_font = get_num_font(num_size)
        for row in self.cells:
            for cell in row:
                cell.draw(surface, num_font, self.cell_size)

    def mark_number(self, num):
        for row in self.cells:
            for cell in row:
                if cell.number == num and not cell.blocked:
                    cell.marked = True
                    return cell
        return None

    def check_bingo(self):
        for row in self.cells:
            if all(cell.marked for cell in row):
                return True
        for c in range(self.size):
            if all(self.cells[r][c].marked for r in range(self.size)):
                return True
        if all(self.cells[i][i].marked for i in range(self.size)):
            return True
        if all(self.cells[i][self.size-1-i].marked for i in range(self.size)):
            return True
        return False

# =====================================================
# ------------------- GAME -------------------
class BingoGame:
    def __init__(self):
        self.player_board, self.bot_board = self.generate_boards()

        self.called_numbers = []
        self.all_numbers = [cell.number for row in self.player_board.cells for cell in row] + \
                           [cell.number for row in self.bot_board.cells for cell in row]
        random.shuffle(self.all_numbers)

        self.current_number = None
        self.winner = None
        self.player_lives = 3
        self.bot_lives = 3

        self.block_message = None
        self.fire_message  = None
        self.heal_message  = None
        self.remove_message = None
        self.block_timer = 0
        self.fire_timer  = 0
        self.heal_timer  = 0
        self.remove_timer = 0

        self.block_selecting = False
               # board เป้าหมาย block/remove
        self.block_target_board = None
        self.remove_selecting = False
        self.remove_target_board = None
        self.remove_trigger_number = None

        self._build_fixed_mid_assets()

    def _build_fixed_mid_assets(self):
        bw, bh = banner_original.get_size()
        target_w = int(INIT_SCREEN_WIDTH * 0.70)
        target_h = int(INIT_SCREEN_HEIGHT * 0.26)
        scale_b  = min(target_w / bw, target_h / bh)
        self.banner_img  = pygame.transform.smoothscale(
            banner_original, (int(bw*scale_b), int(bh*scale_b))
        )

        base_w, base_h = crab_original.get_size()
        max_h = int(INIT_SCREEN_HEIGHT * MAX_H_FRAC)
        max_w = int(INIT_SCREEN_WIDTH  * MAX_W_FRAC)
        scale_fit = min(max_w / base_w, max_h / base_h)
        scale = max(0.1, scale_fit * CRAB_USER_SCALE)
        self.crab_img = pygame.transform.smoothscale(
            crab_original, (int(base_w*scale), int(base_h*scale))
        )

    def generate_boards(self):
        skill_counts = {"fire":5, "block":3, "heal":5, "remove":5, "lateup":2, "latedown":2, "normal":3}
        def generate_numbers_skills(start_num):
            nums = list(range(start_num, start_num + SIZE*SIZE))
            random.shuffle(nums)
            skills = []
            for skill, count in skill_counts.items():
                skills += [skill]*count
            random.shuffle(skills)
            return list(zip(nums, skills))

        player_ns = generate_numbers_skills(1)
        bot_ns    = generate_numbers_skills(1 + SIZE*SIZE)

        return (
            Board(SIZE, player_grid_pos, player_ns, cell_size=PLAYER_CELL_SIZE, grid_offset=tuple(PLAYER_GRID_OFFSET)),
            Board(SIZE, bot_grid_pos,    bot_ns,    cell_size=BOT_CELL_SIZE,    grid_offset=tuple(BOT_GRID_OFFSET))
        )

    def next_number(self):
        if self.all_numbers and not self.winner:
            self.current_number = self.all_numbers.pop(0)
            self.called_numbers.append(self.current_number)

            bot_cell = self.bot_board.mark_number(self.current_number)
            if bot_cell:
                self.activate_skill(bot_cell, "bot")

            if self.bot_board.check_bingo() and not self.winner:
                self.winner = "Bot Wins!"
                pygame.mixer.music.pause()
                lose_sound.play()

    def player_mark(self, pos):
        if self.winner:
            return

        if self.remove_selecting and self.remove_target_board == self.bot_board:
            for row in self.bot_board.cells:
                for cell in row:
                    if cell.rect.collidepoint(pos) and cell.marked and not cell.blocked:
                        cell.marked = False
                        self.remove_message = f"Removed mark {cell.number} from Bot!"
                        self.remove_timer = pygame.time.get_ticks()
                        self.remove_selecting = False
                        self.remove_target_board = None
                        self.remove_trigger_number = None
                        push_skill_desc("player remove T - T's mark")
                        return

        if self.block_selecting and self.block_target_board == self.bot_board:
            for row in self.bot_board.cells:
                for cell in row:
                    if cell.rect.collidepoint(pos) and not cell.blocked:
                        cell.blocked = True
                        cell.marked = False
                        self.block_message = f"BLOCKED {cell.number}"
                        self.block_timer = pygame.time.get_ticks()
                        self.block_selecting = False
                        self.block_target_board = None
                        push_skill_desc(f"Block number {cell.number} T-T")
                        return

        for row in self.player_board.cells:
            for cell in row:
                if cell.rect.collidepoint(pos) and not cell.blocked:
                    if cell.number in self.called_numbers:
                        cell.marked = True
                        self.activate_skill(cell, "player")
                        if self.player_board.check_bingo() and not self.winner:
                            self.winner = "Player Wins!"
                            pygame.mixer.music.pause()   # หยุดเพลงพื้นหลังชั่วคราว
                            win_sound.play()

    # ------------- SKILLS -------------
    def activate_skill(self, cell, owner):
        opponent = "bot" if owner=="player" else "player"

        if cell.skill=="block":
            if owner=="player":
                self.block_selecting = True
                self.block_target_board = self.bot_board
                self.block_message = "CHOOSE TO BLOCK"
                self.block_timer = pygame.time.get_ticks()
                push_skill_desc(say("player", "choose to block bot's number", target="bot"))
                play_sfx("block")
            else:
                self.trigger_block(self.player_board)

        elif cell.skill=="fire":
            self.trigger_fire(opponent, owner)
            play_sfx("fire")

        elif cell.skill=="heal":
            self.trigger_heal(owner)
            play_sfx("heal")

        elif cell.skill=="remove":
            if owner=="player":
                self.remove_selecting=True
                self.remove_target_board=self.bot_board
                self.remove_trigger_number=cell.number
                self.remove_message="REMOVE MARK! Choose Bot's marked cell"
                self.remove_timer=pygame.time.get_ticks()
                push_skill_desc("choose to remove bot's number")
                play_sfx("remove")
            else:
                self.trigger_remove_mark("bot", cell.number)

        elif cell.skill=="lateup":
            self.trigger_lateup(owner)
            play_sfx("lateup")

        elif cell.skill=="latedown":
            self.trigger_latedown(opponent, owner)
            play_sfx("latedown")

    def trigger_block(self, board):
        candidates=[cell for row in board.cells for cell in row if not cell.blocked]
        if candidates:
            c=random.choice(candidates)
            c.blocked=True
            c.marked=False
            push_skill_desc("T-T block player")

    def trigger_heal(self, target):
        if target == "player":
            self.player_lives = min(3, self.player_lives + 1)
        else:
            self.bot_lives = min(3, self.bot_lives + 1)
        push_skill_desc(("ผู้เล่น" if target=="player" else "T-T") + " heal +1")

    def trigger_fire(self, target, attacker):
        if target == "bot":
            self.bot_lives = max(0, self.bot_lives - 1)
            if self.bot_lives == 0:
                self.winner = "Player Wins!"
                pygame.mixer.music.pause()   # หยุดเพลงพื้นหลังชั่วคราว
                win_sound.play()
        else:
            self.player_lives = max(0, self.player_lives - 1)
            if self.player_lives == 0:
                self.winner = "Bot Wins!"
                pygame.mixer.music.pause()
                lose_sound.play()
        push_skill_desc(say(attacker, "โจมตี -1 ❤️", target=target))

    def trigger_remove_mark(self, board_name, number_used):
        if board_name=="player":
            return
        player_marked=[cell for row in self.player_board.cells for cell in row if cell.marked and not cell.blocked]
        if player_marked:
            removed=random.choice(player_marked)
            removed.marked=False
            push_skill_desc("T-Tยกเลิก mark ของผู้เล่น")
        else:
            push_skill_desc("T-Tพยายามยกเลิก mark แต่ไม่มีให้ลบ")
        self.remove_timer=pygame.time.get_ticks()

    def trigger_lateup(self, target):
        board = self.player_board if target=="player" else self.bot_board
        unmarked=[cell.number for row in board.cells for cell in row if not cell.marked]
        if not unmarked: return
        boost_count=max(1,len(unmarked)//6)
        boost_numbers=random.sample(unmarked,min(boost_count,len(unmarked)))
        self.all_numbers=[n for n in self.all_numbers if n not in boost_numbers]
        random.shuffle(boost_numbers)
        self.all_numbers=boost_numbers+self.all_numbers
        self.heal_message=f"✨ LATE UP {target.upper()}!"
        self.heal_timer=pygame.time.get_ticks()
        push_skill_desc(("ผู้เล่น" if target=="player" else "T-T") + " ต่อไปจะเป็นเลขในกระดานT-T")

    def trigger_latedown(self, target, owner):
        board = self.player_board if target=="player" else self.bot_board
        unmarked = [cell.number for row in board.cells for cell in row if not cell.marked]
        if not unmarked:
            return
        reduce_count  = max(1, len(unmarked)//6)
        reduce_numbers = random.sample(unmarked, min(reduce_count, len(unmarked)))
        self.all_numbers = [n for n in self.all_numbers if n not in reduce_numbers] + reduce_numbers
        self.heal_message = f"✨ LATE DOWN {target.upper()}!"
        self.heal_timer = pygame.time.get_ticks()
        push_skill_desc(say(owner, "ถ่วงเลขไปท้ายคิว", target=target))

    def draw_hearts_image(self, surface, lives, pos, img, scale=1.0, gap=None):
        x, y = pos
        size = int(40 * scale)
        if gap is None:
            gap = int(48 * scale)
        heart_img = pygame.transform.smoothscale(img, (size, size))
        for i in range(lives):
            surface.blit(heart_img, (x + i * gap, y))

    def draw(self, surface):
        # 1) BG
        surface.blit(background_scaled, (0, 0))

        # 2) พาเนล + กระดาน
        draw_board_panel(surface, self.player_board.position, "PLAYER")
        draw_board_panel(surface, self.bot_board.position,    "T - T")
        self.player_board.draw(surface, is_bot=False)
        self.bot_board.draw(surface, is_bot=True)

        # --- หัวใจ (ใช้ OFFSET) ---
        px = self.player_board.position[0] + PLAYER_HEART_OFFSET[0]
        py = self.player_board.position[1] + SIZE*(PLAYER_CELL_SIZE + GRID_GAP) + PLAYER_HEART_OFFSET[1]
        self.draw_hearts_image(surface, self.player_lives, (px, py),
                               heart_player_original, scale=PLAYER_HEART_SCALE, gap=72)

        bx = self.bot_board.position[0] + BOT_HEART_OFFSET[0]
        by = self.bot_board.position[1] + SIZE*(BOT_CELL_SIZE + GRID_GAP) + BOT_HEART_OFFSET[1]
        self.draw_hearts_image(surface, self.bot_lives, (bx, by),
                               heart_bot_original, scale=BOT_HEART_SCALE, gap=45)

        # 4) คำนวณจุดกึ่งกลางระหว่างบอร์ด
        player_grid_w = SIZE * PLAYER_CELL_SIZE + (SIZE - 1) * GRID_GAP
        bot_grid_w    = SIZE * BOT_CELL_SIZE    + (SIZE - 1) * GRID_GAP
        PAD_X_PLAYER  = 60
        PAD_X_BOT     = 45
        player_grid_x, player_grid_y = self.player_board.position
        bot_grid_x, bot_grid_y       = self.bot_board.position
        left_panel_right  = player_grid_x + player_grid_w + PAD_X_PLAYER
        right_panel_left  = bot_grid_x    - PAD_X_BOT
        mid_x = (left_panel_right + right_panel_left) / 2
        player_grid_h = SIZE * PLAYER_CELL_SIZE + (SIZE - 1) * GRID_GAP
        bot_grid_h    = SIZE * BOT_CELL_SIZE    + (SIZE - 1) * GRID_GAP
        mid_y = (player_grid_y + player_grid_h/2 + bot_grid_y + bot_grid_h/2) / 2

        # 5) กล่องเหลือง
        draw_skill_descriptions()

        # 6) ปู + แบนเนอร์
        banner_rect = self.banner_img.get_rect(midbottom=(mid_x, mid_y - 180))
        surface.blit(self.banner_img, banner_rect)
        crab_rect = self.crab_img.get_rect(center=(mid_x -15, mid_y+10))
        surface.blit(self.crab_img, crab_rect)

        # 7) เลขใต้ปู
        if self.current_number is not None:
            num_font = get_num_font(48)
            num_text = num_font.render(str(self.current_number), True, (255, 255, 255))
            surface.blit(num_text, num_text.get_rect(center=(mid_x + 8, mid_y + 55)))

        # 8) กล่องประวัติเลข
        draw_history_panel(surface, int(mid_x + Box_recent_number_x), int(mid_y + Box_recent_number_y),
                        510, 275, self.called_numbers, title="Recent Number", cols=7)

        # 9) สถานะชั่วคราว
        if SHOW_CENTER_STATUS:
            now = pygame.time.get_ticks()
            status_font = pick_font("body", "สถานะ")
            messages = [
                (self.block_message,  (255,180,180), self.block_timer),
                (self.fire_message,   PASTEL_FIRE,   self.fire_timer),
                (self.heal_message,   PASTEL_HEAL,   self.heal_timer),
                (self.remove_message, PASTEL_REMOVE, self.remove_timer)
            ]
            y_base = 100
            for idx, (msg, color, t) in enumerate(messages):
                if msg and now - t < 3000:
                    text_surf = status_font.render(msg, True, color)
                    surface.blit(text_surf, text_surf.get_rect(center=(INIT_SCREEN_WIDTH//2, y_base + idx*40)))

        # 10) ปุ่มรีเซ็ต + วิธีเล่น
        mouse_over_reset = RESET_BTN_RECT.collidepoint(pygame.mouse.get_pos())
        draw_button(surface, RESET_BTN_RECT, "รีเซ็ต (R)", hovered=mouse_over_reset)

        mouse_over_help = HELP_BTN_RECT.collidepoint(pygame.mouse.get_pos())
        draw_button(surface, HELP_BTN_RECT, "วิธีเล่น (H)", hovered=mouse_over_help)

        # 11) กล่องคู่มือ
        if show_help:
            draw_help_panel(surface)
        
        # 12) กล่องแจ้งผลแพ้/ชนะ
        popup_btn_rect = None
        if self.winner:
            popup_btn_rect = draw_result_popup(surface, self.winner)
        return popup_btn_rect



# =====================================================
def crash_guard(e):
    print("ERROR:", e)
    traceback.print_exc()

# =====================================================

# ------------------- MAIN LOOP -------------------
try:
    layout_update_buttons()
    game = BingoGame()
    running = True
    last_popup_btn_rect = None

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                SCREEN_WIDTH, SCREEN_HEIGHT = event.w, event.h
                screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                background_scaled = pygame.transform.smoothscale(background_original, (event.w, event.h))
                layout_update_buttons()

            elif game.winner:
                # ตอนเกมจบ: กด R หรือคลิกปุ่มใน popup เพื่อรีเซ็ต
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    update_skill_timer(clear_all=True)
                    game = BingoGame()
                    try: pygame.mixer.music.unpause()
                    except: pass

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if last_popup_btn_rect and last_popup_btn_rect.collidepoint(event.pos):
                        update_skill_timer(clear_all=True)
                        game = BingoGame()
                        try: pygame.mixer.music.unpause()
                        except: pass

            else:
                # โหมดปกติ
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if show_help:
                        show_help = False
                    elif RESET_BTN_RECT.collidepoint(event.pos):
                        update_skill_timer(clear_all=True)
                        game = BingoGame()
                        try: pygame.mixer.music.unpause()
                        except: pass
                    elif HELP_BTN_RECT.collidepoint(event.pos):
                        show_help = True
                    else:
                        game.player_mark(event.pos)

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        update_skill_timer(clear_all=True)
                        game.next_number()
                    elif event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                        CRAB_USER_SCALE = min(3.0, CRAB_USER_SCALE + 0.1)
                        game._build_fixed_mid_assets()
                    elif event.key == pygame.K_MINUS:
                        CRAB_USER_SCALE = max(0.3, CRAB_USER_SCALE - 0.1)
                        game._build_fixed_mid_assets()
                    elif event.key == pygame.K_r:
                        update_skill_timer(clear_all=True)
                        game = BingoGame()
                        try: pygame.mixer.music.unpause()
                        except: pass
                    elif event.key == pygame.K_h:
                        show_help = not show_help
                    elif event.key == pygame.K_ESCAPE and show_help:
                        show_help = False

        # วาดฉากหลัก แล้ว "อัปเดต rect ของปุ่ม popup" ให้ใช้ในเฟรมถัดไป
        last_popup_btn_rect = game.draw(screen)

        pygame.display.flip()
        clock.tick(60)



except Exception as e:
    crash_guard(e)
finally:
    pygame.quit() 

