#!/usr/bin/env bash
set -e

echo "===================================================="
echo "          Φ-BUILD ENGINE v1.1 — ORION"
echo "   Auto-compile · Minify · Bundle · Release"
echo "===================================================="

DIST="dist"
rm -rf "$DIST"
mkdir -p "$DIST"

###############################################
# 1) COPY SITE STRUCTURE
###############################################
echo "● Copying site structure..."
cp -r site/* "$DIST"/

###############################################
# 2) INLINE-MINIFY CSS/JS/HTML
###############################################

mini_css() {
  sed 's:/\*.*\*/::g' | tr -d '\n' | tr -s ' '
}

mini_js() {
  tr -d '\n' | tr -s ' '
}

mini_html() {
  sed 's/<!--.*-->//g' | tr -d '\n' | tr -s ' '
}

echo "● Minifying CSS..."
find "$DIST" -type f -name "*.css" | while read f; do
  mini_css < "$f" > "$f.min"
  mv "$f.min" "$f"
done

echo "● Minifying JS..."
find "$DIST" -type f -name "*.js" | while read f; do
  mini_js < "$f" > "$f.min"
  mv "$f.min" "$f"
done

echo "● Minifying HTML..."
find "$DIST" -type f -name "*.html" | while read f; do
  mini_html < "$f" > "$f.min"
  mv "$f.min" "$f"
done

###############################################
# 3) SUNCORE / FIELD / LAYERS LINK CHECK
###############################################
echo "● Checking Φ-links integrity..."

required_css=(
  "css/phi_suncore_v90.css"
  "css/phi_field_v91.css"
  "css/phi_layers_v80.css"
  "css/phi_text_v88.css"
  "css/phi_rays_v85.css"
)

for css in "${required_css[@]}"; do
  if [ ! -f "$DIST/$css" ]; then
    echo "❗ ERROR: Missing $css in build!"
    exit 1
  fi
done

echo "✓ All required φ-modules present."

###############################################
# 4) RELEASE PACKAGE
###############################################
STAMP=$(date +%Y%m%d_%H%M)
PKG="phi_cosmography_build_$STAMP.zip"

echo "● Creating release: $PKG"
cd "$DIST"
zip -r "../$PKG" . >/dev/null
cd ..

echo "===================================================="
echo "             Φ-BUILD COMPLETED SUCCESSFULLY"
echo "   → dist/"
echo "   → $PKG (ready to upload)"
echo "===================================================="
