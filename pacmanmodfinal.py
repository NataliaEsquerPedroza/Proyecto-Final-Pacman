# Pac-Man Plus: 5° fantasma con IA híbrida, zonas rápidas verdes y dificultad progresiva
from random import choice, random
from turtle import *
from freegames import floor, vector
from math import sqrt

# ----------------------------- Utilidades generales -----------------------------
def dist(a, b):
    """Distancia euclidiana entre dos freegames.vector."""
    return sqrt((a.x - b.x)**2 + (a.y - b.y)**2)

# ----------------------------- Estado global -----------------------------
state = {'score': 0, 'level': 1, 'pellets': 0}

path = Turtle(visible=False)     # Dibuja mapa/pellets (estático)
actor = Turtle(visible=False)    # Dibuja Pac-Man y fantasmas (dinámico)
writer = Turtle(visible=False)   # Dibuja marcador

actor.up()
writer.up()

aim = vector(5, 0)
pacman = vector(-40, -80)

# Fantasmas regulares (cuatro) con colores clásicos
ghosts = [
    {'name': 'blinky', 'pos': vector(-180, 160), 'dir': vector(5, 0),  'speed': 5, 'color': 'red'},
    {'name': 'pinky',  'pos': vector(-180,-160), 'dir': vector(0, 5),  'speed': 5, 'color': 'pink'},
    {'name': 'inky',   'pos': vector(100, 160),  'dir': vector(0,-5),  'speed': 5, 'color': 'cyan'},
    {'name': 'clyde',  'pos': vector(100,-160),  'dir': vector(-5, 0), 'speed': 5, 'color': 'orange'},
]

# Quinto fantasma: Jinx (IA híbrida)
jinx = {
    'pos': vector(100, -120),     # posición válida (NO pared)
    'dir': vector(-5, 0),
    'speed': 5,
    'mode': 'ambush',             # 'chase' o 'ambush'
    'timer': 0                    # cambia de modo periódicamente
}

# fmt: off
# Mapa base (0 = muro, 1 = camino con pellet, 2 = camino vacío)
BASE_TILES = [
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
    0,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,0,0,0,0,
    0,1,0,0,1,0,0,1,0,1,0,0,1,0,0,1,0,0,0,0,
    0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,
    0,1,0,0,1,0,1,0,0,0,1,0,1,0,0,1,0,0,0,0,
    0,1,1,1,1,0,1,1,0,1,1,0,1,1,1,1,0,0,0,0,
    0,1,0,0,1,0,0,1,0,1,0,0,1,0,0,0,0,0,0,0,
    0,1,0,0,1,0,1,1,1,1,1,0,1,0,0,0,0,0,0,0,
    0,1,1,1,1,1,1,0,0,0,1,1,1,1,1,1,0,0,0,0,
    0,0,0,0,1,0,1,1,1,1,1,0,1,0,0,1,0,0,0,0,
    0,0,0,0,1,0,1,0,0,0,1,0,1,0,0,1,0,0,0,0,
    0,1,1,1,1,1,1,1,0,1,1,1,1,1,1,1,0,0,0,0,
    0,1,0,0,1,0,0,1,0,1,0,0,0,0,0,1,0,0,0,0,
    0,1,1,0,1,1,1,1,1,1,1,1,1,0,1,1,0,0,0,0,
    0,0,1,0,1,0,1,0,0,0,1,0,1,0,1,0,0,0,0,0,
    0,1,1,1,1,0,1,1,0,1,1,0,1,1,1,1,0,0,0,0,
    0,1,0,0,0,0,0,1,0,1,0,0,0,0,0,1,0,0,0,0,
    0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
    0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
]
# fmt: on

# Copia mutable del nivel; 3 = zona rápida (con pellet)
tiles = BASE_TILES[:]
FAST_TILE_VALUE = 3

