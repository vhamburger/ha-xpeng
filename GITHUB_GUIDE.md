# 🚀 GitHub Push & Release Anleitung für `ha-xpeng`

Diese Anleitung führt dich Schritt für Schritt durch das Veröffentlichen des Repositories auf GitHub, damit du (und die Community) es direkt via HACS installieren könnt.

---

## Schritt 1: Git initialisieren & ersten Commit erstellen

Öffne ein Terminal auf deinem Mac und führe folgende Befehle aus:

```bash
cd /Users/valentin/Documents/Code/Apps/HomeAssistant/ha-xpeng

# 1. Git Repository initialisieren
git init

# 2. Standard-Branch auf main setzen
git branch -M main

# 3. Alle Dateien stagen (.gitignore schützt sensible/große Daten)
git add .

# 4. Ersten Commit erstellen
git commit -m "feat: initial release of XPENG Vehicles integration for Home Assistant"
```

---

## Schritt 2: Repository auf GitHub erstellen & pushen

### Variante A: Mit dem GitHub CLI (`gh`) – Am schnellsten!
Falls du das `gh` Tool installiert hast, geht alles mit einem einzigen Befehl:

```bash
gh repo create ha-xpeng --public --source=. --remote=origin --push
```

---

### Variante B: Manuell über den Browser (github.com)

1. Gehe im Browser auf [github.com/new](https://github.com/new).
2. **Repository name:** `ha-xpeng`
3. **Visibility:** `Public` (öffentlich, damit HACS darauf zugreifen kann).
4. **Wichtig:** *Initialize this repository with...* (README, .gitignore etc.) **alles DEAKTIVIERT lassen** (wir haben bereits alles lokal).
5. Klicke auf **Create repository**.
6. Führe im Terminal folgende Befehle aus (ersetze `<dein-github-username>` durch deinen GitHub-Namen):

```bash
# Per HTTPS:
git remote add origin https://github.com/<dein-github-username>/ha-xpeng.git

# ODER per SSH (falls du SSH-Keys nutzt):
git remote add origin git@github.com:<dein-github-username>/ha-xpeng.git

# Zu GitHub hochladen
git push -u origin main
```

---

## Schritt 3: Erstes Release / Tag erstellen (Wichtig für HACS!)

HACS orientiert sich standardmäßig an Release-Tags (z. B. `v1.0.0`), um Versionen anzuzeigen:

```bash
# Tag erstellen und zu GitHub pushen
git tag v1.0.0
git push origin v1.0.0
```

*Optional:* Auf GitHub unter **Releases** $\rightarrow$ **Draft a new release** $\rightarrow$ Tag `v1.0.0` auswählen und Titel `"v1.0.0 - Initial Release"` vergeben.

---

## Schritt 4: In Home Assistant via HACS hinzufügen

Sobald das Repo auf GitHub online ist:

1. Öffne **Home Assistant** $\rightarrow$ **HACS**.
2. Klicke oben rechts auf das **Drei-Punkte-Menü** $\rightarrow$ **Benutzerdefinierte Repositories** (*Custom repositories*).
3. Trage deine Repo-URL ein:
   `https://github.com/<dein-github-username>/ha-xpeng`
4. Kategorie: **Integration**.
5. Klicke auf **Hinzufügen**.
6. Suche nach **XPENG Vehicles**, klicke auf **Herunterladen** und starte Home Assistant neu!
