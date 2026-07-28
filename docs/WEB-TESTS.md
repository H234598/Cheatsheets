# Webtests und CI-Gates

## Zweck

Die lokale Befehlsfolge und die GitHub-Actions-Pipeline verwenden dieselben Pythonmodule. Pull Requests werden vollständig geprüft, erhalten aber keine Schreibrechte und veröffentlichen keine Website.

## Lokale Gesamtprüfung

```bash
python -m venv .venv
source .venv/bin/activate

python -m pip install --disable-pip-version-check \
  -r requirements-docs.txt \
  -r requirements-test.txt
python -m pip check

mkdir -p build/reports
export SOURCE_DATE_EPOCH="$(git show -s --format=%ct HEAD)"

python scripts/validate_workflows.py \
  --report build/reports/workflows.json
python -m compileall -q scripts tests
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
  --site-url https://example.invalid/Cheatsheets/

python scripts/validate_pages_artifact.py \
  --site-dir site \
  --report build/reports/pages-artifact.json

git diff --exit-code
git status --short
```

## Blockierende Gates

| Gate | Blockiert bei |
|---|---|
| Workflow-Policy | unsicheren Triggern, Rechten, Runnern, Pins oder Deploymentaktionen |
| Compilecheck | syntaktisch ungültigem Python |
| Pytest | fehlerhaften Unit- oder Integrationsverträgen |
| Contentmodell | Frontmatter-, Kategorie-, Manifest-, Pfad-, Hash- oder Kollisionsfehlern |
| Linkprüfung | fehlenden, mehrdeutigen oder unsicheren internen Links und fehlerhaften Callouts |
| Sicherheitsprüfung | hochpräzisen Secrets, privaten Schlüsselblöcken, aktivem Raw HTML oder externen Laufzeitassets |
| Kanonische Metadaten | jeder byteweisen Abweichung von Manifesten, Buildreport oder Prüfsummen |
| Strict-Build | MkDocs-Warnungen, unvollständigem Webbaum oder Buildfehlern |
| Pages-Artefakt | fehlenden Pflichtseiten, Symlinks, Hardlinks, Sonderdateien, Case-Kollisionen oder Größenüberschreitung |
| Quelldiff | Änderungen an versionierten Dateien durch den Build |

## Workflow-Policy

`scripts/validate_workflows.py` prüft insbesondere:

- `pull_request_target` ist verboten;
- `contents: write` ist verboten;
- direkte `git push`-Befehle sind verboten;
- PR-Validierung darf keine Secrets verwenden;
- externe Actions benötigen einen vollständigen 40-stelligen Commit-SHA und einen Versionskommentar;
- Checkout setzt `persist-credentials: false`;
- Python ist auf 3.12 festgelegt;
- Runner ist `ubuntu-24.04`;
- jeder Job besitzt ein Timeout;
- Diagnoseartefakte werden mit `if: always()` hochgeladen;
- Pages-Actions und Environments sind im Validate-Workflow verboten.

Die Policy prüft auch sich selbst über `tests/test_workflows.py`. Der Pages-Workflow besitzt zusätzlich einen eigenen strukturierten Vertrag in `tests/test_pages_workflow.py`. Dieser erzwingt Trigger, Jobtrennung, minimale Rechte, dynamische Basis-URL, genau einen Site-Build, Environment und Deploymentoutput.

## Sicherheitsprüfung

Der Scanner trennt zwei Aufgaben:

1. **Secretprüfung über den vollständigen Quelltext.** Hochpräzise Token- und Schlüsselblöcke werden auch in Codefences erkannt, weil ein realer Schlüssel durch Markdownformatierung nicht ungefährlich wird.
2. **Aktive Inhaltsprüfung nur im sichtbaren Markdown.** Frontmatter, Fences, Inline-Code und HTML-Kommentare werden positionsstabil maskiert, bevor Raw HTML und Laufzeitassets analysiert werden. Lehrbeispiele bleiben dadurch unverändert.

### Fehler

- GitHub-, AWS-, Google- oder Slack-Tokenmuster;
- Zugangsdaten in URLs;
- vollständige private Schlüsselblöcke;
- aktive Tags wie `script`, `iframe`, `object`, `form`, `style` oder `svg`;
- Eventhandler und `srcdoc`;
- `javascript:` und `data:text/html`;
- extern geladene Bilder, Poster oder andere Laufzeitassets;
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

Die Validate-Pipeline verwendet keinen zweiten temporären Build mehr. Sie erzeugt `site/` genau einmal mit einer vollständigen Project-Page-Test-URL und prüft anschließend genau diesen Baum mit `validate_pages_artifact.py`.

Der Validator kontrolliert:

- `index.html` und `404.html`;
- reguläres Wurzelverzeichnis;
- keine Symlinks;
- keine Hardlinks;
- keine Sonderdateien;
- keine Case-insensitiven Pfadkollisionen;
- Gesamtgröße unter 1.000.000.000 Bytes;
- deterministischen Baum-SHA-256.

Die Tests unter `tests/test_pages_artifact.py` decken gültige Artefakte, fehlende Pflichtseiten, Symlink-/Hardlinkfälle, Größenlimit und JSON-Bericht ab.

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
├── pages-artifact.json
└── expected-metadata/
```

Die Berichte enthalten keine vollständigen erkannten Secrets. Secretfunde werden ausschließlich durch Regelname und gekürzten SHA-256-Fingerabdruck beschrieben.

## Browser- und Accessibility-Tests

Phase 5B prüft Python, MkDocs, Workflowverträge und das vollständige statische Pages-Artefakt. Reale Browserläufe mit JavaScript aus, 320-Pixel-Viewport, Tastatursteuerung, axe und Performancebudgets folgen in Phase 7 und werden dort als zusätzliche Gates eingebunden.
