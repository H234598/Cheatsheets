# Downloads und Provenienz

## Ziel

Die Website stellt neben den einzeln lesbaren Cheatsheets reproduzierbare Downloadpakete bereit. Ein Download soll unabhängig von Browser, GitHub-Oberfläche oder lokalem Git-Client überprüfbar sein:

- **Was wurde ausgeliefert?**
- **Aus welchen kanonischen Dateien entstand es?**
- **Zu welchem Commit gehört es?**
- **Sind Paket und Einzeldateien unverändert?**
- **Kann derselbe Stand erneut bytegleich erzeugt werden?**

Die Downloadartefakte entstehen nicht in einem separaten Veröffentlichungsweg. Sie werden nach dem einmaligen Strict-MkDocs-Build in denselben finalen `site/`-Baum geschrieben, den anschließend `validate_pages_artifact.py` prüft und `pages.yml` veröffentlicht.

## Öffentliche Artefakte

Die stabile URL-Basis lautet:

```text
/downloads/files/
```

| Datei | Zweck |
|---|---|
| `cheatsheets-markdown.zip` | kanonische Markdownquellen und Metadaten als portables ZIP |
| `cheatsheets-markdown.tar.gz` | derselbe Inhalt als reproduzierbares TAR.GZ |
| `cheatsheets-gesamtband.md` | kanonischer zusammengeführter Gesamtband als einzelne Markdown-Datei |
| `source-manifest.json` | Pfad, Bytezahl und SHA-256 jeder aufgenommenen Quelldatei |
| `provenance.intoto.json` | in-toto Statement v1 mit SLSA-Provenance-v1-Prädikat |
| `catalog.json` | maschinenlesbarer Downloadkatalog für Clients und spätere Automatisierung |
| `SHA256SUMS.txt` | SHA-256 der öffentlichen Pakete und Begleitdateien |

Die vorhandene statische Downloadseite erhält beim Build eine serverseitig erzeugte, JavaScript-unabhängige Sektion mit direkten Links, Größenangaben, gekürzten Hashes, Commit und reproduzierbarem Zeitstempel.

## Inhalt der Quellpakete

In die beiden Archive gelangen ausschließlich:

- die 86 kanonischen Fachseiten;
- die zwölf kanonischen Kategorieindizes;
- Startseite, Root-Index und Repository-README;
- der kanonische Gesamtband;
- `MANIFEST.csv`;
- `MANIFEST.md`;
- `BUILD-REPORT.yaml`;
- die kanonische `SHA256SUMS.txt` des Repositorys;
- eine vorhandene Lizenzdatei;
- `BUNDLE-MANIFEST.json` und `BUNDLE-README.txt`, die beim Downloadbuild erzeugt werden.

Nicht aufgenommen werden:

- `.git/` und `.github/`;
- Skripte und Tests;
- technische Wartungsdokumente;
- `build/` und `site/`;
- lokale Obsidian-Daten;
- beliebige unbekannte Rootdateien;
- Symlinks oder Pfade außerhalb der Repositorywurzel.

Damit ist der Download kein ungefiltertes Repositoryarchiv, sondern ein absichtlich begrenztes Paket der öffentlichen kanonischen Inhalte.

## Build type v1

Der lokale und automatisierte Einstieg lautet:

```bash
python scripts/build_downloads.py \
  --root . \
  --site-dir site \
  --site-url https://example.invalid/Cheatsheets/ \
  --report build/reports/downloads.json
```

Voraussetzungen:

1. `site/` wurde im selben Lauf durch `scripts/build_site.py --strict` erzeugt.
2. `SOURCE_DATE_EPOCH` enthält den Commitzeitpunkt.
3. `site/downloads/index.html` ist vorhanden.
4. die kanonischen Content-, Link-, Security- und Metadatenprüfungen sind bereits grün.

Der Generator:

1. sammelt öffentliche Quellen anhand des Contentmodells und der bekannten Rootrollen;
2. liest ausschließlich reguläre Dateien innerhalb der Repositorywurzel;
3. sortiert Pfade Unicode- und Case-stabil;
4. erzeugt Quellmanifest und Gesamtbandkopie;
5. erzeugt ZIP und TAR.GZ mit fixierten Metadaten;
6. erzeugt Provenienz, Katalog und Prüfsummen;
7. ergänzt die bereits gerenderte Downloadseite;
8. liest sämtliche Ausgaben erneut ein und validiert sie fail-closed;
9. schreibt einen JSON-Bericht nach `build/reports/downloads.json`.

## Reproduzierbarkeit

### Gemeinsame Eingaben

Für denselben Byteoutput müssen identisch sein:

- Quellcommit;
- kanonische Quelldateien;
- `SOURCE_DATE_EPOCH`;
- Generatorversion;
- Ziel-Site-URL für Katalog und Provenienz.

### ZIP

Das ZIP verwendet:

- stabile lexikografische Reihenfolge;
- keine Verzeichniseinträge;
- regulären Unix-Dateimodus `0644`;
- einen aus `SOURCE_DATE_EPOCH` abgeleiteten Zeitstempel;
- `ZIP_STORED`, um zlib-abhängige Kompressionsunterschiede zu vermeiden;
- keine Extra-Felder, Symlinks oder absoluten Pfade.

