#!/usr/bin/env bash
# Glyph system launcher with multi-Python runtime discovery
export PYTHONPATH="/usr/share/glyph:${PYTHONPATH}"

# Fall back to software rendering if running in a VM without 3D acceleration
if [ -z "$LIBGL_ALWAYS_SOFTWARE" ] && ! ls /dev/dri/renderD* >/dev/null 2>&1; then
    export LIBGL_ALWAYS_SOFTWARE=1
    if [ -z "$GSK_RENDERER" ]; then
        export GSK_RENDERER=cairo
    fi
fi

# Locate Python 3 interpreter (>= 3.10) with PIL and gi support
PYTHON_CMD=""
for py in python3 python3.13 python3.12 python3.11 python3.10 /usr/bin/python3; do
    if command -v "$py" >/dev/null 2>&1; then
        if "$py" -c "import sys, PIL, gi; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>/dev/null; then
            PYTHON_CMD="$py"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    PYTHON_CMD="python3"
fi

exec "$PYTHON_CMD" -m glyph "$@"

