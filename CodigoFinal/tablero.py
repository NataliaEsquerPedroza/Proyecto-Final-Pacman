# Mapa, zonas rápidas y obstáculos por nivel

# ----------------------------- LABERINTO (20x20) -----------------------------
# 0 = pared, 1 = pellet, 2 = vacío
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

# ----------------------------- ZONAS RÁPIDAS -----------------------------
FAST_ZONE_IDX = set()

def _add_fast_rect(ix, iy, w, h):
    for dy in range(h):
        for dx in range(w):
            x = ix + dx
            y = iy + dy
            idx = x + y * 20
            if 0 <= idx < len(tiles) and tiles[idx] != 0:
                FAST_ZONE_IDX.add(idx)

# Pinta zonas rápidas (verde)
_add_fast_rect(1, 1, 6, 1)
_add_fast_rect(7, 3, 6, 1)
_add_fast_rect(3, 5, 10, 1)
_add_fast_rect(1, 11, 18, 1)
_add_fast_rect(2, 15, 6, 1)
_add_fast_rect(11, 15, 7, 1)

# ----------------------------- OBSTÁCULOS POR NIVEL -----------------------------
LEVEL_OBSTACLES = {
    2: [8 + 9*20, 10 + 9*20, 12 + 7*20, 3 + 13*20],
    3: [6 + 5*20, 13 + 5*20, 7 + 11*20, 12 + 11*20, 9 + 15*20],
    4: [4 + 3*20, 15 + 3*20, 5 + 9*20, 14 + 9*20, 8 + 11*20],
}

def count_pellets(t):
    return sum(1 for v in t if v == 1)

def apply_level_obstacles(level, t, state, levels_applied):
    """Convierte índices a pared una sola vez por nivel. Devuelve True si hubo cambios."""
    if level in levels_applied:
        return False
    changes = LEVEL_OBSTACLES.get(level, [])
    for idx in changes:
        if 0 <= idx < len(t) and t[idx] != 0:
            if t[idx] == 1:
                state['pellets_left'] = max(0, state['pellets_left'] - 1)
            t[idx] = 0
    levels_applied.add(level)
    return bool(changes)
