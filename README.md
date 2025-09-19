# Pac-Man Plus

Versión modernizada del clásico **Pac-Man** hecha en Python.  
Incluye **5º fantasma con IA híbrida**, **zonas rápidas verdes** y **dificultad progresiva**.  
Render sin parpadeos (capas separadas), sprites simples (Pac-Man circular y fantasmas triangulares) y código modular.

---

## Tabla de contenidos
- [Características](#características)
- [Tecnologías](#tecnologías)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Ejecución](#ejecución)
- [Controles](#controles)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Parámetros configurables](#parámetros-configurables)
- [Cómo funciona (resumen técnico)](#cómo-funciona-resumen-técnico)
- [Calidad de código (PEP 8)](#calidad-de-código-pep-8)
- [Convenciones de commits](#convenciones-de-commits)
- [Evidencia (logs de commits por integrante)](#evidencia-logs-de-commits-por-integrante)
- [Documentación (GitHub Pages)](#documentación-github-pages)
- [Roadmap](#roadmap)
- [Licencia](#licencia)

---

## Características
- **5º fantasma (IA híbrida)**: alterna entre persecución directa (60%) y emboscada a ~3 celdas por delante de Pac-Man (40%).
- **Zonas rápidas (verdes)**: *solo* Pac-Man duplica su paso al pisarlas.
- **Dificultad progresiva**: el juego reduce el tiempo por *tick* y aplica obstáculos (paredes estratégicas) por nivel.
- **Render por capas**: laberinto, pellets y actores se dibujan en *turtles* distintas para evitar parpadeo.
- **Código modular**: separado en `config`, `board`, `logic`, `ghosts`, `draw` y `main`.

---

## Tecnologías
- **Python 3.10+**
- **turtle** (estándar de Python)
- **freegames** (para `vector` y utilidades)
- **black** + **ruff** + **pre-commit** (formato/linting)

---

## Requisitos
```bash
python --version        # 3.10 o superior
pip install freegames black ruff pre-commit
```

*(Opcional, recomendado) entorno virtual:*
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

---

## Instalación
Clona el repositorio y coloca los archivos del proyecto en la raíz.  
Si usarás las guías de calidad, añade también `pyproject.toml`, `pre-commit-config.yaml`, `.gitmessage.txt`, `CONTRIBUTING.md` y la carpeta `docs/`.

---

## Ejecución
```bash
python main.py
```

---

## Controles
- **Flechas**: mover a Pac-Man (↑ ↓ ← →).

---

## Estructura del proyecto
```
.
├─ main.py
├─ config.py
├─ board.py
├─ logic.py
├─ ghosts.py
├─ draw.py
├─ scripts/
│  └─ export-commit-logs.sh
├─ docs/
│  ├─ index.md
│  └─ commit_conventions.md
├─ .gitmessage.txt
├─ pyproject.toml
├─ pre-commit-config.yaml
└─ evidence/
   └─ logs/   (se genera con el script)
```

**Breve descripción**
- `config.py`: constantes y parámetros de juego (pasos, ticks, agresividad, etc.).
- `board.py`: mapa (`tiles`), zonas rápidas y obstáculos por nivel.
- `logic.py`: utilidades de grilla, colisiones, *ticks* y progresión.
- `ghosts.py`: construcción de fantasmas y decisión de IA (incluye el híbrido).
- `draw.py`: rendering por capas (`maze_t`, `pellets_t` y la turtle principal para actores) + HUD.
- `main.py`: punto de entrada; loop principal y *bindings* de teclado.
- `scripts/export-commit-logs.sh`: genera evidencias de commits por autor.

---

## Parámetros configurables
(editar en `config.py`)

- `GHOSTS_N = 5` → número de fantasmas (el 5º es híbrido).
- `BASE_STEP = 5` → tamaño del paso (múltiplo de 5 para alinear a la grilla).
- `BASE_TICK_MS = 95` → milisegundos por *tick* inicial (↓ con el nivel).
- `TICK_DECREMENT = 5` / `MIN_TICK_MS = 45` → cuánto acelera por nivel y límite mínimo.
- `FAST_MULT_PAC = 2` → en zonas verdes, Pac-Man da 2 pasos por *tick* (fantasmas no se aceleran).
- `PELLETS_PER_LEVEL = 35` → pellets para subir de nivel.
- `BASE_CHASE_PROB = 0.75` / `CHASE_INCREMENT = 0.05` → agresividad de fantasmas (probabilidad de perseguir).

> **¿Qué es un *tick*?** Es el intervalo de actualización del juego (un “paso” del bucle).  
> En cada *tick* se procesa movimiento, colisiones y se reprograma el siguiente con `ontimer`.

---

## Cómo funciona (resumen técnico)
- **Grilla 20×20 (`tiles`)**: `0` pared, `1` pellet, `2` vacío.
- **Zonas rápidas (`FAST_ZONE_IDX`)**: celdas no-pared marcadas con borde verde; **solo** afectan a Pac-Man.
- **Progresión**: al comer pellets, sube `level` y se aplican obstáculos predefinidos por nivel (se redibujan capas estáticas).
- **IA híbrida** (5º fantasma): en intersecciones decide entre perseguir a Pac-Man o emboscar el punto 3 celdas hacia `aim`.
- **Velocidad de fantasmas**: capados a **1 paso por tick** (nunca más rápidos que el jugador y sin bonus por zonas rápidas).
- **Render**: `draw_maze()` (una vez), `draw_pellets()` (cuando cambian pellets) y turtle principal para Pac-Man/fantasmas cada frame.

---

## Calidad de código (PEP 8)
Formatea y lintéalo todo:
```bash
pre-commit install
pre-commit run -a
```
Configuración en `pyproject.toml` (Black, Ruff).  
Docstrings estilo Google (configurado en Ruff).

---

## Convenciones de commits
Usamos **Conventional Commits** (en español).  
Plantilla: `.gitmessage.txt` (actívala con `git config commit.template .gitmessage.txt`).

**Tipos principales**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`.

**Ejemplos**
```
feat(ghost-ai): agrega 5º fantasma híbrido
fix(colisiones): evita falsa colisión en esquinas
docs(readme): instrucciones de ejecución y calidad
```

Más detalles en `docs/commit_conventions.md`.

---

## Evidencia (logs de commits por integrante)
Genera archivos **por autor** en `evidence/logs/`:

```bash
chmod +x scripts/export-commit-logs.sh
./scripts/export-commit-logs.sh
``

Se crean `commits_<correo_sanitizado>.md` con el historial individual  
(hash corto, fecha ISO, título y cuerpo). Sube esa carpeta al repo.

---

## Documentación (GitHub Pages)
1. Asegúrate de tener `docs/index.md` y (opcional) `docs/_config.yml` con un tema Jekyll.
2. En el repo: **Settings → Pages → Build and deployment → Source: “Deploy from a branch”**.  
   Branch: `main` (o el que uses), Folder: `/docs`.

---

## Roadmap
- Sprites “fantasma” con faldón ondulado (SVG/paths con turtle).
- Fruta bonus y “power pellets”.
- Sonidos (`winsound` o `pygame`).
- Niveles adicionales cargados desde archivo de mapa.

---

## Licencia
Este proyecto puede publicarse bajo **MIT** (o la que defina el equipo).  
Incluye un archivo `LICENSE` si el curso lo requiere.
