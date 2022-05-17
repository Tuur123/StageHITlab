import pygame, sys
from pygame.locals import *
from pupilPlayer import GetCoordsPLayer1


WIDTH = 1920
HEIGHT = 1080   
RED = (255,0,0)
MARKER_WIDTH = MARKER_HEIGHT = WIDTH // 8

pygame.init()
fps = pygame.time.Clock()
coord_getter = GetCoordsPLayer1()

#canvas declaration
window = pygame.display.set_mode((WIDTH, HEIGHT), 0, 32)
pygame.display.set_caption('PONG!')

image = pygame.image.load('reference.png')
image = pygame.transform.scale(image, (WIDTH, HEIGHT))

window.blit(image, (0, 0))



while True:
    for event in pygame.event.get():

        if event.type == QUIT:
            pygame.quit()
            sys.exit()

    marker1_x = WIDTH * 0.25 - MARKER_WIDTH // 2
    marker2_x = WIDTH * 0.75 - MARKER_WIDTH // 2

    marker1_y = HEIGHT * 0.25 - MARKER_HEIGHT // 2
    marker2_y = HEIGHT * 0.75 - MARKER_HEIGHT // 2

    image = pygame.image.load('tag36_11_00000.png')
    image = pygame.transform.scale(image, (MARKER_WIDTH, MARKER_WIDTH))
    window.blit(image, (marker1_x, marker1_y))

    image = pygame.image.load('tag36_11_00001.png')
    image = pygame.transform.scale(image, (MARKER_WIDTH, MARKER_WIDTH))
    window.blit(image, (marker2_x, marker1_y))

    image = pygame.image.load('tag36_11_00002.png')
    image = pygame.transform.scale(image, (MARKER_WIDTH, MARKER_WIDTH))
    window.blit(image, (marker1_x, marker2_y))

    image = pygame.image.load('tag36_11_00003.png')
    image = pygame.transform.scale(image, (MARKER_WIDTH, MARKER_WIDTH))
    window.blit(image, (marker2_x, marker2_y))
    pygame.draw.circle(window, RED, [coord_getter.x_ref, coord_getter.y_ref], 70, 1)

    pygame.display.update()
    fps.tick(60)
