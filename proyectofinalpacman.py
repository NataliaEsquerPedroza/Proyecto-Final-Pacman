# Pac-Man Plus:
# 1) 5° fantasma con IA híbrida
# 2) Zonas rápidas verdes
# 3) Dificultad progresiva (velocidad + obstáculos estratégicos por nivel)

from random import choice, random
from turtle import *
from freegames import floor, vector
from math import sqrt

# ----------------------------- Parámetros editables -----------------------------
GHOSTS_N = 5          # Número fijo de fantasmas (incluye al híbrido)
BASE_STEP = 5         # Paso base (múltiplo de 5 para alinear a grilla)
PACMAN_START = vector(80, -120)
SMART_GHOSTS = True   # IA de persecución
BASE_CHASE_PROB = 0.75
BASE_TICK_MS = 95     # ms entre frames (dinámico por nivel)
MAX_GHOSTS = 5        # TOPE DURO = 5
EXTRA_GHOST_EVERY = 999  # Desactiva aumento de fantasmas

# Multiplicadores en zonas rápidas (enteros: 1 = normal, 2 = doble paso por tick)
FAST_MULT_PAC = 2
FAST_MULT_GHO = 2

# Progresión (nivel = pellets_comidos // PELLETS_PER_LEVEL + 1)
PELLETS_PER_LEVEL = 35
CHASE_INCREMENT = 0.05         # +5% agresividad por nivel
TICK_DECREMENT = 5             # -5 ms por nivel (hasta un mínimo)
MIN_TICK_MS = 45

# ----------------------------- Estado global -----------------------------
state = {
    'score': 0,
    'level': 1,
    'pellets_total': 0,
    'pellets_left': 0,
    'levels_applied': set(),     # para no re-aplicar obstáculos
}
path = Turtle(visible=False)
writer = Turtle(visible=False)
aim = vector(BASE_STEP, 0)
pacman = PACMAN_START.copy()

# Colores para distinguir fantasmas
GHOST_COLORS = ['red', 'pink', 'cyan', 'orange', 'purple']

# ----------------------------- Laberinto (20x20) -----------------------------
# 0 = pared, 1 = punto, 2 = vacío
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

# ---- Zonas rápidas (índices del arreglo tiles) ----
FAST_ZONE_IDX = set()
def add_fast_rect(ix, iy, w, h):
    for dy in range(h):
        for dx in range(w):
            x = ix + dx
            y = iy + dy
            idx = x + y * 20
            if 0 <= idx < len(tiles) and tiles[idx] != 0:
                FAST_ZONE_IDX.add(idx)

# Pintado de zonas (verde): puedes ajustar
add_fast_rect(1, 1, 6, 1)      # barra superior izquierda
add_fast_rect(7, 3, 6, 1)      # segmento medio
add_fast_rect(3, 5, 10, 1)     # segmento medio bajo
add_fast_rect(1, 11, 18, 1)    # pasillo central largo
add_fast_rect(2, 15, 6, 1)     # barra inferior izquierda
add_fast_rect(11, 15, 7, 1)    # barra inferior derecha

# ----------------------------- Obstáculos por nivel -----------------------------
# Listas de índices (tiles) que se convertirán en paredes (0) cuando se alcance el nivel.
# Seleccionados para estrechar pasillos sin bloquear rutas principales.
LEVEL_OBSTACLES = {
    2: [  # unos cuantos cuellos de botella
        8 + 9*20, 10 + 9*20,   # cerca del centro
        12 + 7*20,             # lado derecho medio
        3 + 13*20,             # giro en L izq-baja
    ],
    3: [  # un poco más exigente
        6 + 5*20, 13 + 5*20,   # estrechar carril central alto
        7 + 11*20, 12 + 11*20, # ventanas centrales
        9 + 15*20,             # cuello bajo
    ],
    4: [  # reto alto (sigue habiendo camino)
        4 + 3*20, 15 + 3*20,
        5 + 9*20, 14 + 9*20,
        8 + 11*20,
    ],
}

def safe_apply_wall(idx):
    """Convierte una celda en pared cuidando pellets/contadores."""
    if 0 <= idx < len(tiles) and tiles[idx] != 0:
        if tiles[idx] == 1:
            state['pellets_left'] = max(0, state['pellets_left'] - 1)
        tiles[idx] = 0

