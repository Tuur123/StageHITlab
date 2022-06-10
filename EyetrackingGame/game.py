import random
import pygame, sys
from pygame.locals import *
from pupilPlayer import GetCoordsPLayer1
from pupilPlayer2 import GetCoordsPLayer2

pygame.init()
fps = pygame.time.Clock()

#colors
WHITE = (255,255,255)
RED = (255,0,0)
GREEN = (0,255,0)
BLACK = (0,0,0)

#globals
WIDTH = 1920
HEIGHT = 1080       
BALL_RADIUS = 20
PAD_WIDTH = 8
PAD_HEIGHT = 350
HALF_PAD_WIDTH = PAD_WIDTH // 2
HALF_PAD_HEIGHT = PAD_HEIGHT // 2
MARKER_WIDTH = MARKER_HEIGHT = WIDTH // 8


# player1 = GetCoordsPLayer1()
# player2 = GetCoordsPLayer2()

ball_pos = [0,0]
ball_vel = [0,0]
paddle1_vel = 0
paddle2_vel = 0
l_score = 0
r_score = 0
eye_y = y = 0

#canvas declaration
window = pygame.display.set_mode((WIDTH, HEIGHT), 0, 32)
pygame.display.set_caption('PONG!')


# helper function that spawns a ball, returns a position vector and a velocity vector
# if right is True, spawn to the right, else spawn to the left
def ball_init(right):
    global ball_pos, ball_vel # these are vectors stored as lists
    ball_pos = [WIDTH/2,HEIGHT/2]
    horz = random.randrange(4,8)
    vert = random.randrange(2,6)
    
    if right == False:
        horz = - horz
        
    ball_vel = [horz, -vert]

