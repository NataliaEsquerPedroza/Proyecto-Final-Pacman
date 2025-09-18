from turtle import setup, tracer, listen, onkey, ontimer, done, update
from freegames import vector

import constantes as C
import tablero as T
import graficar as G
import logica as L
import fantasmas as F

# ----------------------------- ESTADO -----------------------------
state = {
    'score': 0,
    'level': 1,
    'pellets_total': 0,
    'pellets_left': 0,
    'levels_applied': set(),
}

pacman = vector(0, 0)
aim = vector(C.BASE_STEP, 0)
ghosts = []

def change(dx, dy):
    global aim
    if L.valid(pacman + vector(dx, dy), T.tiles):
        aim.x = dx
        aim.y = dy

def move():
    # Nivel por progreso
    new_level = L.level_from_score(state)
    if new_level != state['level']:
        state['level'] = new_level

    # Obstáculos por nivel (si hubo cambios, redibuja capas estáticas)
    changed = T.apply_level_obstacles(state['level'], T.tiles, state, state['levels_applied'])
    if changed:
        G.draw_maze(T.tiles, T.FAST_ZONE_IDX)
        G.draw_pellets(T.tiles)

    G.write_hud(state['score'], state['level'])

    # Limpiar SOLO actores
    G.clear_actors()

    # --- Pac-Man ---
    pac_steps = C.FAST_MULT_PAC if L.in_fast_zone(pacman, T.tiles, T.FAST_ZONE_IDX) else 1
    if aim.x != 0 or aim.y != 0:
        L.move_steps(pacman, vector(aim.x, aim.y), pac_steps, T.tiles)

    # Comer pellet
    idx = L.offset(pacman)
    if T.tiles[idx] == 1:
        T.tiles[idx] = 2
        state['score'] += 1
        state['pellets_left'] -= 1
        G.draw_pellets(T.tiles)

    # Dibujar Pac-Man
    G.draw_pacman(pacman.x + 10, pacman.y + 10, 20)

    # --- Fantasmas ---
    for gi, (point, course) in enumerate(ghosts):
        # NUNCA más rápidos que el jugador y NO afectados por zonas rápidas
        g_mult = 1  # fijo

        # Decidir curso en intersección / choque
        if L.valid(point + course, T.tiles):
            if L.at_intersection(point):
                is_hybrid = (gi == 4)
                new_course = F.pick_course(
                    point, course, pacman, aim, is_hybrid,
                    valid_fn=lambda p: L.valid(p, T.tiles),
                    chase_prob_val=L.chase_prob(state)
                )
                ghosts[gi][1] = new_course
                L.move_steps(point, new_course, g_mult, T.tiles)
            else:
                L.move_steps(point, course, g_mult, T.tiles)
        else:
            is_hybrid = (gi == 4)
            new_course = F.pick_course(
                point, course, pacman, aim, is_hybrid,
                valid_fn=lambda p: L.valid(p, T.tiles),
                chase_prob_val=L.chase_prob(state)
            )
            ghosts[gi][1] = new_course
            L.move_steps(point, new_course, g_mult, T.tiles)

        # Dibujar fantasma
        G.draw_ghost(point.x + 10, point.y + 10, gi)

    update()

    # Colisión
    for point, _ in ghosts:
        if abs(pacman - point) < 20:
            G.writer.goto(-70, 0)
            G.writer.color('white')
            G.writer.write('GAME OVER', align='left', font=('Arial', 16, 'bold'))
            return

    ontimer(move, L.current_tick_ms(state))

def init_game():
    global pacman, ghosts
    # Ventana y capas
    setup(420, 460, 370, 0)
    tracer(False)
    G.init_layers()

    # HUD inicial
    G.write_hud(state['score'], state['level'])

    # Teclado
    listen()
    onkey(lambda: change(C.BASE_STEP, 0), 'Right')
    onkey(lambda: change(-C.BASE_STEP, 0), 'Left')
    onkey(lambda: change(0, C.BASE_STEP), 'Up')
    onkey(lambda: change(0, -C.BASE_STEP), 'Down')

    # Pellets
    state['pellets_total'] = T.count_pellets(T.tiles)
    state['pellets_left'] = state['pellets_total']

    # Spawn centrado
    spawn = L.center_spawn(T.tiles)
    pacman = spawn if spawn is not None else C.PACMAN_START.copy()

    # Capas estáticas
    G.draw_maze(T.tiles, T.FAST_ZONE_IDX)
    G.draw_pellets(T.tiles)

    # Fantasmas
    ghosts[:] = F.build_ghosts(C.GHOSTS_N, T.tiles, valid_fn=lambda p: L.valid(p, T.tiles))

    # Loop
    move()
    done()

if __name__ == '__main__':
    init_game()
