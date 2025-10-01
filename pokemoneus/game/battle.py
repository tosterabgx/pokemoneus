import pygame

HIT_DELAY = 200


class Battle:
    def __init__(self, n):
        self.n = n
        self.started = False

    def start(self, trainer1, trainer2):
        if self.started:
            return

        self.trainer1 = trainer1
        self.trainer2 = trainer2
        self.team1 = trainer1.best_team(self.n)
        self.team2 = trainer2.best_team(self.n)

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

        if self.team1 and self.team2:
            if self.turn == 1:
                self.team1[0].attack(self.team2[0])
                if self.team2[0].hp <= 0:
                    self.team2.pop(0)
                    if not self.team2:
                        return self.finish(1)
            else:
                self.team2[0].attack(self.team1[0])
                if self.team1[0].hp <= 0:
                    self.team1.pop(0)
                    if not self.team1:
                        return self.finish(2)

            self.turn = 2 if self.turn == 1 else 1

    def finish(self, result):
        if not self.started:
            return

        self.started = False

        for p in self.team1:
            self.trainer1.add(p)
        for p in self.team2:
            self.trainer2.add(p)
        if result == 1:
            self.trainer1.wins += 1
        else:
            self.trainer2.wins += 1

    def current_pair(self):
        if not self.started or not self.team1 or not self.team2:
            return None, None

        if self.turn == 1:
            return self.team1[0], self.team2[0]
        else:
            return self.team2[0], self.team1[0]
