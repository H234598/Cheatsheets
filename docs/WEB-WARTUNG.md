# GitHub Pages – Betrieb, Deployment und Rollback

## Produktiver Status

Die Zielumgebung wurde am 2026-07-28 durch den Betreiber vollständig in Betrieb genommen und bestätigt:

```text
Pages-Quelle:  GitHub Actions
Custom Domain: https://cheatsheets.telacore.org/
HTTPS:         erzwungen
DNS:           aktiv
Alias-Domains: HTTPS-Redirect auf die kanonische Domain
```

Die kanonische Domain bleibt ausschließlich:

```text
cheatsheets.telacore.org
```

Zusätzliche Namen wie `cheat.telacore.org` werden nicht als zweite GitHub-Pages-Custom-Domain eingetragen. Sie werden vor GitHub durch einen permanenten HTTPS-Redirect auf die kanonische Domain geführt; Pfad und Query-String bleiben dabei erhalten.

## Zielarchitektur

Die Webseite wird ausschließlich aus einem GitHub-Actions-Artefakt veröffentlicht. Weder `build/` noch `site/` werden nach `main` committed.

```text
main-Push oder manuelle Auslösung
          │
          ▼
Pages / build
          │
          ├── Checkout ohne persistente Credentials
          ├── Python 3.12 und gepinnte Abhängigkeiten
          ├── vollständige Validierung
          ├── genau ein zentraler Gesamtbuild
          ├── Online-Site und Offline-HTML
          ├── unabhängige Offline-ZIP-Prüfung
          ├── Pages-Artefaktprüfung
          └── Upload als github-pages-Artefakt
          │
          ▼
Pages / deploy
          │
          ├── needs: build
          ├── Environment github-pages
          ├── OIDC über id-token: write
          └── actions/deploy-pages
          │
          ▼
https://cheatsheets.telacore.org/
```

Ein fehlgeschlagener Build oder ein fehlerhaftes Offlinepaket erzeugt kein Deployment.

## Workflow

Datei:

```text
.github/workflows/pages.yml
```

Trigger:

- Push nach `main`;
- manuelle Auslösung über `workflow_dispatch`;
- ausdrücklich **kein** Pull-Request-Trigger.

Concurrency:

```yaml
concurrency:
  group: github-pages
  cancel-in-progress: false
```

Ein bereits laufendes Deployment wird nicht abgebrochen. Neuere Läufe warten, statt eine möglicherweise halbfertige Veröffentlichung zu erzwingen.

## Berechtigungen

Globale Workflowberechtigungen sind leer:

```yaml
permissions: {}
```

### Buildjob

```yaml
permissions:
  contents: read
  pages: write
```

Der Buildjob darf Inhalte lesen und GitHub Pages konfigurieren. Er besitzt weder `contents: write` noch `id-token: write`.

### Deploymentjob

```yaml
permissions:
  pages: write
  id-token: write
```

Der Deploymentjob checkt das Repository nicht erneut aus und führt keinen Build oder Offline-Export aus. Er veröffentlicht ausschließlich das vom erfolgreichen Buildjob erzeugte Pages-Artefakt.

## Dynamische Site-URL

`actions/configure-pages` liefert die für das Repository tatsächlich konfigurierte Basis-URL. Der Build verwendet ausschließlich diesen Wert:

```yaml
env:
  SITE_URL: ${{ steps.pages.outputs.base_url }}
```

```bash
python scripts/build_site.py \
  --strict \
  --site-url "${SITE_URL%/}/"
```

Damit nennen Online-Site, Downloadseite, Provenienz und Offline-Manifest dieselbe kanonische URL. Seit Aktivierung der Custom Domain liefert GitHub:

```text
https://cheatsheets.telacore.org/
```

Die Markdownquellen enthalten keine fest codierte Domain und keinen fest codierten Repository-Unterpfad. Project-Page-URLs bleiben Bestandteil der Pull-Request-Testmatrix, nicht der produktiven Konfiguration.

## Validierung vor dem Upload

Der Buildjob führt dieselben Kernprüfungen wie die Pull-Request-CI aus:

1. Workflowpolicy;
2. Python-Compilecheck;
3. vollständige Pytest-Suite;
4. Contentmodell;
5. interne Links und Callouts;
6. Secrets, Raw HTML und externe Laufzeitassets;
7. bytegleiche kanonische Metadaten;
8. genau einen zentralen Strict-Gesamtbuild;
9. unabhängige Offline-ZIP-Prüfung;
10. Pages-Artefaktprüfung;
11. unveränderte versionierte Arbeitskopie.