# define event handlers
def init():
    global paddle1_pos, paddle2_pos, paddle1_vel, paddle2_vel, l_score, r_score  # these are floats
    global score1, score2  # these are ints

    paddle1_pos = [HALF_PAD_WIDTH - 1, HEIGHT // 2]
    paddle2_pos = [WIDTH + 1 - HALF_PAD_WIDTH, HEIGHT // 2]

    l_score = 0
    r_score = 0

    if random.randrange(0,2) == 0:
        ball_init(True)
    else:
        ball_init(False)


#draw function of canvas
def draw(canvas):
    global paddle1_pos, paddle2_pos, ball_pos, ball_vel, l_score, r_score, paddle1_vel, paddle2_vel
           
    canvas.fill(BLACK)
    draw_markers(canvas)
    pygame.draw.line(canvas, WHITE, [WIDTH // 2, 0], [WIDTH // 2, HEIGHT], 1)
    pygame.draw.line(canvas, WHITE, [PAD_WIDTH, 0], [PAD_WIDTH, HEIGHT], 1)
    pygame.draw.line(canvas, WHITE, [WIDTH - PAD_WIDTH, 0],[WIDTH - PAD_WIDTH, HEIGHT], 1)
    pygame.draw.circle(canvas, WHITE, [WIDTH // 2, HEIGHT // 2], 70, 1)

    # update paddle's vertical position, keep paddle on the screen

    # paddle pos < 0: only allow positive vel
    if paddle1_pos[1] < HALF_PAD_HEIGHT and paddle1_vel < 0:
        paddle1_vel = 0

    if paddle2_pos[1] < HALF_PAD_HEIGHT and paddle2_vel < 0:
        paddle2_vel = 0

    # paddle pos > height: only allow negative vel
    if paddle1_pos[1] > HEIGHT - HALF_PAD_HEIGHT and paddle1_vel > 0:
        paddle1_vel = 0

    if paddle2_pos[1] > HEIGHT - HALF_PAD_HEIGHT and paddle2_vel> 0:
        paddle2_vel = 0

    # update vel's
    paddle1_pos[1] += paddle1_vel
    paddle2_pos[1] += paddle2_vel

    #update ball
    ball_pos[0] += int(ball_vel[0])
    ball_pos[1] += int(ball_vel[1])

    #draw paddles and ball
    pygame.draw.circle(canvas, RED, ball_pos, 20, 0)
    pygame.draw.polygon(canvas, GREEN, [[paddle1_pos[0] - HALF_PAD_WIDTH, paddle1_pos[1] - HALF_PAD_HEIGHT], [paddle1_pos[0] - HALF_PAD_WIDTH, paddle1_pos[1] + HALF_PAD_HEIGHT], [paddle1_pos[0] + HALF_PAD_WIDTH, paddle1_pos[1] + HALF_PAD_HEIGHT], [paddle1_pos[0] + HALF_PAD_WIDTH, paddle1_pos[1] - HALF_PAD_HEIGHT]], 0)
    pygame.draw.polygon(canvas, GREEN, [[paddle2_pos[0] - HALF_PAD_WIDTH, paddle2_pos[1] - HALF_PAD_HEIGHT], [paddle2_pos[0] - HALF_PAD_WIDTH, paddle2_pos[1] + HALF_PAD_HEIGHT], [paddle2_pos[0] + HALF_PAD_WIDTH, paddle2_pos[1] + HALF_PAD_HEIGHT], [paddle2_pos[0] + HALF_PAD_WIDTH, paddle2_pos[1] - HALF_PAD_HEIGHT]], 0)

    #ball collision check on top and bottom walls
    if int(ball_pos[1]) <= BALL_RADIUS:
        ball_vel[1] = - ball_vel[1]
    if int(ball_pos[1]) >= HEIGHT + 1 - BALL_RADIUS:
        ball_vel[1] = -ball_vel[1]
    
    #ball collison check on gutters or paddles
    if int(ball_pos[0]) <= BALL_RADIUS + PAD_WIDTH and int(ball_pos[1]) in range(paddle1_pos[1] - HALF_PAD_HEIGHT,paddle1_pos[1] + HALF_PAD_HEIGHT,1):
        ball_vel[0] = -ball_vel[0]
        ball_vel[0] *= 1.1
        ball_vel[1] *= 1.1
    elif int(ball_pos[0]) <= BALL_RADIUS + PAD_WIDTH:
        r_score += 1
        ball_init(True)
        
    if int(ball_pos[0]) >= WIDTH + 1 - BALL_RADIUS - PAD_WIDTH and int(ball_pos[1]) in range(paddle2_pos[1] - HALF_PAD_HEIGHT, paddle2_pos[1] + HALF_PAD_HEIGHT,1 ):
        ball_vel[0] = -ball_vel[0]
        ball_vel[0] *= 1.1
        ball_vel[1] *= 1.1
    elif int(ball_pos[0]) >= WIDTH + 1 - BALL_RADIUS - PAD_WIDTH:
        l_score += 1
        ball_init(False)

    #update scores
    myfont1 = pygame.font.SysFont("Comic Sans MS", 20)
    label1 = myfont1.render("Score "+str(l_score), 1, (255,255,0))
    canvas.blit(label1, (WIDTH - WIDTH * 0.8, 20))

    myfont2 = pygame.font.SysFont("Comic Sans MS", 20)
    label2 = myfont2.render("Score "+str(r_score), 1, (255, 255, 0))
    canvas.blit(label2, (WIDTH - WIDTH * 0.2, 20)) 

    # draw markers
def draw_markers(canvas):

    marker1_x = WIDTH * 0.25 - MARKER_WIDTH // 2
    marker2_x = WIDTH * 0.75 - MARKER_WIDTH // 2

    marker1_y = HEIGHT * 0.25 - MARKER_HEIGHT // 2
    marker2_y = HEIGHT * 0.75 - MARKER_HEIGHT // 2

    image = pygame.image.load('tag36_11_00000.png')
    image = pygame.transform.scale(image, (MARKER_WIDTH, MARKER_WIDTH))
    canvas.blit(image, (marker1_x, marker1_y))

    image = pygame.image.load('tag36_11_00001.png')
    image = pygame.transform.scale(image, (MARKER_WIDTH, MARKER_WIDTH))
    canvas.blit(image, (marker2_x, marker1_y))

    image = pygame.image.load('tag36_11_00002.png')
    image = pygame.transform.scale(image, (MARKER_WIDTH, MARKER_WIDTH))
    canvas.blit(image, (marker1_x, marker2_y))

    image = pygame.image.load('tag36_11_00003.png')
    image = pygame.transform.scale(image, (MARKER_WIDTH, MARKER_WIDTH))
    canvas.blit(image, (marker2_x, marker2_y))

    
#keydown handler
# def keydown(event):
#     global paddle2_vel
    
#     if event.key == K_UP:
#         paddle2_vel = -8
#     elif event.key == K_DOWN:
#         paddle2_vel = 8

#keyup handler
# def keyup(event):
#     global paddle2_vel
    
#     if event.key in (K_UP, K_DOWN):
#         paddle2_vel = 0

def eye_player():
    global paddle1_vel, paddle1_pos, paddle2_vel, paddle2_pos, player1, player2

    y1 = player1.y_ref

    if y1:
        
        y1 = clamp(y1, 0, HEIGHT)

        # paddle1_pos[1] = y1

        if paddle1_pos[1] < y1:
            paddle1_vel = 8
        else:
            paddle1_vel = -8

    y2 = player2.y_ref

    if y2:
        
        y2 = clamp(y2, 0, HEIGHT)

        # paddle1_pos[1] = y2

        if paddle2_pos[1] < y2:
            paddle2_vel = 8
        else:
            paddle2_vel = -8


def clamp(n, smallest, largest):
    return max(smallest, min(n, largest))

init()


#game loop
while True:

    draw(window)

    for event in pygame.event.get():

        # if event.type == KEYDOWN:
        #     keydown(event)
        # elif event.type == KEYUP:
        #     keyup(event)
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

    # eye_player()

    pygame.display.update()
    fps.tick(60)