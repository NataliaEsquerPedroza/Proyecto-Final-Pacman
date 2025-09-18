from freegames import vector

# ----------------------------- CONSTANTES -----------------------------
GHOSTS_N = 5                 # Número de fantasmas (el 5º es híbrido)
BASE_STEP = 5                # Paso base (múltiplo de 5 para alinear a grilla)
PACMAN_START = vector(80, -120)  # Fallback si no hay spawn central válido

SMART_GHOSTS = True          # IA de persecución
BASE_CHASE_PROB = 0.75       # Prob. base de persecución

BASE_TICK_MS = 95            # ms entre ticks (baja por nivel)
TICK_DECREMENT = 5           # -5ms por nivel
MIN_TICK_MS = 45             # mínimo de ms por tick

FAST_MULT_PAC = 2            # Pac-Man corre el doble en zonas verdes
PELLETS_PER_LEVEL = 35       # Pellets por nivel
CHASE_INCREMENT = 0.05       # +5% agresividad por nivel

# Colores de fantasmas
GHOST_COLORS = ['red', 'pink', 'cyan', 'orange', 'purple']
