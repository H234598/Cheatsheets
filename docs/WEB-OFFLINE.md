# Reproduzierbares Offline-HTML

## Zweck

Phase 8A ergänzt den stabilen Online-Build um ein vollständig abgeleitetes Offlinepaket:

```text
Cheatsheets-Offline-HTML.zip
```

Das Paket wird aus demselben Checkout, Contentindex, Quellcommit und `SOURCE_DATE_EPOCH` wie die Online-Site erzeugt. Es verändert keine kanonische Markdown-Datei und ist kein zweiter Inhaltsstand.

Die produktive Online-Ausgabe bleibt:

```text
https://cheatsheets.telacore.org/
```

Das Offlinepaket ist ein zusätzliches Downloadartefakt. Sein Fehlschlag blockiert den Gesamtbuild, kann aber durch Entfernung der optionalen Integration zurückgerollt werden, ohne die Online-Architektur umzubauen.

## Betriebsarten

### Direkt über `file://`

1. ZIP vollständig entpacken.
2. `index.html` öffnen.

Ohne lokalen Server funktionieren:

- alle Inhalte;
- Kategorie- und Indexseiten;
- relative Seiten- und Assetlinks;
- Dark-/Light-Darstellung;
- der No-JavaScript-Fallback.

Browser schränken bei `file://` Fetch, Suche und `localStorage` unterschiedlich ein. Das Paket behauptet deshalb nicht, dass jede progressive Komfortfunktion in jedem Browser direkt aus dem Dateisystem verfügbar ist.

### Vollständig über einen lokalen Server

Im entpackten Verzeichnis:

```bash
python offline-server.py
```

Anschließend:

```text
http://127.0.0.1:8765/index.html
```

Der Hilfsserver:

- bindet ausschließlich an `127.0.0.1`;
- gibt nur Dateien aus dem entpackten Paket aus;
- benötigt keine Installation zusätzlicher Pythonpakete;
- benötigt keinen Internetzugang;
- wird mit `Strg+C` beendet.

Über diesen Modus funktionieren auch lokale Suche, Filter, Favoriten und Lesefortschritt wie in der Online-Ausgabe.

## Buildablauf

Der zentrale Gesamtbuild verwendet weiterhin einen Contentindex und einen Quellcommit:

```text
1. Basispakete und Webquellen erzeugen
2. separate Offline-MkDocs-Konfiguration schreiben
3. Offline-Site mit use_directory_urls: false bauen
4. pages.json und categories.json auf relative .html-URLs umstellen
5. verifizierte Basisdownloads in den Offlinebaum kopieren
6. Offlinebaum und sämtliche lokalen Referenzen prüfen
7. Offline-Manifest und Offline-Prüfsummen erzeugen
8. deterministisches Offline-ZIP erzeugen
9. ZIP unabhängig erneut lesen, prüfen und testweise entpacken
10. Offline-ZIP in Downloadmanifest, Downloadprüfsummen und Landingpage aufnehmen
11. Online-Site bauen und vollständiges Pages-Artefakt prüfen
```

Die Online-Site verwendet weiterhin Verzeichnis-URLs. Nur die getrennte Offline-Konfiguration setzt:

```yaml
use_directory_urls: false
```

Dadurch zeigen lokale Links auf reale Dateien wie:

```text
01-Enterprise-Windows/index.html
01-Enterprise-Windows/Beispiel-Cheatsheet.html
```

## Paketinhalt

Neben dem vollständigen statischen HTML-Baum enthält das ZIP:

```text
OFFLINE-LESEN.txt
OFFLINE-MANIFEST.json
OFFLINE-SHA256SUMS.txt
offline-server.py
```

Zusätzlich sind die verifizierten Basisdownloads unter:

```text
downloads/files/
```

enthalten. Das Offline-ZIP nimmt sich selbst nicht rekursiv auf.

## Determinismus

Das Archiv verwendet:

- stabil nach kanonischem POSIX-Pfad sortierte Einträge;
- `ZIP_STORED` ohne implementationsabhängige Kompressionsausgabe;
- feste Unix-Dateirechte `0644`;
- keine ZIP-Kommentare oder Extra-Felder;
- den aus `SOURCE_DATE_EPOCH` abgeleiteten Zeitstempel;
- Abrundung der Sekunden auf die vom ZIP-Format darstellbare Zweierauflösung;
- keine Symlinks, Hardlinks, Verzeichniseinträge oder Sonderdateien.

Zwei Builds desselben Commits mit demselben `SOURCE_DATE_EPOCH` müssen bytegleich sein.

## Integritätsdateien

### `OFFLINE-SHA256SUMS.txt`

Enthält die SHA-256-Werte sämtlicher Paketdateien vor Hinzufügen der Prüfsummen- und Manifestdatei. Dadurch entsteht keine Selbstreferenz.

### `OFFLINE-MANIFEST.json`

Schema-Version 1 dokumentiert:

- Quellcommit;
- `SOURCE_DATE_EPOCH`;
- reproduzierbaren Erzeugungszeitpunkt;
- kanonische Online-URL;
- URL-Modus `relative-html`;
- jede enthaltene Datei mit Größe und SHA-256;
- den deterministischen Baumhash.

Der Baumhash umfasst alle Dateien außer dem Manifest selbst und damit auch die Offline-Prüfsummendatei.

## Sicherheitsmodell

### Dateisystem

Der Generator und der unabhängige Validator lehnen ab:

- Symlinks;
- Hardlinks;
- nicht reguläre Dateien;
- Case-insensitive Pfadkollisionen;
- absolute Archivpfade;
- Laufwerks- und UNC-Pfade;
- `.`- und `..`-Segmente;
- Steuerzeichen;
- Dateiaustausch zwischen Prüfung und Öffnung.

