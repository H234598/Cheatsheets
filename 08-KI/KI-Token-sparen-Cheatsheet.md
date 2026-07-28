---
title: "KI-Token sparen – Cheatsheet"
aliases: ["LLM Kosten senken", "Token Optimierung", "Context Cost Optimization"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [ki, llm, tokens, kosten, caching, rag, optimization]
source: "https://platform.openai.com/docs/guides/prompt-caching"
---

# KI-Token sparen – Cheatsheet

> [!abstract] Zweck
> Praxisreferenz zur Senkung von LLM-Tokenverbrauch und Kosten: messen, Kontext verkleinern, statische Präfixe cachen, RAG statt Volltext, Modellrouting, Batches, kurze Ausgaben, Sitzungsdisziplin, Toolergebnisse komprimieren und Qualität gegen Einsparungen absichern.

> [!important] Billig ist nicht automatisch effizient
> Eine aggressive Kürzung, die Fehler, Wiederholungen oder manuelle Nacharbeit erzeugt, kann insgesamt teurer sein. Optimiere **Kosten pro erfolgreich erledigter Aufgabe**, nicht nur Tokens pro Anfrage.

## Inhalt

- [[#Token-Grundlagen]]
- [[#Zuerst messen]]
- [[#Die größten Kostentreiber]]
- [[#Kontextbudget]]
- [[#Prompts kürzen ohne Informationsverlust]]
- [[#Gesprächsverlauf beherrschen]]
- [[#RAG statt Volltext]]
- [[#Prompt- und Kontext-Caching]]
- [[#Modellrouting]]
- [[#Ausgabe begrenzen]]
- [[#Batches und Parallelität]]
- [[#Werkzeugausgaben komprimieren]]
- [[#Bilder, Audio und Dokumente]]
- [[#Agenten und Flotten]]
- [[#Qualität und Evaluation]]
- [[#Optimierungsplan]]
- [[#Schnellreferenz]]

## Token-Grundlagen

Modelle verarbeiten Text und andere Modalitäten in Tokens. Abgerechnet oder limitiert werden typischerweise:

```text
Eingabetokens
+ Ausgabetokens
+ ggf. Reasoning-/Thinking-Tokens
+ Cache-Schreib-/Lesetokens
+ Tool-/Bild-/Audio-/Dateiverarbeitung
```

Ein Token ist nicht exakt ein Wort. Sprache, Sonderzeichen, Quellcode, JSON und IDs tokenisieren unterschiedlich.

Daher nicht mit „Wörter × fixer Faktor“ planen, sondern Anbieterzähler oder Tokenizer verwenden.

## Zuerst messen

Pro Request protokollieren:

| Feld | Zweck |
|---|---|
| Modell/Version | Preis und Verhalten zuordnen |
| Input Tokens | Kontextkosten |
| Output Tokens | Antwortkosten |
| Cached Tokens | Cachewirkung |
| Latenz | Nutzererfahrung |
| Tool Calls | versteckte Schleifen |
| Erfolg/Fehler | Kosten pro Erfolg |
| Aufgabe/Tenant | Chargeback und Routing |

Beispielmetrik:

```text
cost_per_success = Gesamtkosten / erfolgreich abgeschlossene Aufgaben
```

Weitere sinnvolle Kennzahlen:

```text
input_output_ratio
cache_hit_rate
retry_rate
tokens_per_document
tokens_per_resolved_ticket
p50/p95 latency
human_rework_rate
```

> [!warning] Keine Rohprompts in beliebige Logs
> Prompts können personenbezogene Daten, Quellcode oder Secrets enthalten. Metadaten, Hashes, Redaction und passende Aufbewahrungsfristen verwenden.

## Die größten Kostentreiber

Typische Reihenfolge:

1. vollständige Dokumente bei jeder Runde erneut senden,
2. endlos wachsende Chat-History,
3. ungefilterte Tool- und Logausgaben,
4. teures Modell für triviale Aufgaben,
5. unnötig lange Antworten,
6. Agentenschleifen ohne Abbruchkriterium,
7. fehlende Cache-Nutzung,
8. Retries wegen instabiler Prompts oder Ausgabeformate.

Schneller Audit:

```text
Welche 10 Prompts erzeugen die meisten Inputtokens?
Welche 10 Workflows erzeugen die meisten Wiederholungen?
Welche Aufgaben brauchen das stärkste Modell wirklich?
Welche Präfixe wiederholen sich byte-/tokenähnlich?
```

## Kontextbudget

Ein Context Window ist keine Einladung, es vollständig zu füllen. Mehr Kontext kann Relevanz verschlechtern.

Budget vorgeben:

```text
Gesamtfenster
- reservierte Ausgabe
- Toolergebnisse
- Sicherheits-/Systeminstruktionen
- Reserve für weitere Turns
= verfügbares Nutzkontextbudget
```

Beispiel:

```text
128k Fenster
- 8k maximale Antwort
- 12k Werkzeuge
- 8k System/Reserve
= höchstens 100k Nutzkontext
```

Praktisch meist deutlich darunter bleiben.

### Relevanz vor Vollständigkeit

Statt 500 Seiten:

```text
Frage -> Suchindex/Retriever -> 5 relevante Abschnitte
-> Modell -> Antwort mit Fundstellen
```

## Prompts kürzen ohne Informationsverlust

### Duplikate entfernen

Schlecht:

```text
Sei kurz. Antworte kompakt. Schreibe nicht zu viel.
Halte dich kurz. Maximal kurz.
```

Besser:

```text
Maximal 180 Wörter.
```

### Regeln zentralisieren

Wiederkehrende Regeln in System-/Projektinstruktion statt in jede Nutzerfrage.

### Struktur statt Prosa

```text
Ziel: 502-Fehler diagnostizieren
Umgebung: Fedora 42, nginx, SELinux enforcing
Log: Zeilen 20–80
Ausgabe: Ursache, Test, Fix, Rollback
```

### IDs und Daten normalisieren

Nicht riesige JSON-Objekte mit irrelevanten Feldern senden. Vorverarbeitung:

```python
relevant = {
    "id": item["id"],
    "status": item["status"],
    "error": item.get("error"),
    "timestamp": item["timestamp"],
}
```

### Tabellen komprimieren

- unnötige Dezimalstellen reduzieren,
- leere Spalten entfernen,
- Einheiten einmal im Header,
- nur relevante Zeilen,
- Datentypen als Schema statt Wiederholung.

## Gesprächsverlauf beherrschen

Chats wachsen, weil jede Runde alte Nachrichten erneut enthält.

Strategien:

### Regelmäßige Zustandszusammenfassung

```text
Fasse den bisherigen Arbeitsstand in höchstens 500 Tokens zusammen:
- Ziel
- bestätigte Fakten
- Entscheidungen
- offene Aufgaben
- relevante Dateipfade/IDs
- nicht erneut zu diskutierende Punkte
Lasse Smalltalk und verworfene Ansätze weg.
```

Danach neuen Thread mit Zusammenfassung starten.

### Externes State-Objekt

```json
{
  "goal": "nginx migration",
  "decisions": ["TLS remains at load balancer"],
  "constraints": ["no downtime"],
  "done": ["inventory", "config test"],
  "next": ["canary", "rollback rehearsal"]
}
```

### Nicht jede Antwort zurücksenden

Nur Informationen übernehmen, die für den nächsten Schritt benötigt werden.

### Veraltete Turns verwerfen

Ein alter Fehlerlog nach erfolgreichem Fix muss nicht dauerhaft im Kontext bleiben.

## RAG statt Volltext

Retrieval-Augmented Generation:

```text
Dokumente -> Chunks -> Embeddings/Index
Frage -> Suche/Reranking -> Top-k Chunks -> Modell
```

Sparregeln:

- Chunks semantisch schneiden, nicht starr mitten im Satz.
- Metadatenfilter vor Vektorsuche: Produkt, Version, Datum, Mandant.
- `top_k` klein beginnen.
- Duplikate und überlappende Treffer entfernen.
- Reranker für Präzision einsetzen.
- Fundstellen mit Dokument/Abschnitt erhalten.
- bei geringer Trefferqualität keine scheinpräzise Antwort erzwingen.

Beispiel:

```text
Nur Dokumente mit product=nginx, version>=1.26, language=de/en,
valid_from<=2026-07-17 und tenant=current durchsuchen.
```

> [!warning] RAG spart nur mit gutem Retrieval
> Falsche Treffer machen Antworten billiger, aber unbrauchbar. Recall und Precision mit einem Testset messen.

## Prompt- und Kontext-Caching

Caching lohnt sich bei großen wiederholten Präfixen:

```text
Systeminstruktion
+ Richtlinie
+ Produktkatalog
+ statische Beispiele
+ variable Nutzerfrage
```

Statisches zuerst, Variables zuletzt.

### Cache-freundliche Gestaltung

- identische Reihenfolge,
- identische Formatierung,
- keine wechselnden Zeitstempel im Präfix,
- stabile Tooldefinitionen,
- stabile Systemregeln,
- variable Anfrage am Ende.

Schlecht:

```text
Request-ID und aktuelle Uhrzeit ganz am Anfang,
danach 50.000 Tokens Richtlinie.
```

Besser:

```text
50.000 Tokens stabile Richtlinie,
danach Request-ID, Uhrzeit und Frage.
```

### Anbieterunterschiede

- Einige APIs cachen implizit.
- Andere erlauben explizite Cache-Breakpoints oder Cacheobjekte.
- Mindestlänge, TTL, Schreib- und Lesepreise unterscheiden sich.
- Cache-Tokens können trotzdem zum Context Window zählen.
- Cachetreffer über Usage-Felder prüfen, nicht vermuten.

Aktuelle Dokumentation pro Modell lesen.

## Modellrouting

Nicht jede Aufgabe braucht das größte Reasoning-Modell.

Beispielmatrix:

| Aufgabe | Modellklasse |
|---|---|
| Klassifikation, Extraktion | klein/schnell |
| kurze Umformulierung | klein/schnell |
| Standard-Q&A mit gutem RAG | mittel |
| komplexe Codeänderung | starkes Coding-/Reasoning-Modell |
| Architektur/unklare Fehler | stark |
| finale sicherheitskritische Prüfung | stark plus Mensch |

Router-Regeln:

```text
wenn Text < 2k Tokens und Aufgabe=klassifizieren -> fast
wenn Codeänderung > 3 Dateien -> strong
wenn erste Antwort Unsicherheit hoch -> eskalieren
wenn Datenklasse=hoch -> nur freigegebener privater Endpoint
```

Fallback nicht endlos:

```text
small -> medium -> strong -> Mensch
```

Jede Eskalation braucht Grund und Budget.

## Ausgabe begrenzen

### Konkrete Länge

```text
Maximal 8 Bulletpoints und 250 Wörter.
```

### Nur Delta

```text
Gib nur geänderte Konfigurationszeilen als Unified Diff aus.
```

### Strukturierte Extraktion

```json
{"ticket_id":"...","priority":"P1|P2|P3","owner":"..."}
```

### Kein unnötiges Wiederholen

```text
Wiederhole die Eingabedaten nicht. Zitiere nur die für den Befund
entscheidenden Stellen.
```

### Stopbedingungen

In APIs `max_output_tokens` beziehungsweise äquivalente Grenze setzen. Prompt allein ist keine harte Kostenkontrolle.

> [!warning] Zu knapp kann falsch werden
> Für Begründungen, sicherheitsrelevante Schritte und komplexe Codeänderungen ausreichend Ausgabe reservieren.

## Batches und Parallelität

Batchverarbeitung kann günstiger oder throughputfreundlicher sein, wenn Echtzeit nicht nötig ist.

Geeignet:

- Tausende Klassifikationen,
- Embeddings,
- nächtliche Zusammenfassungen,
- Evaluationen,
- Datenanreicherung.

Nicht blind parallelisieren:

```text
Parallelität -> Rate Limits -> Retries -> doppelte Kosten
```

Sicheres Muster:

- idempotente Request-ID,
- Queue,
- begrenzte Workerzahl,
- Exponential Backoff mit Jitter,
- `Retry-After` beachten,
- Dead-Letter Queue,
- Deduplizierung,
- Kostenlimit pro Batch.

## Werkzeugausgaben komprimieren

Agenten senden Toolresultate oft zurück an das Modell.

### Logs

Statt:

```bash
journalctl -b
```

Besser:

```bash
journalctl -u nginx --since '10 min ago' -p warning..alert --no-pager
```

### Git

Statt komplettes Repository:

```bash
git diff --stat
git diff -- src/relevant.py tests/test_relevant.py
```

### Datenbanken

```sql
SELECT id, status, error_code, updated_at
FROM jobs
WHERE status = 'failed'
ORDER BY updated_at DESC
LIMIT 50;
```

### Tool-Adapter

Vor Rückgabe ans Modell:

- irrelevante Felder entfernen,
- große Binärdaten nicht inline,
- Paging,
- Fehlerauszug plus Referenz auf vollständiges Artefakt,
- Zeichen-/Tokenlimit,
- Redaction.

## Bilder, Audio und Dokumente

Multimodale Eingaben verbrauchen ebenfalls Tokens oder anbieterspezifische Einheiten.

Sparmaßnahmen:

- Bild zuschneiden auf relevanten Bereich,
- unnötige hohe Auflösung reduzieren,
- nicht zehn nahezu gleiche Screenshots,
- Audio vorab segmentieren/VAD,
- Transkript nur für relevante Zeitbereiche,
- PDF-Seiten gezielt auswählen,
- Tabellen strukturiert extrahieren, wenn Layout nicht nötig ist.

Aber: keine Vorverarbeitung, die entscheidende Details zerstört.

## Agenten und Flotten

Agentische Schleifen multiplizieren Tokens:

```text
Plan -> Tool -> Beobachtung -> neuer Plan -> Tool -> Review
```

Begrenzen:

- maximale Turns,
- maximale Tool Calls,
- Zeitlimit,
- Kostenlimit,
- Erfolgskriterium,
- Abbruch bei identischen Fehlern,
- keine zwei Agenten für dieselbe Teilaufgabe,
- kleine Modelle für Suche/Extraktion, starkes Modell für Synthese.

Beispielbudget:

```yaml
workflow: incident-triage
max_total_tokens: 120000
max_cost_eur: 4.00
max_turns: 12
max_tool_calls: 25
escalate_after_repeated_error: 2
```

## Qualität und Evaluation

Jede Optimierung gegen Testset messen:

| Metrik | Frage |
|---|---|
| Task Success | wurde die Aufgabe korrekt gelöst? |
| Exact/Schema Match | ist Ausgabe maschinenlesbar? |
| Citation Accuracy | tragen Quellen die Aussage? |
| Hallucination Rate | wurden Fakten erfunden? |
| Human Rework | wie viel Nacharbeit? |
| Cost per Success | echte Wirtschaftlichkeit? |
| Latency | schnell genug? |

A/B-Test:

```text
Baseline-Prompt + starkes Modell
gegen
gekürzter Prompt + geroutetes Modell + Cache
```

Nicht nur Durchschnitt betrachten; P95 und kritische Fehlertypen prüfen.

## Optimierungsplan

### Stufe 1 – Sichtbarkeit

- Usage-Daten erfassen,
- Top-Kostentreiber identifizieren,
- Erfolg markieren,
- Datenklassifizierung klären.

### Stufe 2 – einfache Gewinne

- Outputlimits,
- Duplikate entfernen,
- Logs filtern,
- Chat-History zusammenfassen,
- triviale Aufgaben routen.

### Stufe 3 – Architektur

- RAG,
- Prompt Caching,
- Batch,
- Tooladapter,
- zentrale Modell-/Promptkonfiguration.

### Stufe 4 – Governance

- harte Budgets,
- Quotas,
- Evals vor Modellwechsel,
- Deprecation-Warnungen,
- Chargeback/Showback,
- Incident-Prozess.

## Schnellreferenz

```text
Messen -> Top-Kostentreiber -> Kontext kürzen -> Cache nutzen
-> RAG -> Modell routen -> Ausgabe begrenzen -> Tooldaten filtern
-> Agenten deckeln -> Qualität gegen Testset prüfen
```

Die fünf stärksten Hebel:

```text
1. Keine vollständigen Dokumente in jeder Runde.
2. Chat-History regelmäßig verdichten.
3. Wiederholte Präfixe cache-freundlich gestalten.
4. Kleine Modelle für einfache Aufgaben.
5. Maximale Turns, Tool Calls und Outputtokens hart begrenzen.
```

## Quellen
- [OpenAI – Prompt Caching](https://platform.openai.com/docs/guides/prompt-caching)
- [OpenAI – Token Usage](https://platform.openai.com/docs/guides/text-generation/managing-tokens)
- [Anthropic – Prompt Caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)
- [Anthropic – Context Windows](https://docs.anthropic.com/en/docs/build-with-claude/context-windows)
- [Google Gemini – Token Counting](https://ai.google.dev/gemini-api/docs/tokens)
- [Google Gemini – Context Caching](https://ai.google.dev/gemini-api/docs/caching)

## Verwandte Notizen
- [[KI-Prompts-Cheatsheet]]
- [[KI-Flottenmanagement-Cheatsheet]]
- [[Codex-Cheatsheet]]
- [[Claude-Cheatsheet]]
- [[Gemini-Cheatsheet]]
