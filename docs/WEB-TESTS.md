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

python scripts/validate_workflows.py \
  --report build/reports/workflows.json
python -m compileall -q scripts tests
python -m pytest -q --junitxml=build/reports/pytest.xml
python scripts/validate_content.py \
  --report build/reports/content.json
python scripts/validate_links.py
python scripts/validate_security.py \
  --report build/reports/security.json

SOURCE_DATE_EPOCH="$(git show -s --format=%ct HEAD)" \
python scripts/build_site.py \
  --check \
  --strict \
  --site-url https://example.invalid/Cheatsheets/

git diff --exit-code
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
| Strict-Build | MkDocs-Warnungen, unvollständigem Webbaum oder Buildfehlern |
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

Die Policy prüft auch sich selbst über `tests/test_workflows.py`.

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

Nicht allowlistetes, aber nicht aktiv gefährliches Raw HTML wird als Warnung protokolliert. Private Beispielnetze und interne Hostnamensuffixe erscheinen als Informationsbefund. Sie blockieren Phase 5A nicht, bleiben aber im JSON-Bericht reviewbar.

## Diagnoseartefakt

Der Workflow erzeugt `validation-reports-<run-id>` mit:

```text
build/reports/
├── workflows.json
├── pytest.xml
├── content.json
├── links.txt
├── security.json
├── metadata-diff.patch
└── expected-metadata/
```

Die Berichte enthalten keine vollständigen erkannten Secrets. Secretfunde werden ausschließlich durch Regelname und gekürzten SHA-256-Fingerabdruck beschrieben.

## Metadatendrift

Die eingecheckten kanonischen Metadaten stammen noch aus dem ursprünglichen Inhaltsstand. Phase 5A erzeugt ihre erwarteten Fassungen reproduzierbar und legt den Unterschied als Patch ab. Erst der separate Metadaten-/Content-PR aktualisiert diese Dateien bewusst; danach wird jede Drift zu einem blockierenden Fehler.

## Browser- und Accessibility-Tests

Phase 5A prüft Python, MkDocs und statische Verträge. Reale Browserläufe mit JavaScript aus, 320-Pixel-Viewport, Tastatursteuerung, axe und Performancebudgets folgen in Phase 7 und werden dort als zusätzliche Gates eingebunden.