Quellen werden mit `lstat`, `O_NOFOLLOW` und Geräte-/Inode-Abgleich gelesen. Eine optionale Extraktion schreibt ausschließlich atomar in ein markiertes Ziel unter `build/`.

### HTML- und CSS-Referenzen

Jede lokale Referenz aus HTML und CSS wird geprüft. Dazu gehören:

- `href` normaler Links;
- `src`, `srcset`, `poster` und `data` aktiver Elemente;
- Stylesheets, Icons, Preload-/Prefetch-Links und Manifeste;
- CSS-`url(...)`;
- CSS-`@import`;
- Inline-Styles und `<style>`-Blöcke;
- HTML-Fragmente auf existierenden Ziel-IDs.

Verboten sind:

- root-relative lokale Links;
- Pfadflucht aus dem Paket;
- Backslashes in lokalen URLs;
- protokollrelative URLs;
- externe Laufzeitassets;
- `<base>`;
- Meta-Refresh;
- gefährliche oder unbekannte URL-Schemata.

Bewusst anklickbare externe `http`, `https`, `mailto`- und `tel`-Links bleiben erlaubt. Sie lösen erst beim Anklicken eine Verbindung aus. Canonical- und Quellrepositorylinks dürfen deshalb auf die Online-Ausgabe beziehungsweise GitHub zeigen, ohne dass das Offlinepaket beim Laden Netzwerkzugriffe ausführt.

## Unabhängige Prüfung

Nach einem Gesamtbuild:

```bash
python scripts/validate_offline_archive.py \
  --archive site/downloads/files/Cheatsheets-Offline-HTML.zip \
  --extract build/offline-site \
  --report build/reports/offline.json \
  --force
```

Der Validator:

1. liest das ZIP ohne vorherige Extraktion;
2. prüft Dateimenge, Reihenfolge, Rechte, Typ, Größe und Zeitstempel;
3. verifiziert Manifest und Einzelhashes;
4. verifiziert die Offline-Prüfsummen;
5. berechnet den Baumhash neu;
6. materialisiert alle Einträge ohne Pfadflucht;
7. prüft danach sämtliche lokalen HTML-/CSS-Referenzen und Fragmente;
8. tauscht ein vorhandenes Extraktionsziel nur bei gültigem Build-Sentinel atomar aus.

## Browserprüfungen

Die Pull-Request-CI startet zwei lokale Server parallel:

```text
Online:  http://127.0.0.1:4173/Cheatsheets/
Offline: http://127.0.0.1:4174/
```

`tests/web/offline.spec.mjs` prüft:

- Offline-Hinweis und Startseite;
- relative `.html`-URLs aus `pages.json`;
- Fachseitennavigation;
- lokale Suche und Filter;
- UI-Initialisierung ohne fremde Requests;
- No-JavaScript-Lesbarkeit direkt über `file://`;
- Navigation von `file://.../index.html` nach `kategorien.html`;
- null Browser- oder Konsolenfehler.

Der Online-Browsertest bleibt unverändert aktiv. Die optionale Erweiterung darf deshalb keine Regression der veröffentlichten Website verdecken.

## CI- und Pages-Gates

Der Validate-Workflow:

- baut Online- und Offline-Ausgabe;
- validiert und entpackt das fertige Offline-ZIP unabhängig;
- schreibt `build/reports/offline.json`;
- startet Online- und Offline-Browsertests;
- lädt Berichte, Traces, Screenshots und Videos nur als Diagnoseartefakt hoch.

Der produktive Pages-Workflow:

- baut das Offline-ZIP aus derselben von GitHub Pages gelieferten Basis-URL;
- validiert das fertige ZIP unabhängig;
- veröffentlicht es erst danach als Bestandteil des geprüften Pages-Artefakts;
- baut oder prüft im Deploymentjob nichts erneut.

## Lokale Gesamtprüfung

```bash
export SOURCE_DATE_EPOCH="$(git show -s --format=%ct HEAD)"

python scripts/build_site.py \
  --strict \
  --site-url https://cheatsheets.telacore.org/

python scripts/validate_offline_archive.py \
  --archive site/downloads/files/Cheatsheets-Offline-HTML.zip \
  --extract build/offline-site \
  --report build/reports/offline.json \
  --force

CI=true \
SITE_DIR=site \
WEB_TEST_BASE_PATH=/Cheatsheets/ \
WEB_TEST_PORT=4173 \
OFFLINE_SITE_DIR=build/offline-site \
OFFLINE_TEST_PORT=4174 \
npm run test:web
```

## Rollback

Die Offlinefunktion ist technisch getrennt. Ein Rollback entfernt:

- den Aufruf von `build_offline_archive` aus dem zentralen Site-Build;
- `Cheatsheets-Offline-HTML.zip` aus dem Downloadmodell;
- den unabhängigen Offlinevalidator und die Offline-Browsertests.

Quell-Markdown, Online-MkDocs-Konfiguration, Navigation, Pages-Deployment und Basisdownloads bleiben dabei unverändert nutzbar.

## Noch nicht enthalten

Nicht Bestandteil von Phase 8A sind:

- Service Worker oder PWA;
- PDF- oder EPUB-Export;
- Wissensgraph;
- signierte GitHub-Attestations;
- Hintergrundaktualisierung des Offlinepakets.

Diese Erweiterungen benötigen jeweils einen eigenen kleinen Pull Request und dürfen das Online-MVP nicht zur Laufzeit oder beim Rollback koppeln.
