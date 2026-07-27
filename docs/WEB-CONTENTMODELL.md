# Web-Contentmodell

## Zweck

Die Markdown- und Obsidian-Dateien im Repository bleiben die fachlich kanonische Quelle. Die Webpipeline liest sie ausschließlich und erzeugt sämtliche abgeleiteten Dateien unter `build/` beziehungsweise `site/`.

## Seitenrollen

| Rolle | Erkennung | Veröffentlichung |
|---|---|---|
| `reference` | Datei in `NN-*` mit `type: reference` | Fachnavigation und Suche |
| `category-index` | `NN-*/INDEX.md` oder `type: index` | Kategorie-Landingpage |
| `root-landing` | `00-START-HIER.md` | generierte Startseite |
| `root-index` | Root-`INDEX.md` | Wartungs-/Quellansicht |
| `root-readme` | `README.md` | Repositorydokumentation |
| `maintenance` | bekannte Root-Metadateien | nicht in der Fachnavigation |
| `download-only` | vorhandener Gesamtband | nur Downloadbereich |
| `technical` | `.github/`, `config/`, `docs/`, `scripts/`, `tests/`, `web/` | nicht als Fachinhalt |
| `unknown` | keine Regel trifft zu | blockierender Fehler |

## Autoritätsreihenfolge

1. reale UTF-8-Markdown-Datei;
2. strukturiertes YAML-Frontmatter;
3. Kategorie aus dem realen Pfad;
4. Linkreihenfolge im Abschnitt `## Seiten` der Kategorie-`INDEX.md`;
5. `MANIFEST.csv` als versionierter Soll-Snapshot;
6. weitere Berichte und Prüfsummen als abgeleitete Ansichten.

Ein Manifest darf keine fehlende Datei erfinden und überschreibt weder Frontmatter noch Inhalt.

## Pflichtfelder

Fachseiten benötigen mindestens:

```yaml
title:
type: reference
status: fertig
tags:
```

Kategorieindizes benötigen zusätzlich `pages`. Gültige Statuswerte sind zunächst `fertig`, `entwurf`, `review` und `archiviert`.

## Stabile Page-ID

Lokale UI-Zustände verwenden keine URL als Primärschlüssel. Die ID entsteht deterministisch aus dem NFC-normalisierten Quellpfad:

```text
sha256("cheatsheets-page-v1\0" + Quellpfad)[:16]
```

Sie wird als `p_<hex>` ausgegeben. Spätere Umbenennungen erhalten ein explizites, reviewbares Alias-Mapping.

## Validierungsfehler

Die Inventur sammelt alle Fehler eines Laufs und bricht nicht nach der ersten Datei ab. Unter anderem blockieren:

- fehlende oder zusätzliche Manifestpfade;
- abweichende Zeilen-, Byte- oder SHA-256-Werte;
- unbekannte Seitenrollen oder Statuswerte;
- fehlende Kategorieindizes;
- Fachseiten, die im Kategorieindex fehlen oder dort mehrfach stehen;
- Titel-, Alias-, Pfad- oder URL-Kollisionen;
- Symlinks und Pfadflucht;
- ungültiges UTF-8 oder YAML.

## Lokale Prüfung

```bash
python -m pip install -r requirements-test.txt
python -m pytest -q tests/test_content_model.py tests/test_manifest.py
python scripts/validate_content.py --strict --report build/reports/baseline.json
```