Der zentrale Gesamtbuild erzeugt intern zwei MkDocs-Ausgaben:

- Online mit Verzeichnis-URLs;
- Offline mit dateibasierten `.html`-URLs.

Das ist kein doppelter Pages-Build: Nur der Onlinebaum wird nach `site/` geschrieben. Die Offlineausgabe wird in einem temporären Buildbereich geprüft und ausschließlich als verifiziertes `Cheatsheets-Offline-HTML.zip` in den finalen Downloadsatz übernommen.

### Offline-Archiv

Vor dem Pages-Upload führt der Workflow aus:

```bash
python scripts/validate_offline_archive.py \
  --archive site/downloads/files/Cheatsheets-Offline-HTML.zip \
  --report build/reports/offline.json
```

Der Validator prüft unabhängig vom Generator:

- ZIP-Pfade, Reihenfolge, Dateitypen und Rechte;
- normalisierte Zeitstempel aus `SOURCE_DATE_EPOCH`;
- Größen- und Eintragslimits;
- Offline-Manifest, Einzelhashes, Prüfsummendatei und Baumhash;
- alle lokalen HTML-/CSS-Referenzen und Fragmente;
- keine externen Laufzeitassets;
- keine Symlinks, Hardlinks, Sonderdateien oder Case-Kollisionen.

### Pages-Artefakt

Das fertige Verzeichnis `site/` wird durch `scripts/validate_pages_artifact.py` geprüft auf:

- vorhandene `index.html`;
- vorhandene `404.html`;
- reguläres Wurzelverzeichnis;
- keine symbolischen Links;
- keine Hardlinks;
- keine Sonderdateien;
- keine Case-insensitiven Pfadkollisionen;
- maximale Gesamtgröße von 1.000.000.000 Bytes;
- deterministischen Baum-SHA-256.

Berichte:

```text
build/reports/offline.json
build/reports/pages-artifact.json
```

## Repository- und Environmenteinstellungen

Produktiv bestätigt:

- Repository → Settings → Pages → Source: **GitHub Actions**;
- Custom Domain: `cheatsheets.telacore.org`;
- Environment: `github-pages`;
- Deployment ausschließlich aus dem erfolgreichen `build`-Job;
- HTTPS aktiv und erzwungen.

Weiterhin empfohlen:

- Deployment-Branch-Regel des Environments auf `main` begrenzen;
- `telacore.org` im GitHub-Konto per TXT-Challenge verifiziert lassen;
- keine Wildcard-DNS-Einträge auf GitHub Pages richten;
- Alias-Subdomains einzeln und vor GitHub als Redirect konfigurieren.

In der Actions-basierten Architektur wird keine `CNAME`-Datei im Repository benötigt. `configure-pages.outputs.base_url` bleibt die einzige URL-Autorität.

## DNS- und Aliasmodell

Kanonischer DNS-Eintrag:

```text
cheatsheets.telacore.org  CNAME  h234598.github.io
```

Zusätzliche Aliasnamen erhalten keinen weiteren GitHub-Pages-Eintrag. Sie benötigen:

1. einen DNS-Eintrag beim vorgeschalteten Proxy oder Redirectdienst;
2. ein Zertifikat für den Alias;
3. einen permanenten HTTP-Redirect auf `https://cheatsheets.telacore.org`;
4. Erhalt von Pfad und Query-String.

Kontrolle:

```bash
curl -I https://cheat.telacore.org/
curl -I 'https://cheat.telacore.org/05-Netzwerk-Sicherheit/?ansicht=kurz'
```

Erwartet wird ein permanenter Redirect mit entsprechendem `Location`-Header auf der kanonischen Domain.

## Lokale Project-Page-Prüfung

```bash
python -m pip install \
  -r requirements-docs.txt \
  -r requirements-test.txt

export SOURCE_DATE_EPOCH="$(git show -s --format=%ct HEAD)"

python scripts/build_site.py \
  --strict \
  --site-url http://127.0.0.1:4173/Cheatsheets/

python scripts/validate_offline_archive.py \
  --archive site/downloads/files/Cheatsheets-Offline-HTML.zip \
  --extract build/offline-site \
  --report build/reports/offline.json \
  --force

python scripts/validate_pages_artifact.py \
  --site-dir site \
  --report build/reports/pages-artifact.json
```

