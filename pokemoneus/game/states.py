import random
from abc import ABC, abstractmethod

import game.controllers as controllers
import pygame
from game.battle import Battle
from game.config import *
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

        self.title = "Pokemoneus!"

        self.mascot = self.vm.load_image("raichu.png", (200, 200))

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
        self.vm.clear_screen(COLOR_BG_MENU)

        tw, th = self.vm.get_text_size(self.title, font_size=130)

        self.vm.draw_text(
            ((SCREEN_WIDTH - tw - 150) // 2, 175),
            self.title,
            COLOR_TEXT_TITLE,
            font_size=130,
        )

        self.vm.draw_image(((SCREEN_WIDTH + tw - 100) // 2, 125), self.mascot)
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
        self.vm.clear_screen(COLOR_WORLD_BG)

        for p in self.pokemons:
            p.draw(draw_hp_bar=False)

        if self.game.box:
            box_w = 7 + (BASE_POKEMON_SIZE[0] + 7) * len(self.game.box)
            box_h = 5 * 2 + BASE_POKEMON_SIZE[1] + (BAR_HEIGHT + 2) * 3

            self.vm.draw_rectangle((5, 5), box_w, box_h, COLOR_PANEL)
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
        self.winner = None
        self._wins_snapshot = (0, 0)
        self._was_running = False
        self.paused = False

    def _reset_enemy_box(self):
        self.trainer2 = Trainer()

    def fill_boxes(self):
        self.trainer1.box = list(self.game.box)
        if not hasattr(self.trainer2, "box"):
            self.trainer2.box = []
        self.trainer2.box = []
        while len(self.trainer2.box) < POKEMONS_PER_TEAM:
            P = random.choice(POKEMON_TYPES)
            self.trainer2.add(P(f"T2_{len(self.trainer2.box)+1}", (0, 0), vm=self.vm))

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

    def _restart_battle(self):
        self.winner = None
        self.paused = False
        self.battle = Battle(POKEMONS_PER_TEAM)
        self.battle.start(self.trainer1, self.trainer2)
        self._wins_snapshot = (self.trainer1.wins, self.trainer2.wins)
        self._compute_center_layout()
        self._position_teams()
        self._was_running = True

    def enter(self):
        self.winner = None
        self.paused = False
        self.fill_boxes()
        self.battle = Battle(POKEMONS_PER_TEAM)
        self.battle.start(self.trainer1, self.trainer2)
        self._wins_snapshot = (self.trainer1.wins, self.trainer2.wins)
        self._compute_center_layout()
        self._position_teams()
        self._was_running = True

    def handle_event(self, event):
        if self.winner is not None:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._reset_enemy_box()
                    self.game.state = "menu"
                elif event.key == pygame.K_r:
                    if self.winner == "paused":
                        self.winner = None
                        self.paused = False
                        if hasattr(self.battle, "last_update"):
                            self.battle.last_update = pygame.time.get_ticks()
                        self._was_running = True
                    else:
                        self._restart_battle()
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.winner = "paused"
                self.paused = True
            elif event.key == pygame.K_r:
                self._restart_battle()

    def update(self):
        if self.winner is not None or self.paused:
            return
        running_now = bool(self.battle.started)
        if running_now:
            self.battle.update()
        if self._was_running and not bool(self.battle.started):
            t1_w, t2_w = self.trainer1.wins, self.trainer2.wins
            p_w0, b_w0 = self._wins_snapshot
            if t1_w > p_w0:
                self.winner = "player"
            elif t2_w > b_w0:
                self.winner = "bot"
            else:
                if self.winner is None:
                    self.winner = "paused"
        self._was_running = bool(self.battle.started)

    def _draw_winner_overlay(self):
        self.vm.clear_screen(COLOR_OVERLAY_BG)
        if self.winner == "player":
            title = "You Win!"
            sub = "Press R to rematch • ESC to menu"
            color = COLOR_WIN
        elif self.winner == "bot":
            title = "Bot Wins!"
            sub = "Press R to try again • ESC to menu"
            color = COLOR_LOSE
        else:
            title = "Match paused"
            sub = "Press R to continue • ESC to menu"
            color = COLOR_PAUSED
        tw, th = self.vm.get_text_size(title, font_size=64)
        self.vm.draw_text(
            ((SCREEN_WIDTH - tw) // 2, (SCREEN_HEIGHT - th) // 2 - 30),
            title,
            color,
            font_size=64,
        )
        sw, sh = self.vm.get_text_size(sub, font_size=24)
        self.vm.draw_text(
            ((SCREEN_WIDTH - sw) // 2, (SCREEN_HEIGHT - sh) // 2 + 40),
            sub,
            COLOR_TEXT_SECONDARY,
            font_size=24,
        )

    def draw(self):
        if self.winner is not None:
            self._draw_winner_overlay()
            return
        self.vm.clear_screen(COLOR_BG_BATTLE)
        self.vm.draw_line(
            (SCREEN_WIDTH // 2, 0),
            (SCREEN_WIDTH // 2, SCREEN_HEIGHT),
            COLOR_DIVIDER,
            2,
        )
        if self.battle.started:
            for p in self.battle.player_team + self.battle.bot_team:
                p.draw()
        attacker, defender = self.battle.current_pair()
        if attacker and defender:
            a_rect = attacker.image.get_rect(topleft=(attacker.x, attacker.y))
            d_rect = defender.image.get_rect(topleft=(defender.x, defender.y))
            if a_rect.midright[0] > d_rect.midleft[0]:
                a_rect, d_rect = d_rect, a_rect
            self.vm.draw_line(a_rect.midright, d_rect.midleft, COLOR_ATTACK_LINE, 3)
        self.vm.draw_text(
            (20, 20),
            f"T1 wins: {self.trainer1.wins}     T2 wins: {self.trainer2.wins}",
            COLOR_TEXT_PRIMARY,
        )
        if not self.battle.started:
            self.vm.draw_text((20, 50), "ESC = menu", COLOR_TEXT_SECONDARY, 20)


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
        self.vm.clear_screen(COLOR_WORLD_BG)

        for p in self.pokemons:
            p.draw(draw_hp_bar=False, draw_stats=False)

    def add_new_random_pokemon(self, pos):
        pokemon_type = random.choice(POKEMON_TYPES)
        self.pokemons.append(pokemon_type("Pokemon", pos, vm=self.vm))
