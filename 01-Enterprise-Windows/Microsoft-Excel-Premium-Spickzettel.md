---
title: "Microsoft Excel – Premium-Spickzettel"
aliases: ["MS Excel Cheatsheet", "Excel Formeln", "Excel Shortcuts"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [microsoft, excel, office, spreadsheets, data, shortcuts]
source: "https://support.microsoft.com/de-de/office/was-ist-excel-26f581fb-8c4d-4cdb-9bf3-51f74598ec33"
---

# Microsoft Excel – Premium-Spickzettel

> [!abstract] Zweck
> Praxisreferenz für Tabellenmodelle, Formeln, strukturierte Tabellen, Nachschlagen, PivotTables, Power Query, Datenprüfung, Performance, Sicherheit und Tastenkürzel.

> [!important]
> Excel ist zugleich Rechenblatt, Analysewerkzeug und einfache Anwendungslaufzeit. Je kritischer ein Modell, desto wichtiger sind klare Eingaben, getrennte Berechnungen, Prüfungen, Versionskontrolle und ein dokumentierter Eigentümer.

## Inhalt

- [[#Sauberes Arbeitsmappenmodell]]
- [[#Bezüge und Formeln]]
- [[#Wichtige Funktionen]]
- [[#Strukturierte Tabellen]]
- [[#Daten bereinigen und Power Query]]
- [[#PivotTables und Auswertung]]
- [[#Datenprüfung und Fehlerkontrollen]]
- [[#Performance und Dateigröße]]
- [[#Tastenkürzel]]
- [[#Diagnose]]

## Sauberes Arbeitsmappenmodell

Empfohlene Schichten:

```text
00_README      Annahmen, Version, Verantwortlicher
10_INPUT       manuelle Eingaben, klar markiert
20_IMPORT      Rohdaten, möglichst unverändert
30_CALC        Berechnungen und Hilfsspalten
40_OUTPUT      Berichte, PivotTables, Diagramme
90_CHECKS      Kontrollsummen und Plausibilitäten
```

### Regeln

- Eine Zeile = ein Datensatz, eine Spalte = ein Merkmal.
- Keine verbundenen Zellen in Datenbereichen.
- Einheiten in Überschrift oder separater Spalte dokumentieren.
- Datumswerte als echte Datumszahlen speichern, nicht als Text.
- Eingaben und Formeln optisch und technisch trennen.
- Harte Konstanten nicht in komplexen Formeln verstecken.
- Externe Links und volatile Funktionen minimieren.
- Kritische Annahmen auf einer README-Seite dokumentieren.

## Bezüge und Formeln

| Bezug | Verhalten beim Kopieren |
|---|---|
| `A1` | Zeile und Spalte relativ |
| `$A$1` | beides absolut |
| `$A1` | Spalte fix, Zeile relativ |
| `A$1` | Zeile fix, Spalte relativ |

Mit `F4` beim Bearbeiten zwischen Bezugstypen wechseln.

### Lesbare Formel

Statt:

```excel
=WENN(B2="";"";RUNDEN(B2*C2*(1-D2);2))
```

Bei modernen Excel-Versionen mit `LET`:

```excel
=LET(
  Menge;B2;
  Preis;C2;
  Rabatt;D2;
  WENN(Menge="";"";RUNDEN(Menge*Preis*(1-Rabatt);2))
)
```

> [!note]
> Funktionsnamen und Argumenttrenner hängen von Sprache/Region ab. In deutschsprachigem Excel ist häufig `;`, in englischem Excel `,` üblich.

## Wichtige Funktionen

### Aggregation

```excel
=SUMME(Tabelle1[Umsatz])
=MITTELWERTWENNS(Tabelle1[Umsatz];Tabelle1[Region];H2)
=SUMMEWENNS(Tabelle1[Umsatz];Tabelle1[Region];H2;Tabelle1[Jahr];H3)
=ZÄHLENWENNS(Tabelle1[Status];"Offen")
```

### Fehlerbehandlung

```excel
=WENNFEHLER(A2/B2;"")
```

Nicht jeden Fehler blind verschlucken. Für Prüfzellen besser sichtbar machen:

```excel
=WENN(B2=0;"FEHLER: Nenner 0";A2/B2)
```

### Nachschlagen

Modern:

```excel
=XVERWEIS(A2;Stamm[ID];Stamm[Name];"nicht gefunden")
```

Mehrere Kriterien über Hilfsschlüssel oder boolesche Arrays:

```excel
=XVERWEIS(1;(Stamm[ID]=A2)*(Stamm[Region]=B2);Stamm[Wert];"nicht gefunden")
```

Klassisch:

```excel
=INDEX(Stamm[Name];VERGLEICH(A2;Stamm[ID];0))
```

### Dynamische Arrays

```excel
=EINDEUTIG(Tabelle1[Region])
=SORTIEREN(EINDEUTIG(Tabelle1[Region]))
=FILTER(Tabelle1;Tabelle1[Status]="Offen";"keine Treffer")
```

Spill-Fehler `#ÜBERLAUF!` entsteht meist, wenn Zielzellen nicht leer sind oder dynamische Arrays in ungeeignetem Kontext stehen.

### Datum

```excel
=HEUTE()
=JETZT()
=MONATSENDE(A2;0)
=ARBEITSTAG(A2;10;Feiertage[Datum])
=NETTOARBEITSTAGE(A2;B2;Feiertage[Datum])
```

`HEUTE()` und `JETZT()` sind volatil und ändern sich bei Neuberechnung.

## Strukturierte Tabellen

Datenbereich markieren:

```text
Ctrl + T
```

Vorteile:

- automatische Erweiterung
- Filter und Tabellenformat
- lesbare strukturierte Verweise
- robuste Pivot-/Power-Query-Quelle
- berechnete Spalten
- Ergebniszeile

Beispiel:

```excel
=[@Menge]*[@Einzelpreis]
```

> [!warning]
> Eine Tabellenzeile sollte logisch atomar bleiben. Zwischensummen, Leerzeilen und dekorative Überschriften gehören nicht in den Rohdatenbereich.

## Daten bereinigen und Power Query

### Power Query eignet sich für

- CSV/Excel/Ordner/SharePoint/Datenbank importieren
- Datentypen setzen
- Spalten teilen/vereinigen
- Joins und Anhängen
- wiederholbare Bereinigung
- Entpivotieren breiter Monatsstrukturen
- Refresh statt Copy-and-paste

Ablauf:

```text
Quelle → Datentypen → Bereinigung → Schlüssel prüfen → Join → Ausgabe
```

### Grundregeln

- Rohquelle nicht manuell verändern.
- Schritte sinnvoll benennen.
- Datentypen früh, aber nach nötiger Textbereinigung setzen.
- Joins auf eindeutige Schlüssel prüfen.
- Zeilenanzahl vor/nach Schritten kontrollieren.
- Zugangsdaten und Datenschutz der Datenquelle beachten.
- Abfrageabhängigkeiten dokumentieren.

## PivotTables und Auswertung

1. Quelle als Tabelle formatieren.
2. **Einfügen → PivotTable**.
3. Dimensionen in Zeilen/Spalten, Kennzahlen in Werte.
4. Wertfeldeinstellung prüfen: Summe, Anzahl, Mittelwert usw.
5. Datumsfelder gruppieren oder Kalenderdimension verwenden.
6. Aktualisierung nach Datenänderung durchführen.
7. Filter/Slicer sinnvoll benennen.

> [!warning]
> Eine PivotTable kann alte Elemente im Cache behalten. Bei sensiblen Daten Aufbewahrung gelöschter Elemente und Dateiverteilung prüfen.

## Datenprüfung und Fehlerkontrollen

### Eingabevalidierung

```text
Daten → Datenüberprüfung
```

Geeignet für:

- Listenwerte
- Wertebereiche
- Datumsgrenzen
- Textlänge
- benutzerdefinierte Prüf Formel

### Kontrollblatt

Beispiele:

```excel
=ANZAHL2(Input[ID])-ANZAHL(EINDEUTIG(Input[ID]))
```

Besser als klare Dublettenprüfung:

```excel
=ZEILEN(Input[ID])-ZEILEN(EINDEUTIG(Input[ID]))
```

Summenabgleich:

```excel
=SUMME(Import[Betrag])-SUMME(Output[Betrag])
```

Status:

```excel
=WENN(ABS(B2)<0,01;"OK";"PRÜFEN")
```

### Formeln anzeigen

```text
Ctrl + `
```

Formelauswertung:

```text
Formeln → Formelauswertung
```

## Performance und Dateigröße

Häufige Bremsen:

- ganze Spalten in Arrayformeln
- tausende volatile Funktionen wie `INDIREKT`, `BEREICH.VERSCHIEBEN`, `JETZT`
- viele bedingte Formatierungen
- externe Verknüpfungen
- übergroßer „verwendeter Bereich“
- wiederholte identische komplexe Teilberechnungen
- viele einzeln importierte Bilder/Objekte

Verbesserungen:

- strukturierte Tabellen und begrenzte Bereiche
- `LET` für wiederverwendete Teilausdrücke
- Power Query statt Formelkaskaden für ETL
- Pivot/Datenmodell für große Aggregationen
- Hilfsspalten, wenn sie Lesbarkeit und Rechenaufwand verbessern
- unnötige Formatierung außerhalb des Datenbereichs löschen
- Berechnungsmodus nur bewusst auf manuell setzen

Berechnungsstatus:

```text
F9          Arbeitsmappen neu berechnen
Shift+F9    aktives Blatt
Ctrl+Alt+F9 vollständige Neuberechnung
```

## Tastenkürzel

| Aktion | Kürzel |
|---|---|
| Neue Arbeitsmappe | `Ctrl+N` |
| Speichern | `Ctrl+S` |
| Tabelle erstellen | `Ctrl+T` |
| Filter ein/aus | `Ctrl+Shift+L` |
| Zellen formatieren | `Ctrl+1` |
| aktuelle Zeit/Datum | `Ctrl+Shift+;` / `Ctrl+;` |
| Zeile/Spalte markieren | `Shift+Leertaste` / `Ctrl+Leertaste` |
| Bereich bis Rand | `Ctrl+Shift+Pfeil` |
| letzte Zelle | `Ctrl+End` |
| Formel nach unten/rechts | `Ctrl+D` / `Ctrl+R` |
| AutoSumme | `Alt+=` |
| absoluten Bezug wechseln | `F4` |
| aktive Zelle bearbeiten | `F2` |
| Zeilenumbruch in Zelle | `Alt+Enter` |
| Suchen/Ersetzen | `Ctrl+F` / `Ctrl+H` |
| Blatt wechseln | `Ctrl+Bild↑/Bild↓` |
| Formeln anzeigen | `Ctrl+`` |
| Flash Fill | `Ctrl+E` |

## Sicherheit

- Makros aus unbekannter Quelle nicht aktivieren.
- `.xlsm`, externe Datenverbindungen und Add-ins vor Freigabe inventarisieren.
- Formeln gegen CSV-/Formel-Injektion absichern, wenn Daten exportiert werden.
- ausgeblendete Blätter/Zeilen sind keine Zugriffskontrolle.
- Kennwortschutz eines Arbeitsblatts ist kein starker Dateischutz.
- vertrauliche Daten minimieren und Rechte über geeignetes Speichersystem steuern.

## Diagnose

### Formel zeigt Text

- Zellenformat „Text“?
- führendes Apostroph?
- **Formeln anzeigen** aktiv?
- Formel neu mit `F2`, `Enter` bestätigen.

### `#NV`

- Suchwert und Schlüsseltyp identisch?
- unsichtbare Leerzeichen?
- Zahl als Text?
- exakte Suche verwendet?
- Schlüssel eindeutig?

Bereinigung:

```excel
=GLÄTTEN(SÄUBERN(A2))
=WERT(A2)
```

### Zahlen stimmen nicht

1. Filter und ausgeblendete Zeilen prüfen.
2. Rundungslogik und Einheit prüfen.
3. Textzahlen identifizieren.
4. Berechnungsmodus kontrollieren.
5. externe Links aktualisiert?
6. Kontrollsummen je Verarbeitungsschritt vergleichen.
7. PivotTable aktualisieren.

### Datei ungewöhnlich groß

- `Ctrl+End`: liegt letzte verwendete Zelle weit außerhalb?
- unnötige Zeilen/Spalten vollständig löschen, speichern, neu öffnen
- Bilder komprimieren
- bedingte Formatierung und Namen prüfen
- externe Verbindungen, Pivot-Caches und eingebettete Objekte inventarisieren

## Quellen
- [Microsoft: Was ist Excel?](https://support.microsoft.com/de-de/office/was-ist-excel-26f581fb-8c4d-4cdb-9bf3-51f74598ec33)
- [Microsoft: Übersicht über Formeln](https://support.microsoft.com/de-de/office/%C3%BCbersicht-%C3%BCber-formeln-in-excel-ecfdc708-9162-49e8-b993-c311f47ca173)
- [Microsoft: Power Query für Excel](https://support.microsoft.com/de-de/office/informationen-zu-power-query-in-excel-7104fbee-9e62-4cb9-a02e-5bfb1a6c536a)

## Verwandte Notizen
- [[Microsoft-Word-Premium-Spickzettel]]
- [[Microsoft-Visio-Premium-Spickzettel]]
- [[Python-3-Premium-Spickzettel]]