def apply_level_obstacles(lvl):
    """Aplica obstáculos una sola vez por nivel."""
    if lvl in state['levels_applied']:
        return
    changes = LEVEL_OBSTACLES.get(lvl, [])
    for idx in changes:
        safe_apply_wall(idx)
    if changes:
        # Redibuja mundo para reflejar paredes nuevas
        clear()
        world()
    state['levels_applied'].add(lvl)

# ----------------------------- Utilidades -----------------------------
def square(x, y):
    path.up(); path.goto(x, y); path.down()
    path.begin_fill()
    for _ in range(4):
        path.forward(20); path.left(90)
    path.end_fill()

def offset(point):
    x = (floor(point.x, 20) + 200) / 20
    y = (180 - floor(point.y, 20)) / 20
    return int(x + y * 20)

def valid(point):
    index = offset(point)
    if tiles[index] == 0:
        return False
    index = offset(point + 19)
    if tiles[index] == 0:
        return False
    return point.x % 20 == 0 or point.y % 20 == 0

def at_intersection(p): return p.x % 20 == 0 and p.y % 20 == 0

def dist(a, b): return sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)

def in_fast_zone(point):
    idx = offset(point)
    return idx in FAST_ZONE_IDX

def pellets_info():
    return sum(1 for t in tiles if t == 1)

def chase_prob():
    return min(0.95, BASE_CHASE_PROB + (state['level'] - 1) * CHASE_INCREMENT)

def current_tick_ms():
    dec = (state['level'] - 1) * TICK_DECREMENT
    return max(MIN_TICK_MS, BASE_TICK_MS - dec)

