# Navigation, Indizes und Suchmetadaten

## Keine zweite Fachseitenliste

Die Webnavigation wird vollständig aus dem strukturierten Contentindex erzeugt. `mkdocs.yml` enthält deshalb keine manuell gepflegte Liste der 86 Fachseiten. Verbindlich sind:

1. die real vorhandene Markdown-Datei;
2. ihr strukturiertes Frontmatter;
3. die Kategorie aus dem Verzeichnispfad `NN-*`;
4. die Reihenfolge im Abschnitt `## Seiten` der jeweiligen Kategorie-`INDEX.md`;
5. `MANIFEST.csv` als reproduzierbarer, reviewbarer Soll-Snapshot.

`config/publication.yaml` beschreibt ausschließlich Root-Sonderrollen, Publikationstypen und Ausschlüsse. Eine Fachseite darf dort nicht einzeln eingetragen werden.

## Generierte Hauptnavigation

```text
Start hier
Kategorien
├── Enterprise & Windows
├── Versionierung & Entwicklung
├── Linux-Administration
├── Webserver
├── Netzwerk & Sicherheit
├── Storage & Sync
├── Android
├── KI
├── Führung & Kommunikation
├── Sicherheit & PKI
├── Wissensmanagement
└── Hardware & Prozessoren
Gesamtindex
Alphabetisch
Tags & Themen
Downloads & Offline
```

Jede Kategorie enthält zuerst ihre Übersicht und danach jede Fachseite genau einmal in der Reihenfolge des Kategorieindex. Fehlende, zusätzliche oder doppelte Seiten blockieren bereits das Contentmodell; der Navigationsgenerator prüft die Setgleichheit nochmals unabhängig.

## Generierte Seiten

| Pfad | Zweck |
|---|---|
| `kategorien/index.md` | alle Kategorien mit realer Seitenzahl |
| `index/gesamt.md` | alle Fachseiten gruppiert nach Kategorie |
| `index/alphabetisch.md` | Unicode-normalisierte alphabetische Ansicht |
| `index/tags.md` | alle gepflegten Frontmatter-Tags |
| `downloads/index.md` | Download-Landingpage; reproduzierbare Artefakte folgen in Phase 6 |
| `intern/buildinformationen.md` | Quellcommit, reproduzierbarer Zeitpunkt und Zähler |

Die Seiten entstehen innerhalb desselben atomaren Staging-Verzeichnisses wie die transformierten Fachseiten. Ein unvollständiger Generatorlauf kann daher keinen halbfertigen `build/docs`-Baum hinterlassen.

## Maschinelle UI-Daten

Unter `build/docs/data/` entstehen vier stabile JSON-Dateien:

- `pages.json`: Page-ID, Titel, Aliase, Kategorie, Tags, Status, Lesezeit, Quellpfad und absolute Build-URL;
- `categories.json`: Reihenfolge, Titel, Seitenzahl und URL je Kategorie;
- `tags.json`: normalisierte Tag-ID, sichtbarer Name und zugehörige Page-IDs;
- `build-info.json`: Schema, Quellcommit, `site_url`, Zähler und `SOURCE_DATE_EPOCH` als ISO-Zeitpunkt.

Diese Daten ergänzen die lokale Material-Suche. Sie führen keine Telemetrie ein und werden später ausschließlich für lokale Filter, Favoriten und Verlauf verwendet.

## URL-Modell

Die basisunabhängige kanonische URL wird aus dem **generierten** Pfad gebildet:

```text
Quelle:       05-Netzwerk-Sicherheit/Linux-Netzwerk-Premium-Spickzettel.md
Kanonisch:    /05-Netzwerk-Sicherheit/Linux-Netzwerk-Premium-Spickzettel/
Project-Page: https://h234598.github.io/Cheatsheets/05-Netzwerk-Sicherheit/Linux-Netzwerk-Premium-Spickzettel/
Custom Domain:https://cheatsheets.example.org/05-Netzwerk-Sicherheit/Linux-Netzwerk-Premium-Spickzettel/
```

Der Repository-Unterpfad wird ausschließlich aus der beim Build übergebenen vollständigen `site_url` ergänzt. Im Markdown und in der Basiskonfiguration wird kein `/Cheatsheets/`-Präfix in interne Links eingebrannt.

## Reproduzierbares Manifest

```bash
# erwartete Metadaten nur unter build/ erzeugen
python scripts/build_manifest.py --output build/metadata

# eingecheckte Metadaten byteweise prüfen
python scripts/build_manifest.py --check

# ausschließlich nach bewusstem Review kanonisch aktualisieren
python scripts/build_manifest.py --update-committed
```

Der Generator erzeugt:

- `MANIFEST.csv`;
- `MANIFEST.md`;
- `BUILD-REPORT.yaml`;
- `SHA256SUMS.txt`.

`BUILD-REPORT.yaml` verwendet einen inhaltsbasierten Fingerprint und das höchste gepflegte `modified`-Datum. Dadurch entsteht kein künstlicher Drift durch reine Infrastrukturcommits. Build- und Downloadartefakte erhalten zusätzlich den tatsächlichen Quellcommit und `SOURCE_DATE_EPOCH`.

## Lokale Prüfung

```bash
python -m compileall -q scripts tests
python -m pytest -q tests/test_navigation.py tests/test_manifest.py tests/test_build_docs.py
python scripts/build_site.py \
  --strict \
  --site-url https://example.invalid/Cheatsheets/
```
