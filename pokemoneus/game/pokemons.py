import math
import random

from game.config import BASE_POKEMON_SIZE, MAX_ATK, MAX_DF, SCREEN_HEIGHT, SCREEN_WIDTH


class Pokemon:
    def __init__(
        self,
        name: str,
        pos: tuple[int, int],
        vm,
        size: tuple[int, int] = BASE_POKEMON_SIZE,
        speed: int = 5,
        atk: int = -1,
        df: int = -1,
        hp: int = 100,
        is_bot: bool = False,
    ) -> None:
        self.vm = vm

        self.name = name
        self.x, self.y = pos
        self.size = size

        angle = random.uniform(0, 2 * math.pi)
        self.dx = int(speed * math.cos(angle))
        self.dy = int(speed * math.sin(angle))

        self.image = self.vm.load_image("error.png", size)

        self.hp = hp

        _max_atk, _max_df = MAX_ATK, MAX_DF
        if is_bot:
            _max_atk *= 0.85
            _max_df *= 0.85

        if atk == -1:
            atk = random.randint(1, int(_max_atk))
        if df == -1:
            df = random.randint(1, int(_max_df))

        self.atk, self.df = atk, df

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = str(value)

    @property
    def hp(self) -> int:
        return self._hp

    @hp.setter
    def hp(self, value: int) -> None:
        self._hp = max(0, value)

    @property
    def atk(self) -> int:
        return self._atk

    @atk.setter
    def atk(self, value: int) -> None:
        self._atk = max(0, value)

    @property
    def df(self) -> int:
        return self._df

    @df.setter
    def df(self, value: int) -> None:
        self._df = max(0, value)

    def move(self):
        if self.hp == 0:
            return

        if self.x <= 0 or self.x + self.size[0] >= SCREEN_WIDTH:
            self.dx *= -1
            self.dy += random.randint(-1, 1)

        if self.y <= 0 or self.y + self.size[1] >= SCREEN_HEIGHT:
            self.dy *= -1
            self.dx += random.randint(-1, 1)

        self.x += self.dx
        self.y += self.dy

    def draw(self, draw_hp_bar: bool = True, draw_stats: bool = True):
        if draw_hp_bar:
            self.vm.draw_hp_bar(
                (self.x, self.y - 8),
                BASE_POKEMON_SIZE[0],
                6,
                self.hp,
            )

        self.vm.draw_image((self.x, self.y), self.image)

        if draw_stats:
            self.vm.draw_bar(
                (self.x, self.y + BASE_POKEMON_SIZE[1] + 2),
                BASE_POKEMON_SIZE[0],
                6,
                (255, 0, 0),
                self.atk,
                MAX_ATK,
            )
            self.vm.draw_bar(
                (self.x, self.y + BASE_POKEMON_SIZE[1] + 10),
                BASE_POKEMON_SIZE[0],
                6,
                (0, 0, 255),
                self.df,
                MAX_DF,
            )

    def attack(self, opponent: "Pokemon") -> None:
        if self.hp > 0 and opponent.hp > 0:
            opponent.hp -= max(1, self.atk - opponent.df)


class WaterPokemon(Pokemon):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.image = self.vm.load_image("water_pokemon.png", self.size)

    def attack(self, opponent: Pokemon) -> None:
        old_atk = self.atk
        if isinstance(opponent, FirePokemon):
            self.atk *= 3

        super().attack(opponent)

        self.atk = old_atk


class FirePokemon(Pokemon):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.image = self.vm.load_image("fire_pokemon.png", self.size)


class GrassPokemon(Pokemon):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.image = self.vm.load_image("grass_pokemon.png", self.size)

    def attack(self, opponent: Pokemon) -> None:
        old_df = opponent.df
        if isinstance(opponent, FirePokemon):
            opponent.df //= 2

        super().attack(opponent)

        opponent.df = old_df


class ElectricPokemon(Pokemon):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.image = self.vm.load_image("electric_pokemon.png", self.size)

    def attack(self, opponent: Pokemon) -> None:
        old_df = opponent.df
        if isinstance(opponent, WaterPokemon):
            opponent.df = 0

        super().attack(opponent)

        opponent.df = old_df


class Trainer:
    def __init__(self) -> None:
        self.wins = 0
        self.box: list[Pokemon] = []

    def add(self, pokemon: Pokemon) -> None:
        self.box.append(pokemon)

    def best_team(self, n: int) -> list[Pokemon]:
        n = min(n, len(self.box))
        team, self.box = self.box[:n], self.box[n:]
        return team


class MediumTrainer(Trainer):
    def best_team(self, n):
        sorted_box = sorted(
            self.box, key=lambda pokemon: pokemon.atk + pokemon.df, reverse=True
        )
        best_team = sorted_box[:n]
        self.box = sorted_box[n:]
        return best_team


class HardTrainer(Trainer):
    def sort_pokemons(self) -> None:
        self.box.sort(key=lambda x: (x.atk + x.df, x.atk, x.df), reverse=True)

    def best_team(self, n: int) -> list:
        self.sort_pokemons()

        non_fire_pokemons = []
        fire_pokemons = []

        for p in self.box:
            if "fire" in type(p).__name__.lower():
                fire_pokemons.append(p)
            else:
                non_fire_pokemons.append(p)

        team = non_fire_pokemons[:n]

        while len(team) < n:
            team.append(fire_pokemons[0])
            del fire_pokemons[0]

        self.box = [pokemon for pokemon in self.box if pokemon not in team]
        return team


POKEMON_TYPES = (ElectricPokemon, FirePokemon, GrassPokemon, WaterPokemon)
