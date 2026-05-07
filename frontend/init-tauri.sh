#!/usr/bin/env bash

# init-tauri.sh  —  Inicialización automática de Tauri para Net Management
# Ejecutar desde la carpeta frontend/: bash init-tauri.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "▶  Instalando @tauri-apps/cli como devDependency..."
npm install --save-dev @tauri-apps/cli

echo "▶  Inicializando Tauri (modo no interactivo)..."
npx tauri init \
  --app-name        "Net Management" \
  --window-title    "Net Management" \
  --dist-dir        "../dist" \
  --dev-url         "http://localhost:5173" \
  --frontend-dist   "../dist" \
  --before-dev-command  "npm run dev" \
  --before-build-command "npm run build"

# Patch tauri.conf.json para ajustes extra
CONF="src-tauri/tauri.conf.json"
if [ -f "$CONF" ]; then
  echo "▶  Ajustando $CONF con jq..."
  if command -v jq &>/dev/null; then
    TMP=$(mktemp)
    jq '
      .productName = "Net Management" |
      .version     = "0.1.0" |
      .identifier  = "com.netmanagement.app" |
      .build.beforeDevCommand   = "npm run dev" |
      .build.beforeBuildCommand = "npm run build" |
      .build.frontendDist       = "../dist" |
      .build.devUrl             = "http://localhost:5173"
    ' "$CONF" > "$TMP" && mv "$TMP" "$CONF"
    echo "   ✓ tauri.conf.json actualizado."
  else
    echo "   ⚠  jq no encontrado — revisa $CONF manualmente si es necesario."
  fi
fi

# Añadir script tauri al package.json
if command -v jq &>/dev/null; then
  echo "▶  Añadiendo script 'tauri' a package.json..."
  TMP=$(mktemp)
  jq '.scripts.tauri = "tauri"' package.json > "$TMP" && mv "$TMP" package.json
  echo "   ✓ Script añadido. Usa: npm run tauri dev / npm run tauri build"
fi

echo ""
echo "✅  Tauri inicializado correctamente."
echo ""
echo "  Próximos pasos:"
echo "    • Desarrollo:   cd frontend && npm run tauri dev"
echo "    • Compilar:     cd frontend && npm run tauri build"
echo "    • Crear release: git tag v1.0.0 && git push origin v1.0.0"
