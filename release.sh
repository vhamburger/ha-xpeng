#!/usr/bin/env bash
set -e

if [ -z "$1" ]; then
  echo "❌ Fehler: Bitte Versionsnummer angeben!"
  echo "Beispiel: ./release.sh 1.0.6"
  exit 1
fi

VERSION="$1"
TAG="v$VERSION"

echo "🚀 Starte Release $TAG..."

# 1. Update version in manifest.json
sed -i '' "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" custom_components/xpeng/manifest.json
echo "✅ manifest.json auf Version $VERSION aktualisiert."

# 2. Git commit & tag
git add .
git commit -m "chore: release $TAG" || echo "Keine uncommitteten Änderungen."
git tag -a "$TAG" -m "Release $TAG"

# 3. Push to GitHub
echo "⬆️ Pushe nach GitHub (Branch & Tag)..."
git push --follow-tags

# 4. GitHub Release via gh CLI erstellen
if command -v gh &> /dev/null; then
  echo "📦 Erstelle offizielles GitHub Release..."
  gh release create "$TAG" --title "$TAG" --generate-notes || echo "⚠️ gh release fehlgeschlagen. Bitte ggf. einmal 'gh auth login' im Terminal ausführen."
fi

echo "🎉 Fertig! Version $TAG ist jetzt live auf GitHub & HACS."
