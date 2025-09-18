# Pac-Man Plus:                                                    
# 1) 5° fantasma con IA híbrida                                     
# 2) Zonas rápidas verdes                                           
# 3) Dificultad progresiva (velocidad + obstáculos estratégicos por nivel) 
# 4) Pac-Man inicia en el centro del tablero (spawn seguro)        

from random import choice, random          
from turtle import *                      
from freegames import floor, vector        
from math import sqrt                      

# ----------------------------- CONSTANTES -----------------------------
GHOSTS_N = 5          # Numero nuevo de fantasmas 4 ==> 5
BASE_STEP = 5         # Paso base (múltiplo de 5 para alinear a grilla)
PACMAN_START = vector(80, -120)  # Valor inicial; usado como fallback en center_spawn() si no hay posición válida
SMART_GHOSTS = True   # IA de persecución
BASE_CHASE_PROB = 0.75  # Probabilidad base de que los fantasmas persigan a Pac-Man (IA de persecución)
BASE_TICK_MS = 95     # ms entre frames (dinámico por nivel)

# Multiplicadores en zonas rápidas (enteros: 1 = normal, 2 = doble paso por tick)
FAST_MULT_PAC = 2     # Pac-Man avanza 2 pasos por tick cuando pisa zona rápida (si es válida la dirección)

# Progresión (nivel = pellets_comidos // PELLETS_PER_LEVEL + 1)
PELLETS_PER_LEVEL = 35     # Cada 35 pellets sube 1 nivel
CHASE_INCREMENT = 0.05     # +5% de agresividad por nivel en la IA de persecución
TICK_DECREMENT = 5         # Cada nivel reduce 5 ms el intervalo del tick (más “fps”)
MIN_TICK_MS = 45           # Límite inferior del tick (no acelera por debajo de esto)

# ----------------------------- DATOS GLOBALES -----------------------------
state = {
    'score': 0,                 # Puntos acumulados
    'level': 1,                 # Nivel actual
    'pellets_total': 0,         # Total de pellets al iniciar
    'pellets_left': 0,          # Pellets que faltan por comer
    'levels_applied': set(),    # Niveles a los que ya se aplicaron obstáculos (para no repetir)
}
maze_t = Turtle(visible=False)     # Turtle para laberinto/zonas verdes (se dibuja una sola vez)
pellets_t = Turtle(visible=False)  # Turtle para dibujar SÓLO los pellets (se redibuja al comer)
writer = Turtle(visible=False)     # Turtle para HUD (marcador)
aim = vector(BASE_STEP, 0)         # Dirección deseada de Pac-Man (inicial hacia la derecha)

# Colores para distinguir fantasmas
GHOST_COLORS = ['red', 'pink', 'cyan', 'orange', 'purple']  # Lista cíclica de colores para fantasmas

