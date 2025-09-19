---
title: Pac-Man Plus
layout: default
---

# Pac-Man Plus

Versión modernizada del clásico **Pac-Man** en Python.

- **5º fantasma con IA híbrida**
- **Zonas rápidas (verdes)** solo para Pac‑Man
- **Dificultad progresiva** (tick dinámico + obstáculos por nivel)
- **Render por capas** (sin parpadeo)

> Este sitio está pensado para GitHub Pages: coloca esta carpeta en `docs/` y habilita Pages desde la configuración del repositorio.

---

## 🎮 Cómo jugar

### Requisitos
- Python **3.10+**
- Librería `freegames` (para `vector` y utilidades)
- `turtle` viene con Python

```bash
pip install freegames
```

> (Recomendado) Usa un entorno virtual:
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### Ejecutar
Desde la carpeta del juego (p. ej. `CodigoFinal/`):

```bash
python main.py
# o el archivo principal que incluya la función init_game()
```

Controles: flechas **↑ ↓ ← →** para mover a Pac‑Man.

---

## 🧩 Características clave

- **IA híbrida (fantasma #5):** en intersecciones decide entre persecución directa (~60%) y emboscada (~40%) hacia un punto ~3 celdas por delante en la dirección actual de Pac‑Man.
- **Zonas rápidas (FAST_ZONE_IDX):** celdas con borde verde; **solo Pac‑Man** duplica su paso cuando las pisa (si la dirección es válida). Los fantasmas **no** se aceleran ni superan al jugador.
- **Progresión por nivel:** se incrementa el nivel conforme se comen pellets; se reduce el `tick` (ms) y se pueden **activar obstáculos** (nuevas paredes) por nivel.
- **Render por capas:** se dibuja una sola vez el laberinto y zonas; los pellets se redibujan solo cuando cambian; Pac‑Man y fantasmas se actualizan cada frame.

---

## ⚙️ Parámetros principales (ejemplo)

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `GHOSTS_N` | Número de fantasmas (el 5º es híbrido) | `5` |
| `BASE_STEP` | Paso base (alineado a grilla de 20px) | `5` |
| `BASE_TICK_MS` | Milisegundos por *tick* inicial | `95` |
| `TICK_DECREMENT` | Reducción de ms por nivel | `5` |
| `MIN_TICK_MS` | Límite inferior del *tick* | `45` |
| `FAST_MULT_PAC` | Multiplicador en zonas rápidas (Pac‑Man) | `2` |
| `PELLETS_PER_LEVEL` | Pellets necesarios para subir de nivel | `35` |
| `BASE_CHASE_PROB` | Prob. base de persecución IA | `0.75` |
| `CHASE_INCREMENT` | Incremento de persecución por nivel | `0.05` |

> **Tick:** intervalo de actualización del juego. En cada tick se procesa movimiento, colisiones y se programa el siguiente con `ontimer()`.

---

## 🧠 Resumen técnico

- **Mapa 20×20 (`tiles`)**: `0` pared, `1` pellet, `2` vacío.
- **Zonas rápidas**: conjunto `FAST_ZONE_IDX` con índices de celdas transitables.
- **IA de fantasmas**: evita reversas, respeta celdas válidas, y usa distancia a un `target` (Pac‑Man o punto de emboscada) para elegir dirección.
- **Velocidad de fantasmas**: limitado a **1 paso por tick** (nunca más rápidos que el jugador; no afectados por zonas rápidas).
- **Capas**: `draw_maze()` (una vez), `draw_pellets()` (cuando cambian), y actores por frame.

---

## 🧹 Estilo y calidad

Se recomienda:
- **Black** (formato), **Ruff** (lint), **pre‑commit** (hooks).
- Docstrings estilo Google.

Ejemplo `pyproject.toml`:

```toml
[tool.black]
line-length = 88

[tool.ruff]
line-length = 88
select = ["E","F","I","N","D"]
ignore = ["E203","W503"]
```

Ejecutar:
```bash
pip install black ruff pre-commit
pre-commit install
pre-commit run -a
```

---

## 📝 Convenciones de commits

Sugerencia: **Conventional Commits**.

```
feat(ghost-ai): agrega 5º fantasma híbrido
fix(colisiones): evita falsa colisión en esquinas
docs(readme): instrucciones de ejecución y calidad
```

---

## 🧾 Evidencia (logs por integrante)

Usa el script `scripts/export-commit-logs.sh` para generar
`evidence/logs/commits_<autor>.md` con el historial individual.

```bash
chmod +x scripts/export-commit-logs.sh
./scripts/export-commit-logs.sh
```

---

## 📄 Licencia

MIT (o la que defina el equipo). Añade `LICENSE` si el curso lo solicita.