Die Pull-Request-CI startet danach Online- und Offline-Testserver und führt zusätzlich einen No-JavaScript-`file://`-Test des entpackten Pakets aus.

## Produktive Abnahme

Folgende Punkte sind durch den Betreiber am 2026-07-28 als erfüllt bestätigt:

- Buildjob grün;
- Deploymentjob grün;
- Pages-Quelle GitHub Actions;
- Custom Domain unter HTTPS erreichbar;
- mindestens eine tiefe Fachseite erreichbar;
- Kategorie-, Gesamt- und Tagindex funktionieren;
- HTTPS wird erzwungen;
- Alias-Weiterleitungen funktionieren;
- keine Buildausgabe wurde nach `main` committed.

Die automatisierten Phase-7-Browsertests prüfen weiterhin Online-Navigation, 404, Downloads, Accessibility, Mobilansicht und fremde Laufzeitrequests bei jedem Pull Request.

## Offlinepaket im Betrieb

Öffentlicher Download:

```text
https://cheatsheets.telacore.org/downloads/files/Cheatsheets-Offline-HTML.zip
```

Nutzung:

```text
ZIP entpacken → index.html öffnen
```

oder für vollständige lokale Suche und UI:

```bash
python offline-server.py
```

Das Paket wird nicht separat hochgeladen oder versioniert. Es ist Bestandteil desselben Pages-Artefakts und derselben Downloadmanifeste wie die Online-Site.

## Rollback

Ein fehlerhaftes Deployment wird nicht durch manuelles Austauschen eines Artefakts repariert.

Empfohlenes Verfahren:

1. fehlerverursachenden `main`-Commit per Review-PR revertieren;
2. vollständige Validate-Gates abwarten;
3. Revert mergen;
4. Pages-Workflow veröffentlicht aus dem wiederhergestellten Commit;
5. kanonische URL und repräsentative Seiten prüfen.

Ist ausschließlich die Workflowdefinition defekt, wird `.github/workflows/pages.yml` in einem kleinen Infrastruktur-PR auf den letzten grünen Stand zurückgesetzt.

Ist ausschließlich Offline-HTML defekt, kann die optionale Integration in einem kleinen Revert entfernt werden. Online-Site, bestehende Basisdownloads und Deploymentarchitektur bleiben davon unabhängig nutzbar.

## Fehlerdiagnose

### `configure-pages` schlägt fehl

Prüfen:

- Pages-Quelle ist GitHub Actions;
- Buildjob besitzt `pages: write`;
- Repository erlaubt GitHub Actions;
- Workflow läuft auf `main` oder manuell, nicht aus einem Pull Request.

### Offlineprüfung schlägt fehl

Prüfen:

- `build/reports/offline.json` beziehungsweise das Buildlog;
- `OFFLINE-MANIFEST.json` und `OFFLINE-SHA256SUMS.txt`;
- root-relative oder noch verzeichnisbasierte Links in Offline-Templates;
- externe Styles, Skripte, Bilder oder Preload-Ziele;
- ZIP-Zeitstempel und `SOURCE_DATE_EPOCH`;
- Symlinks, Hardlinks oder Case-Kollisionen;
- vorhandene Fragment-ID im Ziel-HTML.

Der Validator extrahiert im Produktivworkflow nicht. Im PR-Workflow wird ausschließlich nach `build/offline-site` und über einen markierten atomaren Verzeichnistausch extrahiert.

### Pages-Artefaktprüfung schlägt fehl

Der JSON-Bericht nennt einen stabilen Fehlercode:

| Code | Bedeutung |
|---|---|
| `PA001`–`PA004` | Siteverzeichnis oder Pflichtdatei fehlt |
| `PA005`–`PA008` | Symlink oder unerwarteter Dateityp |
| `PA009` | Hardlink erkannt |
| `PA010` | Case-insensitive Pfadkollision |
| `PA011` | Größenlimit überschritten |

### Deploymentjob schlägt fehl

Prüfen:

- Buildjob, Offline-ZIP und Pages-Artefakt waren grün;
- `deploy` besitzt `pages: write` und `id-token: write`;
- Environment heißt exakt `github-pages`;
- Environment-Regeln erlauben den `main`-Branch;
- kein zweiter Deploymentmechanismus konkurriert mit dem Workflow.