# ----------------------------- LABERINTO (20x20) -----------------------------
# 0 = pared, 1 = punto, 2 = vacío
tiles = [                           # Matriz 20x20 aplanada: mapa del nivel
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

# ----------------------------- ZONAS RAPIDAS -----------------------------
FAST_ZONE_IDX = set()                   # Conjunto de índices (en tiles) que son zonas rápidas
def add_fast_rect(ix, iy, w, h):        # Marca un rectángulo de celdas como “rápidas”
    for dy in range(h):                 # Recorre alto
        for dx in range(w):             # Recorre ancho
            x = ix + dx                 # Columna absoluta
            y = iy + dy                 # Fila absoluta
            idx = x + y * 20            # Índice lineal en tiles
            if 0 <= idx < len(tiles) and tiles[idx] != 0:  # Solo si no es pared
                FAST_ZONE_IDX.add(idx)  # Agrega a zonas rápidas

# Definición de zonas rápidas (rectángulos)
add_fast_rect(1, 1, 6, 1)               # Barra rápida superior izquierda
add_fast_rect(7, 3, 6, 1)               # Segmento medio
add_fast_rect(3, 5, 10, 1)              # Segmento medio bajo
add_fast_rect(1, 11, 18, 1)             # Pasillo central largo
add_fast_rect(2, 15, 6, 1)              # Inferior izquierda
add_fast_rect(11, 15, 7, 1)             # Inferior derecha

# ----------------------------- Obstáculos por nivel -----------------------------
LEVEL_OBSTACLES = {                      # Índices de tiles que se convertirán en pared por nivel
    2: [8 + 9*20, 10 + 9*20, 12 + 7*20, 3 + 13*20],
    3: [6 + 5*20, 13 + 5*20, 7 + 11*20, 12 + 11*20, 9 + 15*20],
    4: [4 + 3*20, 15 + 3*20, 5 + 9*20, 14 + 9*20, 8 + 11*20],
}

def safe_apply_wall(idx):                # Convierte una celda en pared sin desincronizar contadores
    if 0 <= idx < len(tiles) and tiles[idx] != 0:      # Solo si era transitable
        if tiles[idx] == 1:                             # Si tenía un pellet...
            state['pellets_left'] = max(0, state['pellets_left'] - 1)  # Ajusta pellets restantes
        tiles[idx] = 0                                  # Pasa a pared

def apply_level_obstacles(lvl):          # Aplica obstáculos del nivel actual (una sola vez por nivel)
    if lvl in state['levels_applied']:   # Si ya se aplicaron, salir
        return
    changes = LEVEL_OBSTACLES.get(lvl, [])  # Lista de índices a bloquear en este nivel
    for idx in changes:
        safe_apply_wall(idx)             # Convierte cada índice en pared (si corresponde)
    if changes:
        # Si cambian paredes/pellets, hay que redibujar capas estáticas
        maze_t.clear()                   # Limpia la capa de laberinto
        pellets_t.clear()                # Limpia la capa de pellets
        draw_maze()                      # Redibuja laberinto/zonas
        draw_pellets()                   # Redibuja todos los pellets
    state['levels_applied'].add(lvl)     # Marca el nivel como aplicado

# ----------------------------- Utilidades -----------------------------

# Definir función para dibujar triángulo (fantasmas)
def draw_triangle(cx, cy, side, fill):  
    """Dibuja un triángulo equilátero centrado en (cx, cy)."""
    h = side * sqrt(3) / 2               
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
def square(t, x, y, size=20):            # Dibuja un cuadrado de lado "size" con turtle t
    t.up(); t.goto(x, y); t.down()       # Mover sin dibujar; comenzar a dibujar
    t.begin_fill()                       # Inicia relleno
    for _ in range(4):                   # 4 lados
        t.forward(size); t.left(90)      # Trazo lado; gira 90°
    t.end_fill()                         # Termina relleno

def offset(point):                       # Convierte un vector (x,y) a índice en tiles
    x = (floor(point.x, 20) + 200) / 20  # Cuadrícula: columna (ajustado a múltiplos de 20)
    y = (180 - floor(point.y, 20)) / 20  # Cuadrícula: fila (origen arriba)
    return int(x + y * 20)               # Índice lineal

def valid(point):                        # ¿La posición es transitable y alineada a la grilla?
    index = offset(point)                # Índice de la esquina sup-izq
    if tiles[index] == 0:                # Si es pared
        return False
    index = offset(point + 19)           # Índice de la esquina inf-der (para tamaño del sprite)
    if tiles[index] == 0:                # Si pega con pared
        return False
    return point.x % 20 == 0 or point.y % 20 == 0  # Debe estar alineado a la malla

def at_intersection(p): return p.x % 20 == 0 and p.y % 20 == 0  # ¿Está justo en intersección?
def dist(a, b): return sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2) # Distancia Euclidiana
def in_fast_zone(point): return offset(point) in FAST_ZONE_IDX    # ¿Está en celda rápida?
def pellets_info(): return sum(1 for t in tiles if t == 1)        # Cuenta pellets iniciales
def chase_prob():                                                  # Prob. de persecución dinámica
    return min(0.95, BASE_CHASE_PROB + (state['level'] - 1) * CHASE_INCREMENT)
def current_tick_ms():                                             # Intervalo actual del tick
    return max(MIN_TICK_MS, BASE_TICK_MS - (state['level'] - 1) * TICK_DECREMENT)