# Índices que serán zonas rápidas (se dibujan y cuentan como pellet)
fast_indices = [21, 22, 23, 24, 60, 61, 62, 63, 201, 202, 203, 204, 241, 242, 243, 244]
FAST_SET = set(fast_indices)

# Aplicar zonas rápidas sobre tiles
for i in fast_indices:
    if tiles[i] == 1:
        tiles[i] = FAST_TILE_VALUE

# ----------------------------- Utilidades de mapa -----------------------------
def square(x, y, fill='blue'):
    """Dibuja un cuadrado de 20x20 en (x, y) con relleno (usa path)."""
    path.up(); path.goto(x, y); path.down()
    path.color(fill)
    path.begin_fill()
    for _ in range(4):
        path.forward(20); path.left(90)
    path.end_fill()
    path.up()

def offset(point):
    """Índice del tile para un punto dado."""
    x = (floor(point.x, 20) + 200) / 20
    y = (180 - floor(point.y, 20)) / 20
    return int(x + y * 20)

def valid(point):
    """True si la celda es caminable (no muro)."""
    idx = offset(point)
    if tiles[idx] == 0:  # muro
        return False
    idx = offset(point + 19)
    if tiles[idx] == 0:
        return False
    return point.x % 20 == 0 or point.y % 20 == 0

def neighbors_dirs():
    """Direcciones básicas posibles."""
    return [vector(5,0), vector(-5,0), vector(0,5), vector(0,-5)]

def best_dir_towards(origin, target):
    """Elige la dirección que reduce más la distancia a 'target'."""
    options = []
    for d in neighbors_dirs():
        if valid(origin + d):
            options.append(d)
    if not options:
        return None
    return min(options, key=lambda d: dist(origin + d, target))

def pellet_count():
    """Cuenta pellets restantes (1 o 3)."""
    return sum(1 for t in tiles if t in (1, FAST_TILE_VALUE))

# ----------------------------- Dibujo de fantasmas (usa actor) -----------------------------
def draw_ghost_body(x, y, color_str):
    """Dibuja cuerpo de fantasma (20x20) con base ondulada."""
    actor.up()
    actor.goto(x - 10, y - 10)  # esquina inferior-izq del bounding box 20x20
    actor.setheading(0)
    actor.down()
    actor.color(color_str)
    actor.begin_fill()

    # Base ondulada: 4 ondas de 5 px
    for _ in range(4):
        actor.forward(5)
        actor.left(90); actor.forward(5)
        actor.right(90); actor.forward(5)
        actor.right(90); actor.forward(5)
        actor.left(90)

    # Cabeza semicircular
    actor.setheading(180)
    actor.circle(10, 180)

    actor.end_fill()
    actor.up()

def draw_ghost_eyes(x, y, dir_vec):
    """Ojos blancos + pupilas negras mirando en la dirección de movimiento."""
    left_eye  = (x - 4, y + 3)
    right_eye = (x + 4, y + 3)

    # Ojos
    for ex, ey in (left_eye, right_eye):
        actor.goto(ex, ey)
        actor.down(); actor.color('white'); actor.begin_fill()
        actor.circle(3)
        actor.end_fill(); actor.up()

    # Dirección dominante para orientar pupila
    dx = 0; dy = 0
    if abs(dir_vec.x) > abs(dir_vec.y):
        dx = 1 if dir_vec.x > 0 else -1
    elif abs(dir_vec.y) > 0:
        dy = 1 if dir_vec.y > 0 else -1

    pup_off = (1.2*dx, 1.2*dy)
    for ex, ey in (left_eye, right_eye):
        actor.goto(ex + pup_off[0], ey + pup_off[1])
        actor.down(); actor.color('black'); actor.begin_fill()
        actor.circle(1.3)
        actor.end_fill(); actor.up()

def draw_ghost(x, y, color_str, dir_vec):
    """Dibuja un fantasma completo (cuerpo + ojos)."""
    draw_ghost_body(x, y, color_str)
    draw_ghost_eyes(x, y, dir_vec)

