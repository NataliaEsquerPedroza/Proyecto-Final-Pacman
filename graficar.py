from turtle import Turtle, bgcolor
from config import GHOST_COLORS
from math import sqrt

# Capas (turtles) separadas para evitar parpadeo
maze_t = Turtle(visible=False)     # paredes + suelo + marco verde
pellets_t = Turtle(visible=False)  # pellets
actors_t = Turtle(visible=False)   # Pac-Man + fantasmas
writer = Turtle(visible=False)     # HUD

def init_layers():
    for t in (maze_t, pellets_t, actors_t, writer):
        t.hideturtle()
        t.speed(0)
        t.penup()
    writer.goto(60, 190)
    writer.color('white')

def square(t, x, y, size=20):
    t.penup(); t.goto(x, y); t.pendown()
    t.begin_fill()
    for _ in range(4):
        t.forward(size); t.left(90)
    t.end_fill()
    t.penup()

def draw_maze(tiles, fast_idx):
    bgcolor('black')
    maze_t.color('blue'); maze_t.width(1)
    for index, tile in enumerate(tiles):
        if tile > 0:
            x = (index % 20) * 20 - 200
            y = 180 - (index // 20) * 20
            square(maze_t, x, y)
    # Marcos verdes
    for index in fast_idx:
        if tiles[index] > 0:
            x = (index % 20) * 20 - 200
            y = 180 - (index // 20) * 20
            maze_t.penup(); maze_t.goto(x, y); maze_t.pendown()
            maze_t.color('green'); maze_t.width(3)
            for _ in range(2):
                maze_t.forward(20); maze_t.left(90)
                maze_t.forward(20); maze_t.left(90)
            maze_t.width(1); maze_t.color('blue')
            maze_t.penup()

def draw_pellets(tiles):
    pellets_t.clear()
    for index, tile in enumerate(tiles):
        if tile == 1:
            x = (index % 20) * 20 - 200
            y = 180 - (index // 20) * 20
            pellets_t.goto(x + 10, y + 10)
            pellets_t.dot(2, 'white')

def clear_actors():
    actors_t.clear()

def write_hud(score, level):
    writer.undo()
    writer.write(f"Score: {score}  Lvl: {level}")

# --------- Sprites ----------
def draw_pacman(x, y, size=20):
    actors_t.goto(x, y)
    actors_t.dot(size, 'yellow')

def draw_triangle_ghost(cx, cy, side, fill_color):
    t = actors_t
    h = side * sqrt(3) / 2
    top  = (cx,            cy + (2*h/3))
    left = (cx - side/2,   cy - (h/3))
    right= (cx + side/2,   cy - (h/3))

    t.color(fill_color)
    t.penup(); t.goto(*top); t.pendown()
    t.begin_fill()
    t.goto(*right); t.goto(*left); t.goto(*top)
    t.end_fill()
    t.penup()

def draw_ghost(x, y, color_idx):
    # Ajuste leve para que el triángulo “asiente” bien en la celda.
    cx, cy = x, y - 3
    draw_triangle_ghost(cx, cy, 19, GHOST_COLORS[color_idx % len(GHOST_COLORS)])
