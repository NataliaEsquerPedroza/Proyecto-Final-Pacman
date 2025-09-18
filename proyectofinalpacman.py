# Pac-Man Plus: 
# 1) 5° fantasma con IA híbrida
# 2) Zonas rápidas verdes y 
# 3) Dificultad progresiva

from random import choice, random
from turtle import *
from freegames import floor, vector
from math import sqrt

# ----------------------------- Parámetros editables -----------------------------
GHOSTS_N = 6          # Cambia el número de fantasmas (p.ej. 3, 4, 6, 8)
GHOST_STEP = 5        # Velocidad por paso del fantasma (5 original, 2 más lento, 10 más rápido)
PACMAN_START = vector(80, -120)  # Punto de inicio de Pac-Man
SMART_GHOSTS = True   # Activar IA simple de persecución
CHASE_PROB = 0.85     # Probabilidad de que el fantasma elija el mejor movimiento hacia Pac-Man
TICK_MS = 90          # Intervalo del juego (ms). Menor = juego más rápido en general

# ----------------------------- Estado global -----------------------------
state = {'score': 0}
path = Turtle(visible=False)   # Para dibujar el laberinto
writer = Turtle(visible=False) # Para marcador
aim = vector(5, 0)
pacman = PACMAN_START.copy()

# Colores para distinguir fantasmas
GHOST_COLORS = ['red', 'pink', 'cyan', 'orange', 'purple', 'green', 'yellow', 'white']

# ----------------------------- Laberinto (20x20) -----------------------------
# 0 = pared, 1 = casilla con punto, 2 = casilla vacía (ya comida)
# Este laberinto es distinto al original (más bucles y corredores laterales)
tiles = [
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
    0,1,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,0,
    0,1,0,0,0,1,0,0,1,0,1,0,0,0,1,0,0,0,1,0,
    0,1,1,1,0,1,1,1,1,1,1,1,1,0,1,1,1,0,1,0,
    0,0,0,1,0,0,0,1,0,0,1,0,1,0,0,0,1,0,1,0,
    0,1,1,1,1,1,0,1,1,0,1,1,0,1,1,1,1,1,1,0,
    0,1,0,0,0,1,0,0,1,0,0,0,1,0,0,0,1,0,0,0,
    0,1,1,1,0,1,1,1,1,1,1,0,1,1,1,0,1,1,1,0,
    0,1,0,1,0,0,0,0,0,0,1,0,0,0,1,0,1,0,1,0,
    0,1,1,1,1,1,1,0,1,1,1,1,1,0,1,1,1,1,1,0,
    0,1,0,0,0,0,1,0,1,0,0,0,1,0,1,0,0,0,1,0,
    0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,
    0,1,0,0,0,1,0,0,1,0,1,0,0,0,1,0,0,0,1,0,
    0,1,1,1,0,1,1,1,1,0,1,1,1,0,1,1,1,0,1,0,
    0,0,0,1,0,0,0,1,0,0,1,0,1,0,0,0,1,0,0,0,
    0,1,1,1,1,1,0,1,1,0,1,1,0,1,1,1,1,1,1,0,
    0,1,0,0,0,0,0,1,0,1,0,0,0,0,0,1,0,0,1,0,
    0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
]

# ----------------------------- Utilidades -----------------------------
def square(x, y):
    """Dibuja un cuadro de 20x20 en (x, y)."""
    path.up()
    path.goto(x, y)
    path.down()
    path.begin_fill()
    for _ in range(4):
        path.forward(20)
        path.left(90)
    path.end_fill()

def offset(point):
    """Regresa el índice del arreglo tiles para una coordenada vectorial."""
    x = (floor(point.x, 20) + 200) / 20
    y = (180 - floor(point.y, 20)) / 20
    return int(x + y * 20)

def valid(point):
    """True si la posición es válida (no pared) y alineada a la grilla."""
    index = offset(point)
    if tiles[index] == 0:
        return False
    index = offset(point + 19)
    if tiles[index] == 0:
        return False
    return point.x % 20 == 0 or point.y % 20 == 0

def at_intersection(p):
    """True si el punto está justo en una intersección de la grilla."""
    return p.x % 20 == 0 and p.y % 20 == 0

def dist(a, b):
    return sqrt((a.x - b.x)**2 + (a.y - b.y)**2)