def level_from_score():                                            # Nivel a partir de pellets comidos
    eaten = state['pellets_total'] - state['pellets_left']         # Pellets comidos
    return max(1, 1 + eaten // PELLETS_PER_LEVEL)                  # Nivel = 1 + bloques de 35

# --- Spawn seguro en el centro ---
def center_spawn():                                                # Busca una celda libre cerca del centro
    candidates = [                                                 # Posibles posiciones centradas
        vector(-20, -20), vector(0, -20), vector(-20, 0), vector(0, 0),
        vector(-40, -20), vector(20, -20), vector(-20, -40), vector(-20, 20),
        vector(20, 0), vector(0, 20), vector(-40, 0), vector(0, -40)
    ]
    for c in candidates:
        if valid(c): return c                                      # Devuelve la primera válida
    return PACMAN_START                                            # Si ninguna sirve, usa fallback

# ----------------------------- Render por capas -----------------------------
def draw_maze():                                                   # Dibuja capa estática: suelo/paredes + marco verde
    """Capa estática: suelo/paredes (azul) + zonas rápidas (verde)."""
    bgcolor('black')                                               # Fondo negro
    maze_t.color('blue'); maze_t.width(1)                          # Color de celdas transitables
    for index, tile in enumerate(tiles):                           # Recorre el mapa
        if tile > 0:                                               # Si no es pared
            x = (index % 20) * 20 - 200                            # Coord X del tile
            y = 180 - (index // 20) * 20                           # Coord Y del tile
            square(maze_t, x, y)                                   # Dibuja el suelo

    # zonas rápidas (marco verde)
    for index in FAST_ZONE_IDX:                                    # Recorre celdas rápidas
        if tiles[index] > 0:                                       # Solo si no es pared
            x = (index % 20) * 20 - 200
            y = 180 - (index // 20) * 20
            maze_t.up(); maze_t.goto(x, y); maze_t.down()          # Posicionar borde
            maze_t.color('green'); maze_t.width(3)                 # Estilo del marco
            for _ in range(2):                                     # Rectángulo del marco
                maze_t.forward(20); maze_t.left(90)
                maze_t.forward(20); maze_t.left(90)
            maze_t.width(1); maze_t.color('blue')                  # Restaura estilos

def draw_pellets():                                                # Redibuja SÓLO los puntos blancos
    """Capa dinámica: solo puntitos blancos según tiles == 1."""
    pellets_t.clear()                                              # Limpia la capa de pellets
    pellets_t.up()                                                 # No dibujar al mover
    for index, tile in enumerate(tiles):                           # Recorre mapa
        if tile == 1:                                              # Si hay pellet en la celda
            x = (index % 20) * 20 - 200
            y = 180 - (index // 20) * 20
            pellets_t.goto(x + 10, y + 10)                         # Centro de la celda
            pellets_t.dot(2, 'white')                              # Dibuja el pellet

# ----------------------------- IA de fantasmas -----------------------------
def pick_course(point, course, hybrid=False):                      # Decide la dirección en intersecciones
    step = BASE_STEP                                               # Tamaño del paso
    options = [vector(step,0), vector(-step,0), vector(0,step), vector(0,-step)]  # 4 direcciones
    options = [v for v in options if valid(point + v)]             # Filtra movimientos válidos
    if not options:                                                # Si no hay opciones
        return vector(-course.x, -course.y)                        # Da la vuelta

    opposite = vector(-course.x, -course.y)                        # Evitar reversa si hay alternativas
    if len(options) > 1 and opposite in options:
        options.remove(opposite)

    p = pacman                                                     # Posición de Pac-Man para target
    if hybrid:                                                     # Fantasma híbrido (5°)
        if random() < 0.6:                                         # 60%: perseguir directo
            target = p
        else:                                                      # 40%: emboscada 3 celdas adelante
            if aim.x == 0 and aim.y == 0:                          # Si Pac-Man está parado
                forward = vector(BASE_STEP * 3, 0)                 # Embosca hacia la derecha
            else:                                                  # Normaliza aim a un paso de BASE_STEP
                a_norm = vector(BASE_STEP if aim.x > 0 else (-BASE_STEP if aim.x < 0 else 0),
                                BASE_STEP if aim.y > 0 else (-BASE_STEP if aim.y < 0 else 0))
                forward = vector(a_norm.x * 3, a_norm.y * 3)       # 3 celdas por delante
            target = vector(p.x + forward.x, p.y + forward.y)      # Punto de emboscada
        return min(options, key=lambda v: dist(point + v, target)) # Elige la dirección que acerca

    if SMART_GHOSTS and random() < chase_prob():                   # Fantasma “normal” con persecución probabilística
        return min(options, key=lambda v: dist(point + v, pacman)) # Elige la mejor hacia Pac-Man
    return choice(options)                                         # Si no, aleatoria de las válidas

def build_ghosts(n):                                               # Construye lista de fantasmas (pos y dirección)
    candidates = [                                                 # Posibles spawns
        vector(-180, 160), vector(-180, -160), vector(100, 160), vector(100, -160),
        vector(-20, 160), vector(140, -20), vector(-20, -20), vector(140, 160),
        vector(-180, 0), vector(100, 0)
    ]
    ghosts = []                                                    # Lista [ [pos, dir], ... ]
    dirs = [vector(BASE_STEP,0), vector(-BASE_STEP,0), vector(0,BASE_STEP), vector(0,-BASE_STEP)]  # Dir inicial al azar
    for c in candidates:
        if len(ghosts) >= n: break                                 # Parar cuando tengamos n fantasmas
        if valid(c): ghosts.append([c.copy(), choice(dirs)])       # Si spawn válido, agrega fantasma
    while len(ghosts) < n and ghosts:                              # Si faltan, duplica algunos spawns válidos
        p, d = ghosts[len(ghosts) % len(ghosts)]
        ghosts.append([p.copy(), d.copy()])
    return ghosts

ghosts = build_ghosts(GHOSTS_N)                                    # Crea los 5 fantasmas

# ----------------------------- Lógica de juego -----------------------------

def move_steps(entity_pos, move_vec, steps):                        # Aplica “steps” pasos (alineados) a una entidad
    for _ in range(max(1, int(steps))):                            # Al menos 1 paso
        if valid(entity_pos + move_vec):                           # Si la siguiente celda es válida
            entity_pos.move(move_vec)                              # Avanza
        else:
            break                                                  # Si hay pared, detiene

def move():                                                        # Bucle principal llamado cada tick
    # Nivel por progreso
    new_level = level_from_score()                                 # Recalcula nivel por pellets comidos
    if new_level != state['level']:                                # Si subió/bajó nivel
        state['level'] = new_level                                 # Actualiza nivel

    # Obstáculos por nivel (una vez)
    apply_level_obstacles(state['level'])                          # Inserta paredes del nivel si no se aplicaron

    writer.undo()                                                  # Borra texto anterior del HUD
    writer.write(f"Score: {state['score']}  Lvl: {state['level']}")# Escribe nuevo HUD

    # Limpiar SOLO personajes (no el laberinto ni los pellets)
    clear()                                                        # Limpia la turtle principal (Pac-Man + fantasmas)

    # --- Pac-Man ---
    pac_steps = FAST_MULT_PAC if in_fast_zone(pacman) else 1       # Pac-Man acelera si pisa zona rápida
    if aim.x != 0 or aim.y != 0:                                   # Si hay input/dirección válida
        move_steps(pacman, vector(aim.x, aim.y), pac_steps)        # Avanza pac_steps veces

    # Comer punto: actualizar tiles y redibujar SÓLO la capa de pellets
    index = offset(pacman)                                         # Índice de la celda de Pac-Man
    if tiles[index] == 1:                                          # Si hay pellet
        tiles[index] = 2                                           # Marca la celda como vacía
        state['score'] += 1                                        # Suma punto
        state['pellets_left'] -= 1                                 # Resta un pellet pendiente
        draw_pellets()                                             # Redibuja capa de pellets (quitando el comido)

    # DIBUJAMOS PACMAN COMO UN CIRCULO AMARILLO
    up(); goto(pacman.x + 10, pacman.y + 10); dot(20, 'yellow')    # Render de Pac-Man centrado en su celda

    # --- Fantasmas ---
    # --- Fantasmas ---
    for gi, (point, course) in enumerate(ghosts):                  # Recorre fantasmas (índice, (posición, dirección))
        # Pasos “base” por nivel (dificultad). Ej.: nivel 1 -> 1 paso, nivel 2 -> 2 pasos...
        g_mult_raw = 1 + max(0, state['level'] - 1) // 1           # (Se mantiene por claridad aunque capamos luego)

        # Pasos actuales de Pac-Man en este tick (puede ser 1 o 2 si está en zona rápida)
        pac_steps = FAST_MULT_PAC if in_fast_zone(pacman) else 1   # Info disponible (no afecta fantasmas)

        # REGLA: los fantasmas NUNCA pueden ser más rápidos que el jugador
        g_mult = min(g_mult_raw, 1)                                # Capados a 1 paso por tick (constante)

        # REGLA: las zonas rápidas NO afectan a los fantasmas (no sumamos nada por zonas)
        # (Quitamos cualquier código tipo: if in_fast_zone(point): g_mult += ...)

        if valid(point + course):                                  # Si puede seguir en su curso actual
            if at_intersection(point):                             # Si está en intersección
                is_hybrid = (gi == 4)                              # El 5º fantasma es híbrido
                course_new = pick_course(point, course, hybrid=is_hybrid)  # Decide nueva ruta
                ghosts[gi][1] = course_new                         # Actualiza su dirección
                move_steps(point, course_new, g_mult)              # Avanza g_mult pasos
            else:
                move_steps(point, course, g_mult)                  # Sigue recto g_mult pasos
        else:                                                      # Si chocaría con pared
            is_hybrid = (gi == 4)                                  # 5º fantasma híbrido
            course_new = pick_course(point, course, hybrid=is_hybrid)      # Elige nueva dirección
            ghosts[gi][1] = course_new                             # Actualiza dirección
            move_steps(point, course_new, g_mult)                  # Avanza g_mult pasos

        # DIBUJAMOS FANTASMAS COMO TRIÁNGULOS DE COLORES
        cx, cy = point.x + 10, point.y + 7                         # Centro del triángulo (ligeramente más abajo)
        draw_triangle(cx, cy, 19, GHOST_COLORS[gi % len(GHOST_COLORS)])  # Triángulo del color del fantasma

    update()                                                       # Refresca la pantalla (tracer(False) activo)

    # Colisión
    for point, _ in ghosts:                                        # Revisa cada fantasma
        if abs(pacman - point) < 20:                               # Si está lo bastante cerca
            writer.goto(-70, 0); writer.color('white')             # Posiciona texto
            writer.write('GAME OVER', align='left', font=('Arial', 16, 'bold'))  # Mensaje de fin
            return                                                 # Detiene el loop (no reprograma siguiente tick)

    ontimer(move, current_tick_ms())                               # Programa el siguiente tick según el nivel

def change(x, y):                                                  # Intenta cambiar la dirección de Pac-Man
    if valid(pacman + vector(x, y)):                               # Solo si la celda al frente es válida
        aim.x = x; aim.y = y                                       # Actualiza la dirección deseada

# ----------------------------- Setup -----------------------------
def init_game():                                                   # Inicializa y lanza el juego
    global pacman                                                  # Vamos a reasignar pacman
    state['pellets_total'] = pellets_info()                        # Calcula pellets iniciales
    state['pellets_left'] = state['pellets_total']                 # Inicializa contador de pendientes

    setup(420, 460, 370, 0)                                        # Crea ventana (ancho, alto, posX, posY)
    hideturtle(); tracer(False)                                    # Oculta cursor; desactiva animación automática
    writer.up(); writer.goto(60, 190); writer.color('white')       # Posiciona HUD
    writer.write(f"Score: {state['score']}  Lvl: {state['level']}")# Dibuja HUD inicial
    listen()                                                       # Activa escucha de teclado
    onkey(lambda: change(BASE_STEP, 0), 'Right')                   # Flecha derecha -> mover derecha
    onkey(lambda: change(-BASE_STEP, 0), 'Left')                   # Flecha izquierda -> mover izquierda
    onkey(lambda: change(0, BASE_STEP), 'Up')                      # Flecha arriba -> mover arriba
    onkey(lambda: change(0, -BASE_STEP), 'Down')                   # Flecha abajo -> mover abajo

    # --- colocar Pac-Man en el centro válido ---
    pacman = center_spawn()                                        # Busca un spawn seguro centrado

    # Dibujar capas estáticas una vez
    draw_maze()                                                    # Dibuja laberinto y zonas rápidas
    draw_pellets()                                                 # Dibuja todos los pellets

    move()                                                         # Arranca el loop del juego
    done()                                                         # Mainloop de Turtle (mantiene ventana)

if __name__ == '__main__':                                         # Punto de entrada del script
    init_game()                                                    # Llama a la inicialización
