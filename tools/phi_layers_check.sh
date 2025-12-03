#!/usr/bin/env bash
echo "==============================================="
echo "   Φ-LAYERS / FIELD / TEXT CHECK"
echo "==============================================="

for f in site/css/phi_layers_v80.css \
         site/css/phi_field_v91.css \
         site/css/phi_text_v88.css \
         site/css/phi_rays_v85.css; do
    
    echo "● Checking $f"

    o1=$(grep -o '{' $f | wc -l)
    c1=$(grep -o '}' $f | wc -l)
    if [ "$o1" -ne "$c1" ]; then
        echo "❗ ERROR: unmatched {} in $f"
        exit 1
    fi

    o2=$(grep -o '(' $f | wc -l)
    c2=$(grep -o ')' $f | wc -l)
    if [ "$o2" -ne "$c2" ]; then
        echo "❗ ERROR: unmatched () in $f"
        exit 1
    fi
done

echo "✓ Layers/Text/Field stable."
