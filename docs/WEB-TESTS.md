# Webtests und CI-Gates

## Zweck

Die lokale Befehlsfolge und die GitHub-Actions-Pipeline verwenden dieselben Python- und Node-Module. Pull Requests werden vollständig geprüft, erhalten aber keine Schreibrechte, verwenden keine Secrets und veröffentlichen keine Website.

Phase 7 ergänzt den bisherigen statischen Buildvertrag um echte Chromium-, No-JavaScript-, Tastatur-, Mobil- und Accessibility-Prüfungen. Die kanonischen Markdownquellen bleiben unverändert.

## Voraussetzungen

- Python 3.12;
- Node.js 24;
- ein frischer Repository-Checkout;
- `SOURCE_DATE_EPOCH` aus der Commitzeit;
- keine global installierten npm-Pakete als versteckte Voraussetzung.

Die Browserabhängigkeiten sind in `package-lock.json` exakt festgelegt. `npm ci --ignore-scripts` führt keine Installationsskripte der Abhängigkeiten aus. Chromium wird anschließend bewusst über das bereits lokal installierte Playwright-Paket installiert:

```bash
npx --no-install playwright install --with-deps chromium
```

Ein nacktes `npx <paket>` ist in der Workflowpolicy verboten, damit CI nicht unbemerkt ein Paket aus dem Netz nachlädt.

## Lokale Gesamtprüfung

```bash
python -m venv .venv
source .venv/bin/activate

python -m pip install --disable-pip-version-check \
  -r requirements-docs.txt \
  -r requirements-test.txt
python -m pip check

npm ci --ignore-scripts
npm ls --all
npx --no-install playwright install --with-deps chromium

mkdir -p build/reports
export SOURCE_DATE_EPOCH="$(git show -s --format=%ct HEAD)"

python scripts/validate_workflows.py \
  --report build/reports/workflows.json

python -m compileall -q scripts tests
node --check web/assets/javascripts/site-state.js
node --check web/assets/javascripts/filters.js
node --check web/assets/javascripts/accessibility.js
node --check web/assets/javascripts/mermaid-loader.js
node --check playwright.config.mjs
node --check tests/web/site.spec.mjs

python -m pytest -q --junitxml=build/reports/pytest.xml
python scripts/validate_content.py \
  --report build/reports/content.json
python scripts/validate_links.py \
  --report build/reports/links.json
python scripts/validate_security.py \
  --report build/reports/security.json

python scripts/build_manifest.py \
  --output build/reports/expected-metadata
for name in MANIFEST.csv MANIFEST.md BUILD-REPORT.yaml SHA256SUMS.txt; do
  diff -u "$name" "build/reports/expected-metadata/$name"
done

python scripts/build_site.py \
  --strict \
  --site-url http://127.0.0.1:4173/Cheatsheets/

python scripts/validate_pages_artifact.py \
  --site-dir site \
  --report build/reports/pages-artifact.json

python scripts/validate_web_budgets.py \
  --site-dir site \
  --report build/reports/web-budgets.json

CI=true \
SITE_DIR=site \
WEB_TEST_BASE_PATH=/Cheatsheets/ \
WEB_TEST_PORT=4173 \
npm run test:web

git diff --exit-code
git status --short
```

`playwright.config.mjs` startet `scripts/serve_site.py` automatisch. Der Server mountet ausschließlich den regulären `site/`-Baum unter `/Cheatsheets/`, liefert die gebaute `404.html` auch für tiefe unbekannte Pfade und folgt keinen Symlinks.

## Blockierende Gates

