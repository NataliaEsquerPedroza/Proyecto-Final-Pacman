# Pac-Man Plus:
# 1) 5° fantasma con IA híbrida
# 2) Zonas rápidas verdes
# 3) Dificultad progresiva (velocidad + obstáculos estratégicos por nivel)
# 4) Pac-Man inicia en el centro del tablero (spawn seguro)
# 5) Sin parpadeo: render por capas (laberinto/pellets/personajes)

from random import choice, random
from turtle import *
from freegames import floor, vector
from math import sqrt

# ----------------------------- Parámetros editables -----------------------------
GHOSTS_N = 5          # Número fijo de fantasmas (incluye al híbrido)
BASE_STEP = 5         # Paso base (múltiplo de 5 para alinear a grilla)
PACMAN_START = vector(80, -120)  # se sobrescribe con center_spawn() al iniciar
SMART_GHOSTS = True   # IA de persecución
BASE_CHASE_PROB = 0.75
BASE_TICK_MS = 95     # ms entre frames (dinámico por nivel)

# Multiplicadores en zonas rápidas (enteros: 1 = normal, 2 = doble paso por tick)
FAST_MULT_PAC = 2

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
maze_t = Turtle(visible=False)     # paredes + suelo + zonas verdes (estático)
pellets_t = Turtle(visible=False)  # SOLO pellets (dinámico)
writer = Turtle(visible=False)     # HUD
aim = vector(BASE_STEP, 0)

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
    0,1,1,1,1,1,0,1,1,0,1,1,1,1,1,1,1,1,1,0,
    0,1,0,0,0,1,0,0,1,0,0,0,1,0,0,0,1,0,0,0,
    0,1,1,1,0,1,1,1,1,1,1,0,1,1,1,0,1,1,1,0,
    0,1,0,1,0,0,0,0,0,0,1,0,0,0,1,0,1,0,1,0,
    0,1,1,1,1,1,1,0,1,1,1,1,1,0,1,1,1,1,1,0,
    0,1,0,0,0,0,1,0,1,0,0,0,1,0,1,0,0,0,1,0,
    0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0,
    0,1,0,0,0,1,0,0,1,0,1,0,0,0,1,0,0,0,1,0,
    0,1,1,1,0,1,1,1,1,0,1,1,1,1,1,1,1,0,1,0,
    0,0,0,1,0,0,0,1,0,0,1,0,1,0,0,0,1,0,0,0,
    0,1,1,1,1,1,0,1,1,1,1,1,1,1,1,1,1,1,1,0,
    0,1,0,0,0,1,0,1,0,1,0,0,0,0,0,1,0,0,1,0,
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
add_fast_rect(1, 1, 6, 1)
add_fast_rect(7, 3, 6, 1)
add_fast_rect(3, 5, 10, 1)
add_fast_rect(1, 11, 18, 1)
add_fast_rect(2, 15, 6, 1)
add_fast_rect(11, 15, 7, 1)

# ----------------------------- Obstáculos por nivel -----------------------------
LEVEL_OBSTACLES = {
    2: [8 + 9*20, 10 + 9*20, 12 + 7*20, 3 + 13*20],
    3: [6 + 5*20, 13 + 5*20, 7 + 11*20, 12 + 11*20, 9 + 15*20],
    4: [4 + 3*20, 15 + 3*20, 5 + 9*20, 14 + 9*20, 8 + 11*20],
}

def safe_apply_wall(idx):
    if 0 <= idx < len(tiles) and tiles[idx] != 0:
        if tiles[idx] == 1:
            state['pellets_left'] = max(0, state['pellets_left'] - 1)
        tiles[idx] = 0

def apply_level_obstacles(lvl):
    if lvl in state['levels_applied']:
        return
    changes = LEVEL_OBSTACLES.get(lvl, [])
    for idx in changes:
        safe_apply_wall(idx)
    if changes:
        # Si cambian paredes/pellets, hay que redibujar capas estáticas
        maze_t.clear()
        pellets_t.clear()
        draw_maze()
        draw_pellets()
    state['levels_applied'].add(lvl)

# ----------------------------- Utilidades -----------------------------

# DEFINIR LA FORMA DE UN TRIANGULO PARA LOS FANTASMAS
def draw_triangle(cx, cy, side, fill):
    """Dibuja un triángulo equilátero centrado en (cx, cy)."""
    h = side * sqrt(3) / 2  # altura
    # Vértices centrados en (cx, cy)
    top = (cx,            cy + (2*h/3))
    left = (cx - side/2,  cy - (h/3))
    right = (cx + side/2, cy - (h/3))

    up()
    goto(*top)
    color(fill)
    begin_fill()
    down()
    goto(*right)
    goto(*left)
    goto(*top)
    end_fill()
    up()


