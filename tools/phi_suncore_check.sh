#!/usr/bin/env bash

CSS="site/css/phi_suncore_v90.css"

echo "==============================================="
echo "     Φ-SUNCORE INTEGRITY CHECK"
echo "==============================================="

if grep -q "EOF" $CSS; then
  echo "❗ ERROR: Found 'EOF' inside CSS — broken heredoc"
  exit 1
fi

# проверяем закрытие radial-gradient
if ! grep -q "radial-gradient" $CSS; then
  echo "❗ ERROR: radial-gradient missing"
  exit 1
fi

# проверяем баланс ( ) и { }
o1=$(grep -o '(' $CSS | wc -l)
c1=$(grep -o ')' $CSS | wc -l)
if [ "$o1" -ne "$c1" ]; then
  echo "❗ ERROR: unmatched parentheses in SunCore"
  exit 1
fi

o2=$(grep -o '{' $CSS | wc -l)
c2=$(grep -o '}' $CSS | wc -l)
if [ "$o2" -ne "$c2" ]; then
  echo "❗ ERROR: unmatched braces in SunCore"
  exit 1
fi

echo "✓ SunCore stable."
