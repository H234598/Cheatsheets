---
title: "AMD-Prozessorhistorie – Premium-Spickzettel"
aliases: ["AMD CPU Geschichte", "AMD Prozessoren Historie", "Zen Ryzen EPYC Timeline"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [hardware, cpu, amd, x86, ryzen, epyc, zen, geschichte]
source: "https://www.amd.com/en/products/processors.html"
---

# AMD-Prozessorhistorie – Premium-Spickzettel

> [!abstract] Zweck
> Technische AMD-Zeitleiste von frühen x86-kompatiblen Prozessoren über K6, Athlon, AMD64 und Bulldozer bis Ryzen, Threadripper, EPYC, Zen 5 und dem 2026 angelaufenen 6.-Gen-EPYC-Projekt „Venice“. Mit Hardwaremerkmalen, Namenslogik, Benchmark-Einordnung und Diagnose.

> [!warning] Status sauber trennen
> **Angekündigt**, **Produktionshochlauf**, **OEM-Auslieferung** und **breit im Handel verfügbar** sind verschiedene Zustände. „Venice“ befand sich laut AMD im Mai 2026 im Produktionshochlauf; daraus folgt nicht automatisch, dass jede SKU am 17. Juli 2026 frei verfügbar war.

## Inhalt

- [[#Zeitleiste in 30 Sekunden]]
- [[#Frühe x86- und K-Familien]]
- [[#Athlon, Opteron und AMD64]]
- [[#Phenom, Bulldozer und die schwierige Phase]]
- [[#Zen-Renaissance]]
- [[#Ryzen-Desktop und 3D V-Cache]]
- [[#Mobile APUs und Ryzen AI]]
- [[#Threadripper und Workstation]]
- [[#EPYC und Server]]
- [[#Stand Juli 2026]]
- [[#Namensschema lesen]]
- [[#Hardware- und Benchmark-Einordnung]]
- [[#Inventar und Diagnose]]
- [[#Schnellreferenz]]

## Zeitleiste in 30 Sekunden

```text
1969  AMD gegründet
1975  Am9080: kompatible 8080-Implementierung
1980er/90er  Am286/Am386/Am486: x86-Kompatibilität und Wettbewerb
1996  K5: weitgehend eigene x86-Mikroarchitektur
1997  K6: konkurrenzfähiger Desktop-Prozessor
1999  Athlon/K7: starke FPU, EV6-Bus, GHz-Wettbewerb
2003  Opteron/Athlon 64: AMD64, integrierter Speichercontroller, HyperTransport
2005  Athlon 64 X2: Dual-Core im Desktop
2007  Phenom/K10: nativer Quad-Core, L3-Cache
2011  Bulldozer: Modulkonzept, hohe Parallelität, schwache Pro-Thread-Effizienz
2017  Zen/Ryzen/EPYC: Rückkehr in den Hochleistungsmarkt
2019  Zen 2: 7-nm-Compute-Chiplets plus I/O-Die
2020  Zen 3: vereinheitlichter 8-Kern-Complex und großer IPC-Sprung
2022  Zen 4: DDR5, PCIe 5.0, AVX-512-Umsetzung
2024  Zen 5: breitere Ausführung, Ryzen 9000 und EPYC 9005
2026  Ryzen AI 400; EPYC „Venice“ im Produktionshochlauf auf TSMC N2
```

## Frühe x86- und K-Familien

AMD begann nicht als Anbieter einer völlig separaten PC-ISA, sondern als Halbleiterunternehmen und späterer x86-Zweitquellen-/Kompatibilitätsanbieter. Diese Phase war für den Markt wichtig: PC-Hersteller erhielten zusätzliche Lieferquellen, und AMD baute Know-how für eigene Designs auf.

| Familie | Zeit | typische Merkmale | Einordnung |
|---|---:|---|---|
| Am286/386/486 | 1980er–1990er | x86-kompatibel, teils hohe Taktraten | Preis- und Lieferwettbewerb |
| K5 | 1996 | x86-Frontend über intern RISC-artige Mikro-Operationen | erste weitgehend eigene AMD-x86-Architektur |
| K6/K6-2/K6-III | 1997–1999 | 3DNow!, Sockel-7-Ökosystem | günstiger Desktop-Wettbewerber |
| K7/Athlon | ab 1999 | Out-of-Order, starke FPU, EV6-Bus | AMD erreicht Hochleistungssegment |

> [!note]
> „Intern RISC“ bedeutet bei x86-Prozessoren nicht, dass das Betriebssystem eine andere ISA sieht. Die CPU dekodiert x86-Befehle intern in einfachere Mikro-Operationen.

## Athlon, Opteron und AMD64

### Athlon und der GHz-Wettbewerb

Athlon/K7 war ein Wendepunkt. Relevante Eigenschaften:

- leistungsfähige Out-of-Order-Ausführung;
- starke Gleitkommaeinheit;
- getrennter, schneller EV6-Systembus;
- später integrierter L2-Cache;
- Wettbewerb um die erste öffentlich vermarktete 1-GHz-PC-CPU.

Der GHz-Meilenstein war medienwirksam, aber schon damals galt:

```text
Leistung != Takt allein
```

IPC, Cache, Speicherpfad und Compiler bestimmten mit.

### AMD64 und Opteron

2003 führte AMD mit Opteron und Athlon 64 die 64-Bit-Erweiterung der x86-Linie ein. Kerngedanken:

- 64-Bit-Register und erweiterter Adressraum;
- Weiterbetrieb vorhandener 32-Bit-x86-Software;
- integrierter Speichercontroller;
- HyperTransport statt klassischem Front-Side-Bus;
- NUMA-fähige Mehrsockelarchitektur bei Opteron.

AMD64 setzte sich als Grundlage des heutigen x86-64-Ökosystems durch. Betriebssysteme können die ISA unterschiedlich benennen:

```text
x86_64   Linux/Unix-Bezeichnung
amd64    Debian, Go, viele Downloadseiten
x64      Microsoft-/allgemeine Kurzform
```

### Dual-Core

Athlon 64 X2 brachte zwei vollständige Kerne in den Desktop-Mainstream. Das half besonders bei:

- parallelen Anwendungen;
- Hintergrunddiensten;
- Medienkodierung;
- mehreren interaktiven Programmen.

Ein einzelner schlecht parallelisierter Prozess verdoppelte seine Leistung dadurch nicht automatisch.

## Phenom, Bulldozer und die schwierige Phase

### Phenom/K10

Phenom verband mehrere Kerne mit gemeinsamem L3-Cache. Spätere Phenom-II-Modelle verbesserten Takt, Fertigung und Plattformreife. Trotzdem gewann Intel in vielen Desktop- und Serversegmenten die Leistungsführung.

### Bulldozer-Modulkonzept

Bulldozer ab 2011 gruppierte zwei Integer-Cluster mit teilweise geteilten Ressourcen zu einem Modul. Marketing und Betriebssystem konnten diese Ressourcen unterschiedlich als „Kerne“ zählen.

Typische Probleme der Ära:

- geringe Single-Thread-/IPC-Leistung;
- hohe Leistungsaufnahme bei hohen Takten;
- geteilte Frontend-/Gleitkommaressourcen;
- Software und Scheduler nutzten das Moduldesign nicht immer optimal;
- hohe nominelle Kernzahl war kein Ersatz für Pro-Thread-Leistung.

Nachfolger Piledriver, Steamroller und Excavator verbesserten das Konzept, änderten die strategische Lage aber nicht grundlegend.

> [!important] Lehre
> Produktnamen, Kernzahl und GHz sind ohne Mikroarchitektur, Power-Limit und Workload keine hinreichenden Leistungsdaten.

## Zen-Renaissance

Zen wurde als neue, skalierbare Kernfamilie entwickelt. Die erste Ryzen-Generation erschien 2017.

| Generation | Markteinführung | Kernpunkte |
|---|---:|---|
| Zen | 2017 | SMT, großer IPC-Sprung, CCX-Struktur, AM4, Ryzen/EPYC |
| Zen+ | 2018 | verbesserte Latenzen, Takt und 12-nm-Fertigung |
| Zen 2 | 2019 | 7-nm-Compute-Chiplets, zentraler I/O-Die, PCIe 4.0 |
| Zen 3 | 2020 | ein 8-Kern-Complex mit gemeinsamem 32-MB-L3, höherer IPC |
| Zen 4 | 2022 | DDR5, PCIe 5.0, 5 nm, AVX-512-Umsetzung |
| Zen 4c | 2023 | dichtere Kerne für Cloud/Server und bestimmte Mobil-SoCs |
| Zen 5 | 2024 | breiteres Front-/Execution-End, stärkere Vektor-/AI-Pfade |

### Chiplet-Prinzip

Vereinfacht:

```text
Ryzen/EPYC
├── ein oder mehrere Core-Complex-Dies (CCD)
│   └── CPU-Kerne + große Caches
└── I/O-Die
    ├── Speichercontroller
    ├── PCIe
    └── Plattform-I/O
```

Vorteile:

- kleinere Compute-Dies liefern bessere Ausbeute;
- unterschiedliche Fertigungsnodes können kombiniert werden;
- Desktop bis Server lässt sich skalieren;
- defekte oder langsamere Dies können in andere SKUs sortiert werden.

Kosten:

- Inter-Die-Latenz;
- komplexere Packaging-/Power-Steuerung;
- nicht jeder Workload profitiert gleichermaßen.

## Ryzen-Desktop und 3D V-Cache

### Plattformen

| Plattform | Zeit | Speicher | typische Besonderheit |
|---|---:|---|---|
| AM4 | 2017–2024+ | DDR4 | lange Sockellebensdauer, Zen bis Zen 3/ausgewählte spätere Modelle |
| AM5 | ab 2022 | DDR5 | PCIe 5.0, Zen 4/Zen 5 und spätere Plattformpläne |

BIOS/AGESA und Mainboard-Support müssen pro CPU geprüft werden. Gleicher Sockel garantiert nicht jede Kombination.

### Ryzen 9000 / Zen 5

Ryzen 9000 brachte Zen 5 auf AM5. Typisch im oberen Desktopsegment:

- bis 16 Kerne/32 Threads;
- zwei CCDs plus I/O-Die;
- DDR5 und PCIe 5.0;
- integrierte BasisiGPU für Anzeige/Diagnose je Modell;
- freigegebene Boost-/Power-Mechanismen innerhalb definierter Limits.

### 3D V-Cache

Zusätzlicher L3-Cache wird vertikal auf das Compute-Die gestapelt. Nutzen:

- weniger Zugriffe auf DRAM;
- starke Vorteile in cacheempfindlichen Spielen;
- Vorteile in bestimmten Simulationen/EDA-/Analyseworkloads.

Grenzen:

- nicht jeder Workload ist cachelimitiert;
- Takt-/Temperaturstrategie kann von Non-X3D-Modellen abweichen;
- Multi-CCD-Modelle benötigen gutes Thread-/Game-Scheduling;
- ein Gaming-Sieg ist kein allgemeiner Rendering-/Compiler-Sieg.

Stand Juli 2026 führt AMD auf seiner Desktopseite Ryzen-9000- und X3D-Varianten, darunter eine „9950X3D2 Dual Edition“ mit 3D-V-Cache auf beiden Compute-Dies. Herstellerbenchmarks immer samt Fußnoten und Testsystem lesen.

## Mobile APUs und Ryzen AI

Eine AMD-APU kombiniert typischerweise:

```text
Zen-CPU + Radeon-iGPU + Medienblöcke + Speicher-/I/O-Controller
                     + bei neueren Ryzen-AI-Familien eine XDNA-NPU
```

Generationen nutzen nicht immer dieselbe Architektur trotz ähnlicher Produktnummern. Bei Notebookkauf prüfen:

- tatsächliche Zen-Generation;
- CPU-Kernzahl und SMT;
- iGPU-Generation und Compute Units;
- NPU vorhanden und TOPS unter welchem Datentyp;
- Speicherkanäle/-geschwindigkeit;
- OEM-Power-Limit und Kühlung;
- verlöteter oder wechselbarer RAM;
- USB4/PCIe-/Displayausstattung.

### Stand Juli 2026

AMD führt Ryzen AI 400 als aktuelle Notebookfamilie. Auf der Herstellerseite werden unter anderem genannt:

- Zen-basierte CPU-Kerne;
- RDNA-3.5-Grafik je Modell;
- XDNA-2-NPU und mindestens 50 TOPS in entsprechend ausgestatteten Modellen;
- Gerätevarianten mit stark unterschiedlicher TDP/Kühlung.

> [!warning] TOPS
> NPU-TOPS sind Spitzenwerte für bestimmte Datentypen. Sie ersetzen keinen End-to-End-Test des gewünschten Modells, Frameworks und Speichersystems.

## Threadripper und Workstation

Threadripper adressiert hohe Kernzahlen und I/O-Bedarf zwischen Desktop und Server.

| Linie | Ziel |
|---|---|
| Ryzen Threadripper | High-End-Desktop/Creator |
| Threadripper PRO | Workstation, mehr Speicherkanäle/I/O/Management je Plattform |

Typische Kaufgründe:

- Rendering und Simulation;
- viele VMs/Container;
- Software-Builds;
- mehrere GPUs/PCIe-Geräte;
- große Speicherbestückung;
- professionelle ISV-/OEM-Plattformen.

Nicht sinnvoll, wenn die Anwendung nur wenige Threads nutzt oder pro Sockel lizenzierte Software die Kernzahl teuer macht.

## EPYC und Server

### Generationen

```text
Naples  (1st Gen, Zen)    bis 32 Kerne
Rome    (2nd Gen, Zen 2)  Chiplet/I/O-Die, bis 64 Kerne
Milan   (3rd Gen, Zen 3)  stärkere IPC/Cache-Topologie
Genoa   (4th Gen, Zen 4)  DDR5, PCIe 5.0, bis 96 Kerne
Bergamo (4th Gen, Zen 4c) hohe Kerndichte, bis 128 Kerne
Turin   (5th Gen, Zen 5/5c) bis 192 Kerne je nach SKU
Venice  (6th Gen)         Produktionshochlauf 2026, TSMC N2 laut AMD
```

### Servermerkmale

- viele Speicherkanäle und ECC;
- sehr viele PCIe-Lanes;
- Single- und Dual-Socket je Plattform;
- Secure Encrypted Virtualization und Secure Nested Paging je Generation;
- hohe Kern- und VM-Dichte;
- SKU-Spezialisierungen für Cloud, HPC, Telekom und Frequenz.

### NUMA prüfen

```bash
lscpu
numactl --hardware
cat /sys/devices/system/node/online
```

Ein Dual-Socket-System ist nicht einfach „ein großer homogener Prozessor“. Speicherlokalität und Thread-Pinning können Leistung bestimmen.

## Stand Juli 2026

| Segment | aktuelle Orientierung | Statushinweis |
|---|---|---|
| Desktop | Ryzen 9000/9000X3D, AM5 | konkrete SKU-Verfügbarkeit regional prüfen |
| Notebook | Ryzen AI 400, Ryzen AI Max/300 parallel im Markt | OEM-Konfiguration entscheidet stark |
| Workstation | Threadripper/PRO der jeweils verfügbaren Generation | Plattform- und ISV-Zertifizierung prüfen |
| Server | 5th Gen EPYC 9005 breit dokumentiert | bis 192 Zen-5/5c-Kerne je SKU |
| Nächste Servergeneration | 6th Gen EPYC „Venice“ | Produktionshochlauf angekündigt; Auslieferungsstatus separat prüfen |

## Namensschema lesen

AMD-Namen ändern sich zwischen Segmenten und Jahren. Nicht aus einer Ziffer allein die Architektur ableiten.

Beispielhafte Fragen:

```text
Ryzen 9 9950X3D
│     │ │   └─ 3D V-Cache
│     │ └──── Modell-/Leistungsklasse
│     └────── Serie; Architektur separat verifizieren
└──────────── Segmentmarke
```

Suffixe, je nach Familie:

| Suffix | häufige Bedeutung |
|---|---|
| `X` | höheres Leistungs-/Powerziel |
| `X3D` | 3D V-Cache |
| `G` | starke integrierte Grafik bei Desktop-APUs |
| `U` | mobile Effizienzklasse |
| `HS/HX` | mobile Performanceklassen |
| `PRO` | Business-/Manageability-/Lifecycle-Funktionen |
| `F` | je Produktlinie ohne oder mit eingeschränkter iGPU; Datenblatt prüfen |

> [!danger]
> Suffixregeln sind keine universelle Norm. Immer das konkrete Datenblatt lesen.

## Hardware- und Benchmark-Einordnung

### Relevante Hardwaredaten

```text
Mikroarchitektur und Stepping
Kerne/Threads je Kerntyp
Basis-/Boosttakt unter realem Power-Limit
L2/L3 und 3D V-Cache
Speicherkanäle, ECC und maximale Kapazität
PCIe-Version und nutzbare Lanes
iGPU/NPU/Medienblöcke
PPT/TDP sowie Mainboard-Limits
Sockel, BIOS/AGESA und Kühlung
```

### Historische Größenordnung

| Beispiel | Epoche | Kerne/Threads | Aussage |
|---|---:|---:|---|
| Athlon 64 3200+ | 2003 | 1/1 | AMD64 und integrierter Speichercontroller |
| Athlon 64 X2 4800+ | 2005 | 2/2 | frühe Desktop-Dual-Core-Generation |
| FX-8350 | 2012 | 8 Integer-Cluster/8 Threads | hohe Parallelität, schwache Single-Thread-Effizienz |
| Ryzen 7 1800X | 2017 | 8/16 | Zen-Neustart und starke Mehrkernleistung |
| Ryzen 9 3950X | 2019 | 16/32 | 16 Kerne im Mainstream-Sockel |
| Ryzen 9 7950X | 2022 | 16/32 | Zen 4, DDR5/PCIe 5.0 |
| Ryzen 9 9950X3D | 2025 | 16/32 | Zen 5 plus 3D V-Cache |
| EPYC 9965 | 2024 | bis 192/384 | hohe Serverkerndichte mit Zen 5c |

> [!note]
> Threadzahlen und Kerne allein sind nicht über Epochen vergleichbar. Ein moderner Kern hat erheblich andere IPC, SIMD, Cache- und Speicherfähigkeiten.

### Sinnvolle Benchmarks

| Bedarf | geeignete Messung |
|---|---|
| Single-Thread/Compiler | SPECspeed, reale Build-Zeit, Geekbench Single als grobe Näherung |
| Durchsatz | SPECrate, parallele Builds, Rendering/Encoding |
| Gaming | reale Spiele, 1%-Low, gleiche GPU/Settings, CPU-limitierte Auflösung |
| Server | VM-Dichte, DB-Transaktionen, Webdurchsatz, Energie pro Aufgabe |
| HPC | reale Solver, Speicherbandbreite, AVX-/Vektorpfad, MPI/NUMA |
| AI | End-to-End-Latenz und Durchsatz mit realem Modell, nicht nur TOPS |

Vendorvergleiche sind Ausgangspunkte, keine neutrale Rangliste. Exakte Testkonfiguration und Fußnoten archivieren.

## Inventar und Diagnose

### Linux

```bash
lscpu
cat /proc/cpuinfo | sed -n '1,80p'
sudo dmidecode -t processor -t memory
sudo lshw -class processor
```

Microcode:

```bash
dmesg | grep -i microcode
rpm -q amd-ucode-firmware 2>/dev/null
apt policy amd64-microcode 2>/dev/null
```

Topologie/Frequenz:

```bash
lscpu -e=CPU,NODE,SOCKET,CORE,ONLINE,MAXMHZ,MINMHZ
cpupower frequency-info
```

Virtualisierung:

```bash
grep -m1 -oE 'svm|vmx' /proc/cpuinfo
systemd-detect-virt
```

### Windows PowerShell

```powershell
Get-CimInstance Win32_Processor |
  Select-Object Name,Manufacturer,NumberOfCores,NumberOfLogicalProcessors,
                MaxClockSpeed,SocketDesignation

Get-CimInstance Win32_BIOS | Select-Object SMBIOSBIOSVersion,ReleaseDate
Get-ComputerInfo | Select-Object CsSystemType,OsName,OsVersion
```

### Häufige Fehlerbilder

| Symptom | prüfen |
|---|---|
| CPU nicht erkannt | BIOS/AGESA, Sockel-/Board-Supportliste, Pins/Socket |
| RAM instabil | EXPO aus, JEDEC testen, BIOS, SOC-Spannung nicht blind erhöhen |
| Leistung zu niedrig | Temperatur, PPT/TDC/EDC, Eco-Mode, Scheduler, Hintergrundlast |
| einzelne Kerne unterschiedlich | Boost-/Preferred-Cores normal; Topologie prüfen |
| VM-Migration scheitert | CPU-Feature-Level, EVC/Compatibility Mode, Microcode |
| X3D-Spiel nutzt falsches CCD | Chipsatztreiber, Game Mode/Scheduler, BIOS |

## Schnellreferenz

```text
AMD-Geschichte:
K6 -> Athlon -> AMD64/Opteron -> Phenom -> Bulldozer -> Zen

Zen:
2017 Zen -> 2019 Zen 2 Chiplets -> 2020 Zen 3 -> 2022 Zen 4
-> 2024 Zen 5 -> 2026 Venice-Produktion/kommende 6th-Gen-EPYC-Phase

Vor Vergleich:
SKU + Architektur + Power-Limit + RAM + BIOS + Kühlung + Workload

Vor Kauf:
Sockel/Board-Support, ECC, PCIe-Lanes, iGPU/NPU, Lizenzkosten, Energie pro Aufgabe
```

## Quellen

- [AMD Ryzen Desktop Processors](https://www.amd.com/en/products/processors/desktops/ryzen.html)
- [AMD Ryzen Laptop Processors](https://www.amd.com/en/products/processors/laptop/ryzen.html)
- [AMD EPYC Processors](https://www.amd.com/en/products/processors/server/epyc.html)
- [AMD Ryzen 7 launch, 2017](https://www.amd.com/en/newsroom/press-releases/2017-3-2-amd-ryzen-tm-7-desktop-processors-featuring-recor.html)
- [AMD Ryzen 5000 and Zen 3](https://www.amd.com/en/newsroom/press-releases/2020-10-8-amd-launches-amd-ryzen-5000-series-desktop-process.html)
- [AMD Ryzen 9000 and Zen 5](https://www.amd.com/en/newsroom/press-releases/2024-6-2-amd-unveils-next-gen-zen-5-ryzen-processors-to-p.html)
- [5th Gen AMD EPYC](https://www.amd.com/en/newsroom/press-releases/2024-10-10-amd-launches-5th-gen-amd-epyc-cpus-maintaining-le.html)
- [AMD „Venice“ production ramp, 2026](https://www.amd.com/en/newsroom/press-releases/2026-5-20-amd-announces-production-ramp-of-next-generation-a.html)

## Verwandte Notizen

- [[Prozessorhistorie-Intel-AMD-Arm-Premium-Spickzettel]]
- [[Intel-Prozessorhistorie-Premium-Spickzettel]]
- [[Arm-Prozessorhistorie-Premium-Spickzettel]]
- [[CPU-Benchmarks-und-Vergleichbarkeit-Premium-Spickzettel]]
- [[ls-Familie-und-Hardwareinventar-Premium-Spickzettel]]
- [[dmesg-Premium-Spickzettel]]
