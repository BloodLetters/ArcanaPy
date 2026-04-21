import pygame
from editor.theme import Colors, Layout, get_font, font_body, font_small, font_icon


class IconButton:
    def __init__(self, x, y, icon_text, tooltip, callback, size=None, group=None):
        sz = size or Layout.ICON_BUTTON_SIZE
        self.rect = pygame.Rect(x, y, sz, sz)
        self.icon_text = icon_text
        self.tooltip = tooltip
        self.callback = callback
        self.group = group
        self.is_hovered = False
        self.is_active = False
        self.enabled = True

    def set_pos(self, x, y):
        self.rect.x = x
        self.rect.y = y

    def handle_event(self, event):
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                self.callback()
                return True
        return False

    def draw(self, surface):
        if self.is_active:
            bg = Colors.ACCENT
        elif self.is_hovered:
            bg = Colors.SURFACE_HOVER
        else:
            bg = Colors.SURFACE

        shadow = self.rect.copy()
        shadow.y += 1
        pygame.draw.rect(surface, Colors.SHADOW, shadow, border_radius=Layout.BORDER_RADIUS)
        pygame.draw.rect(surface, bg, self.rect, border_radius=Layout.BORDER_RADIUS)
        pygame.draw.rect(surface, Colors.BORDER, self.rect, width=1, border_radius=Layout.BORDER_RADIUS)

        f = font_icon()
        color = Colors.TEXT_PRIMARY if self.enabled else Colors.TEXT_DISABLED
        surf = f.render(self.icon_text, True, color)
        r = surf.get_rect(center=self.rect.center)
        surface.blit(surf, r)

        if self.is_hovered and self.tooltip:
            tip_font = font_small()
            tip_surf = tip_font.render(self.tooltip, True, Colors.TEXT_PRIMARY)
            tip_w = tip_surf.get_width() + 12
            tip_h = tip_surf.get_height() + 6
            tip_rect = pygame.Rect(self.rect.centerx - tip_w // 2, self.rect.bottom + 4, tip_w, tip_h)
            pygame.draw.rect(surface, Colors.PANEL_HEADER, tip_rect, border_radius=4)
            pygame.draw.rect(surface, Colors.BORDER, tip_rect, width=1, border_radius=4)
            surface.blit(tip_surf, (tip_rect.x + 6, tip_rect.y + 3))


class TextButton:
    def __init__(self, x, y, w, h, text, callback, color=None, hover_color=None, danger=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.color = color or (Colors.DANGER if danger else Colors.SURFACE)
        self.hover_color = hover_color or (Colors.DANGER_HOVER if danger else Colors.SURFACE_HOVER)
        self.is_hovered = False
        self.is_active = False
        self.enabled = True

    def set_pos(self, x, y):
        self.rect.x = x
        self.rect.y = y

    def handle_event(self, event):
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                self.callback()
                return True
        return False

    def draw(self, surface):
        bg = self.hover_color if self.is_hovered else self.color
        if self.is_active:
            bg = Colors.ACCENT

        shadow = self.rect.copy()
        shadow.y += 1
        pygame.draw.rect(surface, Colors.SHADOW, shadow, border_radius=Layout.BORDER_RADIUS)
        pygame.draw.rect(surface, bg, self.rect, border_radius=Layout.BORDER_RADIUS)
        pygame.draw.rect(surface, Colors.BORDER, self.rect, width=1, border_radius=Layout.BORDER_RADIUS)

        f = font_body()
        color = Colors.TEXT_PRIMARY if self.enabled else Colors.TEXT_DISABLED
        surf = f.render(self.text, True, color)
        r = surf.get_rect(center=self.rect.center)
        surface.blit(surf, r)


class Toggle:
    def __init__(self, x, y, value, callback, label=""):
        self.rect = pygame.Rect(x, y, 36, 18)
        self.value = value
        self.callback = callback
        self.label = label
        self.is_hovered = False

    def set_pos(self, x, y):
        self.rect.x = x
        self.rect.y = y

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                self.value = not self.value
                self.callback(self.value)
                return True
        return False

    def draw(self, surface):
        track_color = Colors.SUCCESS if self.value else Colors.SURFACE
        pygame.draw.rect(surface, track_color, self.rect, border_radius=9)

        knob_x = self.rect.right - 16 if self.value else self.rect.x + 2
        knob_rect = pygame.Rect(knob_x, self.rect.y + 2, 14, 14)
        pygame.draw.rect(surface, Colors.TEXT_PRIMARY, knob_rect, border_radius=7)

        if self.label:
            f = font_small()
            surf = f.render(self.label, True, Colors.TEXT_SECONDARY)
            surface.blit(surf, (self.rect.right + 6, self.rect.y + 2))


class ScrollArea:
    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.scroll_y = 0
        self.content_height = 0
        self.max_scroll = 0
        self.is_hovered = False
        self.is_dragging = False
        self.drag_start_y = 0
        self.scroll_start_y = 0

    def set_rect(self, rect):
        self.rect = pygame.Rect(rect)
        self._update_max_scroll()

    def set_content_height(self, h):
        self.content_height = h
        self._update_max_scroll()

    def _update_max_scroll(self):
        self.max_scroll = max(0, self.content_height - self.rect.height)
        self.scroll_y = min(self.scroll_y, self.max_scroll)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
            if self.is_dragging:
                dy = event.pos[1] - self.drag_start_y
                bar_h = max(20, int(self.rect.height * (self.rect.height / self.content_height)))
                scrollable_bar_area = self.rect.height - bar_h
                if scrollable_bar_area > 0:
                    scroll_delta = (dy / scrollable_bar_area) * self.max_scroll
                    self.scroll_y = max(0, min(self.scroll_start_y + scroll_delta, self.max_scroll))
                return True

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.max_scroll > 0:
                bar_h = max(20, int(self.rect.height * (self.rect.height / self.content_height)))
                bar_y = self.rect.y + int((self.scroll_y / self.max_scroll) * (self.rect.height - bar_h))
                # Wider hit area for easier dragging
                bar_rect = pygame.Rect(self.rect.right - Layout.SCROLL_BAR_WIDTH - 4, bar_y,
                                       Layout.SCROLL_BAR_WIDTH + 8, bar_h)
                if bar_rect.collidepoint(event.pos):
                    self.is_dragging = True
                    self.drag_start_y = event.pos[1]
                    self.scroll_start_y = self.scroll_y
                    return True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_dragging:
                self.is_dragging = False
                return True

        elif event.type == pygame.MOUSEWHEEL:
            if self.is_hovered:
                self.scroll_y -= event.y * 24
                self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))
                return True
        return False

    def begin_draw(self, surface):
        surface.set_clip(self.rect)
        return -self.scroll_y + self.rect.y

    def end_draw(self, surface):
        surface.set_clip(None)
        if self.max_scroll > 0:
            bar_h = max(20, int(self.rect.height * (self.rect.height / self.content_height)))
            bar_y = self.rect.y + int((self.scroll_y / self.max_scroll) * (self.rect.height - bar_h))
            bar_rect = pygame.Rect(self.rect.right - Layout.SCROLL_BAR_WIDTH, bar_y,
                                   Layout.SCROLL_BAR_WIDTH, bar_h)
            color = Colors.ACCENT if self.is_dragging else Colors.SURFACE_HOVER
            pygame.draw.rect(surface, color, bar_rect, border_radius=3)


