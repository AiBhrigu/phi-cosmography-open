#!/bin/bash
echo "🜂 Φ-Build — Generating /dist"

rm -rf dist/*
mkdir -p dist

cp -r . dist/

echo "✓ Build complete."
