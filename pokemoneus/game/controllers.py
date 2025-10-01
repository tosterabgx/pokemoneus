import os

import game.states as states
import pygame


class VisualManager:
    def __init__(
        self, screen_size: tuple = (500, 500), caption: str = "Noname"
    ) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode(screen_size)
        pygame.display.set_caption(caption)
        self.clock = pygame.time.Clock()

    def draw_line(self, start: tuple[int, int], end: tuple[int, int], color, width):
        pygame.draw.line(self.screen, color, start, end, width)

    def draw_circle(self, pos: tuple[int, int], color, radius: int) -> None:
        if len(color) == 4:
            d = radius * 2
            surf = pygame.Surface((d, d), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (radius, radius), radius)
            self.screen.blit(surf, (pos[0] - radius, pos[1] - radius))
        else:
            pygame.draw.circle(self.screen, color, pos, radius)

    def draw_rectangle(
        self, pos: tuple[int, int], width: int, height: int, color
    ) -> None:
        pygame.draw.rect(self.screen, color, pygame.Rect(*pos, width, height))

    def draw_hp_bar(
        self,
        topleft: tuple[int, int],
        width: int,
        height: int,
        hp: int,
        max_hp: int = 100,
    ) -> None:
        hp = max(0, min(hp, max_hp))
        ratio = 0 if max_hp <= 0 else hp / max_hp
        fill_w = int(width * ratio)

        self.draw_rectangle(topleft, width, height, (60, 60, 60))
        fill_color = (255 - int(255 * ratio), int(255 * ratio), 0)
        if fill_w > 0:
            self.draw_rectangle(topleft, fill_w, height, fill_color)

    def load_image(self, filename: str, size: tuple):
        path = os.path.join("assets", "images", filename)
        im = pygame.image.load(path).convert_alpha()
        return pygame.transform.scale(im, size)

    def draw_image(self, pos: tuple[int, int], im) -> None:
        self.screen.blit(im, pos)

    def update_screen(self) -> None:
        pygame.display.flip()

    def clear_screen(self, color: tuple = (0, 0, 0)) -> None:
        self.screen.fill(color)

    def get_text_size(self, text: str, font_size=24):
        font = pygame.font.Font(None, font_size)
        text_surface = font.render(text, True, (0, 0, 0))

        return text_surface.get_size()

    def draw_text(self, pos: tuple[int, int], text: str, color, font_size=24):
        font = pygame.font.Font(None, font_size)
        text_surface = font.render(text, True, color)
        self.screen.blit(text_surface, pos)

        return text_surface.get_size()


class GameManager:
    def __init__(self, vm: VisualManager):
        self.vm = vm
        self.running = True

        self.box = []

        self._states = {
            "menu": states.MainMenuState(self),
            "collect": states.CollectingPokemonsState(self),
            "battle": states.BattleState(self),
        }

        self.state = "menu"

    @property
    def state(self):
        return self._current_state

    @state.setter
    def state(self, other: str):
        self._current_state = self._states[other]
        self._current_state.enter()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            self.state.handle_event(event)

    def update(self):
        self.state.update()

    def draw(self):
        self.state.draw()
