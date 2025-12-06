#!/bin/bash
echo "🜂 Φ-Inject — Applying Theme + Header + Footer + Grid"

for file in $(find . -name "*.html"); do
  echo "→ Updating $file"

  sed -i 's|</head>|  <link rel="stylesheet" href="/theme/system.css">\n  <link rel="stylesheet" href="/theme/phi_theme.css">\n</head>|' "$file"
  sed -i 's|<body>|<body>\n  <!-- Φ-Header -->\n  '"$(cat components/phi-header.html)"'\n  <div class="phi-grid">|' "$file"
  sed -i 's|</body>|  </div>\n  <!-- Φ-Footer -->\n  '"$(cat components/phi-footer.html)"'\n</body>|' "$file"
done

echo "✓ Inject complete."