def level_from_score():
    eaten = state['pellets_total'] - state['pellets_left']
    return max(1, 1 + eaten // PELLETS_PER_LEVEL)

# ----------------------------- Render del mundo -----------------------------
def world():
    bgcolor('black')
    path.color('blue'); path.width(1)
    for index, tile in enumerate(tiles):
        if tile > 0:
            x = (index % 20) * 20 - 200
            y = 180 - (index // 20) * 20
            square(x, y)
            if tile == 1:
                path.up(); path.goto(x + 10, y + 10); path.dot(2, 'white')

    # zonas rápidas (marco verde)
    for index in FAST_ZONE_IDX:
        if tiles[index] > 0:
            x = (index % 20) * 20 - 200
            y = 180 - (index // 20) * 20
            path.up(); path.goto(x, y); path.down()
            path.color('green'); path.width(3)
            for _ in range(2):
                path.forward(20); path.left(90)
                path.forward(20); path.left(90)
            path.width(1); path.color('blue')

# ----------------------------- IA de fantasmas -----------------------------
def pick_course(point, course, hybrid=False):
    step = BASE_STEP
    options = [vector(step,0), vector(-step,0), vector(0,step), vector(0,-step)]
    options = [v for v in options if valid(point + v)]
    if not options:
        return vector(-course.x, -course.y)

    opposite = vector(-course.x, -course.y)
    if len(options) > 1 and opposite in options:
        options.remove(opposite)

    p = pacman
    if hybrid:
        # 60% persecución directa, 40% emboscada a ~3 celdas por delante
        if random() < 0.6:
            target = p
        else:
            if aim.x == 0 and aim.y == 0:
                forward = vector(BASE_STEP * 3, 0)
            else:
                a_norm = vector(BASE_STEP if aim.x > 0 else (-BASE_STEP if aim.x < 0 else 0),
                                BASE_STEP if aim.y > 0 else (-BASE_STEP if aim.y < 0 else 0))
                forward = vector(a_norm.x * 3, a_norm.y * 3)
            target = vector(p.x + forward.x, p.y + forward.y)
        return min(options, key=lambda v: dist(point + v, target))

    if SMART_GHOSTS and random() < chase_prob():
        return min(options, key=lambda v: dist(point + v, pacman))
    return choice(options)

def build_ghosts(n):
    # El 5° (índice 4) será híbrido si existe
    candidates = [
        vector(-180, 160), vector(-180, -160), vector(100, 160), vector(100, -160),
        vector(-20, 160), vector(140, -20), vector(-20, -20), vector(140, 160),
        vector(-180, 0), vector(100, 0)
    ]
    ghosts = []
    dirs = [vector(BASE_STEP,0), vector(-BASE_STEP,0), vector(0,BASE_STEP), vector(0,-BASE_STEP)]
    for c in candidates:
        if len(ghosts) >= n: break
        if valid(c): ghosts.append([c.copy(), choice(dirs)])
    while len(ghosts) < n and ghosts:
        p, d = ghosts[len(ghosts) % len(ghosts)]
        ghosts.append([p.copy(), d.copy()])
    return ghosts

ghosts = build_ghosts(GHOSTS_N)

# ----------------------------- Lógica de juego -----------------------------
def try_add_ghost():
    """Desactivado por MAX_GHOSTS=5 + EXTRA_GHOST_EVERY=999. Se deja por compatibilidad."""
    return

def move_steps(entity_pos, move_vec, steps):
    for _ in range(max(1, int(steps))):
        if valid(entity_pos + move_vec):
            entity_pos.move(move_vec)
        else:
            break

def move():
    # Nivel por progreso
    new_level = level_from_score()
    if new_level != state['level']:
        state['level'] = new_level

    # Aplicar obstáculos de ese nivel (una vez)
    apply_level_obstacles(state['level'])

    writer.undo()
    writer.write(f"Score: {state['score']}  Lvl: {state['level']}")

    clear()

    # --- Pac-Man ---
    pac_steps = FAST_MULT_PAC if in_fast_zone(pacman) else 1
    if aim.x != 0 or aim.y != 0:
        move_steps(pacman, vector(aim.x, aim.y), pac_steps)

    # Comer punto
    index = offset(pacman)
    if tiles[index] == 1:
        tiles[index] = 2
        state['score'] += 1
        state['pellets_left'] -= 1
        x = (index % 20) * 20 - 200
        y = 180 - (index // 20) * 20
        path.color('blue'); square(x, y)

    # Dibujar Pac-Man
    up(); goto(pacman.x + 10, pacman.y + 10); dot(20, 'yellow')

    # --- Fantasmas ---
    for gi, (point, course) in enumerate(ghosts):
        g_mult = 1 + max(0, state['level'] - 1) // 1
        if in_fast_zone(point):
            g_mult += (FAST_MULT_GHO - 1)

        if valid(point + course):
            if at_intersection(point):
                is_hybrid = (gi == 4)  # 5º fantasma
                course_new = pick_course(point, course, hybrid=is_hybrid)
                ghosts[gi][1] = course_new
                move_steps(point, course_new, g_mult)
            else:
                move_steps(point, course, g_mult)
        else:
            is_hybrid = (gi == 4)
            course_new = pick_course(point, course, hybrid=is_hybrid)
            ghosts[gi][1] = course_new
            move_steps(point, course_new, g_mult)

        up(); goto(point.x + 10, point.y + 10)
        dot(20, GHOST_COLORS[gi % len(GHOST_COLORS)])

    update()

    # Colisión
    for point, _ in ghosts:
        if abs(pacman - point) < 20:
            writer.goto(-70, 0); writer.color('white')
            writer.write('GAME OVER', align='left', font=('Arial', 16, 'bold'))
            return

    ontimer(move, current_tick_ms())

def change(x, y):
    if valid(pacman + vector(x, y)):
        aim.x = x; aim.y = y

# ----------------------------- Setup -----------------------------
def init_game():
    state['pellets_total'] = pellets_info()
    state['pellets_left'] = state['pellets_total']

    setup(420, 460, 370, 0)
    hideturtle(); tracer(False)
    writer.up(); writer.goto(60, 190); writer.color('white')
    writer.write(f"Score: {state['score']}  Lvl: {state['level']}")
    listen()
    onkey(lambda: change(BASE_STEP, 0), 'Right')
    onkey(lambda: change(-BASE_STEP, 0), 'Left')
    onkey(lambda: change(0, BASE_STEP), 'Up')
    onkey(lambda: change(0, -BASE_STEP), 'Down')
    world()
    move()
    done()

if __name__ == '__main__':
    init_game()
