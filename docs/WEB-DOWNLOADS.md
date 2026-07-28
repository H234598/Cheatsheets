# Reproduzierbare Downloads und Provenienz

## Zweck

Phase 6 erzeugt sämtliche Basisdownloads im selben Prozess wie die Website. Phase 8A ergänzt diesen Satz um ein selbstenthaltendes Offline-HTML-Paket. Es gibt keinen separaten Checkout, keinen nachträglichen Release-Upload und keinen manuellen Austausch einzelner Dateien. Website, Quellarchiv, Offline-HTML, Gesamt-Markdown, Manifeste und Prüfsummen stammen daher immer aus demselben Commit und demselben `SOURCE_DATE_EPOCH`.

Die kanonischen Markdown-Dateien im Repository werden ausschließlich gelesen. Alle Ergebnisse entstehen unter:

```text
build/downloads/
```

und werden erst nach erfolgreichem Online- und Offline-Build nach:

```text
site/downloads/files/
```

kopiert. `build/`, `site/` und Downloadartefakte werden nicht nach `main` committed.

## Artefaktsatz

Der vollständige Site-Build erzeugt elf öffentliche Downloaddateien:

| Datei | Rolle |
|---|---|
| `Cheatsheets-Quellen.zip` | Obsidian-taugliches Quellarchiv |
| `Cheatsheets-Offline-HTML.zip` | selbstenthaltende dateibasierte HTML-Ausgabe |
| `Cheatsheet-Gesamtband.md` | reproduzierbar zusammengeführte 86 Fachseiten |
| `MANIFEST.csv` | maschinenlesbares Fachseitenmanifest |
| `MANIFEST.md` | menschenlesbare Manifestansicht |
| `BUILD-REPORT.yaml` | Umfang und Inhaltsfingerabdruck |
| `SOURCE-SHA256SUMS.txt` | Prüfsummen der Dateien im Quellarchiv |
| `PROVENANCE.json` | Quellcommit, Zeitpunkt, Umfang und Quellbaumhash |
| `DOWNLOAD-MANIFEST.json` | JSON-Inventar aller Downloaddateien |
| `DOWNLOAD-MANIFEST.csv` | CSV-Inventar aller Downloaddateien |
| `DOWNLOAD-SHA256SUMS.txt` | Prüfsummen des vollständigen Downloadsatzes außer sich selbst |

`Cheatsheets-Offline-HTML.zip` ist im Standalone-Aufruf von `build_downloads.py` optional, weil es den getrennten Offline-MkDocs-Build benötigt. Im zentralen `build_site.py` ist es verpflichtender Bestandteil des finalen Downloadsatzes. JSON, CSV, Prüfsummen und Landingpage führen nur tatsächlich erzeugte Artefakte auf.

Die öffentliche Seite `downloads/index.md` wird bei jedem Gesamtbuild aus den geprüften Artefaktdatensätzen neu geschrieben. Dateigrößen, Hashwerte, Commitangaben und die Anzahl der Artefakte werden nicht manuell gepflegt.

## Quellarchiv

`Cheatsheets-Quellen.zip` enthält:

- alle 86 Fachseiten;
- alle zwölf Kategorieindizes;
- Startseite, Root-Index, README und Wartungsdokumente;
- reale, Git-getrackte Inhaltsassets unter Kategorien sowie unter `assets/` oder `media/`;
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

Das Quellarchiv verwendet:

- stabil nach NFC-normalisiertem POSIX-Pfad sortierte Einträge;
- `ZIP_STORED`, also keine implementationsabhängige Kompressionsausgabe;
- feste Unix-Dateirechte `0644`;
- keine Extra- oder Kommentardatensätze;
- den Zeitstempel aus `SOURCE_DATE_EPOCH`;
- den frühesten zulässigen ZIP-Zeitpunkt 1980-01-01 als Fallbackuntergrenze;
- keine Symlinks, Hardlinks oder Sonderdateien.

Zwei Builds desselben Commits mit demselben `SOURCE_DATE_EPOCH` müssen bytegleiche ZIP-Dateien erzeugen.

## Offline-HTML

`Cheatsheets-Offline-HTML.zip` enthält den vollständigen statischen HTML-Baum mit relativen `.html`-Links und lokalen Assets. Es wird aus einer getrennten MkDocs-Konfiguration mit:

```yaml
use_directory_urls: false
```

erzeugt. Die Online-Site behält weiterhin Verzeichnis-URLs.

Zusätzliche Paketdateien:

```text
OFFLINE-LESEN.txt
OFFLINE-MANIFEST.json
OFFLINE-SHA256SUMS.txt
offline-server.py
```

Nutzung ohne Installation:

```text
ZIP entpacken → index.html öffnen
```

Vollständige lokale Suche, Filter, Favoriten und Fortschritt:

```bash
python offline-server.py
```

Der Server bindet ausschließlich an `127.0.0.1:8765` und benötigt keine externen Pythonpakete oder Internetverbindung.

