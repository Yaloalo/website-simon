# Simon Website

## A. Developer workflow

### Struktur

- `src/` enthält Layout, HTML-Templates, CSS und JavaScript.
- `content/site.json` enthält alle vom Kunden editierbaren Texte, Preise, Kontaktangaben und Bildreferenzen.
- `static/uploads/` ist das Upload-Ziel für Bilder aus Pages CMS.
- `static/images/` enthält feste Entwickler-Assets wie das Favicon.
- `build.py` rendert die Jinja2-Templates nach `dist/` und kopiert alle statischen Dateien.

### Lokales Setup

macOS / Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python build.py
```

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python build.py
```

### Lokale Vorschau

```bash
python -m http.server 8080 --directory dist
```

Danach ist die Vorschau unter `http://localhost:8080` erreichbar.

### Inhalte und Pages CMS

- Der Kunde bearbeitet nur `content/site.json` über Pages CMS.
- Bild-Uploads landen in `static/uploads/` und werden als `/uploads/...` referenziert.
- Layout, Farben, HTML, CSS und JavaScript bleiben vollständig im Entwicklerbereich unter `src/`.

### Deployment-Architektur

Die Produktionskette ist:

`Pages CMS -> GitHub -> GitHub Actions -> python build.py -> dist/ -> rsync über SSH -> Dogado`

Wenn `build.py` fehlschlägt, wird nichts nach Dogado übertragen.

### Administrator: einmalige Einrichtung

1. In GitHub unter `Settings -> Secrets and variables -> Actions` diese Secrets anlegen:
   - `DOGADO_HOST`
   - `DOGADO_USER`
   - `DOGADO_PORT`
   - `DOGADO_SSH_KEY`
   - `DOGADO_TARGET_PATH`
2. Den öffentlichen Schlüssel zur privaten `DOGADO_SSH_KEY`-Datei auf dem Dogado-Zielserver autorisieren.
3. Sicherstellen, dass `DOGADO_TARGET_PATH` auf das gewünschte Webroot zeigt.
4. Einen Commit nach `main` pushen und den Lauf unter `Actions` prüfen.

Hinweis: Der Workflow füllt `~/.ssh/known_hosts` per `ssh-keyscan` mit dem Host-Key des Dogado-Servers. `StrictHostKeyChecking` bleibt dabei aktiv; es wird nicht global deaktiviert.

### Design ändern

- HTML-Struktur: `src/templates/`
- Styles: `src/css/main.css`
- Interaktionen: `src/js/main.js`

Die Inhalte in `content/site.json` müssen dafür nicht umgebaut werden.

## B. Client workflow

1. Pages CMS im Browser öffnen.
2. `Website` öffnen.
3. Text, Preis oder Bild ändern.
4. Auf `Save` klicken.
5. Die Veröffentlichung läuft danach automatisch im Hintergrund.
