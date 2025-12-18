#!/usr/bin/env bash
set -euo pipefail

HOOK_DIR=".git/hooks"
mkdir -p "$HOOK_DIR"

cat > "$HOOK_DIR/pre-commit" <<'H'
#!/usr/bin/env bash
set -euo pipefail
[ -x ./tools/preflight.sh ] && ./tools/preflight.sh
H
chmod +x "$HOOK_DIR/pre-commit"

cat > "$HOOK_DIR/pre-push" <<'H'
#!/usr/bin/env bash
set -euo pipefail
[ -x ./tools/preflight.sh ] && ./tools/preflight.sh
H
chmod +x "$HOOK_DIR/pre-push"

echo "OK: installed hooks:"
ls -la "$HOOK_DIR/pre-commit" "$HOOK_DIR/pre-push"
