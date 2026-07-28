# Webbuild

## Grundsatz

Die Markdown- und Obsidian-Dateien im Repository sind unveränderliche Build-Eingaben. `scripts/build_docs.py` erzeugt eine vollständig abgeleitete Webkopie in `build/docs`; MkDocs schreibt ausschließlich nach `site`. Beide Zielbäume tragen die Sentinel-Datei `.cheatsheets-build-root` und werden nur dann atomar ersetzt, wenn diese Markierung vorhanden ist.

## Lokale Umgebung

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-docs.txt
python -m pip install -r requirements-test.txt
python -m pip check
```

## Vollständiger Build

```bash
SOURCE_DATE_EPOCH="$(git show -s --format=%ct HEAD)" \
python scripts/build_site.py \
  --strict \
  --site-url https://h234598.github.io/Cheatsheets/
```

Die erzeugte MkDocs-Konfiguration liegt unter `build/mkdocs.generated.yml`. Sie wird strukturiert aus `mkdocs.yml` erzeugt; `site_url`, `docs_dir`, `site_dir` und `theme.custom_dir` werden nicht per Textersetzung manipuliert.

## Prüfmodi

```bash
# vollständiger temporärer Build ohne bleibende Ausgabe
python scripts/build_site.py --check --site-url https://example.invalid/Cheatsheets/

# reine Inventur; keine Datei wird geschrieben
python scripts/build_site.py --dry-run --verbose

# begrenzte Inventur für Entwicklung und Fixtures
python scripts/build_site.py --dry-run --max-pages 5 --verbose
```

`--max-pages` ist absichtlich mit `--strict` und mit echten Ausgaben unvereinbar. Ein Deployment darf niemals aus einem Teilbuild entstehen.

## Schutzmechanismen

- alle Contentmodellfehler blockieren vor dem ersten Austausch;
- interne Links und Callouts werden ausschließlich in der Webkopie transformiert;
- die Hashsequenz jedes Codefences muss vor und nach der Transformation identisch sein;
- Quellhashes werden vor und nach dem Build verglichen;
- ein vorhandenes unmarkiertes Zielverzeichnis wird selbst mit `--force` niemals gelöscht;
- MkDocs muss `index.html` und `404.html` erzeugen;
- symbolische Links im Pages-Baum blockieren den Build;
- externe Fonts, CDNs und Analytics werden nicht eingebunden.

## Abhängigkeiten

Der Build ist auf MkDocs 1.6.1, Material for MkDocs 9.7.7, PyMdown Extensions 11.0.1 und PyYAML 6.0.3 gepinnt. Aktualisierungen erfolgen ausschließlich über reviewbare Pull Requests.