| Gate | Blockiert bei |
|---|---|
| Workflow-Policy | unsicheren Triggern, Rechten, Runnern, Pins, remote nachladendem `npx` oder Deploymentaktionen |
| Python-/JavaScript-Syntax | syntaktisch ungültigem Python, UI-JavaScript, Playwright-Konfiguration oder Browsertest |
| Pytest | fehlerhaften Unit- oder Integrationsverträgen |
| Contentmodell | Frontmatter-, Kategorie-, Manifest-, Pfad-, Hash- oder Kollisionsfehlern |
| Linkprüfung | fehlenden, mehrdeutigen oder unsicheren internen Links und fehlerhaften Callouts |
| Sicherheitsprüfung | hochpräzisen Secrets, privaten Schlüsselblöcken, aktivem Raw HTML oder externen Laufzeitassets |
| Kanonische Metadaten | jeder byteweisen Abweichung von Manifesten, Buildreport oder Prüfsummen |
| Strict-Build | MkDocs-Warnungen, unvollständigem Webbaum oder Buildfehlern |
| Pages-Artefakt | fehlenden Pflichtseiten, Symlinks, Hardlinks, Sonderdateien, Case-Kollisionen oder Größenüberschreitung |
| Webbudgets | zu großem eigenem JS/CSS, zu großer Einzel-HTML-Datei oder externem HTML-/CSS-Laufzeitasset |
| Chromium | Browserfehlern, fremden Requests, defekter Navigation, No-JS-, Tastatur-, Mobil-, Download- oder 404-Funktion |
| axe | jedem `serious`- oder `critical`-Befund in den aktivierten WCAG-2.x-/2.2-AA-Regelsätzen |
| Quelldiff | Änderungen an versionierten Dateien durch den Build |

## Workflow-Policy

`scripts/validate_workflows.py` prüft insbesondere:

- `pull_request_target` ist verboten;
- `contents: write` ist verboten;
- direkte `git push`-Befehle sind verboten;
- PR-Validierung darf keine Secrets verwenden;
- externe Actions benötigen einen vollständigen 40-stelligen Commit-SHA und einen Versionskommentar;
- Checkout setzt `persist-credentials: false`;
- Python ist auf 3.12 und Node.js auf 24 festgelegt;
- Runner ist `ubuntu-24.04`;
- jeder Job besitzt ein Timeout;
- Diagnoseartefakte werden mit `if: always()` hochgeladen;
- Pages-Actions und Environments sind im Validate-Workflow verboten;
- `npm ci --ignore-scripts`, lokale Chromium-Installation, Webbudgetprüfung und Browsertests müssen vorhanden sein.

Die Policy prüft sich selbst über `tests/test_workflows.py`. Der Pages-Workflow besitzt zusätzlich einen eigenen strukturierten Vertrag in `tests/test_pages_workflow.py`. Dieser erzwingt Trigger, Jobtrennung, minimale Rechte, dynamische Basis-URL, genau einen Site-Build, Environment und Deploymentoutput.

## Sicherheitsprüfung

Der Scanner trennt zwei Aufgaben:

1. **Secretprüfung über den vollständigen Quelltext.** Hochpräzise Token- und Schlüsselblöcke werden auch in Codefences erkannt, weil ein realer Schlüssel durch Markdownformatierung nicht ungefährlich wird.
2. **Aktive Inhaltsprüfung nur im sichtbaren Markdown.** Frontmatter, Fences, Inline-Code und HTML-Kommentare werden positionsstabil maskiert, bevor Raw HTML und Laufzeitassets analysiert werden. Lehrbeispiele bleiben dadurch unverändert.

Die statische Webbudgetprüfung analysiert zusätzlich alle gebauten HTML- und CSS-Dateien. Sie erlaubt keine externen `script`, `img`, `iframe`, `object`, `embed`, `audio`, `video`, `track`, Preload-, Stylesheet- oder CSS-`url(...)`-Ressourcen.

### Fehler

- GitHub-, AWS-, Google- oder Slack-Tokenmuster;
- Zugangsdaten in URLs;
- vollständige private Schlüsselblöcke;
- aktive Tags wie `script`, `iframe`, `object`, `form`, `style` oder `svg` aus Inhalten;
- Eventhandler und `srcdoc`;
- `javascript:` und `data:text/html`;
- extern geladene Laufzeitassets;
- Symlinks als Markdownquellen.

### Warnungen und Informationen

Nicht allowlistetes, aber nicht aktiv gefährliches Raw HTML wird als Warnung protokolliert. Private Beispielnetze und interne Hostnamensuffixe erscheinen als Informationsbefund. Sie blockieren den Build nicht, bleiben aber im JSON-Bericht reviewbar.

## Kanonische Metadaten

Die Pipeline erzeugt bei jedem Lauf folgende Dateien neu:

```text
MANIFEST.csv
MANIFEST.md
BUILD-REPORT.yaml
SHA256SUMS.txt
```

Die erwarteten Dateien entstehen unter `build/reports/expected-metadata/` und werden byteweise mit dem eingecheckten Stand verglichen. Jede Abweichung blockiert den Pull Request. Der vollständige Unterschied wird als `metadata-diff.patch` im Diagnoseartefakt gespeichert.