Das Offlinepaket übernimmt die bereits geprüften Basisdownloads unter `downloads/files/`, nimmt sich selbst aber nicht rekursiv auf. Die finalen Downloadmanifeste außerhalb des ZIPs enthalten anschließend auch den Hash des Offlinepakets.

### Offline-Determinismus

Das Offline-ZIP verwendet ebenfalls:

- kanonisch sortierte POSIX-Pfade;
- `ZIP_STORED`;
- feste Rechte `0644`;
- leere ZIP-Kommentare und Extra-Felder;
- `SOURCE_DATE_EPOCH` mit Abrundung auf die vom ZIP-Format darstellbare Zwei-Sekunden-Auflösung;
- ausschließlich reguläre Dateien;
- keine Verzeichniseinträge, Symlinks, Hardlinks oder Sonderdateien.

`OFFLINE-MANIFEST.json` enthält Quellcommit, Zeitpunkt, kanonische Online-URL, jede Paketdatei mit Größe und SHA-256 sowie einen Baumhash. `OFFLINE-SHA256SUMS.txt` deckt sämtliche Dateien vor Hinzufügen der beiden selbstreferenziellen Integritätsdateien ab.

Der unabhängige Validator liest das fertige ZIP erneut ein, prüft Manifest, Prüfsummen, Baumhash, Rechte, Zeitstempel und Dateimenge, materialisiert es ohne Pfadflucht und validiert danach jede lokale HTML-/CSS-Referenz und jeden Fragmentanker.

Details stehen in `docs/WEB-OFFLINE.md`.

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

Die kanonische Online-URL wird im produktiven Workflow aus `actions/configure-pages` übernommen und lautet seit der bestätigten Custom-Domain-Aktivierung:

```text
https://cheatsheets.telacore.org/
```

Das Offline-Manifest übernimmt denselben Wert als Herkunfts- und Rückverweis.

## Manifeste und Selbstreferenz

JSON und CSV führen im vollständigen Site-Build alle elf Downloaddateien auf. Ein Manifest kann seinen eigenen endgültigen SHA-256 nicht ohne Selbstreferenzproblem in seinem Inhalt speichern. Deshalb gilt:

- normale Artefakte einschließlich Offline-ZIP tragen Größe und SHA-256 direkt im Manifest;
- die beiden Downloadmanifestdateien und `DOWNLOAD-SHA256SUMS.txt` sind ebenfalls als Dateien aufgeführt;
- ihre selbstreferenziellen Felder bleiben im Manifest leer;
- `DOWNLOAD-SHA256SUMS.txt` enthält die Hashwerte beider Downloadmanifeste und aller übrigen Dateien;
- nur die Prüfsummendatei selbst kann naturgemäß nicht ihren eigenen Hash enthalten.

Damit existiert keine Downloaddatei ohne Manifestzeile und jede unabhängig prüfbare Datei ist durch die Downloadprüfsummen abgedeckt.

## Sichere Dateizugriffe

Kanonische Dateien werden vor dem Öffnen mit `lstat` geprüft. Symlinks und nicht reguläre Dateien werden abgelehnt. Auf unterstützten Plattformen verhindert `O_NOFOLLOW`, dass ein Pfad zwischen Prüfung und Öffnen gegen einen Symlink ausgetauscht wird. Ein zusätzlicher Geräte-/Inode-Vergleich erkennt einen Dateiaustausch während des Öffnens.

Inhaltsassets und generierte Offlinequellen, die als Symlink vorliegen, blockieren den Build. Sie werden nicht stillschweigend ausgelassen oder dereferenziert.

Alle Artefakte entstehen zunächst in markierten Stagingverzeichnissen. Ein vorhandenes Ziel darf nur ersetzt werden, wenn es die Sentinel-Datei `.cheatsheets-build-root` trägt. Bei einem Fehler bleibt der vorherige vollständige Stand erhalten.

Der Offlinevalidator lehnt zusätzlich ab:

- absolute, Laufwerks- oder UNC-Archivpfade;
- `.`- und `..`-Segmente;
- Steuerzeichen und Backslashes in lokalen URLs;
- Case-insensitive Pfadkollisionen;
- externe Laufzeitassets;
- `<base>`, Meta-Refresh und unbekannte URL-Schemata;
- fehlende lokale Ziele oder Fragment-IDs;
- übergroße Archive oder Einträge.

## Einbindung in den Gesamtbuild

Der zentrale Ablauf lautet:

```text
1. Quellcommit und SOURCE_DATE_EPOCH bestimmen
2. Basisdownloads atomar unter build/downloads erzeugen
3. Webquellen atomar unter build/docs erzeugen
4. vorläufige Download-Landingpage schreiben
5. getrennte Offline-Site temporär mit relativen .html-URLs bauen
6. Basisdownloads in den Offlinebaum kopieren
7. Offlinebaum und lokale Referenzen prüfen
8. Offline-ZIP, Offline-Manifest und Offline-Prüfsummen erzeugen
9. Offline-ZIP unabhängig erneut prüfen
10. finalen Downloadsatz einschließlich Offline-ZIP erzeugen
11. finale Download-Landingpage schreiben
12. Online-MkDocs-Baum nach site-Staging bauen
13. geprüfte Downloaddateien nach site/downloads/files kopieren
14. vollständiges Pages-Artefakt validieren
15. Site atomar veröffentlichen
```

Die Downloaddateien werden erst nach dem Online-MkDocs-Lauf in den Sitebaum kopiert. Dadurch werden `.md`-Downloads nicht versehentlich als zusätzliche HTML-Seiten gerendert. Die Download-Landingpage verwendet bewusst statische `<a download>`-Links auf `files/<Dateiname>`.

## Lokale Nutzung

Basisdownloadbuild ohne Offline-MkDocs:

```bash
export SOURCE_DATE_EPOCH="$(git show -s --format=%ct HEAD)"
python scripts/build_downloads.py \
  --strict \
  --output build/downloads
```

Vollständiger Online-/Offline-Gesamtbuild:

```bash
export SOURCE_DATE_EPOCH="$(git show -s --format=%ct HEAD)"
python scripts/build_site.py \
  --strict \
  --site-url https://cheatsheets.telacore.org/
```

Offline-ZIP unabhängig prüfen und testweise entpacken:

```bash
python scripts/validate_offline_archive.py \
  --archive site/downloads/files/Cheatsheets-Offline-HTML.zip \
  --extract build/offline-site \
  --report build/reports/offline.json \
  --force
```

## Integrität prüfen

Unter Linux, macOS oder BSD im Downloadverzeichnis:

```bash
sha256sum -c DOWNLOAD-SHA256SUMS.txt
```

Einzeldateien unter PowerShell:

```powershell
Get-FileHash .\Cheatsheets-Quellen.zip -Algorithm SHA256
Get-FileHash .\Cheatsheets-Offline-HTML.zip -Algorithm SHA256
```

Ein Quellarchiv kann zusätzlich geprüft werden:

```bash
unzip -q Cheatsheets-Quellen.zip -d cheatsheets-source
cd cheatsheets-source
sha256sum -c SOURCE-SHA256SUMS.txt
```

Das Offline-ZIP sollte nicht mit einem beliebigen `unzip` in ein sicherheitsrelevantes Ziel extrahiert werden. Der Repositoryvalidator prüft Pfade und extrahiert ausschließlich atomar unter `build/`.

## CI-Gates

Die Pull-Request-CI führt den zentralen Site-Build aus. Dadurch blockieren:

- ein nicht reproduzierbarer Downloadsatz;
- ein ungültiger oder unvollständiger Quellcommit im Strict-Modus;
- veränderte Codefences im Gesamtband;
- Symlink-Inhaltsassets;
- fehlende Manifestdateien;
- falsche Downloadhashes;
- fehlgeschlagenes Kopieren in den Pages-Baum;
- ein beschädigtes, manipuliertes oder unsicheres Offline-ZIP;
- fehlende Offlineziele oder Fragmente;
- externe Offline-Laufzeitassets;
- defekte Offline-Navigation über Server oder `file://`;
- Überschreitung der Pages-Artefaktgrenzen.

Unit-, Integrations- und Browsertests prüfen unter anderem:

- bytegleiche Wiederholungsbuilds;
- vollständige JSON- und CSV-Manifeste;
- optionale und finale Aufnahme des Offline-ZIPs;
- Prüfsummen aller Dateien;
- Quellarchiveinträge, Sortierung, Zeitstempel und Rechte;
- ZIP-Zwei-Sekunden-Zeitnormalisierung;
- Ausschluss von `.github` und `.obsidian`;
- stabile Gesamtbandanker und fence-sichere Konvertierung;
- Site-Kopie mit erneutem Hashvergleich;
- fail-closed Behandlung von Symlinks und Pfadtraversal;
- unabhängige Offline-Manifest-, Prüfsummen- und Baumhashprüfung;
- lokale HTML-/CSS- und Fragmentauflösung;
- atomare Extraktion;
- Offline-Suche, Filter und Tastaturnavigation;
- No-JavaScript-Lesbarkeit direkt über `file://`.

## Noch optionale Erweiterungen

Nicht Bestandteil des gegenwärtigen Downloadbuilds sind:

- PDF;
- EPUB;
- PWA-/Service-Worker-Pakete;
- Wissensgraph-Export;
- signierte GitHub-Attestations;
- GitHub Releases als zweiter Veröffentlichungsort.

Diese Erweiterungen bleiben getrennte Phase-8-Arbeitsstränge. Sie dürfen Online-Build, Basisdownloads und Offline-HTML weder zur Laufzeit noch beim Rollback koppeln.
