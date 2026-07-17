---
title: "Intel-Prozessorhistorie – Premium-Spickzettel"
aliases: ["Intel CPU Geschichte", "Intel Prozessoren Historie", "x86 Intel Timeline"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [hardware, cpu, intel, x86, xeon, core-ultra, geschichte]
source: "https://timeline.intel.com/"
---

# Intel-Prozessorhistorie – Premium-Spickzettel

> [!abstract] Zweck
> Knappe, technisch belastbare Intel-Zeitleiste vom 4004 bis zu Core Ultra Series 3 und Xeon 6/6+ – mit Hardwaremerkmalen, Architekturwechseln, Plattformfolgen und typischen Fehlinterpretationen.

## Inhalt

- [[#Zeitleiste in 30 Sekunden]]
- [[#1971 bis 1989 – Mikroprozessor und x86]]
- [[#1990er – Pentium und Out-of-Order]]
- [[#2000 bis 2005 – NetBurst und die Leistungswand]]
- [[#2006 bis 2015 – Core und integrierte Plattform]]
- [[#2016 bis 2020 – Mehr Kerne, lange 14-nm-Phase]]
- [[#2021 bis 2026 – Hybridkerne, Tiles und 18A]]
- [[#Xeon-Entwicklung]]
- [[#Namensschema lesen]]
- [[#Technische Leitmotive]]
- [[#Inventar und Diagnose]]
- [[#Schnellreferenz]]

## Zeitleiste in 30 Sekunden

```text
1971 4004       kommerzieller 4-Bit-Mikroprozessor
1974 8080       frühe Mikrocomputer
1978 8086       Start der x86-Linie
1985 80386      32-Bit-x86 und Paging
1989 80486      Cache/FPU/Pipeline stärker integriert
1993 Pentium    superskalare x86-CPU
1995 Pentium Pro Out-of-Order, Basis der P6-Familie
2000 Pentium 4  NetBurst und sehr hohe Taktraten
2006 Core 2     Effizienz statt nur Pipeline/Takt
2008 Nehalem    integrierter Speichercontroller, Turbo, SMT
2011 Sandy Bridge starke CPU/iGPU-Plattformintegration
2017 Xeon Scalable neue Serverplattform-Marke
2021 Alder Lake Hybrid aus P- und E-Kernen
2023 Core Ultra Tile-Aufbau und NPU im PC
2026 Core Ultra Series 3 auf Intel 18A; Xeon 6+ bis 288 E-Kerne laut Intel
```

## 1971 bis 1989 – Mikroprozessor und x86

| Jahr | Produkt | typische Eckdaten | Bedeutung |
|---:|---|---|---|
| 1971 | 4004 | 4 Bit, etwa 2.300 Transistoren, rund 10 µm | frühe kommerzielle CPU auf einem Chip |
| 1972 | 8008 | 8 Bit | allgemeiner als 4004 |
| 1974 | 8080 | 8 Bit, typischerweise um 2 MHz | Mikrocomputer-Ökosystem |
| 1978 | 8086 | 16 Bit, etwa 29.000 Transistoren | Ursprung der x86-ISA |
| 1979 | 8088 | 16-Bit-Kern, externer 8-Bit-Bus | Basis des IBM PC |
| 1982 | 80286 | Protected Mode | mehr Speicher und Schutzmechanismen |
| 1985 | 80386 | 32 Bit, Paging, etwa 275.000 Transistoren | moderne 32-Bit-x86-Grundlage |
| 1989 | 80486 | Pipeline, Cache und je Modell FPU integriert | höhere Integration und IPC |

### Warum der 8088 wichtig war

Der 8088 war intern eng mit dem 8086 verwandt, konnte aber durch seinen schmaleren externen Bus kostengünstigere 8-Bit-Peripherie verwenden. Der IBM PC etablierte dadurch eine Kompatibilitätslinie, die bis zu modernem x86-64 nachwirkt.

> [!important]
> „x86“ bezeichnet die Befehlssatzfamilie, nicht eine einzelne Mikroarchitektur. Ein 8086, Pentium Pro und Core Ultra führen verwandte ISA-Linien aus, intern aber völlig unterschiedlich.

## 1990er – Pentium und Out-of-Order

### Pentium

Der 1993 eingeführte Pentium führte die PC-Linie unter einem Markennamen fort. Typische Merkmale:

- zwei Integer-Pipelines für begrenzte superskalare Ausführung;
- verbesserte Gleitkommaeinheit;
- breiterer externer Datenpfad;
- später MMX für Multimedia-Integeroperationen.

### Pentium Pro und P6

Der Pentium Pro von 1995 war architektonisch wichtiger als seine damalige Desktopverbreitung vermuten lässt:

```text
x86-Instruktionen
-> interne Mikrooperationen
-> Out-of-Order-Ausführung
-> Retirement in Programmreihenfolge
```

Die P6-Linie prägte Pentium II, Pentium III und später indirekt die Core-Entwicklung. Wichtige Konzepte:

- spekulative Ausführung;
- Registerumbenennung;
- große Reorder-Strukturen;
- bessere Sprungvorhersage;
- zunehmende SIMD-Erweiterungen wie SSE.

### Celeron und Xeon

Intel segmentierte zunehmend:

- **Celeron:** günstigere Varianten, häufig weniger Cache/Takt;
- **Pentium/Core:** Mainstream und Performance;
- **Xeon:** Server/Workstation mit Plattform-, RAS- und Mehrsockelfunktionen.

Modellnamen allein garantieren keine Architektur oder Plattformfunktion.

## 2000 bis 2005 – NetBurst und die Leistungswand

Pentium 4/NetBurst setzte auf sehr tiefe Pipelines und hohe Taktraten. Das erlaubte hohe GHz-Werte, brachte aber Nachteile:

- Fehlvorhersagen kosteten viele Zyklen;
- Leistungsaufnahme und Wärme stiegen stark;
- IPC war je Workload nicht automatisch höher;
- weitere Taktskalierung wurde thermisch und energetisch unattraktiv.

Hyper-Threading nutzte einen Kern mit zwei logischen Threads. Der Gewinn hing stark davon ab, ob ungenutzte Ausführungseinheiten parallel verwendet werden konnten.

> [!summary] Lehre
> Frequenz ist nur ein Faktor. Nachhaltige Leistung benötigt IPC, Energieeffizienz, Cache, Parallelität und Speicherverhalten.

Parallel entwickelte Intel mobile Pentium-M-Prozessoren mit stärkerem Effizienzfokus. Diese Linie beeinflusste die spätere Core-Architektur.

## 2006 bis 2015 – Core und integrierte Plattform

### Core 2

Core 2 markierte 2006 die Abkehr von NetBurst. Typische Verbesserungen:

- kürzere, effizientere Pipeline;
- höhere IPC;
- bessere Performance pro Watt;
- Mehrkernvarianten als Mainstream;
- 64-Bit-Unterstützung in der PC-Linie.

### Nehalem

Ab 2008:

- integrierter Speichercontroller;
- QuickPath Interconnect in geeigneten Plattformen;
- Turbo Boost;
- Hyper-Threading in vielen Core-i7-/Xeon-Modellen;
- gemeinsamer Last-Level-Cache.

### Sandy Bridge

Ab 2011 wurde die Plattform stärker integriert:

- CPU und GPU enger auf einem Die;
- Ringbus in vielen Clientdesigns;
- AVX;
- verbesserter Turbo und Energieverwaltung;
- hohe Pro-Takt-Leistung.

### Tick-Tock und seine Grenzen

Intel wechselte zeitweise zwischen:

```text
Tick = Fertigungsprozess verkleinern
Tock = neue Mikroarchitektur
```

In der Praxis überlappten Produkt-, Plattform- und Fertigungszyklen zunehmend. Die lange 14-nm-Phase zeigte, dass ein einfaches Zweitaktmodell nicht dauerhaft aufrechterhalten werden konnte.

## 2016 bis 2020 – Mehr Kerne, lange 14-nm-Phase

Clientprodukte von Skylake bis Comet Lake teilten viele Grundzüge, wurden aber über Takt, Kernzahl, Cache, iGPU und Plattform weiterentwickelt.

Marktdruck führte zu:

- mehr Mainstream-Kernen;
- höheren Turbo- und Power-Limits;
- stärkerer Modellsegmentierung;
- Sicherheits- und Microcode-Mitigationen für spekulative Seitenkanäle;
- zunehmender Bedeutung von realer Dauerleistung statt kurzer Turbo-Spitzen.

### Sicherheitsfolgen

Seit Spectre/Meltdown-Ära müssen Vergleiche berücksichtigen:

- Microcode-Version;
- Betriebssystem-Mitigations;
- Hypervisor-Konfiguration;
- SMT-Zustand;
- Firmware/BIOS;
- Benchmarkzeitpunkt.

Historische Ergebnisse vor und nach Mitigationen sind nicht immer direkt vergleichbar.

## 2021 bis 2026 – Hybridkerne, Tiles und 18A

### Alder Lake

2021 brachte Intel Performance- und Efficiency-Kerne in den PC-Mainstream:

```text
P-Cores: hohe Single-Thread- und Latenzleistung
E-Cores: gute Flächen-/Energieeffizienz für Parallelität
Thread Director: Hinweise an den Scheduler
```

Ein Hybridprozessor benötigt passenden OS-Scheduler und realistische Tests. „24 Kerne“ sagt ohne Aufteilung wenig aus.

### Core Ultra

Mit Core Ultra verschob Intel den Fokus von einer reinen CPU zu einem integrierten Clientpaket:

- Compute-, Grafik-, SoC- und I/O-Tiles je Plattform;
- NPU für ausgewählte lokale KI-Workloads;
- stärkere Medien- und Grafikblöcke;
- Packaging und Fertigung aus mehreren Bausteinen.

### Core Ultra Series 3

Intel listet Core Ultra Series 3 mit Launchdaten ab Q1 2026. Die Familie umfasst unterschiedliche Mobil-/Client-SKUs, beispielsweise 6 bis 16 Kerne, verschiedene Arc-/Intel-Grafikvarianten und unterschiedliche Cache-/Taktklassen.

> [!warning]
> „Series 3“ ist keine einzelne CPU. Exaktes SKU, Kernmix, GPU, NPU, Speicher, OEM-Power-Limit und Kühlung prüfen.

### Intel 18A

18A ist Intels Fertigungsbezeichnung für eine Prozessgeneration. Node-Namen verschiedener Foundries nicht als direkt vergleichbare geometrische Nanometerwerte lesen. Relevant sind reale Produkteigenschaften:

- Dichte und Yield;
- Spannung/Takt;
- Leakage;
- Packaging;
- verfügbare Bibliotheken;
- Performance pro Watt.

## Xeon-Entwicklung

### Von Pentium Pro zu Xeon Scalable

Server-CPUs differenzieren sich nicht nur durch Kernzahl:

- ECC und RAS;
- mehr Speicherkanäle und Kapazität;
- Mehrsockelbetrieb je Modell;
- PCIe/CXL-Lanes;
- Beschleuniger wie AMX, DSA, QAT je Plattform;
- lange Validierung und Supportzyklen.

### Xeon Scalable

Seit 2017 verwendet Intel die Xeon-Scalable-Marke für viele Servergenerationen. Sockel, Generation, Plattform und Featurematrix sind entscheidend; „Gold“ oder „Platinum“ allein ist keine vollständige technische Angabe.

### Xeon 6

Xeon 6 trennt Produktvarianten stärker nach Ziel:

- **P-Core-Modelle:** hohe Pro-Kern-/HPC-/AI-Host-Leistung;
- **E-Core-Modelle:** Dichte und Cloud-/Scale-out-Durchsatz.

Intel kündigte Xeon 6+ auf 18A mit bis zu 288 E-Kernen und geplanter Einführung in der ersten Jahreshälfte 2026 an. Bei Beschaffung stets tatsächlich verfügbare SKU, BIOS-/Plattformfreigabe und unabhängige Workloadtests prüfen.

> [!danger]
> Kernzahlen verschiedener Kerntypen, SMT-Zustände und Serverklassen nicht ohne Weiteres vergleichen. Lizenzkosten pro Kern und Memory-/NUMA-Verhalten können wichtiger sein als ein synthetischer Gesamtscore.

## Namensschema lesen

Beispiele:

```text
Core i7-12700K
Core Ultra 9 285K
Core Ultra 7 356H
Xeon 6980P
```

Typische Suffixe, generationsabhängig:

| Suffix | häufige Bedeutung |
|---|---|
| `K` | frei einstellbarer Multiplikator |
| `F` | keine aktive integrierte Grafik |
| `KF` | K plus F |
| `H/HX` | leistungsorientierte Mobilklasse |
| `U` | energieorientierte Mobilklasse |
| `T` | reduzierte Leistungs-/TDP-Klasse |
| `P/E` bei Xeon-Kontext | Produkt-/Kerntyp, nicht mit Client-P/E-Kernen verwechseln |

> [!warning]
> Suffixe ändern sich über Generationen. ARK-Datenblatt der exakten Bestellnummer ist maßgeblich.

## Technische Leitmotive

### Von Takt zu Parallelität

```text
1990er: Takt + Out-of-Order
2000er: Taktgrenze -> Mehrkern
2010er: Integration + Effizienz
2020er: Hybrid, Tiles, Beschleuniger, Packaging
```

### Kompatibilität als Stärke und Last

x86-Kompatibilität ermöglicht jahrzehntelange Softwarebasis, verlangt aber:

- komplexes Frontend/Decoding;
- Legacy-Modi;
- sorgfältige Validierung;
- Microcode und Plattformfirmware;
- Sicherheitskompatibilität.

### Benchmarks

Intel-Vergleich nie allein über „bis zu“ Herstellerwerte durchführen. Prüfen:

```text
Single-Thread
Multi-Thread
Dauerleistung
Energie pro Aufgabe
Speicher/NUMA
iGPU/NPU/Medien
Plattformkosten
reale Anwendung
```

Siehe [[CPU-Benchmarks-und-Vergleichbarkeit-Premium-Spickzettel]].

## Inventar und Diagnose

Linux:

```bash
lscpu
cat /proc/cpuinfo
sudo dmidecode -t processor
sudo turbostat --Summary --interval 1
sudo perf stat -a sleep 10
```

Microcode:

```bash
dmesg | grep -i microcode
rpm -q microcode_ctl 2>/dev/null
dpkg -l intel-microcode 2>/dev/null
```

P-/E-Kern-Topologie:

```bash
lscpu -e=CPU,CORE,SOCKET,NODE,MAXMHZ,MINMHZ,ONLINE
find /sys/devices/system/cpu/cpu*/topology -maxdepth 1 -type f -print 2>/dev/null | head
```

Windows:

```powershell
Get-CimInstance Win32_Processor |
  Select-Object Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed

Get-ComputerInfo | Select-Object BiosVersion,OsName,OsVersion
```

Intel ARK und OEM-Datenblatt nutzen, um zu prüfen:

- exakte SKU;
- Kern-/Threadmix;
- Speicherunterstützung;
- PCIe-Lanes;
- maximale Turbo-/Base-Power;
- GPU/NPU;
- Virtualisierung, ECC und vPro je Modell.

## Schnellreferenz

```text
4004 -> 8086 -> 386 -> Pentium -> P6 -> NetBurst -> Core
-> Nehalem/Sandy Bridge -> lange 14-nm-Phase
-> Hybrid P/E -> Core Ultra Tiles/NPU -> Series 3 / 18A

Xeon: Plattform/RAS/Memory/I/O wichtiger als Markenstufe allein.
GHz, Kernzahl und Node-Name nie isoliert vergleichen.
```

## Quellen

- [Intel Technology Timeline](https://timeline.intel.com/)
- [Intel Microprocessor Quick Reference](https://www.intel.com/pressroom/kits/quickreffam.htm)
- [Intel Processor Products](https://www.intel.com/content/www/us/en/products/details/processors.html)
- [Intel Core Ultra Series 3](https://www.intel.com/content/www/us/en/products/details/processors/core-ultra.html)
- [Intel Panther Lake and Xeon 6+ announcement](https://newsroom.intel.com/client-computing/intel-unveils-panther-lake-architecture-first-ai-pc-platform-built-on-18a)
- [Intel Xeon](https://www.intel.com/content/www/us/en/products/details/processors/xeon.html)

## Verwandte Notizen

- [[Prozessorhistorie-Intel-AMD-Arm-Premium-Spickzettel]]
- [[AMD-Prozessorhistorie-Premium-Spickzettel]]
- [[Arm-Prozessorhistorie-Premium-Spickzettel]]
- [[CPU-Benchmarks-und-Vergleichbarkeit-Premium-Spickzettel]]
- [[ls-Familie-und-Hardwareinventar-Premium-Spickzettel]]
- [[dmesg-Premium-Spickzettel]]
