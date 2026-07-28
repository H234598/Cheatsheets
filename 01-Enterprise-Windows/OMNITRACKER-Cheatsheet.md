---
title: "OMNITRACKER – Cheatsheet"
aliases: ["OMNINET OMNITRACKER", "OMNITRACKER Administration", "OMNITRACKER ITSM"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [omnitracker, itsm, workflow, enterprise, service-management]
source: "https://www.omnitracker.com/en/products/interfaces/"
---

# OMNITRACKER – Cheatsheet

> [!abstract] Zweck
> Praxisreferenz für Anwender, Administratoren und Integratoren von OMNITRACKER: Grundmodell, Objekte, Workflows, Sichten, Berechtigungen, Schnittstellen, Betrieb und Fehlersuche.

> [!note] Versions- und kundenspezifisch
> OMNITRACKER ist stark konfigurierbar. Bezeichnungen, Masken, Statuswerte, Pflichtfelder, Rollen und API-Endpunkte unterscheiden sich je Installation. Dieser Spickzettel beschreibt das belastbare Grundmodell; lokale Betriebsdokumentation und Herstellerhandbuch haben Vorrang.

## Inhalt

- [[#Grundmodell]]
- [[#Typischer Arbeitsablauf]]
- [[#Suchen, Filtern und Sichten]]
- [[#Objekte sauber bearbeiten]]
- [[#Workflows und Statuswechsel]]
- [[#Berechtigungen und Rollen]]
- [[#Administration und Konfiguration]]
- [[#Schnittstellen und Automatisierung]]
- [[#Betrieb, Sicherung und Änderungen]]
- [[#Diagnose-Reihenfolge]]
- [[#Schnellreferenz]]

## Grundmodell

| Begriff | Bedeutung |
|---|---|
| **Objekt** | Datensatz wie Incident, Change, Auftrag, Asset, Person oder Projekt |
| **Objekttyp** | Schema eines Objekts mit Feldern, Regeln, Formularen und Rechten |
| **Ordner** | Logische Sammlung von Objekten oder Konfigurationselementen |
| **Workflow** | Zustände, Übergänge, Prüfungen und automatische Aktionen |
| **Maske/Formular** | Benutzeroberfläche für Anzeige und Bearbeitung |
| **Sicht/View** | Gefilterte und sortierte Darstellung von Objekten |
| **Rolle** | Bündel fachlicher oder technischer Berechtigungen |
| **Regel/Aktion** | Automatisierung bei Ereignissen, Fristen oder Statuswechseln |
| **Interface Bus** | Integrationsschicht für REST-/SOAP-Webservices und Fremdsysteme |
| **Automation Interface** | Programmierschnittstelle für Skripte und externe Anwendungen |

Ein belastbares mentales Modell:

```text
Benutzer/Rolle
      │
      ▼
Maske ──► Objekt ──► Workflow/Status
  │         │              │
  │         ├── Historie   ├── Regeln
  │         ├── Anhänge    ├── Benachrichtigungen
  │         └── Relationen └── Eskalationen
  │
  └── Sicht/Filter
```

## Typischer Arbeitsablauf

1. Passende Anwendung und Sicht öffnen.
2. Vorhandenes Objekt suchen, bevor ein Duplikat angelegt wird.
3. Pflicht- und Klassifizierungsfelder vollständig erfassen.
4. Betroffene Person, Organisation, Service oder Asset verknüpfen.
5. Beschreibung mit **Ist-Zustand, Soll-Zustand, Reproduktion und Auswirkung** schreiben.
6. Zuständigkeit und Priorität nach lokaler Matrix setzen.
7. Statuswechsel bewusst ausführen; dabei ausgelöste Regeln beachten.
8. Lösung, Kommunikationsverlauf und Nachweise dokumentieren.
9. Objekt erst schließen, wenn Abschlusskriterien erfüllt sind.

### Gute Ticketbeschreibung

```text
Kurzbeschreibung:
VPN-Anmeldung scheitert seit 07:35 Uhr für Standort Nord

Auswirkung:
18 Benutzer betroffen, keine externe Einwahl möglich

Reproduktion:
1. Client starten
2. Benutzername eingeben
3. MFA bestätigen
4. Fehler 809 erscheint

Bereits geprüft:
- Internetzugang vorhanden
- Zertifikat gültig
- Gegenprobe mit zweitem Gerät identisch

Erwartung:
Erfolgreicher Aufbau des VPN-Tunnels
```

> [!tip] Historie statt Überschreiben
> Neue Erkenntnisse als nachvollziehbare Aktivität oder Kommentar ergänzen. Frühere Aussagen nicht stillschweigend ersetzen, wenn dadurch die Chronologie verloren geht.

## Suchen, Filtern und Sichten

### Suchstrategie

| Ziel | Vorgehen |
|---|---|
| Exakte ID bekannt | Nach Objekt-ID oder Schlüssel suchen |
| Person/Asset bekannt | Über Relation oder Stammdatenfeld filtern |
| Fehlertext bekannt | Volltextsuche plus Zeitraum und Objekttyp |
| Offene eigene Arbeit | Zuständigkeit = eigener Benutzer/Gruppe, Abschlussstatus ausschließen |
| Eskalationsrisiko | SLA-/Fälligkeitsfeld, Priorität und Status kombinieren |
| Dubletten | Kurzbeschreibung, Melder, CI und enger Zeitraum vergleichen |

Sichten sollten mindestens enthalten:

- Objekt-ID
- Kurzbeschreibung
- Status
- Priorität
- Zuständige Gruppe/Person
- Ersteller oder Melder
- Erstellungs- und Änderungszeit
- Fälligkeit beziehungsweise SLA
- betroffenen Service oder CI

> [!warning] Persönliche Sichten sind keine Prozesslogik
> Ein Filter ändert nicht den Datensatz und ersetzt keine fachliche Regel. Kritische Steuerung gehört in Workflow, Berechtigungen oder serverseitige Automatisierung.

## Objekte sauber bearbeiten

### Vor dem Speichern prüfen

- Ist der richtige Objekttyp gewählt?
- Stimmen Kunde, Organisation und betroffene Person?
- Ist das richtige Configuration Item oder Asset verknüpft?
- Entspricht die Priorität der lokalen Auswirkungs-/Dringlichkeitsmatrix?
- Ist der Verantwortliche tatsächlich zuständig oder nur informiert?
- Sind personenbezogene oder geheime Daten wirklich erforderlich?
- Sind Anhänge virengeprüft und sinnvoll benannt?
- Wird durch den Statuswechsel eine E-Mail, Eskalation oder Schnittstelle ausgelöst?

### Relationen statt Freitext

Bevorzugen:

```text
Incident ── betrifft ──► Service
Incident ── gemeldet von ──► Person
Change   ── ändert ──► Configuration Item
Problem  ── verursacht ──► Incident-Sammlung
```

Relationen ermöglichen Reporting, Auswirkungsanalyse und konsistente Stammdaten. Freitext bleibt für Kontext, nicht für strukturierbare Kerndaten.

## Workflows und Statuswechsel

Ein Statuswechsel kann auslösen:

- Pflichtfeldprüfungen
- Rechtewechsel
- Zeitstempel und SLA-Stopps
- E-Mail-Benachrichtigungen
- Folgeobjekte oder Aufgaben
- Schnittstellenaufrufe
- Genehmigungen
- Eskalationen
- Archivierung

### Sichere Änderung eines Workflows

1. Ist-Prozess und Zielprozess dokumentieren.
2. Betroffene Objekttypen, Regeln, Masken, Sichten und Berichte identifizieren.
3. Änderung in Test-/Staging-Umgebung umsetzen.
4. Positiv-, Negativ- und Berechtigungstests durchführen.
5. Migration vorhandener Objekte planen.
6. Rückfallplan und Export/Sicherung erstellen.
7. Fachliche Abnahme einholen.
8. In Wartungsfenster ausrollen und Logs überwachen.

> [!danger] Statuswerte nicht „mal eben“ löschen
> Historische Objekte, Auswertungen, Regeln und Schnittstellen können auf interne IDs oder Werte verweisen. Werte bevorzugt deaktivieren oder migrieren, statt sie unkontrolliert zu entfernen.

## Berechtigungen und Rollen

Prüfebenen:

```text
Anmeldung
  └─ Lizenz/Clientzugriff
      └─ Anwendung/Ordner
          └─ Objekttyp
              └─ Objekt/Datensatz
                  └─ Feld/Aktion/Statuswechsel
```

### Prinzipien

- Rollen statt Einzelrechte verwenden.
- Lesen, Erstellen, Ändern, Löschen und Statuswechsel getrennt betrachten.
- Servicekonten minimal berechtigen und nicht interaktiv nutzen.
- Administrative Rollen zeitlich und organisatorisch begrenzen.
- Testbenutzer je Rollentyp vorhalten.
- Rechteänderungen protokollieren und regelmäßig rezertifizieren.

### Diagnose bei „Objekt nicht sichtbar“

1. Richtige Umgebung und Anwendung?
2. Filter oder Sicht schließt das Objekt aus?
3. Objekt archiviert oder in anderem Ordner?
4. Benutzer Mitglied der erwarteten Gruppe/Rolle?
5. Leserecht auf Objekttyp und konkretes Objekt?
6. Feld-/Mandantenfilter oder Organisationseinschränkung?
7. Replikation, Cache oder Anmeldetoken veraltet?

## Administration und Konfiguration

### Änderungsobjekte inventarisieren

| Bereich | Beispiele |
|---|---|
| Datenmodell | Objekttypen, Felder, Listenwerte, Relationen |
| Oberfläche | Masken, Register, Pflichtfelder, Standardwerte |
| Prozess | Status, Übergänge, Regeln, Timer, Eskalationen |
| Sicherheit | Rollen, Gruppen, Objekt- und Feldrechte |
| Integration | REST, SOAP, E-Mail, Datenbank-Views, Skripte |
| Ausgabe | Reports, Exporte, Dashboards, Vorlagen |
| Betrieb | Dienste, Jobs, Logs, Lizenzen, Backups |

### Konfigurationsdisziplin

- Eindeutige Präfixe für kundeneigene Objekte nutzen.
- Zweck, Eigentümer, Abhängigkeiten und Änderungsgrund dokumentieren.
- Keine produktiven Experimente mit anonymen Skripten.
- Wiederverwendbare Regeln statt Kopien bevorzugen.
- Zeit- und Gebietsschema explizit testen.
- Performance bei Massendaten und breiten Sichten messen.

## Schnittstellen und Automatisierung

OMNITRACKER stellt je nach Lizenz und Ausbau unter anderem REST-/SOAP-Webservices, Interface Bus, Automation Interface, E-Mail-Gateway, Datenbank-Views und weitere Gateways bereit.

### Integrations-Checkliste

```text
[ ] Richtung: eingehend, ausgehend oder bidirektional
[ ] Identität: technisches Konto, Zertifikat, Token oder anderes Verfahren
[ ] Datenvertrag: Felder, Datentypen, Pflichtwerte, Zeichensatz
[ ] Schlüssel: stabile externe ID statt nur Anzeigename
[ ] Idempotenz: Wiederholung erzeugt keine Dublette
[ ] Fehlerkanal: Retry, Dead-Letter, Alarmierung
[ ] Rate/Batch: Lastgrenzen und Zeitfenster
[ ] Datenschutz: Minimierung, Löschung, Maskierung
[ ] Monitoring: Korrelation-ID und nachvollziehbare Logs
[ ] Rollback: Rücksetz- oder Kompensationsweg
```

### Generisches REST-Muster

```bash
curl --fail-with-body \
  --request GET \
  --header 'Accept: application/json' \
  --header 'Authorization: Bearer <TOKEN>' \
  'https://omnitracker.example.org/<installationsspezifischer-endpunkt>'
```

```powershell
$headers = @{
  Accept        = 'application/json'
  Authorization = 'Bearer <TOKEN>'
}
Invoke-RestMethod `
  -Uri 'https://omnitracker.example.org/<endpunkt>' `
  -Headers $headers `
  -Method Get
```

> [!important] Keine universellen Endpunkte erfinden
> Basis-URL, Authentisierung, Objektpfade, Feldnamen und Payload hängen von Version, Interface-Bus-Konfiguration und kundenspezifischem Datenmodell ab. WSDL/OpenAPI beziehungsweise lokale Schnittstellendokumentation verwenden.

## Betrieb, Sicherung und Änderungen

### Vor Wartung

- aktiven Benutzer- und Jobbetrieb prüfen
- Datenbank- und Anwendungssicherung verifizieren
- Schnittstellen pausieren oder Pufferung sicherstellen
- geplante Jobs, Mailabruf und Eskalationen berücksichtigen
- Lizenz- und Zertifikatsstatus prüfen
- Ansprechpartner und Rückfallkriterium festlegen

### Monitoring-Signale

- Anwendung und Webclient erreichbar
- Datenbankverbindung stabil
- Hintergrundjobs ohne Rückstau
- E-Mail-Ein-/Ausgang aktuell
- Integrationsfehler und Retry-Warteschlangen
- Speicher, CPU, Datenbankwachstum und Logvolumen
- Lizenz- oder Zertifikatsablauf
- ungewöhnliche Anmelde- oder Berechtigungsfehler

## Diagnose-Reihenfolge

```text
1. Betroffener Benutzer, Zeitpunkt, Objekt-ID und Aktion erfassen
2. Fehler reproduzieren oder Screenshot/Fehlertext sichern
3. Client-/Browserproblem gegen zweiten Client abgrenzen
4. Sicht/Filter und Berechtigungen prüfen
5. Workflowregel, Pflichtfeld und Statusübergang prüfen
6. Server-, Job- und Schnittstellenlogs korrelieren
7. Datenbank-/Netzwerk-/TLS-Abhängigkeiten prüfen
8. Letzte Konfigurationsänderung und Deployment vergleichen
9. Nur gezielt neu starten; Beweise vorher sichern
10. Ursache, Behebung und Prävention im Ticket dokumentieren
```

### Typische Fehlerbilder

| Symptom | Häufige Ursache | Erste Prüfung |
|---|---|---|
| Speichern nicht möglich | Pflichtfeld, Validierungsregel, fehlendes Recht | Meldung, Feldmarkierungen, Rolle |
| Objekt fehlt | Filter, Mandant, Ordner, Leserecht | unbeschränkte Testsicht, Admin-Gegenprobe |
| E-Mail bleibt aus | Regelbedingung, Mailjob, Adresse, SMTP | Objekt-Historie, Queue, Mail-Log |
| Schnittstelle erzeugt Dubletten | kein stabiler Schlüssel, fehlende Idempotenz | externe ID und Retry-Verhalten |
| Sicht langsam | zu breite Abfrage, nicht selektive Spalten, Massendaten | Filter eingrenzen, Server-/DB-Analyse |
| Statuswechsel falsch | Regelreihenfolge oder Seiteneffekt | Testobjekt und Workflowprotokoll |

## Schnellreferenz

```text
Vor Bearbeitung: suchen → Kontext prüfen → Beziehungen prüfen
Vor Statuswechsel: Pflichtfelder → Empfänger → Automatismen → SLA
Vor Adminänderung: Export/Backup → Test → Abnahme → Rollback
Bei Fehler: ID + Zeit + Benutzer + Aktion + exakter Text + Korrelation
Bei Integration: stabiler Schlüssel + Idempotenz + Retry + Monitoring
```

## Quellen
- [OMNITRACKER Interfaces](https://www.omnitracker.com/en/products/interfaces/)
- [OMNITRACKER Interface Bus](https://www.omnitracker.com/en/products/interfaces/interface-bus/)
- [OMNITRACKER REST Web Services](https://www.omnitracker.com/en/products/interfaces/interface-bus/rest-web-services/)

## Verwandte Notizen
- [[MS-RPC-Verbindungen-Cheatsheet]]
- [[GitLab-Cheatsheet]]
- [[Umgang-mit-Teamleitern-Cheatsheet]]
