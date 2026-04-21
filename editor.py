import sys
import os
import pygame
from core.settings import WINDOW_WIDTH, WINDOW_HEIGHT, FPS, BG_COLOR, MAP_FILE, MAP_WIDTH, LEFT_UI_WIDTH, RIGHT_UI_WIDTH, TILE_SIZE
from core.grid import draw_grid, get_grid_pos
from core.map import MapData

class Theme:
    PANEL_BG = (40, 42, 54)
    SURFACE = (68, 71, 90)
    SURFACE_LIGHT = (98, 114, 164)
    TEXT = (248, 248, 242)
    ACCENT = (189, 147, 249)
    WALKABLE = (80, 250, 123)
    SOLID = (255, 85, 85)
    SHADOW = (20, 20, 30)

class UIButton:
    def __init__(self, x, y, w, h, text, color, hover_color, callback, border_radius=8, is_active=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.callback = callback
        self.border_radius = border_radius
        self.is_hovered = False
        self.is_active = is_active

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.is_hovered:
                self.callback()
                return True
        return False

    def update_color(self, color, hover_color):
        self.color = color
        self.hover_color = hover_color

    def draw(self, surface, font):
        # Highlighting for active tool
        if self.is_active:
            glow_rect = self.rect.inflate(6, 6)
            pygame.draw.rect(surface, Theme.ACCENT, glow_rect, border_radius=self.border_radius + 2)

        curr_color = self.hover_color if self.is_hovered else self.color
        # Shadow effect
        shadow_rect = self.rect.copy()
        shadow_rect.y += 2
        pygame.draw.rect(surface, Theme.SHADOW, shadow_rect, border_radius=self.border_radius)
        
        pygame.draw.rect(surface, curr_color, self.rect, border_radius=self.border_radius)
        pygame.draw.rect(surface, (100, 100, 120), self.rect, width=1, border_radius=self.border_radius)
        
        text_surf = font.render(self.text, True, Theme.TEXT)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

class ContextMenu:
    def __init__(self, x, y, col, row, map_data, close_callback):
        self.rect = pygame.Rect(x, y, 160, 90)
        self.col = col
        self.row = row
        self.map_data = map_data
        self.close_callback = close_callback
        
        # Constrain to window
        if self.rect.right > WINDOW_WIDTH: self.rect.x -= self.rect.width
        if self.rect.bottom > WINDOW_HEIGHT: self.rect.y -= self.rect.height
        
        tile_exists = (col, row) in map_data.tiles
        walkable = map_data.tiles[(col, row)]["walkable"] if tile_exists else False
        
        btn_color = Theme.WALKABLE if walkable else Theme.SOLID
        btn_hover = (100, 255, 150) if walkable else (255, 100, 100)
        
        self.buttons = [
            UIButton(self.rect.x + 10, self.rect.y + 10, self.rect.width - 20, 30, 
                     "DELETE TILE", (120, 40, 40), (180, 60, 60), self.delete_tile),
            UIButton(self.rect.x + 10, self.rect.y + 48, self.rect.width - 20, 30, 
                     f"WALKABLE: {'Y' if walkable else 'N'}", btn_color, btn_hover, self.toggle_walkable)
        ]

    def delete_tile(self):
        self.map_data.remove_wall(self.col, self.row)
        self.close_callback()

    def toggle_walkable(self):
        if (self.col, self.row) in self.map_data.tiles:
            tile = self.map_data.tiles[(self.col, self.row)]
            tile["walkable"] = not tile["walkable"]
            
            walkable = tile["walkable"]
            new_color = Theme.WALKABLE if walkable else Theme.SOLID
            new_hover = (100, 255, 150) if walkable else (255, 100, 100)
            
            self.buttons[1].text = f"WALKABLE: {'Y' if walkable else 'N'}"
            self.buttons[1].update_color(new_color, new_hover)

    def handle_event(self, event):
        for btn in self.buttons:
            if btn.handle_event(event):
                return True
        if event.type == pygame.MOUSEBUTTONDOWN:
            if not self.rect.collidepoint(event.pos):
                self.close_callback()
                return True
        return False

    def draw(self, surface, font):
        # Draw background shadow
        bg_shadow = self.rect.inflate(4, 4)
        pygame.draw.rect(surface, Theme.SHADOW, bg_shadow, border_radius=10)
        
        pygame.draw.rect(surface, Theme.PANEL_BG, self.rect, border_radius=8)
        pygame.draw.rect(surface, Theme.ACCENT, self.rect, width=2, border_radius=8)
        for btn in self.buttons:
            btn.draw(surface, font)

class Editor:
    def __init__(self):
        pygame.init()
        self.window_width = WINDOW_WIDTH
        self.window_height = WINDOW_HEIGHT
        self.map_width = MAP_WIDTH
        self.is_fullscreen = False
        
        self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
        pygame.display.set_caption("Map Editor")
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.map_data = MapData()
        self.map_data.load(MAP_FILE)
        
        self.left_mouse_down = False
        self.right_mouse_down = False
        
        self.assets = []
        self.load_assets()
        self.active_asset = self.assets[0] if self.assets else None
        self.ui_rects = []
        self.is_walkable_mode = False
        
        # Camera variables
        self.camera_x = 0
        self.camera_y = 0
        self.camera_speed = 5
        self.mouse_last_pos = (0, 0)
        
        # State
        self.current_tool = "DRAW" # DRAW, MOVE, DELETE
        self.context_menu = None
        
        # UI Setup
        self.font_main = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self.font_small = pygame.font.SysFont("Segoe UI", 14)
        self.font_title = pygame.font.SysFont("Segoe UI", 24, bold=True)
        
        self.recalculate_layout()

    def recalculate_layout(self):
        w, h = self.screen.get_size()
        self.window_width = w
        self.window_height = h
        self.map_width = w - LEFT_UI_WIDTH - RIGHT_UI_WIDTH
        # Ensure map doesn't get negative
        self.map_width = max(100, self.map_width)
        
        # Re-setup buttons at new positions
        self.setup_ui_buttons()

    def setup_ui_buttons(self):
        btn_w = RIGHT_UI_WIDTH - 40
        btn_h = 35
        x = LEFT_UI_WIDTH + self.map_width + 20
        y_start = 120
        
        # Tool Buttons
        self.tool_buttons = {
            "MOVE": UIButton(x, y_start, btn_w, btn_h, "MOVE TOOL", Theme.SURFACE, Theme.SURFACE_LIGHT, lambda: self.set_tool("MOVE")),
            "DRAW": UIButton(x, y_start + 40, btn_w, btn_h, "DRAW TOOL", Theme.SURFACE, Theme.SURFACE_LIGHT, lambda: self.set_tool("DRAW")),
            "DELETE": UIButton(x, y_start + 80, btn_w, btn_h, "DELETE TOOL", Theme.SURFACE, Theme.SURFACE_LIGHT, lambda: self.set_tool("DELETE"))
        }
        
        # Action Buttons
        y_actions = y_start + 140
        self.buttons = [
            UIButton(x, y_actions, btn_w, btn_h, "SAVE (S)", Theme.SURFACE, Theme.SURFACE_LIGHT, lambda: self.map_data.save(MAP_FILE)),
            UIButton(x, y_actions + 40, btn_w, btn_h, "LOAD (L)", Theme.SURFACE, Theme.SURFACE_LIGHT, lambda: self.map_data.load(MAP_FILE)),
            UIButton(x, y_actions + 80, btn_w, btn_h, "TOGGLE (W)", Theme.SURFACE, Theme.SURFACE_LIGHT, self.toggle_walkable),
            UIButton(x, y_actions + 120, btn_w, btn_h, "CLEAR ALL", (100, 50, 50), (150, 70, 70), self.clear_map)
        ]

    def set_tool(self, tool):
        self.current_tool = tool
        for name, btn in self.tool_buttons.items():
            btn.is_active = (name == tool)

    def toggle_walkable(self):
        self.is_walkable_mode = not self.is_walkable_mode

    def clear_map(self):
        self.map_data.tiles.clear()

    def load_assets(self):
        assets_dir = "assets"
        if not os.path.exists(assets_dir):
            return
        for root, _, files in os.walk(assets_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                    path = os.path.join(root, file).replace('\\', '/')
                    self.assets.append(path)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.recalculate_layout()
            
            # Context Menu has priority
            if self.context_menu:
                if self.context_menu.handle_event(event):
                    continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    self.map_data.save(MAP_FILE)
                elif event.key == pygame.K_l:
                    self.map_data.load(MAP_FILE)
                elif event.key == pygame.K_w:
                    self.toggle_walkable()
                elif event.key == pygame.K_m: self.set_tool("MOVE")
                elif event.key == pygame.K_d: self.set_tool("DELETE")
                elif event.key == pygame.K_b: self.set_tool("DRAW")
                elif event.key == pygame.K_F11:
                    self.toggle_fullscreen()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                
                # Check UI Buttons in Right Panel
                ui_clicked = False
                for btn in self.buttons + list(self.tool_buttons.values()):
                    if btn.handle_event(event):
                        ui_clicked = True
                        break
                if ui_clicked:
                    continue

                if mouse_pos[0] < LEFT_UI_WIDTH:
                    # Clicked UI Assets (Left Panel)
                    for rect, asset in self.ui_rects:
                        if rect.collidepoint(mouse_pos):
                            self.active_asset = asset
                            self.set_tool("DRAW")
                elif LEFT_UI_WIDTH <= mouse_pos[0] < LEFT_UI_WIDTH + self.map_width:
                    # Clicked Map Area
                    if event.button == 1:
                        self.left_mouse_down = True
                        self.mouse_last_pos = mouse_pos
                    elif event.button == 3:
                        col, row = get_grid_pos(mouse_pos, self.camera_x, self.camera_y)
                        self.context_menu = ContextMenu(mouse_pos[0], mouse_pos[1], col, row, self.map_data, self.close_context_menu)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.left_mouse_down = False
                elif event.button == 3:
                    self.right_mouse_down = False
            elif event.type == pygame.MOUSEMOTION:
                # Update button hover states
                for btn in self.buttons + list(self.tool_buttons.values()):
                    btn.handle_event(event)

                if self.current_tool == "MOVE" and self.left_mouse_down:
                    current_pos = event.pos
                    dx = current_pos[0] - self.mouse_last_pos[0]
                    dy = current_pos[1] - self.mouse_last_pos[1]
                    self.camera_x -= dx
                    self.camera_y -= dy
                    self.mouse_last_pos = current_pos

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.RESIZABLE)
        else:
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
        self.recalculate_layout()

    def close_context_menu(self):
        self.context_menu = None

    def update(self):
        # Handle camera movement with arrow keys
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.camera_x -= self.camera_speed
        if keys[pygame.K_RIGHT]:
            self.camera_x += self.camera_speed
        if keys[pygame.K_UP]:
            self.camera_y -= self.camera_speed
        if keys[pygame.K_DOWN]:
            self.camera_y += self.camera_speed

        mouse_pos = pygame.mouse.get_pos()
        if LEFT_UI_WIDTH <= mouse_pos[0] < LEFT_UI_WIDTH + self.map_width:
            col, row = get_grid_pos(mouse_pos, self.camera_x, self.camera_y)
            if self.left_mouse_down:
                if self.current_tool == "DRAW":
                    self.map_data.add_wall(col, row, self.active_asset, getattr(self, 'is_walkable_mode', False))
                elif self.current_tool == "DELETE":
                    self.map_data.remove_wall(col, row)

    def draw_ui(self):
        self.draw_assets_panel()
        self.draw_properties_panel()
        
    def draw_assets_panel(self):
        panel_rect = pygame.Rect(0, 0, LEFT_UI_WIDTH, self.window_height)
        pygame.draw.rect(self.screen, Theme.PANEL_BG, panel_rect)
        pygame.draw.line(self.screen, Theme.SURFACE_LIGHT, (LEFT_UI_WIDTH, 0), (LEFT_UI_WIDTH, self.window_height), 2)
        
        title_surf = self.font_title.render("ASSET LIBRARY", True, Theme.ACCENT)
        self.screen.blit(title_surf, (20, 20))
        
        padding = 10
        thumb_size = 45
        x = 20
        y = 70
        self.ui_rects.clear()
        
        for asset in self.assets:
            img = self.map_data.get_image(asset)
            if img:
                mouse_pos = pygame.mouse.get_pos()
                thumb_rect = pygame.Rect(x, y, thumb_size, thumb_size)
                self.ui_rects.append((thumb_rect, asset))
                
                is_hovered = thumb_rect.collidepoint(mouse_pos)
                if self.active_asset == asset:
                    bg_rect = thumb_rect.inflate(8, 8)
                    pygame.draw.rect(self.screen, Theme.ACCENT, bg_rect, border_radius=6)
                elif is_hovered:
                    bg_rect = thumb_rect.inflate(8, 8)
                    pygame.draw.rect(self.screen, Theme.SURFACE_LIGHT, bg_rect, border_radius=6)
                
                thumb = pygame.transform.scale(img, (thumb_size, thumb_size))
                self.screen.blit(thumb, (x, y))
                
                x += thumb_size + padding + 5
                if x + thumb_size > LEFT_UI_WIDTH - 10:
                    x = 20
                    y += thumb_size + padding + 5

    def draw_properties_panel(self):
        panel_rect = pygame.Rect(LEFT_UI_WIDTH + self.map_width, 0, RIGHT_UI_WIDTH, self.window_height)
        pygame.draw.rect(self.screen, Theme.PANEL_BG, panel_rect)
        pygame.draw.line(self.screen, Theme.SURFACE_LIGHT, (LEFT_UI_WIDTH + self.map_width, 0), (LEFT_UI_WIDTH + self.map_width, self.window_height), 2)
        
        title_surf = self.font_title.render("PROPERTIES", True, Theme.ACCENT)
        self.screen.blit(title_surf, (LEFT_UI_WIDTH + self.map_width + 20, 20))
        
        mode_text = "WALK" if self.is_walkable_mode else "SOLID"
        mode_color = Theme.WALKABLE if self.is_walkable_mode else Theme.SOLID
        
        pill_rect = pygame.Rect(LEFT_UI_WIDTH + self.map_width + 20, 60, RIGHT_UI_WIDTH - 40, 30)
        pygame.draw.rect(self.screen, Theme.SURFACE, pill_rect, border_radius=15)
        
        lbl_surf = self.font_small.render("MODE:", True, (150, 150, 150))
        self.screen.blit(lbl_surf, (LEFT_UI_WIDTH + self.map_width + 30, 67))
        
        txt_surf = self.font_main.render(mode_text, True, mode_color)
        txt_rect = txt_surf.get_rect(midleft=(LEFT_UI_WIDTH + self.map_width + 85, 75))
        self.screen.blit(txt_surf, txt_rect)

        for btn in self.tool_buttons.values():
            btn.draw(self.screen, self.font_main)

        for btn in self.buttons:
            btn.draw(self.screen, self.font_main)
            
        help_surf = self.font_small.render("F11: Fullscreen | Arrows: Pan", True, (100, 100, 100))
        self.screen.blit(help_surf, (LEFT_UI_WIDTH + self.map_width + 12, self.window_height - 25))

    def draw(self):
        self.screen.fill(BG_COLOR)
        self.map_data.draw(self.screen, self.camera_x, self.camera_y, self.map_width, self.window_height)
        draw_grid(self.screen, self.camera_x, self.camera_y, self.map_width, self.window_height)
        self.draw_ui()
        
        # Draw context menu on top
        if self.context_menu:
            self.context_menu.draw(self.screen, self.font_small)
            
        pygame.display.flip()

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()
            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    editor = Editor()
    editor.run()
