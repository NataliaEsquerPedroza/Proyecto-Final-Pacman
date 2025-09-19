# Pac-Man Plus

Versión modernizada del clásico **Pac-Man** en Python.  
Incluye **5º fantasma con IA híbrida**, **zonas rápidas** (verdes) solo para Pac-Man, **dificultad progresiva** y **render sin parpadeo** por capas.

> Estructura actual del repo: `CodigoFinal/`, `CodigoContinuoDraft/`, `__pycache__/`, `README.md`.

---

## Características

- **5º fantasma (IA híbrida):** alterna entre persecución directa (~60%) y emboscada (apunta ~3 celdas por delante de la dirección de Pac-Man) ~40%.
- **Zonas rápidas (verdes):** al pisarlas, **solo Pac-Man** duplica su paso en ese tick; los fantasmas no se aceleran.
- **Dificultad progresiva:** el juego reduce el **tick** (ms entre frames) por nivel y puede **agregar obstáculos** (paredes estratégicas) predefinidos por nivel.
- **Render por capas:** laberinto, pellets y actores (Pac-Man y fantasmas) se dibujan con turtles separadas para evitar parpadeo.

---

## Estructura del repositorio

```
.
├─ CodigoFinal/           # Código listo para jugar (ejecuta aquí el script principal)
├─ CodigoContinuoDraft/   # Prototipos/iteraciones de desarrollo
├─ __pycache__/           # Caché de Python (se genera automáticamente)
└─ README.md              # Este archivo
```

> Dentro de `CodigoFinal/` ejecuta `main.py`
---

## 🔧 Requisitos

- **Python 3.10+**
- Librerías:
  - `turtle` (viene con Python)
  - `freegames` (para `vector` y utilidades)

Instala dependencias:

```bash
pip install freegames
```

*(Opcional, recomendado)* Crear entorno virtual:

```bash
python -m venv .venv
# Windows
.venv\Scriptsctivate
# macOS/Linux
source .venv/bin/activate
```

---

## Ejecución

1. Entra a la carpeta del código final:

```bash
cd CodigoFinal
```

2. Ejecuta el archivo principal (ajusta el nombre exacto):

```bash
python main.py
```

---

## Controles

- **Flechas** del teclado: mover a Pac-Man (↑ ↓ ← →).

---

## ⚙️ Parámetros principales (típicos en el código)

> Ajusta estos valores en el archivo de configuración o en constantes del script (según tu organización en `CodigoFinal/`):

- `GHOSTS_N = 5` → cantidad de fantasmas (el 5º es híbrido).
- `BASE_STEP = 5` → tamaño del paso (múltiplo de 5 para alinear a la grilla).
- `BASE_TICK_MS = 95` → milisegundos por tick (baja con el nivel, hasta `MIN_TICK_MS`).
- `TICK_DECREMENT = 5` / `MIN_TICK_MS = 45` → ajuste de velocidad por nivel y límite mínimo.
- `FAST_MULT_PAC = 2` → en zonas verdes, Pac-Man da 2 pasos por tick (fantasmas **no** se aceleran).
- `PELLETS_PER_LEVEL = 35` → pellets para subir de nivel.
- `BASE_CHASE_PROB = 0.75` / `CHASE_INCREMENT = 0.05` → agresividad de persecución de los fantasmas.

> **¿Qué es un *tick*?** Es el intervalo de actualización del juego (un “paso” del bucle). En cada tick se procesa movimiento, colisiones y se reprograma el siguiente con `ontimer`.

---

## Resumen técnico

- **Grilla 20×20 (`tiles`)**: `0` = pared, `1` = pellet, `2` = vacío.  
- **Zonas rápidas (`FAST_ZONE_IDX`)**: celdas transitables con borde verde; afectan **solo a Pac-Man**.  
- **Progresión por nivel**: al comer pellets, sube `state['level']` y se **aplican obstáculos** predefinidos (se redibujan capas estáticas).  
- **IA híbrida (fantasma #5)**: en intersecciones decide entre **perseguir** a Pac-Man o **emboscar** un punto adelantado en la dirección actual de Pac-Man (`aim`).  
- **Velocidad de fantasmas**: **capada a 1 paso por tick** (no pueden ser más rápidos que el jugador y no reciben bonus por zonas rápidas).  
- **Render**: `draw_maze()` (una vez), `draw_pellets()` (al comer), y turtle principal para Pac-Man/fantasmas cada frame.

---
