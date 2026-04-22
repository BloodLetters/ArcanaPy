import pygame

class Colors:
    BG_DARK = (25, 26, 35)
    BG_MAIN = (30, 31, 42)
    PANEL_BG = (36, 38, 50)
    PANEL_HEADER = (42, 44, 58)
    SURFACE = (52, 55, 72)
    SURFACE_HOVER = (68, 71, 94)
    SURFACE_ACTIVE = (80, 84, 110)
    BORDER = (58, 61, 80)
    BORDER_LIGHT = (78, 82, 106)

    TEXT_PRIMARY = (235, 235, 240)
    TEXT_SECONDARY = (160, 164, 180)
    TEXT_MUTED = (100, 104, 120)
    TEXT_DISABLED = (70, 74, 90)

    ACCENT = (139, 107, 219)         # Purple
    ACCENT_HOVER = (160, 130, 235)
    ACCENT_DIM = (90, 70, 150)
    SUCCESS = (80, 220, 120)         # Green
    SUCCESS_HOVER = (100, 240, 140)
    DANGER = (220, 70, 70)           # Red
    DANGER_HOVER = (240, 90, 90)
    WARNING = (230, 180, 60)         # Yellow
    INFO = (80, 170, 240)            # Blue

    GRID_LINE = (44, 46, 62)
    GRID_LINE_MAJOR = (55, 58, 78)
    CANVAS_BG = (22, 23, 32)
    SELECTION = (139, 107, 219, 100)  # Semi-transparent purple
    CURSOR_PREVIEW = (139, 107, 219, 80)
    SHADOW = (12, 12, 18)

    LAYER_BG = (60, 140, 90)
    LAYER_OBJ = (140, 100, 60)
    LAYER_COL = (180, 60, 60)
    LAYER_DEC = (60, 120, 180)


class Layout:
    TOOLBAR_HEIGHT = 48
    LEFT_PANEL_WIDTH = 220
    RIGHT_PANEL_WIDTH = 250
    PANEL_PADDING = 12
    ITEM_SPACING = 6
    SECTION_SPACING = 16
    BUTTON_HEIGHT = 32
    ICON_BUTTON_SIZE = 36
    THUMB_SIZE = 48
    BORDER_RADIUS = 6
    SCROLL_BAR_WIDTH = 6


class Icons:
    BRUSH = "B"
    ERASER = "E"
    MOVE = "M"
    FILL = "F"
    SELECT = "S"
    PLAY = "P"
    SAVE = "S"
    LOAD = "L"
    CLEAR = "X"
    FULLSCREEN = "[]"
    EYE_OPEN = "O"
    EYE_CLOSED = "-"
    LOCK = "#"
    UNLOCK = "."
    ARROW_UP = "^"
    ARROW_DOWN = "v"
    PLUS = "+"
    MINUS = "-"
    ZOOM_IN = "+"
    ZOOM_OUT = "-"


_fonts_cache = {}


def get_font(size, bold=False):
    key = (size, bold)
    if key not in _fonts_cache:
        _fonts_cache[key] = pygame.font.SysFont("Segoe UI", size, bold=bold)
    return _fonts_cache[key]


def font_title():
    return get_font(16, bold=True)


def font_section():
    return get_font(13, bold=True)


def font_body():
    return get_font(13)


def font_small():
    return get_font(11)


def font_icon():
    return get_font(16, bold=True)


def font_huge():
    return get_font(22, bold=True)
