# Reproduzierbare Downloads und Provenienz

## Zweck

Phase 6 erzeugt sämtliche öffentlichen Downloaddateien im selben Prozess wie die Website. Es gibt keinen separaten Checkout, keinen nachträglichen Release-Upload und keinen manuellen Austausch einzelner Dateien. Website, Quellarchiv, Gesamt-Markdown, Manifeste und Prüfsummen stammen daher immer aus demselben Commit und demselben `SOURCE_DATE_EPOCH`.

Die kanonischen Markdown-Dateien im Repository werden ausschließlich gelesen. Alle Ergebnisse entstehen unter:

```text
build/downloads/
```

und werden erst nach erfolgreichem MkDocs-Build nach:

```text
site/downloads/files/
```

kopiert. `build/`, `site/` und Downloadartefakte werden nicht nach `main` committed.

## Artefaktsatz

| Datei | Rolle |
|---|---|
| `Cheatsheets-Quellen.zip` | Obsidian-taugliches Quellarchiv |
| `Cheatsheet-Gesamtband.md` | reproduzierbar zusammengeführte 86 Fachseiten |
| `MANIFEST.csv` | maschinenlesbares Fachseitenmanifest |
| `MANIFEST.md` | menschenlesbare Manifestansicht |
| `BUILD-REPORT.yaml` | Umfang und Inhaltsfingerabdruck |
| `SOURCE-SHA256SUMS.txt` | Prüfsummen der Dateien im Quellarchiv |
| `PROVENANCE.json` | Quellcommit, Zeitpunkt, Umfang und Quellbaumhash |
| `DOWNLOAD-MANIFEST.json` | JSON-Inventar aller Downloaddateien |
| `DOWNLOAD-MANIFEST.csv` | CSV-Inventar aller Downloaddateien |
| `DOWNLOAD-SHA256SUMS.txt` | Prüfsummen des vollständigen Downloadsatzes außer sich selbst |

Die öffentliche Seite `downloads/index.md` wird bei jedem Gesamtbuild aus den geprüften Artefaktdatensätzen neu geschrieben. Dateigrößen, Hashwerte und Commitangaben werden nicht manuell gepflegt.

## Quellarchiv

`Cheatsheets-Quellen.zip` enthält:

- alle 86 Fachseiten;
- alle zwölf Kategorieindizes;
- Startseite, Root-Index, README und Wartungsdokumente;
- reale Inhaltsassets unter Kategorien sowie unter `assets/` oder `media/`;
- die generatorisch erwarteten Fassungen von `MANIFEST.csv`, `MANIFEST.md` und `BUILD-REPORT.yaml`;
- `SOURCE-SHA256SUMS.txt`;
- `LICENSE`, sofern vorhanden.

Ausgeschlossen sind insbesondere:

```text
.git/
.github/
.obsidian/
.venv/
build/
node_modules/
site/
tests/
__pycache__/
```

Das bereits versionierte Sammeldokument `Cheatsheet-Gesamtband.md` wird nicht in das Quellarchiv übernommen. Stattdessen wird es für jeden Build aus den realen Fachseiten neu erzeugt und als eigenes Artefakt angeboten. Damit kann ein historischer Sammelstand nicht unbemerkt vom aktuellen Inhalt abweichen.

### ZIP-Determinismus

Das Archiv verwendet:

- stabil nach NFC-normalisiertem POSIX-Pfad sortierte Einträge;
- `ZIP_STORED`, also keine implementationsabhängige Kompressionsausgabe;
- feste Unix-Dateirechte `0644`;
- keinen Extra- oder Kommentardatensatz;
- den Zeitstempel aus `SOURCE_DATE_EPOCH`;
- den frühesten zulässigen ZIP-Zeitpunkt 1980-01-01 als Fallbackuntergrenze;
- keine Symlinks, Hardlinks oder Sonderdateien.

Zwei Builds desselben Commits mit demselben `SOURCE_DATE_EPOCH` müssen deshalb bytegleiche ZIP-Dateien erzeugen.

## Gesamt-Markdown

`Cheatsheet-Gesamtband.md` wird ausschließlich aus den Fachseiten in der kanonischen Reihenfolge der Kategorieindizes erzeugt.

Jede Fachseite erhält:

- eine fortlaufende Manifestnummer;
- einen stabilen Page-ID-Anker;
- Kategorie;
- Quellpfad;
- SHA-256 der kanonischen Quelle.

Interne Wikilinks werden in lokale Anker umgewandelt. Überschriftenanker werden mit der Page-ID präfixiert, damit gleichnamige Abschnitte verschiedener Fachseiten nicht kollidieren. Links zu nicht enthaltenen Wartungsseiten werden als Text erhalten.

Codefences werden vor und nach der Konvertierung gehasht. Jede Veränderung eines geschützten Fence-Segments blockiert den Downloadbuild.

## Provenienz

`PROVENANCE.json` verwendet Schema-Version 1 und enthält mindestens:

```json
{
  "schema_version": 1,
  "source_repository": "H234598/Cheatsheets",
  "source_commit": "<40-stelliger Commit>",
  "source_date_epoch": 0,
  "generated_at": "1970-01-01T00:00:00Z",
  "reference_pages": 86,
  "categories": 12,
  "source_files": 0,
  "source_bytes": 0,
  "source_tree_sha256": "<SHA-256>",
  "zip_compression": "stored"
}
```

Der Quellbaumhash wird aus der sortierten Folge von Pfad und Dateihash berechnet:

```text
SHA256(
  path_1 + NUL + sha256(file_1) + LF +
  path_2 + NUL + sha256(file_2) + LF +
  ...
)
```