# ----------------------------- Mundo -----------------------------
def world():
    """Dibuja el mundo (tablero + pellets) con path."""
    bgcolor('black')
    state['pellets'] = pellet_count()

    for index, tile in enumerate(tiles):
        if tile > 0:
            x = (index % 20) * 20 - 200
            y = 180 - (index // 20) * 20

            # Zonas rápidas en verde, resto en azul
            if index in FAST_SET and tile != 0:
                square(x, y, fill='green')
            else:
                square(x, y, fill='blue')

            # Pellets (en 1 y 3)
            if tile in (1, FAST_TILE_VALUE):
                path.goto(x + 10, y + 10)
                path.dot(2, 'white')

# ----------------------------- Dificultad -----------------------------
def apply_difficulty():
    """Ajusta la velocidad de fantasmas y el ritmo de Jinx según el nivel."""
    lvl = state['level']
    speed = min(5 + (lvl - 1), 11)   # sube 1 por nivel, tope 11

    for g in ghosts:
        g['speed'] = speed
        if g['dir'].x: g['dir'] = vector(speed if g['dir'].x > 0 else -speed, 0)
        if g['dir'].y: g['dir'] = vector(0, speed if g['dir'].y > 0 else -speed)

    jinx['speed'] = speed
    if jinx['dir'].x: jinx['dir'] = vector(speed if jinx['dir'].x > 0 else -speed, 0)
    if jinx['dir'].y: jinx['dir'] = vector(0, speed if jinx['dir'].y > 0 else -speed)

def next_level():
    """Reinicia pellets, sube nivel y recoloca enemigos."""
    state['level'] += 1

    # Restaura pellets en caminos originales; mantiene zonas rápidas verdes
    for i, base in enumerate(BASE_TILES):
        if base == 1:
            tiles[i] = FAST_TILE_VALUE if i in FAST_SET else 1

    world()

    # Recolocar posiciones
    pacman.x, pacman.y = -40, -80
    base_g = [(-180,160),(-180,-160),(100,160),(100,-160)]
    base_d = [(1,0),(0,1),(0,-1),(-1,0)]
    for i,g in enumerate(ghosts):
        g['pos'].x, g['pos'].y = base_g[i]
        spd = g['speed']
        g['dir'].x, g['dir'].y = base_d[i][0]*spd, base_d[i][1]*spd

    jinx['pos'].x, jinx['pos'].y = 100, -120   # misma posición válida
    jinx['dir'] = vector(-jinx['speed'], 0)
    jinx['mode'] = 'ambush'
    jinx['timer'] = 0

    apply_difficulty()

# ----------------------------- Movimiento -----------------------------
def tile_speed_modifier(point):
    """Devuelve modificador de velocidad para Pac-Man según el tile."""
    idx = offset(point)
    return 1.4 if (idx in FAST_SET) else 1.0  # acelera 40% en pista rápida

def move():
    """Mueve a Pac-Man y a los fantasmas; maneja IA de Jinx y niveles."""
    writer.undo()
    writer.write(f"Score: {state['score']}  Lvl: {state['level']}")
    actor.clear()  # <-- limpia actores del frame anterior

    # ----- Mover Pac-Man (con boost en zonas rápidas) -----
    mod = tile_speed_modifier(pacman)
    desired = vector(aim.x, aim.y)
    if valid(pacman + desired):
        repeats = 1 if mod <= 1.05 else 2
        for _ in range(repeats):
            if valid(pacman + desired):
                pacman.move(desired)
            else:
                break

    # ----- Comer pellets -----
    idx = offset(pacman)
    if tiles[idx] in (1, FAST_TILE_VALUE):
        tiles[idx] = 2
        state['score'] += 1
        x = (idx % 20) * 20 - 200
        y = 180 - (idx // 20) * 20
        # Re-dibuja el piso sin pellet (verde si era zona rápida, azul si normal)
        square(x, y, fill=('green' if idx in FAST_SET else 'blue'))

    # ----- Dibujar Pac-Man -----
    actor.goto(pacman.x + 10, pacman.y + 10)
    actor.dot(20, 'yellow')

    # ----- Mover fantasmas regulares -----
    for g in ghosts:
        pos, direc, spd = g['pos'], g['dir'], g['speed']
        if valid(pos + direc):
            pos.move(direc)
        else:
            opts = [vector(spd,0), vector(-spd,0), vector(0,spd), vector(0,-spd)]
            plan = choice([d for d in opts if valid(pos + d)] or opts)
            g['dir'] = plan
        draw_ghost(pos.x + 10, pos.y + 10, g['color'], g['dir'])

    # ----- IA de Jinx (quinto fantasma) -----
    # Salvavidas: si por error quedó en pared, empuja a un vecino válido
    if tiles[offset(jinx['pos'])] == 0:
        spdJ = jinx['speed']
        for d in [vector(spdJ,0), vector(-spdJ,0), vector(0,spdJ), vector(0,-spdJ)]:
            if valid(jinx['pos'] + d):
                jinx['pos'].move(d); jinx['dir'] = d; break

    jinx['timer'] += 1
    switch_every = 16 - min(state['level'], 10)  # con nivel alto, cambia más seguido
    if jinx['timer'] >= switch_every + int(random()*8):
        jinx['timer'] = 0
        jinx['mode'] = 'chase' if jinx['mode'] == 'ambush' else 'ambush'

    # Objetivo según modo
    if jinx['mode'] == 'chase':
        target = vector(pacman.x, pacman.y)
    else:
        target = vector(pacman.x + 4*aim.x, pacman.y + 4*aim.y)  # emboscada

    posJ, dirJ, spdJ = jinx['pos'], jinx['dir'], jinx['speed']
    if random() < 0.12:
        opts = [vector(spdJ,0), vector(-spdJ,0), vector(0,spdJ), vector(0,-spdJ)]
        dirJ = choice([d for d in opts if valid(posJ + d)] or opts)
    else:
        plan = best_dir_towards(posJ, target)
        if plan is not None:
            dirJ = plan

    if valid(posJ + dirJ):
        posJ.move(dirJ); jinx['dir'] = dirJ
    else:
        opts = [vector(spdJ,0), vector(-spdJ,0), vector(0,spdJ), vector(0,-spdJ)]
        jinx['dir'] = choice([d for d in opts if valid(posJ + d)] or opts)

    draw_ghost(posJ.x + 10, posJ.y + 10, '#FF00FF', jinx['dir'])  # Jinx magenta

    # ----- Colisiones -----
    for g in ghosts:
        if abs(pacman - g['pos']) < 20:
            return  # fin del juego
    if abs(pacman - jinx['pos']) < 20:
        return

    # ----- ¿Nivel completado? -----
    if pellet_count() == 0:
        next_level()

    # Velocidad del loop (menor = más rápido)
    delay = max(40, 100 - 6 * (state['level'] - 1))
    ontimer(move, delay)

# ----------------------------- Controles -----------------------------
def change(x, y):
    """Cambia la dirección de Pac-Man si el siguiente step es válido."""
    new = vector(x, y)
    if valid(pacman + new):
        aim.x = x; aim.y = y

# ----------------------------- Setup -----------------------------
def reset_and_start():
    world()
    apply_difficulty()
    move()

setup(420, 420, 370, 0)
hideturtle()
tracer(False)

writer.goto(70, 160)
writer.color('white')
writer.write(f"Score: {state['score']}  Lvl: {state['level']}")

listen()
onkey(lambda: change(5, 0), 'Right')
onkey(lambda: change(-5, 0), 'Left')
onkey(lambda: change(0, 5), 'Up')
onkey(lambda: change(0, -5), 'Down')

reset_and_start()
done()