class Separator:
    @staticmethod
    def draw(surface, x, y, width, label=None):
        mid_y = y + 8
        if label:
            f = font_small()
            lbl = f.render(label, True, Colors.TEXT_MUTED)
            lbl_w = lbl.get_width()
            pygame.draw.line(surface, Colors.BORDER, (x, mid_y), (x + 8, mid_y))
            surface.blit(lbl, (x + 14, y + 1))
            pygame.draw.line(surface, Colors.BORDER, (x + 20 + lbl_w, mid_y), (x + width, mid_y))
            return 20
        else:
            pygame.draw.line(surface, Colors.BORDER, (x, mid_y), (x + width, mid_y))
            return 16


class ContextMenu:

    def __init__(self, x, y, items, close_callback, window_size=None):
        self.close_callback = close_callback
        item_h = 30
        w = 180
        h = len(items) * item_h + 16
        self.rect = pygame.Rect(x, y, w, h)

        if window_size:
            if self.rect.right > window_size[0]:
                self.rect.x -= self.rect.width
            if self.rect.bottom > window_size[1]:
                self.rect.y -= self.rect.height

        self.buttons = []
        by = self.rect.y + 8
        for label, callback, color in items:
            btn = TextButton(
                self.rect.x + 8, by, w - 16, item_h - 4, label, callback,
                color=color or Colors.SURFACE, hover_color=Colors.SURFACE_HOVER
            )
            self.buttons.append(btn)
            by += item_h

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            for btn in self.buttons:
                btn.handle_event(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            for btn in self.buttons:
                if btn.handle_event(event):
                    return True
            if not self.rect.collidepoint(event.pos):
                self.close_callback()
                return True
        return False

    def draw(self, surface):
        shadow = self.rect.inflate(6, 6)
        pygame.draw.rect(surface, Colors.SHADOW, shadow, border_radius=8)
        pygame.draw.rect(surface, Colors.PANEL_BG, self.rect, border_radius=8)
        pygame.draw.rect(surface, Colors.ACCENT, self.rect, width=1, border_radius=8)
        for btn in self.buttons:
            btn.draw(surface)
