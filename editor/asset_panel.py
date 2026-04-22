import os
import pygame
from editor.theme import Colors, Layout, font_title, font_section, font_small
from editor.ui_components import ScrollArea


class AssetPanel:
    def __init__(self, editor):
        self.editor = editor
        self.rect = pygame.Rect(0, Layout.TOOLBAR_HEIGHT, Layout.LEFT_PANEL_WIDTH, 600)
        self.categories = {}  # {category_name: [asset_path, ...]}
        self.scroll = ScrollArea((0, 0, 10, 10))
        self.asset_rects = []  # [(rect, asset_path), ...]
        self.image_cache = {}

    def load_assets(self, assets_dir="assets"):
        self.categories.clear()
        if not os.path.exists(assets_dir):
            self.categories["Default"] = []
            return

        for root, dirs, files in os.walk(assets_dir):
            # Exclude specific directories
            if root == assets_dir:
                if 'players' in dirs:
                    dirs.remove('Players')
                if 'enemies' in dirs:
                    dirs.remove('Enemies')
                if 'effect' in dirs:
                    dirs.remove('Effects')

            rel = os.path.relpath(root, assets_dir)
            category = rel.replace("\\", "/")
            if category == ".":
                category = "General"

            images = []
            for f in sorted(files):
                if f.lower().endswith(('.png', '.jpg', '.jpeg')):
                    path = os.path.join(root, f).replace('\\', '/')
                    images.append(path)
            if images:
                self.categories[category] = images

    def get_all_assets(self):
        result = []
        for assets in self.categories.values():
            result.extend(assets)
        return result

    def get_image(self, path):
        if path not in self.image_cache:
            try:
                img = pygame.image.load(path).convert_alpha()
                self.image_cache[path] = img
            except Exception:
                self.image_cache[path] = None
        return self.image_cache[path]

    def recalculate(self, window_height):
        self.rect.height = window_height - Layout.TOOLBAR_HEIGHT
        self.rect.y = Layout.TOOLBAR_HEIGHT

        scroll_rect = (
            self.rect.x, self.rect.y + 44,
            self.rect.width, self.rect.height - 44
        )
        self.scroll.set_rect(scroll_rect)

        content_h = 0
        cols = max(1, (self.rect.width - Layout.PANEL_PADDING * 2 + Layout.ITEM_SPACING)
                   // (Layout.THUMB_SIZE + Layout.ITEM_SPACING))
        for cat, assets in self.categories.items():
            content_h += 28  # Category header
            rows = (len(assets) + cols - 1) // cols
            content_h += rows * (Layout.THUMB_SIZE + Layout.ITEM_SPACING) + Layout.SECTION_SPACING
        self.scroll.set_content_height(content_h)

    def handle_event(self, event):
        if self.scroll.handle_event(event):
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                for rect, asset_path in self.asset_rects:
                    if rect.collidepoint(event.pos):
                        self.editor.active_asset = asset_path
                        self.editor.set_tool("DRAW")
                        return True
                return True
        elif event.type == pygame.MOUSEMOTION:
            pass
        return False

    def draw(self, surface):
        pygame.draw.rect(surface, Colors.PANEL_BG, self.rect)
        pygame.draw.line(surface, Colors.BORDER,
                         (self.rect.right - 1, self.rect.y),
                         (self.rect.right - 1, self.rect.bottom), 2)

        f = font_title()
        title = f.render("ASSETS", True, Colors.ACCENT)
        surface.blit(title, (self.rect.x + Layout.PANEL_PADDING, self.rect.y + 14))

        self.asset_rects.clear()
        offset_y = self.scroll.begin_draw(surface)

        pad = Layout.PANEL_PADDING
        thumb = Layout.THUMB_SIZE
        gap = Layout.ITEM_SPACING
        cols = max(1, (self.rect.width - pad * 2 + gap) // (thumb + gap))
        mouse_pos = pygame.mouse.get_pos()

        y = offset_y
        for cat, assets in self.categories.items():
            cat_font = font_section()
            cat_surf = cat_font.render(cat.upper(), True, Colors.TEXT_SECONDARY)
            if self.rect.y <= y + 20 <= self.rect.bottom:
                surface.blit(cat_surf, (self.rect.x + pad, y + 4))
            y += 28

            for i, asset_path in enumerate(assets):
                col_idx = i % cols
                row_idx = i // cols
                ax = self.rect.x + pad + col_idx * (thumb + gap)
                ay = y + row_idx * (thumb + gap)

                r = pygame.Rect(ax, ay, thumb, thumb)
                self.asset_rects.append((r, asset_path))

                if r.bottom >= self.scroll.rect.y and r.top <= self.scroll.rect.bottom:
                    is_hovered = r.collidepoint(mouse_pos)

                    if self.editor.active_asset == asset_path:
                        bg = r.inflate(6, 6)
                        pygame.draw.rect(surface, Colors.ACCENT, bg, border_radius=4)
                    elif is_hovered:
                        bg = r.inflate(6, 6)
                        pygame.draw.rect(surface, Colors.SURFACE_HOVER, bg, border_radius=4)

                    img = self.get_image(asset_path)
                    if img:
                        scaled = pygame.transform.scale(img, (thumb, thumb))
                        surface.blit(scaled, (ax, ay))
                    else:
                        pygame.draw.rect(surface, Colors.SURFACE, r, border_radius=4)
                        err = font_small().render("?", True, Colors.TEXT_MUTED)
                        surface.blit(err, err.get_rect(center=r.center))

                    if is_hovered:
                        name = os.path.basename(asset_path)
                        tip = font_small().render(name, True, Colors.TEXT_PRIMARY)
                        tw = tip.get_width() + 10
                        tr = pygame.Rect(ax, ay - 18, tw, 16)
                        pygame.draw.rect(surface, Colors.PANEL_HEADER, tr, border_radius=3)
                        surface.blit(tip, (tr.x + 5, tr.y + 1))

            rows = (len(assets) + cols - 1) // cols
            y += rows * (thumb + gap) + Layout.SECTION_SPACING

        self.scroll.end_draw(surface)