Er ist kein Ersatz für die Einzelprüfsummen, ermöglicht aber einen kompakten Vergleich des vollständigen Archivumfangs.

## Manifeste und Selbstreferenz

JSON und CSV führen alle zehn Downloaddateien auf. Ein Manifest kann seinen eigenen endgültigen SHA-256 nicht ohne Selbstreferenzproblem in seinem Inhalt speichern. Deshalb gilt:

- normale Artefakte tragen Größe und SHA-256 direkt im Manifest;
- die beiden Manifestdateien und `DOWNLOAD-SHA256SUMS.txt` sind ebenfalls als Dateien aufgeführt;
- ihre selbstreferenziellen Felder bleiben im Manifest leer;
- `DOWNLOAD-SHA256SUMS.txt` enthält die Hashwerte beider Manifestdateien und aller übrigen Dateien;
- nur die Prüfsummendatei selbst kann naturgemäß nicht ihren eigenen Hash enthalten.

Damit existiert keine Downloaddatei ohne Manifestzeile und jede unabhängig prüfbare Datei ist durch die Downloadprüfsummen abgedeckt.

## Sichere Dateizugriffe

Kanonische Dateien werden vor dem Öffnen mit `lstat` geprüft. Symlinks und nicht reguläre Dateien werden abgelehnt. Auf unterstützten Plattformen verhindert `O_NOFOLLOW`, dass ein Pfad zwischen Prüfung und Öffnen gegen einen Symlink ausgetauscht wird. Ein zusätzlicher Geräte-/Inode-Vergleich erkennt einen Dateiaustausch während des Öffnens.

Inhaltsassets, die als Symlink vorliegen, blockieren den Build. Sie werden nicht stillschweigend ausgelassen oder dereferenziert.

Alle Artefakte entstehen zunächst in einem markierten Stagingverzeichnis. Ein vorhandenes Ziel darf nur ersetzt werden, wenn es die Sentinel-Datei `.cheatsheets-build-root` trägt. Bei einem Fehler bleibt der vorherige vollständige Stand erhalten.

## Einbindung in den Webbuild

Der zentrale Ablauf lautet:

```text
1. Quellcommit und SOURCE_DATE_EPOCH bestimmen
2. Downloadartefakte atomar unter build/downloads erzeugen
3. Webquellen atomar unter build/docs erzeugen
4. Download-Landingpage aus den Artefaktdatensätzen schreiben
5. MkDocs genau einmal nach site-Staging bauen
6. geprüfte Downloaddateien nach site/downloads/files kopieren
7. vollständiges Pages-Artefakt validieren
8. Site atomar veröffentlichen
```

Die Downloaddateien werden erst nach MkDocs kopiert. Dadurch werden `.md`-Downloads nicht versehentlich als zusätzliche HTML-Seiten gerendert. Die Download-Landingpage verwendet bewusst statische `<a download>`-Links auf `files/<Dateiname>`.

## Lokale Nutzung

Vollständiger Downloadbuild:

```bash
export SOURCE_DATE_EPOCH="$(git show -s --format=%ct HEAD)"
python scripts/build_downloads.py \
  --strict \
  --output build/downloads
```

Prüflauf in einem temporären Verzeichnis:

```bash
export SOURCE_DATE_EPOCH="$(git show -s --format=%ct HEAD)"
python scripts/build_downloads.py --check
```

Der normale Gesamtbuild erzeugt dieselben Dateien automatisch:

```bash
export SOURCE_DATE_EPOCH="$(git show -s --format=%ct HEAD)"
python scripts/build_site.py \
  --strict \
  --site-url https://example.invalid/Cheatsheets/
```

## Integrität prüfen

Unter Linux, macOS oder BSD im Downloadverzeichnis:

```bash
sha256sum -c DOWNLOAD-SHA256SUMS.txt
```

Einzeldatei unter PowerShell:

```powershell
Get-FileHash .\Cheatsheets-Quellen.zip -Algorithm SHA256
```

Ein Quellarchiv kann zusätzlich geprüft werden:

```bash
unzip -q Cheatsheets-Quellen.zip -d cheatsheets-source
cd cheatsheets-source
sha256sum -c SOURCE-SHA256SUMS.txt
```

## CI-Gates

Die vorhandene Pull-Request-CI führt weiterhin den zentralen Site-Build aus. Dadurch blockieren nun zusätzlich:

- ein nicht reproduzierbarer Downloadsatz;
- ein ungültiger oder unvollständiger Quellcommit im Strict-Modus;
- veränderte Codefences im Gesamtband;
- Symlink-Inhaltsassets;
- fehlende Manifestdateien;
- falsche Downloadhashes;
- fehlgeschlagenes Kopieren in den Pages-Baum;
- Überschreitung der Pages-Artefaktgrenzen.

Unit-Tests prüfen:

- bytegleiche Wiederholungsbuilds;
- vollständige JSON- und CSV-Manifeste;
- Prüfsummen aller Dateien;
- Quellarchiveinträge, Sortierung, Zeitstempel und Rechte;
- Ausschluss von `.github` und `.obsidian`;
- stabile Gesamtbandanker und fence-sichere Konvertierung;
- Site-Kopie mit erneutem Hashvergleich;
- fail-closed Behandlung von Symlink-Assets.

## Nicht Bestandteil von Phase 6

Noch nicht erzeugt werden:

- Offline-HTML-ZIP;
- PDF;
- EPUB;
- PWA-/Service-Worker-Pakete;
- GitHub Releases als zweiter Veröffentlichungsort.

Diese Erweiterungen bleiben Phase 8 vorbehalten. Der Online-Build und der gegenwärtige Downloadsatz benötigen keine optionalen Exportabhängigkeiten.
