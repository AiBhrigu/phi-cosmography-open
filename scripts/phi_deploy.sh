#!/bin/bash
echo "🜂 Φ-Deploy — Deploying to GitHub Pages"

git add .
git commit -m "Φ-Release Engine v2 — Auto-Deploy"
git push

echo "✓ Deploy pushed. Ensure GitHub Pages is set to serve /dist/"
