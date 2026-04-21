import sys
import pygame
from core.settings import FPS, MAP_FILE, EDITOR_WIDTH, EDITOR_HEIGHT
from editor.theme import Colors, Layout
from editor.camera import Camera
from editor.layer_manager import LayerManager
from editor.toolbar import Toolbar
from editor.asset_panel import AssetPanel
from editor.properties_panel import PropertiesPanel
from editor.canvas import Canvas


class EditorApp:
    def __init__(self):
        pygame.init()

        self.window_width = EDITOR_WIDTH
        self.window_height = EDITOR_HEIGHT
        self.is_fullscreen = False

        self.icon = pygame.image.load("preview/images/icon-379x300.png")
        pygame.display.set_icon(self.icon)

        self.screen = pygame.display.set_mode(
            (self.window_width, self.window_height), pygame.RESIZABLE
        )
        pygame.display.set_caption("Map Editor - ArcanaPY")
        self.clock = pygame.time.Clock()
        self.running = True

        self.camera = Camera()
        self.layer_manager = LayerManager()
        self.layer_manager.load(MAP_FILE)

        self.current_tool = "DRAW"
        self.walkable_mode = False
        self.active_asset = None
        self.context_menu = None

        self.left_mouse_down = False
        self.middle_mouse_down = False
        self.mouse_last_pos = (0, 0)

        self.toolbar = Toolbar(self)
        self.asset_panel = AssetPanel(self)
        self.properties_panel = PropertiesPanel(self)
        self.canvas = Canvas(self)

        self.asset_panel.load_assets()
        all_assets = self.asset_panel.get_all_assets()
        if all_assets:
            self.active_asset = all_assets[0]

        self._recalculate_layout()

    def _recalculate_layout(self):
        w, h = self.screen.get_size()
        self.window_width = w
        self.window_height = h

        self.toolbar.recalculate(w)
        self.asset_panel.recalculate(h)
        self.properties_panel.recalculate(w, h)
        self.canvas.recalculate(w, h)

    def set_tool(self, tool_id):
        self.current_tool = tool_id
        self.toolbar.set_active_tool(tool_id)

    def toggle_walkable(self):
        self.walkable_mode = not self.walkable_mode

    def save_map(self):
        self.layer_manager.save(MAP_FILE)

    def load_map(self):
        self.layer_manager.load(MAP_FILE)

    def clear_all(self):
        self.layer_manager.clear_all()

    def zoom_in(self):
        cx = self.canvas.rect.centerx
        cy = self.canvas.rect.centery
        self.camera.zoom_at((cx, cy), 1, self.canvas.rect.x)

    def zoom_out(self):
        cx = self.canvas.rect.centerx
        cy = self.canvas.rect.centery
        self.camera.zoom_at((cx, cy), -1, self.canvas.rect.x)

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.RESIZABLE)
        else:
            self.screen = pygame.display.set_mode(
                (EDITOR_WIDTH, EDITOR_HEIGHT), pygame.RESIZABLE
            )
        self._recalculate_layout()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue

            if event.type == pygame.VIDEORESIZE:
                self._recalculate_layout()
                continue

            if self.context_menu:
                if self.context_menu.handle_event(event):
                    continue

            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
                if event.pos[1] < Layout.TOOLBAR_HEIGHT:
                    self.toolbar.handle_event(event)
                    continue

            if event.type == pygame.KEYDOWN:
                self._handle_key(event)
                continue

            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION, pygame.MOUSEBUTTONUP):
                pos = event.pos
                if self.asset_panel.scroll.is_dragging or pos[0] < Layout.LEFT_PANEL_WIDTH:
                    self.asset_panel.handle_event(event)
                elif pos[0] > self.window_width - Layout.RIGHT_PANEL_WIDTH:
                    self.properties_panel.handle_event(event)
                else:
                    self.canvas.handle_event(event)
            elif event.type == pygame.MOUSEWHEEL:
                mouse_pos = pygame.mouse.get_pos()
                if mouse_pos[0] < Layout.LEFT_PANEL_WIDTH:
                    self.asset_panel.handle_event(event)
                else:
                    self.canvas.handle_event(event)

    def _handle_key(self, event):
        mods = pygame.key.get_mods()
        ctrl = mods & pygame.KMOD_CTRL

        if ctrl:
            if event.key == pygame.K_s:
                self.save_map()
            elif event.key == pygame.K_l:
                self.load_map()
            return

        if event.key == pygame.K_b:
            self.set_tool("DRAW")
        elif event.key == pygame.K_e:
            self.set_tool("ERASE")
        elif event.key == pygame.K_m:
            self.set_tool("MOVE")
        elif event.key == pygame.K_f:
            self.set_tool("FILL")
        elif event.key == pygame.K_w:
            self.toggle_walkable()
        elif event.key == pygame.K_s:
            self.save_map()
        elif event.key == pygame.K_l:
            self.load_map()
        elif event.key == pygame.K_F11:
            self.toggle_fullscreen()
        elif event.key == pygame.K_ESCAPE:
            if self.context_menu:
                self.context_menu = None
        elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
            idx = event.key - pygame.K_1
            if idx < len(self.layer_manager.layers):
                self.layer_manager.set_active(idx)

    def update(self):
        keys = pygame.key.get_pressed()
        self.camera.update_keys(keys)

    def draw(self):
        self.screen.fill(Colors.BG_DARK)

        self.canvas.draw(self.screen)
        self.asset_panel.draw(self.screen)
        self.properties_panel.draw(self.screen)
        self.toolbar.draw(self.screen)

        if self.context_menu:
            self.context_menu.draw(self.screen)

        pygame.display.flip()

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self.handle_events()
            self.update()
            self.draw()

        pygame.quit()
        sys.exit()
