import pygame

HIT_DELAY = 200


class Battle:
    def __init__(self, n):
        self.n = n
        self.started = False

    def start(self, player_trainer, bot_trainer):
        if self.started:
            return

        self.player_trainer = player_trainer
        self.bot_trainer = bot_trainer
        self.player_team = player_trainer.best_team(self.n)
        self.bot_team = bot_trainer.best_team(self.n)

        self.turn = 1
        self.started = True
        self.last_update = pygame.time.get_ticks()

    def update(self):
        if not self.started:
            return

        now = pygame.time.get_ticks()
        if now - self.last_update <= HIT_DELAY:
            return
        self.last_update = now

        if self.player_team and self.bot_team:
            if self.turn == 1:
                self.player_team[0].attack(self.bot_team[0])
                if self.bot_team[0].hp <= 0:
                    self.bot_team.pop(0)
                    if not self.bot_team:
                        return self.finish(1)
            else:
                self.bot_team[0].attack(self.player_team[0])
                if self.player_team[0].hp <= 0:
                    self.player_team.pop(0)
                    if not self.player_team:
                        return self.finish(2)

            self.turn = 2 if self.turn == 1 else 1

    def finish(self, result):
        if not self.started:
            return

        self.started = False

        for p in self.player_team:
            self.player_trainer.add(p)
        for p in self.bot_team:
            self.bot_trainer.add(p)

        if result == 1:
            self.player_trainer.wins += 1
        elif result == 2:
            self.bot_trainer.wins += 1

    def current_pair(self):
        if not self.started or not self.player_team or not self.bot_team:
            return None, None

        if self.turn == 1:
            return self.player_team[0], self.bot_team[0]
        else:
            return self.bot_team[0], self.player_team[0]
