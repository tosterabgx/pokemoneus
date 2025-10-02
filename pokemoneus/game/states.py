import random
from abc import ABC, abstractmethod

import game.controllers as controllers
import pygame
from game.battle import Battle
from game.config import (
    BAR_HEIGHT,
    BASE_POKEMON_SIZE,
    POKEMONS_PER_TEAM,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from game.misc import Button
from game.pokemons import POKEMON_TYPES, Trainer


class GameState(ABC):
    def __init__(self, game):
        self.game = game
        self.vm: controllers.VisualManager = game.vm

    def enter(self):
        pass

    @abstractmethod
    def handle_event(self, event):
        pass

    @abstractmethod
    def update(self, dt):
        pass

    @abstractmethod
    def draw(self, vm):
        pass


class MainMenuState(GameState):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.title = "Pokemoneus"

        button_w, button_h = 500, 70
        x_center = (SCREEN_WIDTH - button_w) // 2
        y_center = (SCREEN_WIDTH - button_h) // 2
        y_offset = -50

        self.buttons = [
            Button(
                self.vm, (10, 10), (20, 20), "FPS", on_click=self.fps_test, font_size=12
            ),
            Button(
                self.vm,
                (x_center, y_center + y_offset),
                (button_w, button_h),
                "Go to the world",
                on_click=self.collect_pokemons,
            ),
            Button(
                self.vm,
                (x_center, y_center + y_offset + 5 + button_h),
                (button_w, button_h),
                "Battle",
                on_click=self.battle,
            ),
            Button(
                self.vm,
                (x_center, y_center + y_offset + (5 + button_h) * 2),
                (button_w, button_h),
                "Quit",
                on_click=self.quit_game,
            ),
        ]

    def fps_test(self):
        self.game.state = "fps"

    def collect_pokemons(self):
        self.game.state = "collect"

    def battle(self):
        self.game.state = "battle"

    def quit_game(self):
        self.game.running = False

    def handle_event(self, event):
        for btn in self.buttons:
            btn.handle_event(event)

    def update(self):
        pass

    def draw(self):
        self.vm.clear_screen((30, 30, 30))

        tw, th = self.vm.get_text_size(self.title, font_size=52)

        self.vm.draw_text(
            ((SCREEN_WIDTH - tw) // 2, 80), self.title, (220, 220, 255), font_size=52
        )
        for btn in self.buttons:
            btn.draw()


class CollectingPokemonsState(GameState):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pokemons = []

    def enter(self):
        self.pokemons = []
        for _ in range(random.randint(20, 30)):
            x = random.randint(0, SCREEN_WIDTH - BASE_POKEMON_SIZE[0])
            y = random.randint(0, SCREEN_HEIGHT - BASE_POKEMON_SIZE[1])

            self.add_new_random_pokemon((x, y))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.state = "menu"
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for p in self.game.box:
                rect = p.image.get_rect(topleft=(p.x, p.y))
                if rect.collidepoint(event.pos):
                    self.game.box.remove(p)
                    break

            for p in self.pokemons:
                rect = p.image.get_rect(topleft=(p.x, p.y))
                if rect.collidepoint(event.pos):
                    self.pokemons.remove(p)
                    self.game.box.append(p)
                    break

            if len(self.game.box) > POKEMONS_PER_TEAM:
                self.game.box.pop(0)

    def update(self):
        for p in self.pokemons:
            p.move()

        for i in range(len(self.game.box)):
            self.game.box[i].x = 5 + 7 + (BASE_POKEMON_SIZE[0] + 7) * i
            self.game.box[i].y = 5 + 5 + BAR_HEIGHT + 2

    def draw(self):
        self.vm.clear_screen((0, 166, 62))

        for p in self.pokemons:
            p.draw(draw_hp_bar=False)

        if self.game.box:
            box_w = 7 + (BASE_POKEMON_SIZE[0] + 7) * len(self.game.box)
            box_h = 5 * 2 + BASE_POKEMON_SIZE[1] + (BAR_HEIGHT + 2) * 3

            self.vm.draw_rectangle((5, 5), box_w, box_h, (255, 255, 255))
            for p in self.game.box:
                p.draw()

    def add_new_random_pokemon(self, pos):
        pokemon_type = random.choice(POKEMON_TYPES)
        self.pokemons.append(pokemon_type("Pokemon", pos, vm=self.vm))


class BattleState(GameState):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.battle = Battle(POKEMONS_PER_TEAM)
        self.trainer1 = Trainer()
        self.trainer2 = Trainer()

        self.spacing = (BAR_HEIGHT + 2) * 3 + 2 + 20

    def fill_boxes(self):
        self.trainer1.box = self.game.box

        while len(self.trainer2.box) < POKEMONS_PER_TEAM:
            pokemon_type = random.choice(POKEMON_TYPES)
            self.trainer2.add(pokemon_type("Pokemon", (0, 0), vm=self.vm))

    def _compute_center_layout(self):
        column_gap = 120

        h1_list = [p.image.get_rect().height for p in self.battle.player_team]
        h2_list = [p.image.get_rect().height for p in self.battle.bot_team]
        total_h1 = sum(h1_list) + self.spacing * max(len(h1_list) - 1, 0)
        total_h2 = sum(h2_list) + self.spacing * max(len(h2_list) - 1, 0)
        column_h = max(total_h1, total_h2)

        self.y_start = max(20, (SCREEN_HEIGHT - column_h) // 2)

        cx = SCREEN_WIDTH // 2
        self.x1 = cx - (column_gap // 2) - BASE_POKEMON_SIZE[0]
        self.x2 = cx + (column_gap // 2)

    def _position_teams(self):
        y = self.y_start
        for p in self.battle.player_team:
            rect = p.image.get_rect()
            p.x, p.y = self.x1, y
            y += rect.height + self.spacing

        y = self.y_start
        for p in self.battle.bot_team:
            rect = p.image.get_rect()
            p.x, p.y = self.x2, y
            y += rect.height + self.spacing

    def enter(self):
        self.fill_boxes()
        self.battle.start(self.trainer1, self.trainer2)
        self._compute_center_layout()
        self._position_teams()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.game.state = "menu"
                self.battle.finish(-1)

    def update(self):
        if self.battle.started:
            self.battle.update()

    def draw(self):
        self.vm.clear_screen((18, 26, 38))

        self.vm.draw_line(
            (SCREEN_WIDTH // 2, 0),
            (SCREEN_WIDTH // 2, SCREEN_HEIGHT),
            (60, 80, 100),
            2,
        )

        if self.battle.started:
            for p in self.battle.player_team + self.battle.bot_team:
                p.draw()

        attacker, defender = self.battle.current_pair()
        if attacker and defender:
            attacker_rect = attacker.image.get_rect(topleft=(attacker.x, attacker.y))
            defender_rect = defender.image.get_rect(topleft=(defender.x, defender.y))

            if attacker_rect.midright[0] > defender_rect.midleft[0]:
                attacker_rect, defender_rect = defender_rect, attacker_rect

            self.vm.draw_line(
                attacker_rect.midright,
                defender_rect.midleft,
                (255, 0, 0),
                3,
            )

        self.vm.draw_text(
            (20, 20),
            f"T1 wins: {self.trainer1.wins}     T2 wins: {self.trainer2.wins}",
            (255, 255, 255),
        )

        if not self.battle.started:
            self.vm.draw_text(
                (20, 50),
                "ESC = menu",
                (200, 200, 200),
                20,
            )


class FpsStateState(GameState):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.pokemons = []

    def enter(self):
        self.pokemons = []

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.state = "menu"

        elif pygame.key.get_pressed()[pygame.K_SPACE]:
            mouse_pos = pygame.mouse.get_pos()
            self.add_new_random_pokemon(
                (
                    mouse_pos[0] - BASE_POKEMON_SIZE[0] // 2,
                    mouse_pos[1] - BASE_POKEMON_SIZE[1] // 2,
                )
            )

    def update(self):
        for p in self.pokemons:
            p.move()

    def draw(self):
        self.vm.clear_screen((0, 166, 62))

        for p in self.pokemons:
            p.draw(draw_hp_bar=False, draw_stats=False)

    def add_new_random_pokemon(self, pos):
        pokemon_type = random.choice(POKEMON_TYPES)
        self.pokemons.append(pokemon_type("Pokemon", pos, vm=self.vm))