Dadurch müssen Änderungen an Fachseiten, Kategorieindizes, Dateinamen, Frontmatter, Zeilenzahlen oder Dateigrößen immer gemeinsam mit den generatorisch aktualisierten kanonischen Metadaten reviewt werden.

## Reales Pages-Artefakt im Pull Request

Die Validate-Pipeline erzeugt `site/` genau einmal mit der vollständigen Project-Page-Test-URL `http://127.0.0.1:4173/Cheatsheets/`. Alle statischen und browserbasierten Prüfungen arbeiten auf genau diesem Baum.

Der Artefaktvalidator kontrolliert:

- `index.html` und `404.html`;
- reguläres Wurzelverzeichnis;
- keine Symlinks;
- keine Hardlinks;
- keine Sonderdateien;
- keine Case-insensitiven Pfadkollisionen;
- Gesamtgröße unter 1.000.000.000 Bytes;
- deterministischen Baum-SHA-256.

Reine Downloadquellen werden nicht als mehrere Megabyte große HTML-Seiten gerendert. Links auf `download-only`-Seiten werden stattdessen beim Webbuild als echte `download`-Links auf die verifizierten Dateien unter `downloads/files/` ausgegeben.

## Statische Performance- und Laufzeitbudgets

`scripts/validate_web_budgets.py` erzwingt:

| Messwert | Grenze |
|---|---:|
| eigenes JavaScript, Gzip-Summe | 30 KiB |
| eigenes CSS, Gzip-Summe | 35 KiB |
| einzelne HTML-Datei | 2 MiB |
| externe Laufzeitassets | 0 |

Der vollständige Funktionslauf `30343694759` auf Head `fe4ed478fc432fcb400cf258ac63e2fdb3fb6a53` bestätigte vor der abschließenden Dokumentationspflege:

- eigenes JavaScript: **8.410 Gzip-Bytes**;
- eigenes CSS: **2.187 Gzip-Bytes**;
- 113 HTML-Dateien;
- größte HTML-Datei: `index/tags/index.html` mit 288.067 Bytes;
- null externe Laufzeitassets.

Lighthouse-Scores werden noch nicht als blockierende Zahl behauptet. Entsprechend dem Implementierungsplan wird eine Lighthouse-Schwelle erst nach einer stabilen dreifachen Messbaseline aktiviert. Die deterministischen Größen-, Request-, axe- und Funktionsgates sind bereits blockierend.

## Chromium- und Accessibility-Szenarien

`tests/web/site.spec.mjs` führt mit einem Worker sieben reproduzierbare Szenarien aus:

1. Startseite, Kategorien, Downloads sowie kurze und lange Fachseite laden ohne Browserfehler und ohne fremde Origin;
2. axe findet auf Start- und repräsentativer Fachseite keine `serious`- oder `critical`-Verstöße;
3. ohne JavaScript bleiben Inhalte, Schnellstart und Navigation sichtbar, während progressive Werkzeuge verborgen bleiben;
4. Favorit, LocalStorage, Fokusmodus, Tastaturhilfe, Escape und Suchkürzel funktionieren;
5. lokale Titel-/Alias-/Tag-/Kategorie-/Zeitfilter finden und setzen vollständig zurück;
6. bei 320 CSS-Pixeln gibt es keinen Gesamtseitenüberlauf, Fokus bleibt sichtbar, Reduced Motion greift und Code-/Tabellencontainer sind tastaturfokussierbar;
7. Downloadartefakte sind erreichbar und die tiefe 404-Seite antwortet mit HTTP 404 und sicherem Rücklink zur Project-Page-Startseite.

Der Lauf `30343694759` bestätigte **7 von 7 Browsertests** ohne Fehler, Wiederholung oder Flake. Gleichzeitig bestanden **116 von 116 Python-Tests**.

## Diagnoseartefakt

Der Workflow erzeugt `validation-reports-<run-id>` mit:

```text
build/reports/
├── workflows.json
├── pytest.xml
├── content.json
├── links.json
├── links.txt
├── security.json
├── metadata-diff.patch
├── build-site.txt
├── pages-artifact.json
├── web-budgets.json
├── playwright.json
├── playwright.xml
├── web-test-results/       # nur bei Fehlern mit Trace, Bild und Video
└── expected-metadata/
```

Die Berichte enthalten keine vollständigen erkannten Secrets. Secretfunde werden ausschließlich durch Regelname und gekürzten SHA-256-Fingerabdruck beschrieben.
