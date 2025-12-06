#!/usr/bin/env bash
echo "==============================================="
echo "   Φ-AUTOVALIDATOR v1.0 — CSS/HTML/JS CHECK"
echo "==============================================="

ROOT="site"

# ---------- 1) Проверка CSS ----------
echo ""
echo "▶ Checking CSS files..."
for f in $(find $ROOT/css -type f -name "*.css"); do
    echo "● $f"

    # Проверка незакрытых скобок
    open_curly=$(grep -o '{' "$f" | wc -l)
    close_curly=$(grep -o '}' "$f" | wc -l)

    if [ "$open_curly" -ne "$close_curly" ]; then
        echo "   ❗ ERROR: Unmatched { } in $f"
    fi

    # Проверка незакрытых скобок ()
    open_par=$(grep -o '(' "$f" | wc -l)
    close_par=$(grep -o ')' "$f" | wc -l)

    if [ "$open_par" -ne "$close_par" ]; then
        echo "   ❗ ERROR: Unmatched ( ) in $f"
    fi

    # Поймать мусор после EOF
    if grep -q "EOF" "$f"; then
        echo "   ⚠ WARNING: 'EOF' sequence detected inside real CSS (possible broken heredoc)"
    fi
done

# ---------- 2) Проверка HTML ----------
echo ""
echo "▶ Checking HTML..."
for f in $(find $ROOT -type f -name "*.html"); do
    echo "● $f"

    div_open=$(grep -o "<div" "$f" | wc -l)
    div_close=$(grep -o "</div>" "$f" | wc -l)

    if [ "$div_open" -ne "$div_close" ]; then
        echo "   ❗ ERROR: Unbalanced <div> tags"
    fi

    # Дубли φ-sun-core
    count=$(grep -c 'phi-sun-core' "$f")
    if [ "$count" -gt 1 ]; then
        echo "   ⚠ WARNING: duplicated phi-sun-core blocks"
    fi
done

# ---------- 3) Проверка JS ----------
echo ""
echo "▶ Checking JS files..."
for f in $(find $ROOT/js -type f -name "*.js"); do
    echo "● $f"

    o1=$(grep -o '{' "$f" | wc -l)
    c1=$(grep -o '}' "$f" | wc -l)
    if [ "$o1" -ne "$c1" ]; then
        echo "   ❗ ERROR: Unmatched JS {}"
    fi
done

echo ""
echo "==============================================="
echo "       Φ-AUTOVALIDATOR COMPLETED"
echo "==============================================="