### TAR.GZ

Das TAR.GZ verwendet:

- USTAR;
- UID und GID `0`;
- leere Benutzer- und Gruppennamen;
- Dateimodus `0644`;
- denselben festen Zeitstempel für TAR und Gzip-Header;
- stabile Eintragsreihenfolge;
- ausschließlich reguläre Dateien.

## Provenienzmodell

`provenance.intoto.json` ist ein:

```text
https://in-toto.io/Statement/v1
```

mit dem Prädikattyp:

```text
https://slsa.dev/provenance/v1
```

Die `subject`-Einträge nennen die drei Primärartefakte und das Quellmanifest jeweils mit SHA-256. Das Prädikat dokumentiert:

- Repository und Commit;
- Commitzeit als reproduzierbaren Buildzeitpunkt;
- optionale Site-URL;
- Generatorpfad und Generatorversion;
- Pages-Workflow als Builder-ID;
- den Git-Commit als aufgelöste Abhängigkeit.

Die Aussage ist eine überprüfbare Buildherkunft. Sie ist **keine kryptografische Signatur**. Eine spätere Sigstore-/GitHub-Attestationsstufe kann darauf aufbauen, ohne das Dateiformat der Downloads zu ändern.

## Lokale Prüfung

### SHA-256

```bash
cd site/downloads/files
sha256sum -c SHA256SUMS.txt
```

### Vollständiger Validator

```bash
python scripts/build_downloads.py \
  --root . \
  --site-dir site \
  --source-commit "$(git rev-parse HEAD)" \
  --report build/reports/downloads-check.json \
  --check-only
```

### ZIP inspizieren

```bash
unzip -l site/downloads/files/cheatsheets-markdown.zip
unzip -p site/downloads/files/cheatsheets-markdown.zip \
  Cheatsheets/BUNDLE-MANIFEST.json | less
```

### TAR.GZ inspizieren

```bash
tar -tzf site/downloads/files/cheatsheets-markdown.tar.gz
```

### Einzeldatei prüfen

```bash
sha256sum site/downloads/files/cheatsheets-gesamtband.md
```

Der Hash muss mit `SHA256SUMS.txt`, `catalog.json` und dem entsprechenden Provenienz-Subject übereinstimmen.

## Sicherheitsinvarianten

Der Build bricht ab bei:

- fehlendem oder verlinktem `site/`;
- Symlinkquellen;
- Pfadflucht;
- Case-insensitiven Quellkollisionen;
- mehreren oder fehlenden Gesamtbandquellen;
- einem bereits vorhandenen fremden Downloadverzeichnis ohne Generatormarker;
- unerwarteten Ausgabedateien;
- Symlinks, Hardlinks oder Sonderdateien in der Ausgabe;
- unsicheren Archivpfaden;
- Abweichungen zwischen Archiv und Quellmanifest;
- manipuliertem Gesamtband;
- fehlerhaften Prüfsummen;
- unvollständigem Katalog;
- fehlender oder mehrfacher Downloadsektion in HTML;
- falschem Commit oder ungültiger Provenienzstruktur.

Der Generator löscht ausschließlich `site/downloads/files/`, wenn dort sein eigener Marker vorhanden ist. Andere Verzeichnisse und unmarkierte Inhalte werden nicht entfernt.

## CI- und Pages-Vertrag

Sowohl `.github/workflows/validate.yml` als auch `.github/workflows/pages.yml` führen genau diese Reihenfolge aus:

```text
Strict-Site-Build
→ Downloadpakete und Provenienz
→ Pages-Artefaktvalidierung
```

Der Deploymentjob erzeugt oder verändert keine Dateien. Er veröffentlicht nur das bereits vollständig geprüfte Pages-Artefakt.

Der Diagnosebericht enthält danach zusätzlich:

```text
build/reports/downloads.json
```

mit:

- Quellcommit;
- Quellzeit;
- Anzahl der Quelldateien;
- Primärartefakten und Hashes;
- Gesamtgröße;
- deterministischem SHA-256 des Downloadbaums.

## Änderung und Wartung

Bei einer Änderung des Downloadformats sind gemeinsam zu aktualisieren:

- `scripts/build_downloads.py`;
- `tests/test_download_artifacts.py`;
- `tests/test_download_workflow_contract.py`;
- diese Dokumentation;
- gegebenenfalls `SCHEMA_VERSION` oder `GENERATOR_VERSION`.

Eine neue Schemaversion ist erforderlich, wenn sich die Bedeutung vorhandener JSON-Felder ändert. Reine zusätzliche optionale Felder können unter derselben Version ergänzt werden, wenn alte Leser weiterhin korrekt arbeiten.

## Rollback

Ein fehlerhaftes Downloadformat wird nicht manuell in `site/` repariert. Stattdessen:

1. den verursachenden Commit revertieren;
2. die vollständige Validate-Pipeline abwarten;
3. nach Merge den Pages-Workflow neu ausführen;
4. SHA-256 und Provenienz des neu veröffentlichten Stands prüfen.

Da Pages immer das vollständige Artefakt eines Commits veröffentlicht, gibt es keinen Mischstand aus alter Site und neuen Downloads.
