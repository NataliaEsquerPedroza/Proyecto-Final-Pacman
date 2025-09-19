#!/usr/bin/env bash
# export-commit-logs.sh
# Genera evidencia de commits por integrante en evidence/logs/ como archivos Markdown.
# Requiere ejecutarse dentro de un repositorio Git.

set -euo pipefail

# --- Config ---
OUT_DIR="evidence/logs"
mkdir -p "$OUT_DIR"

# Rango opcional: por ejemplo, "main", "origin/main..HEAD" o fechas con --since/--until
RANGE="${1:-}"

# Verificación mínima
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Este script debe ejecutarse dentro de un repositorio Git."
  exit 1
fi

# Obtener lista única de autores (Nombre <email>)
mapfile -t AUTHORS < <(git log ${RANGE:+$RANGE} --format='%aN <%aE>' | sort -u)

if [ "${#AUTHORS[@]}" -eq 0 ]; then
  echo "No se encontraron commits en el rango especificado."
  exit 0
fi

# Función para sanear email para nombre de archivo
sanitize() {
  # Reemplaza caracteres problemáticos por '_'
  echo "$1" | sed -E 's/[^A-Za-z0-9._-]+/_/g'
}

echo "Generando logs por autor en $OUT_DIR ..."

for AUTHOR in "${AUTHORS[@]}"; do
  # Extraer email entre <...>
  EMAIL="$(echo "$AUTHOR" | sed -n 's/.*<\(.*\)>.*/\1/p')"
  NAME="$(echo "$AUTHOR" | sed -n 's/\(.*\) <.*/\1/p')"
  SAFE_EMAIL="$(sanitize "$EMAIL")"

  FILE="$OUT_DIR/commits_${SAFE_EMAIL}.md"

  {
    echo "# Commits de $NAME <$EMAIL>"
    echo
    echo "> Rango: ${RANGE:-(completo)}"
    echo
    echo "| Hash | Fecha | Título |"
    echo "|------|-------|--------|"

    # Tabla compacta
    git log ${RANGE:+$RANGE} --author="$EMAIL" --no-merges --date=iso \
      --pretty=format:'| `%h` | %ad | %s |'

    echo
    echo "---"
    echo
    echo "## Detalle"
    echo

    # Detalle por commit
    git log ${RANGE:+$RANGE} --author="$EMAIL" --date=iso --no-merges \
      --pretty=format:'- **%h** %ad — %s%n%n%b%n---%n'
  } > "$FILE"

  echo "✓ $FILE"
done

echo "Listo."
