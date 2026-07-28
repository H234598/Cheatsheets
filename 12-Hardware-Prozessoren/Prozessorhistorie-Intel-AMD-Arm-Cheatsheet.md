---
title: "Prozessorhistorie Intel, AMD und Arm – Cheatsheet"
aliases: ["CPU Geschichte", "Intel AMD ARM Historie", "Prozessor Benchmark Cheatsheet", "x86 Arm Vergleich"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [hardware, cpu, intel, amd, arm, x86, benchmark, geschichte]
source: "Herstellerdokumentation, Geekbench Browser und SPEC CPU"
---

# Prozessorhistorie Intel, AMD und Arm – Cheatsheet

> [!abstract] Zweck
> Kompakte, aber belastbare Geschichte wichtiger Intel-, AMD- und Arm-Meilensteine bis **17. Juli 2026** – mit Architekturbegriffen, typischen Hardwaredaten, Marktverschiebungen, Benchmarkbeispielen, Messmethodik und Kauf-/Diagnosehinweisen.

> [!info] Unterseiten
> - [[Intel-Prozessorhistorie-Cheatsheet|Intel – ausführliche Zeitleiste]]
> - [[AMD-Prozessorhistorie-Cheatsheet|AMD – ausführliche Zeitleiste]]
> - [[Arm-Prozessorhistorie-Cheatsheet|Arm – ausführliche Zeitleiste]]
> - [[CPU-Benchmarks-und-Vergleichbarkeit-Cheatsheet|Benchmarkmethodik und Vergleichbarkeit]]

> [!warning] Benchmarkzahlen richtig lesen
> Einzelwerte sind **keine ewige Rangliste**. BIOS, Kühlung, RAM, Power Limits, Betriebssystem, Compiler, Microcode, Benchmarkversion und Stichprobengröße verändern Ergebnisse. Crowdsourcing-Werte wie PassMark sind Momentaufnahmen; Server-, Mobil- und Desktop-CPUs sind nicht ohne Weiteres direkt vergleichbar.

## Inhalt

- [[#Grundbegriffe]]
- [[#Die kurze Gesamtgeschichte]]
- [[#Intel – Meilensteine]]
- [[#AMD – Meilensteine]]
- [[#Arm – Meilensteine]]
- [[#Architekturen im Vergleich]]
- [[#Fertigungsprozesse und Chiplets]]
- [[#Kerne, Threads, Caches und Speicher]]
- [[#Beschleuniger und NPUs]]
- [[#Benchmark-Snapshot 2026]]
- [[#Historische Benchmark-Einordnung]]
- [[#Selbst benchmarken unter Linux]]
- [[#CPU unter Windows und Linux inventarisieren]]
- [[#Kauf- und Auswahlmatrix]]
- [[#Fehlinterpretationen vermeiden]]
- [[#Schnellreferenz]]

## Grundbegriffe

| Begriff | Bedeutung |
|---|---|
| **ISA** | Befehlssatzarchitektur, z. B. x86-64 oder Armv9 |
| **Mikroarchitektur** | konkrete interne Umsetzung einer ISA, z. B. Zen, Core, Cortex |
| **SoC** | System-on-Chip mit CPU, GPU, I/O, NPU usw. |
| **Core** | physischer Rechenkern |
| **Thread/SMT** | logischer Ausführungskontext pro Kern |
| **IPC** | Instructions per Cycle; workloadabhängig |
| **Takt** | Zyklen pro Sekunde, nicht alleinige Leistungsaussage |
| **Cache** | schneller Speicher L1/L2/L3 nahe an den Kernen |
| **TDP/PBP** | thermische/planerische Leistungsgröße, nicht immer reale Maximalaufnahme |
| **Chiplet** | getrennte Dies in einem Paket, z. B. Compute + I/O |
| **Node** | Fertigungsbezeichnung; Nanometerwerte verschiedener Hersteller nicht direkt geometrisch vergleichen |
| **NPU** | Beschleuniger für neuronale Netze/Matrixoperationen |

Leistung grob:

```text
Performance ≈ IPC × effektiver Takt × nutzbare Parallelität × Speicher-/I/O-Verhalten
```

> [!important]
> **Arm** ist nicht einfach ein einzelner CPU-Hersteller. Arm entwickelt ISA und Core-/System-IP; Apple, Qualcomm, Ampere, AWS und andere bauen eigene oder lizenzierte Implementierungen.

## Die kurze Gesamtgeschichte

```text
1971 Intel 4004: Mikroprozessor wird kommerziell greifbar
1978 Intel 8086: Ursprung der x86-Linie
1980er Arm1/ARM2: einfache, energieeffiziente RISC-Idee
1990er Pentium/AMD K5-K6: PC-Leistungswettbewerb
2003 AMD64: x86 wird 64-Bit und bleibt kompatibel
2006 Intel Core: Abkehr von NetBurst, Effizienzsprung
2011–2015 Mobilboom: Arm dominiert Smartphones, x86 stagniert teilweise
2017 AMD Zen/Ryzen/EPYC: Wettbewerb bei Kernen, IPC und Chiplets kehrt zurück
2020 Apple M1: Arm-SoCs zeigen Desktop-/Notebook-Leistung bei hoher Effizienz
2021–2026 Hybridkerne, Chiplets, 3D-Cache, NPUs und spezialisierte Beschleuniger
2026 Intel 18A, AMD N2-EPYC und neue Arm-C1-Plattformen markieren nächste Integrationsstufe
```

## Intel – Meilensteine

### Frühe Mikroprozessoren

| Jahr | Produkt | typische Eckdaten | Bedeutung |
|---:|---|---|---|
| 1971 | Intel 4004 | 4 Bit, ca. 2.300 Transistoren, ca. 108 kHz, 10 µm | erster kommerziell erfolgreicher Einchip-Mikroprozessor |
| 1972 | 8008 | 8 Bit | frühe General-Purpose-CPU |
| 1974 | 8080 | 8 Bit, bis etwa 2 MHz | Mikrocomputer-Ökosystem |
| 1978 | 8086 | 16 Bit, 5–10 MHz, ca. 29.000 Transistoren | Start der x86-Familie |
| 1979 | 8088 | 16-Bit-Kern, 8-Bit-Bus | IBM-PC-Basis |

### x86 wird leistungsfähiger

| Jahr | Familie | Innovation |
|---:|---|---|
| 1982 | 80286 | Protected Mode, mehr adressierbarer Speicher |
| 1985 | 80386 | 32-Bit-x86, Paging, ca. 275.000 Transistoren |
| 1989 | 80486 | integrierte FPU/Cache je Modell, Pipeline |
| 1993 | Pentium | superskalar, 64-Bit-Datenbus, starke FPU |
| 1995 | Pentium Pro | Out-of-Order, Basis der späteren P6-Linie |
| 1997–1999 | Pentium II/III | MMX/SSE, höhere Integration |

### NetBurst und die Taktgrenze

Pentium 4 setzte ab 2000 auf sehr tiefe Pipelines und hohe Taktraten. Vorteile in bestimmten Workloads, aber steigende Leistungsaufnahme und Wärme. Die Erwartung, Performance primär über GHz zu skalieren, scheiterte an Energie- und Pipelinekosten.

```text
Lehre: hoher Takt ohne IPC/Effizienz ist kein nachhaltiger Fortschritt.
```

### Core-Ära

| Jahr | Familie | Bedeutung |
|---:|---|---|
| 2006 | Core 2 | effizientere P6-abgeleitete Architektur, Mehrkern wird Mainstream |
| 2008 | Nehalem/Core i7 | integrierter Speichercontroller, SMT/Hyper-Threading zurück, Turbo |
| 2011 | Sandy Bridge | starke integrierte Plattform, AVX, hohe Effizienz |
| 2013–2020 | Haswell bis Comet Lake | inkrementelle IPC-/iGPU-/Plattformfortschritte, lange 14-nm-Phase |
| 2017+ | Xeon Scalable | neue Servermarke, Mesh/mehr Kerne/Accelerators je Generation |

### Hybrid- und Tile-Ära

- **Alder Lake (2021):** Performance- und Efficiency-Kerne im PC-Mainstream.
- **Meteor Lake/Core Ultra (2023/24):** Tile-/Chiplet-artiger Aufbau, NPU, neue Marke.
- **Lunar Lake (2024):** starke Notebook-Effizienz, integrierte Speicher-/GPU-/NPU-Plattform.
- **Arrow Lake/Core Ultra 200 (2024/25):** Desktop- und Mobilfortführung.
- **Core Ultra Series 3 / Panther Lake (2026):** Client-Familie auf Intel-18A-Basis, neue CPU/GPU/NPU-Integration.
- **Xeon 6 / Xeon 6+ (2024–2026):** P-Core- und E-Core-Varianten; Xeon 6+ bis zu 288 E-Kerne pro Sockel laut Intel.

> [!note]
> Intel-Marketingnamen, interne Codenamen und konkrete SKUs nicht gleichsetzen. „Core Ultra Series 3“ umfasst unterschiedliche Plattformen und Leistungsbereiche.

## AMD – Meilensteine

### Von x86-Kompatibilität zu eigener Architektur

AMD begann als Zweitquelle/Kompatibilitätsanbieter und entwickelte zunehmend eigene x86-Kerne.

| Jahr | Familie | Bedeutung |
|---:|---|---|
| 1996 | K5 | erste weitgehend eigene x86-Mikroarchitektur |
| 1997 | K6 | konkurrenzfähige Desktop-CPU, 3DNow! später |
| 1999 | Athlon/K7 | erstmals 1 GHz im PC-Markt, starker FPU-/Bus-Wettbewerb |
| 2003 | Opteron/Athlon 64 | AMD64/x86-64, integrierter Speichercontroller, HyperTransport |
| 2005 | Athlon 64 X2 | Dual-Core im Desktop-Mainstream |

### AMD64 verändert die Branche

AMD erweiterte x86 auf 64 Bit und bewahrte 32-Bit-Kompatibilität. Intel übernahm kompatible 64-Bit-Erweiterungen. Dadurch setzte sich x86-64 im PC- und Servermarkt durch.

### Schwierige Zwischenphase

Bulldozer und Nachfolger (ab 2011) setzten auf Module mit geteilten Ressourcen. Hohe Kern-/Modulzahlen konnten niedrige Pro-Thread-Leistung und Effizienz nicht immer kompensieren. AMD verlor Marktanteile und musste Architektur und Produktstrategie neu ausrichten.

### Zen-Renaissance

| Jahr | Generation | Highlights |
|---:|---|---|
| 2017 | Zen / Ryzen 1000 / EPYC Naples | deutlicher IPC-Sprung, SMT, skalierbare Mehrkernstrategie |
| 2018 | Zen+ | Latenz/Takt/Fertigung verbessert |
| 2019 | Zen 2 | 7-nm-Compute-Chiplets + I/O-Die, PCIe 4.0, bis 64 Serverkerne |
| 2020 | Zen 3 | vereinheitlichter 8-Kern-CCX, großer Gaming-/IPC-Sprung |
| 2022 | Zen 4 | DDR5, PCIe 5.0, AVX-512-Umsetzung, 5 nm |
| 2023 | Zen 4c | dichtere Kerne für Cloud/Server |
| 2024 | Zen 5 | breitere Front-/Execution-End-Verbesserungen, Ryzen 9000/EPYC Turin |
| 2022+ | 3D V-Cache | gestapelter L3-Cache, besonders stark in vielen Spielen/Cacheworkloads |

### Stand 2026

- **Ryzen AI 400 / PRO 400:** mobile Plattform mit CPU/GPU/NPU; AMD nennt bis zu 60 NPU-TOPS.
- **EPYC Venice, 6. Generation:** Produktionshochlauf 2026; TSMC-N2-Fertigung für Compute-Chiplets laut AMD.
- Chiplets, 3D-Stacking und getrennte dichte Kerne bleiben zentrale Strategie.

> [!tip]
> Eine Ryzen-Modellnummer allein reicht nicht: Generation, Architektur, TDP-Klasse, Kernzahl, iGPU/NPU und OEM-Power-Limit prüfen.

## Arm – Meilensteine

### Ursprung

| Jahr | Meilenstein | Eckdaten/Bedeutung |
|---:|---|---|
| 1985 | ARM1 | etwa 25.000 Transistoren, 3 µm; erster Testchip |
| 1987 | ARM2 | kommerzieller Einsatz im Acorn Archimedes |
| 1990 | Arm Ltd. | Ausgründung/JV; Lizenzmodell wird skalierbar |
| 1990er | ARM6/7 | Embedded- und Mobilverbreitung |
| 2000er | ARM9/11 | Feature-Phones, frühe Smartphones, Embedded |
| 2011 | ARMv8 angekündigt | 64-Bit-AArch64 neben AArch32 |
| 2010er | Cortex-A/R/M | Application, Real-time und Microcontroller klar getrennt |

### Smartphone- und SoC-Ära

Arm-Ökosystem wuchs durch:

- lizenzierbare ISA und Cores,
- hohe Performance pro Watt,
- Integration von GPU, Modem, ISP und Security,
- große Android-/iOS-Softwarebasis,
- Foundry- und SoC-Wettbewerb.

### Server und PCs

- **AWS Graviton:** Cloudserver mit eigener Arm-CPU.
- **Ampere Altra/AmpereOne:** viele Arm-Serverkerne ohne klassisches SMT je Produktlinie.
- **Apple M1 (2020):** Arm-basierter Mac-SoC mit hoher Single-Thread-Leistung und Effizienz.
- **Qualcomm Snapdragon X (2024+):** Windows-on-Arm mit eigenen Oryon-Kernen.
- **NVIDIA Grace:** Arm-CPU für HPC/AI-Systeme.

### Armv9 und C1-Plattform

Armv9 erweitert Sicherheits-, Vektor-/Matrix- und Plattformfunktionen. 2025/26 eingeführte C1-Kernfamilien wie C1-Ultra, C1-Pro und C1-Nano adressieren verschiedene Leistungs-/Effizienzklassen. Herstellerangaben zu Prozentverbesserungen sind Referenzdesignvergleiche und nicht automatisch Endgerätebenchmarks.

> [!important]
> „Arm ist effizienter“ ist zu pauschal. Effizienz hängt von Kern, SoC, Fertigung, Speicher, OS, Compiler und Leistungsziel ab. Ebenso kann x86 in optimierten Server- oder Desktop-Workloads sehr effizient sein.

## Architekturen im Vergleich

| Eigenschaft | x86-64 | Arm64/AArch64 |
|---|---|---|
| historisches Modell | komplexe variable Instruktionen, starke Kompatibilität | RISC-Ursprung, Lizenz-/SoC-Ökosystem |
| dominierende Märkte | PC, Workstation, klassischer Server | Mobil, Embedded, zunehmend PC/Cloud/HPC |
| Implementierer | Intel, AMD | Apple, Qualcomm, Ampere, AWS, NVIDIA u. a. |
| Softwarekompatibilität | sehr große Legacy-Basis | stark gewachsen, Übersetzung bei Altsoftware möglich |
| Plattformintegration | diskrete und SoC-/Tile-Designs | häufig hochintegrierte SoCs |
| Vergleich | nur workload- und systembezogen sinnvoll | nur workload- und systembezogen sinnvoll |

Moderne Kerne beider ISAs nutzen ähnliche Hochleistungstechniken:

- Out-of-Order-Ausführung,
- Sprungvorhersage,
- breite Decoder/Execution Units,
- große Caches,
- SIMD/Vektorbefehle,
- Prefetching,
- Power-/Clock-Gating,
- heterogene Kerne.

## Fertigungsprozesse und Chiplets

### Warum Chiplets?

```text
großer monolithischer Die
→ schlechtere Ausbeute und hohe Kosten

mehrere kleinere Dies/Chiplets
→ bessere Ausbeute, modulare Produktlinien, gemischte Nodes
```

Nachteile:

- Interconnect-Latenz,
- Packaging-Komplexität,
- Energie für Die-to-Die-Verbindungen,
- NUMA-/Cacheeffekte,
- schwierigeres thermisches Design.

Intel spricht je Produkt von Tiles, AMD häufig von CCD/IOD. 2.5D/3D-Packaging und gestapelte Caches verwischen die Grenze zwischen „Chip“ und „System“.

### Node-Namen

```text
Intel 18A ≠ TSMC N2 ≠ Samsung 2 nm als direkt messbare Geometrie
```

Vergleiche besser:

- Dichte,
- Performance/Watt,
- Leakage,
- Yield,
- verfügbare Bibliotheken,
- Packaging,
- reale Produktdaten.

## Kerne, Threads, Caches und Speicher

### Mehr Kerne helfen nur bei Parallelität

```text
Single-Thread: UI, Teile von Spielen, sequenzielle Logik
Multi-Thread: Rendering, Kompilieren, wissenschaftliche Jobs, VMs
Memory-bound: Datenbanken, Analytics, Simulationen
Latency-bound: Interaktive/abhängige Workloads
```

### SMT

Intel Hyper-Threading und AMD SMT teilen Kernressourcen zwischen Threads. Gewinn variiert; bei Sicherheit, Lizenzierung oder deterministischer Latenz kann SMT deaktiviert werden.

### Cache

3D V-Cache zeigt, dass mehr L3 in Spielen und bestimmten Datenworkloads starke Gewinne bringt. In rechen- oder bandbreitenlimitierten Aufgaben kann derselbe Cache wenig helfen.

### Speicher

Prüfen:

- DDR-Generation und Kanäle,
- ECC-Unterstützung,
- maximale Kapazität,
- Bandbreite und Latenz,
- NUMA-Domänen,
- CXL/PCIe-Version,
- integrierter Speicher bei SoCs.

## Beschleuniger und NPUs

CPU-Pakete integrieren zunehmend:

- GPU,
- NPU/AI-Engine,
- Medienencoder/-decoder,
- Verschlüsselung,
- Netzwerk-/Datenbewegungsbeschleuniger,
- Sicherheitsenklaven.

TOPS ist nur eine Spitzenkennzahl. Prüfen:

```text
Datentyp (INT8/FP16/...)
Sparsity-Annahme
Speicherbandbreite
Software-/Frameworksupport
Modellkompatibilität
Dauerleistung
End-to-End-Latenz
```

> [!warning]
> 60 NPU-TOPS bedeuten nicht, dass eine Anwendung 60 Billionen nützliche Modelloperationen pro Sekunde erzielt.

## Benchmark-Snapshot 2026

### Beispielwerte – PassMark CPU Mark

**Momentaufnahme vom 17. Juli 2026**, gerundete öffentliche Vergleichswerte; je Modellseite können Stichprobe und Wert später abweichen.

| CPU | Klasse | Kerne/Threads | CPU Mark ungefähr | Single Thread ungefähr | Einordnung |
|---|---|---:|---:|---:|---|
| AMD Ryzen 9 9950X3D | Desktop | 16/32 | 70.100 | 4.740 | sehr stark Multi, 3D-Cache/Gaming |
| Intel Core Ultra 9 285K | Desktop | 24 Kerne, Hybrid | 67.300 | 5.090 | hohe Single- und Multi-Leistung |
| Intel Core i9-14900K | Desktop | 24 Kerne, Hybrid | 58.300 | 4.690 | sehr hohe Leistungsaufnahme je Limits möglich |
| Apple M5 Max 18-Core | SoC/Notebook | 18 CPU-Kerne | 57.700 | 5.940 | starke Single-Leistung, SoC-Kontext |
| Intel Core Ultra X9 388H | Mobil | Hybrid | 36.900 | abhängig von Datenstand | OEM-/Power-Limit entscheidend |
| Apple M5 10-Core | SoC/Notebook | 10 CPU-Kerne | 26.800 | 5.760 | hohe Single-/Effizienzklasse |
| AMD EPYC 9654 | Server | 96/192 | 119.300 | 2.900 | Server-Multi, nicht Desktopvergleich |
| Ampere 192-Core Arm | Server | 192/192 | ca. 57.400 | ca. 1.230 | geringe Stichprobe; Cloud-/Serverziel |

> [!danger] Nicht falsch vergleichen
> Ein EPYC-Wert beinhaltet 96 Kerne und enorme Speicher-/Plattformressourcen; ein Notebook-SoC arbeitet in anderem Power- und Kühlrahmen. CPU Mark ist kein Preis-, Energie-, Gaming-, Datenbank- oder KI-Gesamtscore.

### Bessere Vergleichsmatrix

```text
1. identischer Workload
2. identische Software-/Compiler-Version
3. reale Power-Limits
4. Energie pro Aufgabe
5. Latenz und Durchsatz
6. Speicher-/I/O-Konfiguration
7. Anschaffung und Plattformkosten
```

## Historische Benchmark-Einordnung

PassMark-Vergleichswerte illustrieren Größenordnungen, nicht exakte Generationseffekte:

| CPU | Jahr grob | CPU Mark ungefähr | Single ungefähr |
|---|---:|---:|---:|
| Pentium 4 3,4 GHz | 2004 | 300 | 650 |
| Core 2 Duo E6600 | 2006 | 1.535 | 923 |
| Core 2 Quad Q6600 | 2007 | 1.846 | 953 |
| Core i7-2600K | 2011 | 5.479 | 1.740 |
| Core i7-3770 | 2012 | 6.413 | 2.070 |
| Ryzen 5 3600 | 2019 | 17.661 | 2.558 |
| Apple M1 | 2020 | 14.125 | 3.674 |
| Ryzen 5 5600X | 2020 | 21.828 | 3.365 |
| Ryzen 7 7800X3D | 2023 | 34.277 | 3.760 |

Interpretation:

- Mehrkernwerte wachsen durch Kernzahl und SMT stark.
- Single-Thread wächst langsamer, aber stetig über IPC/Takt/Cache.
- Benchmarkversionen verändern die Skala; historische Werte nicht wie SI-Einheiten behandeln.
- Moderne CPUs erledigen zusätzlich Medien-, KI- und Kryptofunktionen in Spezialblöcken.

## Selbst benchmarken unter Linux

### Systemzustand dokumentieren

```bash
uname -a
lscpu
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null
free -h
lsblk
```

Temperatur/Takt:

```bash
sensors
watch -n1 'grep -m1 "cpu MHz" /proc/cpuinfo'
```

### sysbench CPU

```bash
sudo dnf install sysbench      # Fedora/RHEL
sudo apt install sysbench      # Debian/Ubuntu

sysbench cpu --threads=1 --time=30 run
sysbench cpu --threads="$(nproc)" --time=30 run
```

### stress-ng

```bash
stress-ng --cpu 1 --cpu-method matrixprod --metrics-brief --timeout 60s
stress-ng --cpu 0 --metrics-brief --timeout 60s
```

### OpenSSL

```bash
openssl speed -seconds 10 sha256
openssl speed -seconds 10 -multi "$(nproc)" sha256
openssl speed -seconds 10 aes-256-gcm
```

### perf

```bash
sudo perf stat -r 5 -- taskset -c 0 ./mein-benchmark
```

Wichtige Zähler:

```text
cycles
instructions
IPC = instructions / cycles
branches / branch-misses
cache-references / cache-misses
context-switches
```

### Phoronix Test Suite

```bash
phoronix-test-suite list-available-tests
phoronix-test-suite benchmark pts/build-linux-kernel
```

> [!important]
> Vor/nach jedem Lauf Temperatur, Frequenz, Energieprofil und Hintergrundlast prüfen. Mindestens mehrere Durchläufe mit Median und Streuung berichten.

### Energie messen

Je Plattform:

```bash
sudo turbostat --Summary --interval 1
sudo powertop
```

AMD/Arm benötigen ggf. andere Sensoren oder externe Leistungsmessung. Steckdosenmessung erfasst das Gesamtsystem und ist für „Energie pro Aufgabe“ oft nützlicher.

## CPU unter Windows und Linux inventarisieren

### Linux

```bash
lscpu
cat /proc/cpuinfo
sudo dmidecode -t processor
numactl --hardware
lstopo-no-graphics
```

Microcode:

```bash
dmesg | grep -i microcode
rpm -q microcode_ctl 2>/dev/null
dpkg -l 'intel-microcode' 'amd64-microcode' 2>/dev/null
```

### Windows PowerShell

```powershell
Get-CimInstance Win32_Processor |
  Select-Object Name,Manufacturer,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed

Get-ComputerInfo | Select-Object CsProcessors,OsName,OsVersion
```

Leistungsindikatoren:

```powershell
Get-Counter '\Processor Information(_Total)\% Processor Utility'
```

### Virtuelle Maschine

```bash
systemd-detect-virt
lscpu | grep -E 'Hypervisor|Virtualization'
```

In VMs kann angezeigtes Modell maskiert sein; vCPU ist keine garantierte physische Kernleistung.

## Kauf- und Auswahlmatrix

| Anwendungsfall | Prioritäten |
|---|---|
| Office/Alltag | Effizienz, Plattform, leise Kühlung, Single-Thread |
| Gaming | GPU zuerst, dann CPU-Latenz/Cache; Benchmarks des konkreten Spiels |
| Kompilieren/Rendering | Kerne, Dauerleistung, RAM, Kühlung |
| VMs/Container | Kerne, RAM-Kapazität, ECC/IOMMU, Plattform-I/O |
| Datenbank | Latenz, Cache, Speicherkanäle, NUMA, Lizenzmodell |
| AI lokal | GPU/NPU-Software, VRAM/RAM, unterstützte Datentypen |
| Server | RAS, ECC, PCIe/CXL, Energie pro Arbeit, Support, Lizenzkosten |
| Notebook | reale Akkulaufzeit, Dauerleistung, OEM-Kühlung, Standby/Treiber |

Gesamtkosten:

```text
CPU + Mainboard + RAM + Kühlung + Netzteil + Lizenz + Energie + Betrieb
```

## Fehlinterpretationen vermeiden

### „Mehr GHz ist schneller“

Nur innerhalb ähnlicher Architektur und Last begrenzt brauchbar.

### „Mehr Kerne sind immer besser“

Nur wenn Software parallelisiert und Speicher/I/O nachkommt.

### „Arm ist RISC, x86 ist CISC, daher ...“

Zu grob. Moderne Kerne übersetzen und planen intern komplex; Systemdesign ist entscheidend.

### „2 nm ist doppelt so gut wie 4 nm“

Node-Namen sind keine direkte Längen- oder Leistungsgarantie.

### „TDP ist Verbrauch“

TDP/PBP ist eine Auslegungsgröße; reale Package-Power kann darunter oder deutlich darüber liegen.

### „Ein Benchmark entscheidet alles“

Mindestens relevante Anwendung, Energie, Latenz, Preis und Plattform messen.

### „Herstellerprozent = unabhängiger Test“

Herstellerangaben dokumentieren Testbedingungen und zeigen Potenzial, brauchen aber unabhängige Reproduktion.

## Schnellreferenz

```text
ISA ≠ Mikroarchitektur ≠ SoC.
Performance = IPC × Takt × Parallelität × Speicher/I/O.
GHz und Kernzahl nie isoliert vergleichen.
PassMark ist Momentaufnahme, kein Naturgesetz.
Für Kauf: konkrete Anwendung + Power-Limit + Gesamtsystem.
Für Benchmark: gleiche Software, mehrere Läufe, Temperatur/Energie/Streuung dokumentieren.
2026: Intel 18A/Panther Lake und Xeon 6+, AMD Ryzen AI 400 und EPYC Venice,
Armv9/C1 sowie kundenspezifische Arm-Server-/PC-SoCs.
```

## Quellen

### Hersteller und Geschichte

- [Intel Technology Timeline](https://timeline.intel.com/)
- [Intel Microprocessor Quick Reference](https://www.intel.com/pressroom/kits/quickreffam.htm)
- [Intel Core Ultra Series 3](https://www.intel.com/content/www/us/en/products/details/processors/core-ultra/series-3.html)
- [Intel Xeon 6](https://www.intel.com/content/www/us/en/products/details/processors/xeon/6.html)
- [AMD Ryzen Geschichte und Produkte](https://www.amd.com/en/products/processors/desktops/ryzen.html)
- [AMD EPYC](https://www.amd.com/en/products/processors/server/epyc.html)
- [Arm Official History](https://newsroom.arm.com/blog/arm-official-history)
- [Arm Architecture](https://www.arm.com/architecture)

### Benchmarks

- [PassMark CPU Benchmarks](https://www.cpubenchmark.net/)
- [Phoronix Test Suite](https://www.phoronix-test-suite.com/)
- [Linux perf](https://perf.wiki.kernel.org/)

## Verwandte Notizen

- [[ls-Familie-und-Hardwareinventar-Cheatsheet]]
- [[dmesg-Cheatsheet]]
- [[Fedora-RHEL-Cheatsheet]]
- [[Windows-Terminal-Cheatsheet]]
- [[Rust-Cheatsheet]]
- [[Python-3-Cheatsheet]]
