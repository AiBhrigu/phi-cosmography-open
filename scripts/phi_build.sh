#!/bin/bash
echo "🜂 Φ-Build v2 — Creating clean /dist"

rm -rf dist
mkdir -p dist

# Копируем только файлы проекта, исключая dist, scripts, .git, node_modules
rsync -av --exclude='dist' --exclude='scripts' --exclude='.git' --exclude='node_modules' ./ dist/

echo "✓ Build complete (rsync-safe)."
