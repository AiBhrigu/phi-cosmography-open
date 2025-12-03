#!/usr/bin/env bash

echo "==============================================="
echo "     Φ-CLEANER v1.0 — Backup & Duplicate purge"
echo "==============================================="

# чистим старые автослепки
find site -type d -name "_backup_*" -exec rm -rf {} +

# удаляем все файлы вида index_backup_*.html
find site -type f -name "index_backup_*.html" -delete

# чистим дубликаты SunCore
find site/css -type f -name "phi_suncore_v*.css" ! -name "phi_suncore_v90.css" -delete

echo "Cleanup completed."
