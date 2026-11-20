#!/usr/bin/env bash
# setup_blender.sh — install Blender's Python module (bpy) for the Blender
# Short pipeline in a fresh cloud container. bpy gets its own venv because it
# pins numpy 1.26, which would break Kokoro (numpy >= 2) in the main env.
# Cycles (CPU) needs nothing else; EEVEE would also need libegl1, but on this
# CPU-only machine it is slower than Cycles, so it is not installed here.
set -euo pipefail
VENV=/root/.venvs/blender
if [ ! -x "$VENV/bin/python" ]; then
    python3 -m venv "$VENV"
fi
"$VENV/bin/pip" install -q bpy
"$VENV/bin/python" -c "import bpy; print('bpy', bpy.app.version_string, 'ready in', '$VENV')"