# DEFINIR LOS CUADRADOS DEL TABLERO
def square(t, x, y, size=20):
    t.up(); t.goto(x, y); t.down()
    t.begin_fill()
    for _ in range(4):
        t.forward(size); t.left(90)
    t.end_fill()

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
def in_fast_zone(point): return offset(point) in FAST_ZONE_IDX
def pellets_info(): return sum(1 for t in tiles if t == 1)
def chase_prob(): return min(0.95, BASE_CHASE_PROB + (state['level'] - 1) * CHASE_INCREMENT)
def current_tick_ms(): return max(MIN_TICK_MS, BASE_TICK_MS - (state['level'] - 1) * TICK_DECREMENT)
def level_from_score():
    eaten = state['pellets_total'] - state['pellets_left']
    return max(1, 1 + eaten // PELLETS_PER_LEVEL)

# --- Spawn seguro en el centro ---
def center_spawn():
    candidates = [
        vector(-20, -20), vector(0, -20), vector(-20, 0), vector(0, 0),
        vector(-40, -20), vector(20, -20), vector(-20, -40), vector(-20, 20),
        vector(20, 0), vector(0, 20), vector(-40, 0), vector(0, -40)
    ]
    for c in candidates:
        if valid(c): return c
    return PACMAN_START

# ----------------------------- Render por capas -----------------------------
def draw_maze():
    """Capa estática: suelo/paredes (azul) + zonas rápidas (verde)."""
    bgcolor('black')
    maze_t.color('blue'); maze_t.width(1)
    for index, tile in enumerate(tiles):
        if tile > 0:
            x = (index % 20) * 20 - 200
            y = 180 - (index // 20) * 20
            square(maze_t, x, y)

    # zonas rápidas (marco verde)
    for index in FAST_ZONE_IDX:
        if tiles[index] > 0:
            x = (index % 20) * 20 - 200
            y = 180 - (index // 20) * 20
            maze_t.up(); maze_t.goto(x, y); maze_t.down()
            maze_t.color('green'); maze_t.width(3)
            for _ in range(2):
                maze_t.forward(20); maze_t.left(90)
                maze_t.forward(20); maze_t.left(90)
            maze_t.width(1); maze_t.color('blue')

def draw_pellets():
    """Capa dinámica: solo puntitos blancos según tiles == 1."""
    pellets_t.clear()
    pellets_t.up()
    for index, tile in enumerate(tiles):
        if tile == 1:
            x = (index % 20) * 20 - 200
            y = 180 - (index // 20) * 20
            pellets_t.goto(x + 10, y + 10)
            pellets_t.dot(2, 'white')

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

    # Obstáculos por nivel (una vez)
    apply_level_obstacles(state['level'])

    writer.undo()
    writer.write(f"Score: {state['score']}  Lvl: {state['level']}")

    # Limpiar SOLO personajes (no el laberinto ni los pellets)
    clear()

    # --- Pac-Man ---
    pac_steps = FAST_MULT_PAC if in_fast_zone(pacman) else 1
    if aim.x != 0 or aim.y != 0:
        move_steps(pacman, vector(aim.x, aim.y), pac_steps)

    # Comer punto: actualizar tiles y redibujar SÓLO la capa de pellets
    index = offset(pacman)
    if tiles[index] == 1:
        tiles[index] = 2
        state['score'] += 1
        state['pellets_left'] -= 1
        draw_pellets()  # <- este pellet ya no se dibuja

# DIBUJAMOS PACMAN COMO UN CIRCULO AMARILLO
    up(); goto(pacman.x + 10, pacman.y + 10); dot(20, 'yellow')

    # --- Fantasmas ---
# --- Fantasmas ---
    for gi, (point, course) in enumerate(ghosts):
        # Pasos “base” por nivel (dificultad). Ej.: nivel 1 -> 1 paso, nivel 2 -> 2 pasos...
        g_mult_raw = 1 + max(0, state['level'] - 1) // 1

        # Pasos actuales de Pac-Man en este tick (puede ser 1 o 2 si está en zona rápida)
        pac_steps = FAST_MULT_PAC if in_fast_zone(pacman) else 1

        # REGLA: los fantasmas NUNCA pueden ser más rápidos que el jugador
        g_mult = min(g_mult_raw, 1)

        # REGLA: las zonas rápidas NO afectan a los fantasmas (no sumamos nada por zonas)
        # (Quitamos cualquier código tipo: if in_fast_zone(point): g_mult += ...)

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

# DIBUJAMOS FANTASMAS COMO TRIÁNGULOS DE COLORES
        cx, cy = point.x + 10, point.y + 7
        draw_triangle(cx, cy, 19, GHOST_COLORS[gi % len(GHOST_COLORS)])




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
    global pacman
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

    # --- colocar Pac-Man en el centro válido ---
    pacman = center_spawn()

    # Dibujar capas estáticas una vez
    draw_maze()
    draw_pellets()

    move()
    done()

if __name__ == '__main__':
    init_game()