def world():
    """Dibuja el laberinto y los puntos."""
    bgcolor('black')
    path.color('blue')
    for index, tile in enumerate(tiles):
        if tile > 0:
            x = (index % 20) * 20 - 200
            y = 180 - (index // 20) * 20
            square(x, y)
            if tile == 1:
                path.up()
                path.goto(x + 10, y + 10)
                path.dot(2, 'white')

# ----------------------------- Fantasmas -----------------------------
def pick_course(point, course):
    """Elige una nueva dirección para el fantasma en una intersección."""
    step = GHOST_STEP
    options = [vector(step,0), vector(-step,0), vector(0,step), vector(0,-step)]
    options = [v for v in options if valid(point + v)]
    if not options:
        # Si no hay opciones válidas, da la vuelta
        return vector(-course.x, -course.y)

    # Evita reversa si hay alternativas
    opposite = vector(-course.x, -course.y)
    if len(options) > 1 and opposite in options:
        options.remove(opposite)

    if SMART_GHOSTS and random() < CHASE_PROB:
        # Elige el movimiento que minimiza la distancia a Pac-Man
        best = min(options, key=lambda v: dist(point + v, pacman))
        return best
    else:
        return choice(options)

def build_ghosts(n):
    """Crea 'n' fantasmas distribuidos en el mapa en posiciones válidas."""
    # Posibles spawn points (alineados a 20 px y normalmente libres)
    candidates = [
        vector(-180, 160), vector(-180, -160), vector(100, 160), vector(100, -160),
        vector(-20, 160), vector(140, -20), vector(-20, -20), vector(140, 160),
        vector(-180, 0), vector(100, 0)
        ]
    ghosts = []
    step = GHOST_STEP
    dirs = [vector(step,0), vector(-step,0), vector(0,step), vector(0,-step)]
    i = 0
    for c in candidates:
        if len(ghosts) >= n:
            break
        if valid(c):
            ghosts.append([c.copy(), choice(dirs)])
            i += 1
    # Si no alcanzan los candidatos, duplica algunos
    while len(ghosts) < n and ghosts:
        p, d = ghosts[len(ghosts) % len(ghosts)]
        ghosts.append([p.copy(), d.copy()])
    return ghosts

ghosts = build_ghosts(GHOSTS_N)

# ----------------------------- Lógica de juego -----------------------------
def move():
    """Mueve a Pac-Man y a todos los fantasmas."""
    writer.undo()
    writer.write(state['score'])

    clear()

    # Mover Pac-Man si es válido
    if valid(pacman + aim):
        pacman.move(aim)

    # Comer punto
    index = offset(pacman)
    if tiles[index] == 1:
        tiles[index] = 2
        state['score'] += 1
        x = (index % 20) * 20 - 200
        y = 180 - (index // 20) * 20
        square(x, y)

    # Dibujar Pac-Man
    up()
    goto(pacman.x + 10, pacman.y + 10)
    dot(20, 'yellow')

    # Mover y dibujar fantasmas
    for gi, (point, course) in enumerate(ghosts):
        if valid(point + course):
            # Si está en intersección, decide nueva ruta (IA)
            if at_intersection(point):
                course_new = pick_course(point, course)
                ghosts[gi][1] = course_new
                point.move(course_new)
            else:
                point.move(course)
        else:
            # Chocó contra pared, elegir nueva ruta
            course_new = pick_course(point, course)
            ghosts[gi][1] = course_new
            point.move(course_new)

        up()
        goto(point.x + 10, point.y + 10)
        dot(20, GHOST_COLORS[gi % len(GHOST_COLORS)])

    update()

    # Colisión con fantasma
    for point, _ in ghosts:
        if abs(pacman - point) < 20:
            # Mostrar "Game Over" simple
            writer.goto(-40, 0)
            writer.color('white')
            writer.write('GAME OVER', align='left', font=('Arial', 14, 'bold'))
            return

    ontimer(move, TICK_MS)

def change(x, y):
    """Cambia la dirección de Pac-Man si es válida."""
    if valid(pacman + vector(x, y)):
        aim.x = x
        aim.y = y

# ----------------------------- Setup de Turtle -----------------------------
setup(420, 460, 370, 0)
hideturtle()
tracer(False)
writer.up()
writer.goto(160, 190)
writer.color('white')
writer.write(state['score'])
listen()
onkey(lambda: change(5, 0), 'Right')
onkey(lambda: change(-5, 0), 'Left')
onkey(lambda: change(0, 5), 'Up')
onkey(lambda: change(0, -5), 'Down')
world()
move()
done()
