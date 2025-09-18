# Pac-Man Plus: 
# 1) 5° fantasma con IA híbrida
# 2) Zonas rápidas verdes
# 3) Dificultad progresiva

from random import choice, random
from turtle import *
from freegames import floor, vector
from math import sqrt

# ----------------------------- Parámetros editables -----------------------------
GHOSTS_N = 5          # Número inicial de fantasmas (5 incluye al híbrido)
BASE_STEP = 5         # Paso base (mantener múltiplo de 5 para alinear a grilla)
PACMAN_START = vector(80, -120)
SMART_GHOSTS = True   # IA de persecución
BASE_CHASE_PROB = 0.75
BASE_TICK_MS = 95     # ms entre frames (dinámico por nivel)
MAX_GHOSTS = 8        # Límite si decides subirlos dinámicamente

# Multiplicadores en zonas rápidas (enteros: 1 = normal, 2 = el doble de pasos por tick)
FAST_MULT_PAC = 2
FAST_MULT_GHO = 2

# Progresión (se recalcula por nivel = pellets_comidos // PELLETS_PER_LEVEL + 1)
PELLETS_PER_LEVEL = 35
EXTRA_GHOST_EVERY = 2          # Cada 2 niveles intenta sumar un fantasma (hasta MAX_GHOSTS)
CHASE_INCREMENT = 0.05         # +5% de agresividad por nivel
TICK_DECREMENT = 5             # -5 ms por nivel (hasta un mínimo)
MIN_TICK_MS = 45

# ----------------------------- Estado global -----------------------------
state = {'score': 0, 'level': 1, 'pellets_total': 0, 'pellets_left': 0}
path = Turtle(visible=False)
writer = Turtle(visible=False)
aim = vector(BASE_STEP, 0)
pacman = PACMAN_START.copy()

# Colores para distinguir fantasmas
GHOST_COLORS = ['red', 'pink', 'cyan', 'orange', 'purple', 'green', 'yellow', 'white']

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
# Puedes editar la selección para “pintar” corredores rápidos.
FAST_ZONE_IDX = set()
# Ejemplo: una “S” grande de corredores rápidos
def add_fast_rect(ix, iy, w, h):
    # ix, iy en celdas (0..19), w/h en celdas (ancho/alto)
    for dy in range(h):
        for dx in range(w):
            x = ix + dx
            y = iy + dy
            idx = x + y * 20
            if 0 <= idx < len(tiles) and tiles[idx] != 0:
                FAST_ZONE_IDX.add(idx)

# Dibujo de zonas (modifica a tu gusto)
add_fast_rect(1, 1, 6, 1)      # barra superior izquierda
add_fast_rect(7, 3, 6, 1)      # segmento medio
add_fast_rect(3, 5, 10, 1)     # segmento medio bajo
add_fast_rect(1, 11, 18, 1)    # pasillo central largo
add_fast_rect(2, 15, 6, 1)     # barra inferior izquierda
add_fast_rect(11, 15, 7, 1)    # barra inferior derecha

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
    """Índice en tiles para una coordenada."""
    x = (floor(point.x, 20) + 200) / 20
    y = (180 - floor(point.y, 20)) / 20
    return int(x + y * 20)

def valid(point):
    """True si la posición es válida (no pared) y alineada a grilla."""
    index = offset(point)
    if tiles[index] == 0:
        return False
    index = offset(point + 19)
    if tiles[index] == 0:
        return False
    return point.x % 20 == 0 or point.y % 20 == 0

def at_intersection(p):
    return p.x % 20 == 0 and p.y % 20 == 0

def dist(a, b):
    return sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)

def in_fast_zone(point):
    """True si el centro de la celda pertenece a zona rápida."""
    idx = offset(point)
    return idx in FAST_ZONE_IDX

def pellets_info():
    total = sum(1 for t in tiles if t == 1)
    return total

def chase_prob():
    # Agresividad dinámica por nivel
    return min(0.95, BASE_CHASE_PROB + (state['level'] - 1) * CHASE_INCREMENT)

def current_tick_ms():
    # Velocidad de juego por nivel
    dec = (state['level'] - 1) * TICK_DECREMENT
    return max(MIN_TICK_MS, BASE_TICK_MS - dec)

