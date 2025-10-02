import pygame
from game.config import COLOR_BUTTON_BG, COLOR_BUTTON_HOVER, COLOR_BUTTON_TEXT


class Button:
    def __init__(
        self,
        vm,
        pos: tuple[int, int],
        size: tuple[int, int],
        text: str,
        on_click=None,
        font_size=32,
        text_color_idle=COLOR_BUTTON_TEXT,
        text_color_hover=(255, 255, 255),
        bg_idle=COLOR_BUTTON_BG,
        bg_hover=COLOR_BUTTON_HOVER,
    ):
        self.vm = vm
        self.rect = pygame.Rect(pos + size)
        self.text = text
        self.on_click = on_click
        self.font_size = font_size
        self.text_color_idle = text_color_idle
        self.text_color_hover = text_color_hover
        self.bg_idle = bg_idle
        self.bg_hover = bg_hover

        self.hovered = False
        self._mouse_down_inside = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._mouse_down_inside = self.rect.collidepoint(event.pos)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._mouse_down_inside and self.rect.collidepoint(event.pos):
                if callable(self.on_click):
                    self.on_click()
            self._mouse_down_inside = False

    def draw(self):
        bg = self.bg_hover if self.hovered else self.bg_idle
        self.vm.draw_rectangle((self.rect.x, self.rect.y), self.rect.w, self.rect.h, bg)

        color = self.text_color_hover if self.hovered else self.text_color_idle

        tw, th = self.vm.get_text_size(self.text, font_size=self.font_size)
        tx = self.rect.x + (self.rect.w - tw) // 2
        ty = self.rect.y + (self.rect.h - th) // 2
        self.vm.draw_text((tx, ty), self.text, color, font_size=self.font_size)
