from random import choice, random
from freegames import vector
from constantes import BASE_STEP, SMART_GHOSTS
from logica import dist

def pick_course(point, course, pacman, aim, hybrid, valid_fn, chase_prob_val):
    """Elige dirección en intersección. Híbrido: 60% persecución, 40% emboscada."""
    step = BASE_STEP
    options = [vector(step,0), vector(-step,0), vector(0,step), vector(0,-step)]
    options = [v for v in options if valid_fn(point + v)]
    if not options:
        return vector(-course.x, -course.y)

    opposite = vector(-course.x, -course.y)
    if len(options) > 1 and opposite in options:
        options.remove(opposite)

    if hybrid:
        if random() < 0.6:
            target = pacman
        else:
            if aim.x == 0 and aim.y == 0:
                forward = vector(step * 3, 0)
            else:
                a_norm = vector(step if aim.x > 0 else (-step if aim.x < 0 else 0),
                                step if aim.y > 0 else (-step if aim.y < 0 else 0))
                forward = vector(a_norm.x * 3, a_norm.y * 3)
            target = vector(pacman.x + forward.x, pacman.y + forward.y)
        return min(options, key=lambda v: dist(point + v, target))

    if SMART_GHOSTS and random() < chase_prob_val:
        return min(options, key=lambda v: dist(point + v, pacman))
    return choice(options)

def build_ghosts(n, tiles, valid_fn):
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
        if valid_fn(c):
            ghosts.append([c.copy(), choice(dirs)])
    while len(ghosts) < n and ghosts:
        p, d = ghosts[len(ghosts) % len(ghosts)]
        ghosts.append([p.copy(), d.copy()])
    return ghosts
