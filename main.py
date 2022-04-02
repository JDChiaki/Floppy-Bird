import random
import pygame
from random import choice
from itertools import cycle
from sys import exit
from abc import ABC, abstractmethod
import os


pygame.mixer.pre_init()
pygame.init()

WIDTH = 450
HEIGHT = 800
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Flappy')
ICON_SURFACE = pygame.image.load(os.path.join('assets', 'favicon.ico')).convert()
pygame.display.set_icon(ICON_SURFACE)

BG_DAY_SURFACE = pygame.image.load(os.path.join('assets', 'background-day.png')).convert()
BG_NIGHT_SURFACE = pygame.transform.scale(pygame.image.load(os.path.join('assets', 'background-night.png')).convert(),
                                          (WIDTH, HEIGHT))
BG_SURFACE_LIST = [BG_DAY_SURFACE, BG_NIGHT_SURFACE]
FLOOR_SURFACE = pygame.image.load(os.path.join('assets', 'base.png')).convert()
GAMEOVER_SURFACE = pygame.image.load(os.path.join('assets', 'message.png')).convert_alpha()

BIRD_DOWNFLAP_SURFACE = pygame.image.load(os.path.join('assets', 'bluebird-downflap.png')).convert_alpha()
BIRD_MIDLAP_SURFACE = pygame.image.load(os.path.join('assets', 'bluebird-midflap.png')).convert_alpha()
BIRD_UPFLAP_SURFACE = pygame.image.load(os.path.join('assets', 'bluebird-upflap.png')).convert_alpha()
BIRD_FRAMES = cycle([BIRD_DOWNFLAP_SURFACE, BIRD_MIDLAP_SURFACE, BIRD_UPFLAP_SURFACE])

PIPE_SURFACE = pygame.image.load(os.path.join('assets', 'pipe-green.png')).convert_alpha()
PIPE_FLIP_SURFACE = pygame.transform.flip(PIPE_SURFACE, False, True).convert_alpha()

GAME_FONT = pygame.font.Font(os.path.join('fonts', 'flappy_font.ttf'), 40)

FLAP_SFX = pygame.mixer.Sound(os.path.join('sfxs', 'swoosh.wav'))
HIT_SFX = pygame.mixer.Sound(os.path.join('sfxs', 'hit.wav'))
SCORE_SFX = pygame.mixer.Sound(os.path.join('sfxs', 'point.wav'))

G = 0.25  # gravity


class Obj(ABC):
    def __init__(self, x, y, surface):
        self.x = x
        self.y = y
        self.surface = surface
        self.mask = pygame.mask.from_surface(surface)

    @abstractmethod
    def draw(self):
        pass

    @abstractmethod
    def move(self):
        pass


class Floor(Obj):
    def __init__(self, x, y, surface):
        super().__init__(x, y, surface)

    def draw(self):
        WIN.blit(self.surface, (self.x, self.y))
        self.move()

    def move(self):
        self.x -= 1
        if self.x <= -WIDTH:
            self.x = WIDTH


class Bird(Obj):
    def __init__(self, x, y, surface):
        super().__init__(x, y, surface)
        self.vel = 0

    def rotate(self):
        rotated_surface = pygame.transform.rotozoom(self.surface, -self.vel * 3, 1)
        return rotated_surface

    def draw(self):
        WIN.blit(self.rotate(), (self.x, self.y))
        self.move()

    def move(self):
        self.vel += G
        self.y += self.vel
        if self.y <= 0:
            self.y = 0


class Pipe(Obj):
    def __init__(self, x, y, surface):
        super().__init__(x, y, surface)

    def draw(self):
        WIN.blit(self.surface, (self.x, self.y))
        self.move()

    def move(self):
        self.x -= 4


class Score(Obj):
    def __init__(self, x, y):
        self.s = 0
        self.surface = GAME_FONT.render(str(self.s), True, (255, 255, 255))
        self.x = x - self.surface.get_width() / 2
        super().__init__(self.x, y, self.surface)

    def draw(self):
        WIN.blit(GAME_FONT.render(str(self.s), True, (255, 255, 255)), (self.x, self.y))

    def get_score(self, bird: Bird, pipe: Pipe, other):
        if self.s > other.s:
            other.s = self.s
        return pipe.x - bird.x == 0

    def move(self):
        pass


HIGHEST_SCORE = Score(WIDTH / 2, HEIGHT * 4 / 5)


def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) is not None


def start():
    running = True
    game_active = True
    FPS = 120
    clock = pygame.time.Clock()

    score = Score(WIDTH / 2, HEIGHT / 9)

    floor1 = Floor(0, 700, FLOOR_SURFACE)
    floor2 = Floor(WIDTH, 700, FLOOR_SURFACE)

    bird_surface = next(BIRD_FRAMES)
    bird = Bird(50, HEIGHT / 2.5, bird_surface)

    pipes = ()

    SPAWNPIPE = pygame.USEREVENT
    pygame.time.set_timer(SPAWNPIPE, 2400)
    BIRDFLAP = pygame.USEREVENT + 1
    pygame.time.set_timer(BIRDFLAP, 2400)

    BG_SURFACE = random.choice(BG_SURFACE_LIST)

    def redraw_window():
        WIN.blit(BG_SURFACE, (0, 0))

        if game_active:
            bird.draw()

            for pipe in pipes:
                pipe.draw()

            score.draw()
            if pipes and score.get_score(bird, pipes[0], HIGHEST_SCORE):
                score.s += 1
                SCORE_SFX.play()
        else:
            WIN.blit(GAMEOVER_SURFACE, (WIDTH / 2 - GAMEOVER_SURFACE.get_width() / 2,
                                        HEIGHT / 2 - GAMEOVER_SURFACE.get_height() / 2))
        HIGHEST_SCORE.draw()

        floor1.draw()
        floor2.draw()
        pygame.display.update()

    def check_collide():
        if collide(bird, floor1) or collide(bird, floor2):
            return True
        for pipe in pipes:
            if collide(bird, pipe):
                return True
        return False

    while running:
        clock.tick(FPS)
        redraw_window()

        if check_collide() and game_active:
            HIT_SFX.play()
            game_active = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game_active:
                    bird.vel = -8
                    FLAP_SFX.play()
                if event.key == pygame.K_SPACE and not game_active:
                    start()
            if event.type == SPAWNPIPE:
                p_height = choice(
                    [HEIGHT * (1 / 2), HEIGHT * (3 / 4), HEIGHT * (2 / 3), HEIGHT * (3 / 5), HEIGHT * (4 / 7)])
                p1 = Pipe(WIDTH + 100, p_height, PIPE_SURFACE)
                p2 = Pipe(WIDTH + 100, p_height - PIPE_SURFACE.get_height() - 300, PIPE_FLIP_SURFACE)
                pipes = (p1, p2)
            if event.type == BIRDFLAP:
                bird.surface = next(BIRD_FRAMES)


def main():
    running = True
    BG_SURFACE = random.choice(BG_SURFACE_LIST)
    while running:
        WIN.blit(BG_SURFACE, (0, 0))
        WIN.blit(GAMEOVER_SURFACE, (WIDTH / 2 - GAMEOVER_SURFACE.get_width() / 2,
                                    HEIGHT / 2 - GAMEOVER_SURFACE.get_height() / 2))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    running = False
    start()


if __name__ == '__main__':
    main()
