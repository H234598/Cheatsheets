---
title: "Arm-Prozessorhistorie – Cheatsheet"
aliases: ["ARM CPU Geschichte", "Arm Prozessoren Historie", "AArch64 Cortex Neoverse Timeline"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [hardware, cpu, arm, aarch64, cortex, neoverse, apple-silicon, geschichte]
source: "https://www.arm.com/architecture"
---

# Arm-Prozessorhistorie – Cheatsheet

> [!abstract] Zweck
> Technische Geschichte des Arm-Ökosystems von ARM1/ARM2 über ARM7, Cortex und AArch64 bis Apple Silicon, Neoverse, C1/Lumex und dem 2026 angekündigten Arm-AGI-CPU-Silizium. Mit ISA-/Core-Unterscheidung, Hardwaremerkmalen, Benchmarkregeln und Diagnose.

> [!important] Arm ist nicht „ein Prozessor“
> **Arm Ltd.** entwickelt Befehlssatzarchitekturen, Core-IP, Compute Subsystems und seit 2026 auch angekündigte eigene Produktionssilizium-Produkte. Endprozessoren stammen unter anderem von Apple, Qualcomm, MediaTek, Samsung, AWS, Ampere, NVIDIA und zahlreichen Mikrocontrollerherstellern. Zwei „Arm64“-Chips können intern so verschieden sein wie zwei unterschiedliche x86-Mikroarchitekturen.

## Inhalt

- [[#Zeitleiste in 30 Sekunden]]
- [[#ARM1, ARM2 und das RISC-Konzept]]
- [[#Lizenzmodell und Ökosystem]]
- [[#Architekturversionen]]
- [[#Cortex-A, Cortex-R und Cortex-M]]
- [[#big.LITTLE und DynamIQ]]
- [[#Smartphone- und SoC-Ära]]
- [[#Apple Silicon und Arm-PCs]]
- [[#Neoverse, Cloud und HPC]]
- [[#Armv9, C1 und Lumex]]
- [[#Arm AGI CPU 2026]]
- [[#Hardware- und Benchmark-Einordnung]]
- [[#Kompatibilität und Software]]
- [[#Inventar und Diagnose]]
- [[#Schnellreferenz]]

## Zeitleiste in 30 Sekunden

```text
1985  ARM1-Testchip bei Acorn
1986/87 ARM2 im Archimedes: einfache, effiziente 32-Bit-RISC-CPU
1990  Advanced RISC Machines Ltd. gegründet
1994  ARM7TDMI wird Embedded-Massenkern
1998  StrongARM/XScale-Ära zeigt höhere mobile Leistung
2002  ARM11-Familie
2004  Cortex-M3: moderne Mikrocontrollerlinie
2005  Cortex-A8: Application-Prozessor mit höherer Leistung
2010  Cortex-A9-Multicore verbreitet sich
2011  ARMv8-A angekündigt: AArch64/64 Bit
2011  big.LITTLE verbindet Leistungs- und Effizienzkerne
2013+ 64-Bit-Smartphone-/Server-SoCs
2018  Neoverse für Infrastruktur
2020  Apple M1 etabliert Arm-SoCs im Mac
2021  Armv9 angekündigt
2024+ Snapdragon X und weitere Windows-on-Arm-Plattformen
2025  C1-Kernfamilie/Lumex mit Armv9.3 und SME2
2026  Arm AGI CPU: Arm kündigt eigenes Datacenter-Produktionssilizium an
```

## ARM1, ARM2 und das RISC-Konzept

Acorn suchte in den 1980er-Jahren eine CPU für leistungsfähige, bezahlbare Computer. Die entstehende Architektur setzte auf:

- relativ einfache, regelmäßig kodierte Instruktionen;
- viele Register;
- bedingte Ausführung in frühen Versionen;
- Load/Store-Prinzip;
- geringe Transistorzahl und Leistungsaufnahme;
- einfache Pipeline.

Der ARM1-Testchip von 1985 und ARM2 in Acorn-Computern zeigten, dass gute Leistung nicht zwingend eine sehr komplexe Hardwaredekodierung erforderte.

> [!note] RISC vs. CISC heute
> Die historische Einteilung erklärt Wurzeln, aber moderne Hochleistungskerne beider Welten nutzen Out-of-Order-Ausführung, Registerumbenennung, Mikro-Operationen, große Caches und komplexe Vorhersage. Aus dem ISA-Etikett allein folgt keine aktuelle Leistung oder Effizienz.

## Lizenzmodell und Ökosystem

Arm skalierte nicht primär durch den Verkauf identischer CPUs, sondern durch IP-Lizenzen.

### Typische Lizenzstufen

| Modell | Bedeutung |
|---|---|
| Core-IP-Lizenz | Partner integriert einen fertigen Cortex-/Neoverse-Kern |
| Compute Subsystem | vorintegrierter Cluster samt Interconnect/System-IP |
| Architekturlizenz | Partner entwickelt eine eigene Mikroarchitektur für die Arm-ISA |
| Produktionssilizium | Arm liefert selbst entworfene fertige Chips; 2026 mit AGI angekündigt |

Beispiele eigener Mikroarchitekturen auf Arm-ISA:

- Apple Performance-/Efficiency-Cores;
- Qualcomm Oryon;
- AWS Graviton-Kerne beziehungsweise angepasste Neoverse-Basis je Generation;
- NVIDIA Grace-CPU-Plattform;
- Ampere-eigene Serverdesigns je Generation.

Vorteile des Ökosystems:

- viele Anbieter und Zielmärkte;
- Integration von CPU, GPU, NPU, Modem, ISP und Security im SoC;
- Anpassung an Energie-, Flächen- und Leistungsziele;
- große Embedded- und Mobilsoftwarebasis.

Nachteile/Komplexität:

- gleiche ISA bedeutet nicht gleiche Plattformfunktionen;
- Firmware/Bootketten sind herstellerspezifisch;
- Treiber- und Mainline-Kernel-Support variiert;
- Produktnamen verraten oft wenig über den realen Kern.

## Architekturversionen

| Architektur | Zeit grob | wichtige Punkte |
|---|---:|---|
| ARMv4T | 1990er | Thumb-Befehlssatz, ARM7TDMI |
| ARMv5 | späte 1990er/2000er | DSP-/Systemerweiterungen |
| ARMv6 | 2000er | SIMD-/Multiprocessing-Erweiterungen, ARM11 |
| ARMv7-A | ab 2007 | Cortex-A, NEON, VFP, 32-Bit-Application-Prozessoren |
| ARMv7-R | Echtzeit | deterministische Systeme |
| ARMv7-M | Mikrocontroller | Thumb-only-Profil, NVIC, Cortex-M |
| ARMv8-A | ab 2011/2013 | AArch64 plus optionales AArch32, 64-Bit-Register und Adressierung |
| ARMv8.x-A | 2010er | inkrementelle Security-, Virtualisierungs- und SIMD-Erweiterungen |
| Armv9-A | ab 2021 | Sicherheits-/Vektorplattform, SVE2, CCA als Architekturrahmen |
| Armv9.3-A | 2025+ | Basis der C1-Familie, SME2-Integration je Plattform |

### AArch32 und AArch64

```text
AArch32  32-Bit-Ausführungszustand, klassische ARM/Thumb-Linie
AArch64  64-Bit-Ausführungszustand mit neuem Register-/Instruktionsmodell
arm64    übliche OS-/Kernel-Bezeichnung für AArch64
```

Ein moderner Armv9-Chip muss nicht jeden alten 32-Bit-Modus in Hardware anbieten. Betriebssystem, Firmware und Hersteller bestimmen den tatsächlichen Support.

## Cortex-A, Cortex-R und Cortex-M

| Profil | Ziel | Beispiele |
|---|---|---|
| Cortex-A | Application, MMU, Linux/Android, hohe Leistung | A53, A72, A78, X4, C1 |
| Cortex-R | Echtzeit mit hoher Zuverlässigkeit | Storage, Automotive, Controller |
| Cortex-M | Mikrocontroller, geringe Fläche/Leistung | M0+, M3, M4, M7, M33, M55 |

### Cortex-M

Cortex-M prägte Mikrocontroller durch:

- standardisiertes Interruptmodell/NVIC;
- Thumb-Instruktionen;
- breite Tool- und RTOS-Unterstützung;
- Varianten mit DSP, FPU, TrustZone und Vektor-/ML-Erweiterungen.

Ein Cortex-M33 und ein Cortex-A78 sind beide Arm, aber nicht austauschbar: anderer Systemaufbau, andere MMU-/OS-Annahmen und völlig andere Leistungsziele.

### Cortex-A

Cortex-A entwickelte sich von In-Order- und frühen Out-of-Order-Kernen zu breiten Mobil-/Client-Kernen. Die Cortex-X-Linie priorisierte Spitzenleistung, während A5xx-Kerne Effizienzaufgaben übernahmen.

## big.LITTLE und DynamIQ

### big.LITTLE

Ein SoC kombiniert:

```text
leistungsstarke „big“-Kerne + kleine effiziente „LITTLE“-Kerne
```

Der Scheduler verschiebt Threads passend zu Last, Temperatur und Energieziel. Frühere Implementierungen nutzten Clusterwechsel; spätere Plattformen können Kerne flexibler gemeinsam verwenden.

### DynamIQ

DynamIQ erlaubt heterogenere Kerne innerhalb eines Clusters und gemeinsame Cache-/Interconnect-Strukturen. Daraus entstanden typische Smartphone-Konfigurationen mit:

- einem Spitzenkern;
- mehreren Performancekernen;
- mehreren Effizienzkernen.

> [!warning]
> „8 Kerne“ sagt ohne Kerntypen wenig aus. Ein 1+3+4-SoC unterscheidet sich stark von acht identischen Serverkernen.

## Smartphone- und SoC-Ära

Arm wurde zur dominierenden Basis für Smartphones, weil das Gesamtsystem optimiert werden konnte:

```text
CPU-Cluster
+ GPU
+ NPU/DSP
+ Modem
+ Kamera-ISP
+ Video-Codecs
+ Secure Enclave/TEE
+ Speichercontroller
+ Power-Management
```

Ein Smartphonebenchmark misst deshalb oft mehr als reine CPU-Leistung. Thermisches Gehäuse, Speicher, Scheduler, Kühlung und Hintergrundprozesse beeinflussen Dauerleistung.

### Typische historische Stationen

| Zeit | Plattformbeispiel | Bedeutung |
|---:|---|---|
| 2007–2010 | ARM11/Cortex-A8 | frühe moderne Smartphones |
| 2011–2013 | Cortex-A9/A15 | Multicore und höhere Spitzenleistung |
| 2014–2016 | Cortex-A53/A57/A72 | 64-Bit-Übergang und big.LITTLE |
| 2017–2020 | A73–A78, Cortex-X1 | steigende IPC und neue Spitzenkernklasse |
| 2021–2024 | Armv9, X2–X4/A7xx/A5xx | SVE2/Security, heterogene Cluster |
| 2025+ | C1-Ultra/Pro/Premium/Nano | Armv9.3, SME2, neue Namensfamilie |

## Apple Silicon und Arm-PCs

### Apple M1 als Wendepunkt

2020 führte Apple den M1 für Macs ein. Wichtig war nicht nur die ISA, sondern das Systemdesign:

- eigene breite CPU-Kerne;
- gemeinsam genutzte Speicherarchitektur;
- starke integrierte GPU;
- Medienblöcke und Neural Engine;
- enge Abstimmung von Hardware, macOS und Compiler;
- Übersetzung vorhandener x86-64-Software über Rosetta 2.

Folge: Arm wurde im allgemeinen PC-Diskurs nicht mehr nur als Mobil-/Embedded-Architektur betrachtet.

### Windows on Arm

Windows-on-Arm-Plattformen entwickelten sich über Qualcomm-Snapdragon-Generationen weiter. Seit Snapdragon X/Oryon ist die Kategorie leistungsfähiger, aber Kompatibilität bleibt workloadabhängig.

Prüfen:

- native ARM64-Version vorhanden?
- x64-/x86-Emulation unterstützt die Anwendung und Treiber?
- Kernel-, VPN-, Security- und Virtualisierungstreiber nativ?
- Plugins/Codecs/COM-Komponenten verfügbar?
- Leistung und Akku im konkreten Gerät, nicht nur Referenzdesign?

> [!danger]
> Benutzeranwendungen können emuliert werden; Kernel- und Hardwaretreiber benötigen in der Regel native Unterstützung. Das ist bei Kauf und Rollout wichtiger als eine einzelne Benchmarkzahl.

## Neoverse, Cloud und HPC

Arm bündelt Infrastrukturkerne unter **Neoverse**.

| Linie | Schwerpunkt |
|---|---|
| Neoverse N | Cloud-/Netzwerkdurchsatz und Effizienz |
| Neoverse V | hohe Pro-Thread-/HPC-Leistung |
| Neoverse E | Edge und energie-/flächenoptimierte Infrastruktur |

Beispiele im Markt:

- AWS Graviton in EC2;
- Ampere Altra/AmpereOne;
- NVIDIA Grace und Grace Hopper;
- Cloud-/Telekom-/Storage-SoCs verschiedener Hersteller;
- Fujitsu A64FX als SVE-HPC-Prozessor.

### Warum viele Serverkerne?

Viele Arm-Serverdesigns setzen auf viele physische Kerne ohne SMT. Mögliche Vorteile:

- planbarere Threadzuordnung;
- hohe Durchsatzdichte;
- weniger geteilte Kernressourcen;
- gute Energieeffizienz für horizontale Dienste.

Das ist kein allgemeiner Sieg. Datenbanken, Compiler, Vektor-HPC, Lizenzmodelle und Memory-Bandwidth reagieren unterschiedlich.

### NUMA und Plattformdaten

```bash
lscpu
numactl --hardware
lstopo-no-graphics 2>/dev/null
```

Bei Cloudinstanzen zusätzlich prüfen:

- vCPU-Definition;
- dediziert oder shared;
- Speicherbandbreite;
- Netzwerk/EBS/Local NVMe;
- Generation und Hostmodell;
- Preis pro erledigter Arbeit, nicht nur pro Instanzstunde.

## Armv9, C1 und Lumex

### Armv9

Armv9 ist eine Evolutionsplattform mit Schwerpunkten wie:

- SVE2 für skalierbare Vektorverarbeitung;
- Confidential Compute Architecture als Architekturrahmen;
- Memory-Tagging-/Security-Funktionen je Implementierung;
- Matrix-/AI-Erweiterungen in späteren Versionen;
- fortentwickelte Virtualisierung und Systemfunktionen.

Nicht jedes Feature ist in jedem Chip aktiv. Datenblatt und Betriebssystem-Support prüfen.

### C1-Kernfamilie

Die 2025 vorgestellte C1-Familie umfasst:

| Kern | Ziel |
|---|---|
| C1-Ultra | Spitzenleistung |
| C1-Premium | Sub-Flagship/AI-Offload und ausgewogene Leistung |
| C1-Pro | nachhaltige Performance und Flächeneffizienz |
| C1-Nano | LITTLE-/Always-on-Effizienz |

Arm beschreibt C1 als Armv9.3-A-Familie im Lumex Compute Subsystem. SME2 kann Matrix-/AI-Workloads beschleunigen, wenn Hardware, Compiler, Bibliothek und Modellpfad dies nutzen.

Herstellerangaben gegenüber der Vorgängergeneration umfassen je nach Cluster und Test:

- bis zu 5-fache AI-Beschleunigung;
- im Mittel etwa 30 % Benchmark-Leistungszuwachs;
- Effizienzverbesserungen je Kernklasse.

> [!warning] Herstellervergleich
> Diese Werte gelten für definierte Referenzkonfigurationen. Ein Endgerät kann wegen Takt, Cache, Fertigung, RAM und Kühlung deutlich abweichen.

## Arm AGI CPU 2026

Am 24. März 2026 kündigte Arm eine Erweiterung vom IP-/CSS-Angebot zu eigenem Produktionssilizium an. Erstes Produkt ist der **Arm AGI CPU** für agentische AI-Infrastruktur.

Einordnung:

- von Arm entworfenes Datacenter-CPU-Produkt;
- Ziel: Steuerung, Orchestrierung und allgemeine CPU-Arbeit in AI-Racks;
- enger Partner-/Systemkontext;
- Hersteller nennt mehr als doppelte Rack-Performance gegenüber ausgewählten x86-Plattformen unter eigenen Bedingungen.

> [!important]
> Eine Produktankündigung ist keine unabhängige Benchmarkbestätigung. Für Beschaffung sind verfügbare Systeme, SPEC-/Anwendungsresultate, Preis, Leistungsaufnahme, Software und Lieferstatus maßgeblich.

## Hardware- und Benchmark-Einordnung

### Relevante Daten

```text
ISA-Version und optionales Feature-Set
Mikroarchitektur/Kerntypen
Clusteraufbau und Cachehierarchie
Kerne/Threads
Takt und Dauer-Power-Limit
Speicherkanäle/-bandbreite/-latenz
SVE/SVE2/SME/NEON-Unterstützung
GPU/NPU/DSP/Medienblöcke
PCIe/CXL/I/O
Firmware, ACPI/Device Tree und OS-Support
```

### Repräsentative Hardwareentwicklung

| Beispiel | Jahr | grobe CPU-Struktur | Bedeutung |
|---|---:|---|---|
| ARM2 | 1987 | 1 einfacher 32-Bit-Kern | frühe effiziente RISC-CPU |
| ARM7TDMI | 1994 | 32-Bit, Thumb | Embedded-Massenverbreitung |
| Cortex-A9-SoC | 2010er | 1–4 Kerne | Smartphone-/Tablet-Multicore |
| Cortex-A53/A57-SoC | 2014 | 64-Bit big.LITTLE | AArch64-Mobilübergang |
| Apple M1 | 2020 | 4 Performance + 4 Effizienzkerne | Arm im Mac-Mainstream |
| Ampere Altra Max | 2021 | bis 128 physische Serverkerne | Cloud-Durchsatz ohne SMT |
| NVIDIA Grace | 2023 | 72 Arm-Kerne je CPU-Superchip-Komponente | HPC/AI-Host-CPU |
| C1-Cluster | 2025+ | heterogene Armv9.3-Kerne | SME2 und mobile AI-Plattform |
| Arm AGI CPU | 2026 angekündigt | Datacenter-Silizium | Arm tritt zusätzlich als Chipanbieter auf |

### Benchmarkwahl

| Frage | Messung |
|---|---|
| CPU-Pro-Thread | SPECspeed 2026, reale Build-/App-Latenz |
| Serverdurchsatz | SPECrate 2026, Web/DB/VM-Dichte |
| Smartphone | Dauerlast plus Temperatur, Geekbench nur als Teilbild |
| Notebook | reale App, Akku, Lüfter, Performance on battery |
| Cloud | Kosten pro Request/Build/Query, gleiche Region/Storage/Netzwerk |
| AI | End-to-End-Modell auf CPU/NPU/GPU, Latenz und Energie |

### Cross-ISA-Regeln

```text
gleiche Quellcode-/Anwendungsversion
gleicher Qualitätsmodus und Datensatz
native Builds auf beiden ISAs
gleichwertige Compilerflags
gleiche Threadzahl oder klarer Throughputvergleich
Power und Energie mitmessen
RAM/Storage/Netzwerk dokumentieren
Emulation separat ausweisen
```

> [!danger]
> Ein x86-Binary unter Übersetzung gegen eine native Arm-App zu testen misst auch den Übersetzer. Das kann praktisch relevant sein, ist aber kein reiner ISA-/CPU-Vergleich.

## Kompatibilität und Software

### Linux

Architektur anzeigen:

```bash
uname -m
getconf LONG_BIT
dpkg --print-architecture 2>/dev/null
rpm --eval '%{_arch}' 2>/dev/null
```

Typische Werte:

```text
aarch64  Kernel/RPM/Toolchains
arm64    Debian-/Container-/Cloud-Bezeichnung
armv7l   32-Bit-Armv7-Linux
```

Multiarch auf Debian/Ubuntu:

```bash
dpkg --print-foreign-architectures
sudo dpkg --add-architecture arm64
```

Nur verwenden, wenn Paketquellen und Ziel klar sind.

### Container

Manifest prüfen:

```bash
docker buildx imagetools inspect image:tag
podman manifest inspect image:tag
```

Multiarch-Build:

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag registry.example.org/app:1.0 \
  --push .
```

QEMU-Emulation hilft beim Build/Test, kann aber langsam sein und Hardware-/Timingfehler verdecken. Native CI-Runner ergänzen.

### Software-Fallstricke

- fest verdrahtete `amd64`-Download-URLs;
- native Python-/Ruby-/Node-Addons ohne arm64-Wheel/Binary;
- proprietäre Treiber oder Agenten;
- SIMD-Intrinsics nur für x86;
- `long`-/Pointer-/Endian-Annahmen;
- JITs und selbstmodifizierender Code;
- kleine Embedded-Systeme ohne MMU/FPU.

## Inventar und Diagnose

### Linux

```bash
lscpu
cat /proc/cpuinfo
uname -a
sudo dmidecode -t processor 2>/dev/null
sudo lshw -class processor 2>/dev/null
```

Featureflags:

```bash
lscpu | grep -E 'Architecture|Model name|Flags|Features'
grep -m1 '^Features' /proc/cpuinfo
```

Firmware/Device Tree:

```bash
cat /sys/firmware/devicetree/base/model 2>/dev/null; echo
find /sys/firmware/devicetree/base/cpus -maxdepth 2 -type f 2>/dev/null | head
```

Temperatur/Frequenz:

```bash
sensors 2>/dev/null
find /sys/devices/system/cpu/cpufreq -name scaling_cur_freq -print -exec cat {} \;
```

### macOS

```bash
uname -m
system_profiler SPHardwareDataType
sysctl -n machdep.cpu.brand_string 2>/dev/null
sysctl -a | grep -E 'hw.optional.arm|hw.perflevel' | head -40
```

Prozessarchitektur:

```bash
file /Applications/APP.app/Contents/MacOS/*
arch
```

### Windows PowerShell

```powershell
Get-CimInstance Win32_Processor |
  Select-Object Name,Architecture,AddressWidth,NumberOfCores,
                NumberOfLogicalProcessors

$env:PROCESSOR_ARCHITECTURE
Get-ComputerInfo | Select-Object CsSystemType,OsArchitecture
```

### Häufige Fehlerbilder

| Symptom | prüfen |
|---|---|
| `Exec format error` | Binary-/Containerarchitektur falsch |
| Paket nicht verfügbar | Repo unterstützt arm64/aarch64? |
| App startet nur emuliert | native Ausgabe/Plugin/Treiber fehlt |
| geringe Dauerleistung | Temperatur, Gehäuse, Power-Mode, Scheduler |
| Feature fehlt | ISA-Extension im Chip und OS aktiviert? |
| VM bootet nicht | UEFI/ACPI/Device Tree und Gastarchitektur |
| Container läuft lokal, nicht in CI | Multiarch-Manifest, native Abhängigkeiten |

## Schnellreferenz

```text
Arm-Ebenen:
ISA -> Core/Mikroarchitektur -> SoC -> Gerät/System -> Software

Nicht verwechseln:
Armv9 != Cortex/Neoverse/C1 != Snapdragon/M-Serie/Graviton

Vor Vergleich:
nativ vs. emuliert, Kerntypen, Power, RAM, Kühlung, Compiler, Workload

Vor Rollout:
Treiber + Security/VPN-Agenten + Plugins + Container + native CI prüfen
```

## Quellen

- [Arm Architecture](https://www.arm.com/architecture)
- [Arm CPU IP Portfolio](https://www.arm.com/products/silicon-ip-cpu)
- [35 years of Arm innovation](https://newsroom.arm.com/blog/arm-35-years-technology-innovation)
- [Arm C1 CPU cluster](https://newsroom.arm.com/blog/arm-c1-cpu-cluster-on-device-ai-performance)
- [Arm C1-Pro](https://www.arm.com/products/silicon-ip-cpu/c1-pro)
- [Arm C1-Nano](https://www.arm.com/products/silicon-ip-cpu/c1-nano)
- [Arm Lumex/C1 announcement](https://newsroom.arm.com/news/announcing-lumex-css-platform-ai-era)
- [Arm AGI CPU announcement, 2026](https://newsroom.arm.com/news/arm-agi-cpu-launch)
- [Neoverse N2](https://www.arm.com/products/silicon-ip-cpu/neoverse/neoverse-n2)
- [Cortex-A320 / Armv9 IoT](https://newsroom.arm.com/blog/introducing-arm-cortex-a320-cpu)

## Verwandte Notizen

- [[Prozessorhistorie-Intel-AMD-Arm-Cheatsheet]]
- [[Intel-Prozessorhistorie-Cheatsheet]]
- [[AMD-Prozessorhistorie-Cheatsheet]]
- [[CPU-Benchmarks-und-Vergleichbarkeit-Cheatsheet]]
- [[Linux-Netzwerk-Cheatsheet]]
- [[ls-Familie-und-Hardwareinventar-Cheatsheet]]
- [[dmesg-Cheatsheet]]