def level_from_score():
    eaten = state['pellets_total'] - state['pellets_left']
    return max(1, 1 + eaten // PELLETS_PER_LEVEL)

# ----------------------------- Render del mundo -----------------------------
def world():
    bgcolor('black')
    # Suelo/paredes
    path.color('blue')
    for index, tile in enumerate(tiles):
        if tile > 0:
            x = (index % 20) * 20 - 200
            y = 180 - (index // 20) * 20
            square(x, y)
            # puntos
            if tile == 1:
                path.up()
                path.goto(x + 10, y + 10)
                path.dot(2, 'white')

    # Pintar zonas rápidas (encima del suelo)
    for index in FAST_ZONE_IDX:
        if tiles[index] > 0:
            x = (index % 20) * 20 - 200
            y = 180 - (index // 20) * 20
            path.up()
            path.goto(x, y)
            path.down()
            path.color('green')
            path.width(3)
            # marco/rectángulo hueco para que se vea el punto
            for _ in range(2):
                path.forward(20)
                path.left(90)
                path.forward(20)
                path.left(90)
            path.width(1)
            path.color('blue')

# ----------------------------- IA de fantasmas -----------------------------
def pick_course(point, course, hybrid=False):
    """Elige dirección nueva en intersección.
       hybrid=True activa modo emboscada ocasional.
    """
    step = BASE_STEP
    options = [vector(step,0), vector(-step,0), vector(0,step), vector(0,-step)]
    options = [v for v in options if valid(point + v)]
    if not options:
        return vector(-course.x, -course.y)

    opposite = vector(-course.x, -course.y)
    if len(options) > 1 and opposite in options:
        options.remove(opposite)

    p = pacman
    # Modo híbrido: por “ciclos” cambia entre perseguir y emboscar
    if hybrid:
        # 60% perseguir directo, 40% emboscada hacia una casilla adelantada del pacman
        if random() < 0.6:
            target = p
        else:
            # punto de emboscada: unas 3 casillas hacia la mira actual (o derecha si está quieto)
            forward = vector(0, 0)
            if aim.x == 0 and aim.y == 0:
                forward = vector(BASE_STEP * 3, 0)
            else:
                a_norm = vector(0, 0)
                if abs(aim.x) > 0:
                    a_norm.x = BASE_STEP if aim.x > 0 else -BASE_STEP
                if abs(aim.y) > 0:
                    a_norm.y = BASE_STEP if aim.y > 0 else -BASE_STEP
                forward = vector(a_norm.x * 3, a_norm.y * 3)
            target = vector(p.x + forward.x, p.y + forward.y)
        best = min(options, key=lambda v: dist(point + v, target))
        return best

    # Fantasma “normal”: con probabilidad de persecución
    if SMART_GHOSTS and random() < chase_prob():
        best = min(options, key=lambda v: dist(point + v, pacman))
        return best
    else:
        return choice(options)

def build_ghosts(n):
    """Crea 'n' fantasmas. El 5° (índice 4) será híbrido si existe."""
    candidates = [
        vector(-180, 160), vector(-180, -160), vector(100, 160), vector(100, -160),
        vector(-20, 160), vector(140, -20), vector(-20, -20), vector(140, 160),
        vector(-180, 0), vector(100, 0)
    ]
    ghosts = []
    dirs = [vector(BASE_STEP,0), vector(-BASE_STEP,0), vector(0,BASE_STEP), vector(0,-BASE_STEP)]
    for c in candidates:
        if len(ghosts) >= n:
            break
        if valid(c):
            ghosts.append([c.copy(), choice(dirs)])
    while len(ghosts) < n and ghosts:
        p, d = ghosts[len(ghosts) % len(ghosts)]
        ghosts.append([p.copy(), d.copy()])
    return ghosts

ghosts = build_ghosts(GHOSTS_N)

# ----------------------------- Lógica de juego -----------------------------
def try_add_ghost():
    """Intenta sumar un fantasma en niveles altos (hasta MAX_GHOSTS)."""
    global ghosts
    if len(ghosts) >= MAX_GHOSTS:
        return
    # Busca un spawn válido
    spawns = [
        vector(-180, 160), vector(-180, -160), vector(100, 160), vector(100, -160),
        vector(-20, 160), vector(140, -20), vector(-20, -20), vector(140, 160)
    ]
    dirs = [vector(BASE_STEP,0), vector(-BASE_STEP,0), vector(0,BASE_STEP), vector(0,-BASE_STEP)]
    for s in spawns:
        if valid(s):
            ghosts.append([s.copy(), choice(dirs)])
            break

def move_steps(entity_pos, move_vec, steps):
    """Mueve 'steps' veces de 'BASE_STEP' manteniendo alineación."""
    for _ in range(max(1, int(steps))):
        if valid(entity_pos + move_vec):
            entity_pos.move(move_vec)
        else:
            break

def move():
    """Loop principal."""
    # Actualiza nivel según pellets comidos
    new_level = level_from_score()
    if new_level != state['level']:
        state['level'] = new_level
        # Cada ciertos niveles añade un fantasma extra
        if state['level'] % EXTRA_GHOST_EVERY == 0:
            try_add_ghost()

    writer.undo()
    writer.write(f"Score: {state['score']}  Lvl: {state['level']}")

    clear()

    # --- Pac-Man ---
    pac_steps = FAST_MULT_PAC if in_fast_zone(pacman) else 1
    # desglosa movimiento en pasos BASE_STEP para no romper la grilla
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
        # repintar el suelo
        path.color('blue')
        square(x, y)

    # Dibujar Pac-Man
    up()
    goto(pacman.x + 10, pacman.y + 10)
    dot(20, 'yellow')

    # --- Fantasmas ---
    for gi, (point, course) in enumerate(ghosts):
        # velocidad adicional por nivel y zona rápida
        g_mult = 1 + max(0, state['level'] - 1) // 1  # +1 paso por tick por nivel
        if in_fast_zone(point):
            g_mult += (FAST_MULT_GHO - 1)

        # En intersección decide nueva ruta
        if valid(point + course):
            if at_intersection(point):
                # 5° fantasma (índice 4): híbrido
                is_hybrid = (gi == 4)
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

        # Dibujar fantasma
        up()
        goto(point.x + 10, point.y + 10)
        dot(20, GHOST_COLORS[gi % len(GHOST_COLORS)])

    update()

    # Colisión
    for point, _ in ghosts:
        if abs(pacman - point) < 20:
            writer.goto(-70, 0)
            writer.color('white')
            writer.write('GAME OVER', align='left', font=('Arial', 16, 'bold'))
            return

    ontimer(move, current_tick_ms())

def change(x, y):
    """Cambia la dirección de Pac-Man si es válida."""
    if valid(pacman + vector(x, y)):
        aim.x = x
        aim.y = y

# ----------------------------- Setup -----------------------------
def init_game():
    # Pellets
    state['pellets_total'] = pellets_info()
    state['pellets_left'] = state['pellets_total']

    setup(420, 460, 370, 0)
    hideturtle()
    tracer(False)
    writer.up()
    writer.goto(60, 190)
    writer.color('white')
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