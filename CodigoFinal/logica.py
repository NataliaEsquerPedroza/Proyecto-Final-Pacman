from math import sqrt
from freegames import floor, vector
from constantes import (BASE_STEP, BASE_TICK_MS, TICK_DECREMENT, MIN_TICK_MS,
                    PELLETS_PER_LEVEL, BASE_CHASE_PROB, CHASE_INCREMENT)

def offset(point):
    x = (floor(point.x, 20) + 200) / 20
    y = (180 - floor(point.y, 20)) / 20
    return int(x + y * 20)

def valid(point, tiles):
    i = offset(point)
    if tiles[i] == 0:
        return False
    i = offset(point + 19)
    if tiles[i] == 0:
        return False
    return point.x % 20 == 0 or point.y % 20 == 0

def at_intersection(p): 
    return p.x % 20 == 0 and p.y % 20 == 0

def dist(a, b):
    return sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)

def in_fast_zone(point, tiles, fast_idx):
    return offset(point) in fast_idx

def chase_prob(state):
    return min(0.95, BASE_CHASE_PROB + (state['level'] - 1) * CHASE_INCREMENT)

def current_tick_ms(state):
    return max(MIN_TICK_MS, BASE_TICK_MS - (state['level'] - 1) * TICK_DECREMENT)

def level_from_score(state):
    eaten = state['pellets_total'] - state['pellets_left']
    return max(1, 1 + eaten // PELLETS_PER_LEVEL)

def center_spawn(tiles):
    candidates = [
        vector(-20, -20), vector(0, -20), vector(-20, 0), vector(0, 0),
        vector(-40, -20), vector(20, -20), vector(-20, -40), vector(-20, 20),
        vector(20, 0), vector(0, 20), vector(-40, 0), vector(0, -40)
    ]
    for c in candidates:
        if valid(c, tiles):
            return c
    return None

def move_steps(entity_pos, move_vec, steps, tiles):
    for _ in range(max(1, int(steps))):
        if valid(entity_pos + move_vec, tiles):
            entity_pos.move(move_vec)
        else:
            break
