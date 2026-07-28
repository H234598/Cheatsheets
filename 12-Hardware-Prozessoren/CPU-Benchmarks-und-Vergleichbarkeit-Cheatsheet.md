---
title: "CPU-Benchmarks und Vergleichbarkeit – Cheatsheet"
aliases: ["Prozessor Benchmarks", "CPU Benchmark Methodik", "SPEC Geekbench Phoronix Vergleich"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [hardware, cpu, benchmark, spec, geekbench, phoronix, performance, energie]
source: "https://www.spec.org/cpu2026/"
---

# CPU-Benchmarks und Vergleichbarkeit – Cheatsheet

> [!abstract] Zweck
> Praxisreferenz für belastbare CPU-Messungen: Latenz, Durchsatz, Single-/Multi-Thread, SPEC CPU 2026, Anwendungsbenchmarks, Energie, Statistik, Cross-ISA-Vergleiche, Linux-/Windows-Kommandos und reproduzierbare Ergebnisprotokolle.

> [!danger] Die wichtigste Regel
> Ein Score ist nur innerhalb **derselben Benchmarkversion, desselben Modus und einer dokumentierten Testklasse** sinnvoll vergleichbar. Ein höherer Wert in Benchmark A beweist keine höhere Leistung in Anwendung B.

## Inhalt

- [[#Was soll gemessen werden?]]
- [[#Benchmarkarten]]
- [[#SPEC CPU 2026]]
- [[#SPEC CPU 2017 und historische Reihen]]
- [[#Alltags- und Anwendungsbenchmarks]]
- [[#Cross-ISA-Vergleiche]]
- [[#Testsystem vorbereiten]]
- [[#Linux-Werkzeuge]]
- [[#Windows-Werkzeuge]]
- [[#Energie und Effizienz]]
- [[#Statistik und Wiederholungen]]
- [[#Benchmark-Snapshot 2026]]
- [[#Reproduzierbares Testprotokoll]]
- [[#Fehlinterpretationen]]
- [[#Schnellreferenz]]

## Was soll gemessen werden?

Vor dem Tool die Fragestellung festlegen.

| Ziel | geeignete Kennzahl |
|---|---|
| interaktive Reaktionszeit | Zeit pro Aufgabe, p50/p95-Latenz |
| einzelne rechenintensive Aufgabe | Single-Thread/geringe Threadzahl |
| viele unabhängige Jobs | Throughput pro Zeit |
| Serverkonsolidierung | Requests/VMs/JOBS pro Sockel oder Watt |
| Software-Build | reale Clean-/Incremental-Build-Zeit |
| Rendering | Samples/Minute oder Zeit pro Szene |
| Video | FPS bei identischem Codec/Qualitätsmodus |
| Datenbank | Transaktionen/s plus Latenzverteilung |
| HPC | Solverzeit, Bandbreite, Skalierung, Energie |
| Notebook | Leistung on battery, Laufzeit, Lautstärke |
| Cloud | Arbeit pro Euro und pro vCPU-Stunde |
| AI | End-to-End-Latenz/Throughput mit realem Modell |

Formeln:

```text
Latenz-Leistung:   niedrige Zeit ist besser
Durchsatz:         erledigte Arbeit / Zeit
Speedup:           Zeit_alt / Zeit_neu
Effizienz:         Arbeit / Energie
Skalierung:        Throughput_n_Threads / Throughput_1_Thread
Kostenleistung:    Arbeit / Gesamtkosten
```

> [!important]
> „Single Core“ und „Single Thread“ sind nicht immer identisch. SMT, Hybridkerne, Scheduler und Boost können die Ausführung beeinflussen.

## Benchmarkarten

### Mikrobenchmark

Misst einen kleinen Mechanismus:

- Integer-/Floating-Point-Operationen;
- Cache-/Speicherlatenz;
- Bandbreite;
- Sprungvorhersage;
- Systemcall;
- Lock/Atomics;
- SIMD.

Vorteil: gezielte Diagnose. Nachteil: leicht zu überinterpretieren oder compileroptimiert wegzuoptimieren.

### Synthetischer Benchmark

Erzeugt eine definierte Last, etwa `sysbench cpu`. Gut für schnelle Regressionen, aber nicht automatisch repräsentativ.

### Anwendungskern

Verwendet reale oder daraus abgeleitete Softwareteile. SPEC CPU, Blender, Kompression und Compilerbenchmarks liegen näher an realen Workloads.

### End-to-End-Workload

Misst den tatsächlichen Geschäfts-/Nutzerablauf:

```text
Quellbaum auschecken -> kompilieren -> testen -> Artefakt erzeugen
API-Request -> Datenbank -> Template -> Antwort
Video importieren -> filtern -> kodieren
```

Dies ist meist entscheidungsrelevant, aber schwieriger zu standardisieren.

## SPEC CPU 2026

SPEC CPU 2026 wurde am **5. Mai 2026** veröffentlicht und ist die aktuelle SPEC-CPU-Suite. Sie misst rechenintensive Leistung des Gesamtsystems aus Prozessor, Speicherhierarchie und Compiler.

### Vier Hauptsuiten

| Suite | Ziel | Kennzahl |
|---|---|---|
| SPECspeed 2026 Integer | Zeit einzelner Integer-Aufgaben | höherer Ratio-Score besser |
| SPECspeed 2026 Floating Point | Zeit einzelner FP-Aufgaben | höher besser |
| SPECrate 2026 Integer | Integer-Durchsatz mit mehreren Kopien | höher besser |
| SPECrate 2026 Floating Point | FP-Durchsatz | höher besser |

Die Suite umfasst laut SPEC **52 Benchmarks**. `SPECspeed` und `SPECrate` sind nicht austauschbar.

### Base und Peak

| Modus | Bedeutung |
|---|---|
| `base` | einheitlichere, weniger aggressive Compilerregeln |
| `peak` | stärker workloadbezogenes Tuning innerhalb der Regeln |

Für schnellen, fairen Überblick zuerst **base** vergleichen. Peak zeigt zusätzlich Optimierungspotenzial, aber auch Compiler-/Tuningkompetenz.

### Ergebnis lesen

Ein gültiger SPEC-Eintrag dokumentiert unter anderem:

- Systemmodell und CPU-SKU;
- Sockel, Kerne, Threads und Kopien;
- RAM-Kapazität und -Konfiguration;
- Compiler und Flags;
- BIOS-/Firmwareeinstellungen;
- Betriebssystem;
- Base/Peak und Speed/Rate;
- Validitäts- und Veröffentlichungshinweise.

> [!warning]
> Ein SPECrate-Ergebnis eines Dual-Socket-Servers darf nicht als Single-Thread-Leistung interpretiert werden. Umgekehrt sagt SPECspeed wenig über maximale VM-Dichte.

### SPEC CPU 2026 und Energie

Die Suite besitzt optionale Energiemetriken. Energie pro Aufgabe ist oft wichtiger als bloße Spitzenleistung:

```text
System A: 100 Einheiten/s bei 500 W = 0,20 Einheiten/J
System B:  85 Einheiten/s bei 300 W = 0,283 Einheiten/J
```

System B ist langsamer, aber effizienter.

### Lizenz und Fair Use

SPEC CPU ist lizenzpflichtig. Veröffentlichungen müssen Lizenz-, Run-Rule- und Fair-Use-Regeln einhalten. Quellcode/Inputs nicht einfach aus einer lizenzierten Installation weitergeben.

## SPEC CPU 2017 und historische Reihen

SPEC CPU 2017 besitzt 43 Benchmarks in vier Suiten. SPEC kündigte für 2026 den Übergang zu CPU 2026 an:

- CPU 2026 ist seit Mai 2026 aktuell;
- neue 2017-Veröffentlichungen werden im Übergangszeitraum eingeschränkt;
- CPU 2017 soll im November 2026 retired werden;
- CPU-2017- und CPU-2026-Scores sind **nicht direkt konvertierbar**.

> [!danger]
> Nicht einen 2017-Ratio-Wert mit einem 2026-Ratio-Wert in dieselbe Rangliste schreiben. Referenzmaschinen, Workloads und Regeln unterscheiden sich.

Historische Suites:

```text
SPEC CPU89 -> CPU92 -> CPU95 -> CPU2000 -> CPU2006 -> CPU2017 -> CPU2026
```

Jede Suite bildet eine eigene Messskala.

## Alltags- und Anwendungsbenchmarks

### Geekbench

Geekbench ist einfach und plattformübergreifend. Es enthält mehrere CPU-/Speicherworkloads und liefert Single-/Multi-Core-Scores.

Sinnvoll für:

- schnellen Gerätevergleich;
- grobe Cross-Platform-Orientierung;
- Regressionen auf demselben System.

Grenzen:

- Versionswechsel verändern Workloads und Skala;
- kurzer Lauf kann thermische Dauerleistung übersehen;
- hochintegrierte Plattformen und OS-Bibliotheken wirken mit;
- Crowdsourcing-Ergebnisse enthalten unterschiedliche RAM-/Power-/Firmwarezustände.

Nur vergleichen:

```text
Geekbench 6.x mit Geekbench 6.x
identischer Architekturmodus: native vs. native
ähnliche Geräte-/Powerklasse
Median mehrerer Läufe
```

### Cinebench

Nutzt die Cinema-4D-Renderingengine. Gut für:

- Single-/Multi-Core-Rendering;
- thermische Schleifen;
- schnelle Desktop-/Notebooktests.

Nicht gleichbedeutend mit Gaming, Compiler oder Datenbank.

### Blender Benchmark

Reale Render-Szenen, CPU- und GPU-Modi klar trennen. Version, Szene, Backend und Samples dokumentieren.

### 7-Zip

Kompression/Dekompression reagieren auf Integerleistung, Cache und Speicher. Dictionary- und Threadkonfiguration dokumentieren.

```bash
7z b
7z b -mmt1
7z b -mmt"$(nproc)"
```

### Compiler-/Build-Benchmark

Besonders wertvoll für Entwickler:

```bash
/usr/bin/time -v make -j1 clean all
/usr/bin/time -v make -j"$(nproc)" clean all
```

Besser in getrennten Worktrees/Build-Verzeichnissen und mit kontrolliertem Cache.

### Video-Encoding

```bash
ffmpeg -benchmark -i input.mkv \
  -c:v libx265 -preset medium -crf 22 \
  -an -f null -
```

Konstant halten:

- FFmpeg-/Codecversion;
- Input;
- Preset und Qualitätsziel;
- Threadzahl;
- Hardwarebeschleunigung aus oder klar separat.

### Datenbank/Web

Nicht nur maximalen Durchsatz messen:

```text
Requests/s + p50/p95/p99 + Fehlerquote + CPU-Watt + RAM
```

## Cross-ISA-Vergleiche

Intel/AMD-x86-64 und Arm64 fair vergleichen:

1. native Anwendung auf beiden Plattformen;
2. gleiche Anwendungsversion und Eingabedaten;
3. gleiche Ergebnisqualität;
4. vergleichbare Compileroptimierung;
5. Threadzahl und Throughputmodus offenlegen;
6. Speicher-/Storage-/Netzwerkengpässe dokumentieren;
7. reale Leistungsaufnahme oder Cloudkosten erfassen;
8. Emulation als eigenen Test ausweisen.

### Compilerflags

```text
-portabel:  -O2 oder dokumentierter Baseline-Modus
-nativ:     -O3 -march=native  (nur wenn auf beiden Systemen analog)
-ISA-spezifisch: getrennt als optimierter Peak-Test
```

> [!warning]
> `-march=native` kann unterschiedliche Befehlssatzerweiterungen aktivieren. Das ist für „bestmögliche Plattformleistung“ legitim, aber kein neutraler ISA-Basistest.

### Container

Vor dem Vergleich:

```bash
uname -m
docker image inspect IMAGE --format '{{.Architecture}}'
docker buildx imagetools inspect IMAGE:TAG
```

QEMU-Emulation nicht als native CPU-Leistung ausgeben.

## Testsystem vorbereiten

### Hardware dokumentieren

```bash
lscpu
sudo dmidecode -t bios -t processor -t memory
lsblk -o NAME,MODEL,SIZE,ROTA,TRAN
lspci -nn
```

### Softwarezustand

```bash
uname -a
cat /etc/os-release
gcc --version
clang --version
ldd --version | head -1
```

### Firmware/Microcode

```bash
dmesg | grep -i microcode
sudo fwupdmgr get-devices 2>/dev/null
```

### Last und Temperatur

```bash
uptime
ps -eo pid,comm,%cpu,%mem --sort=-%cpu | head
sensors
```

### Powerprofile

```bash
powerprofilesctl get 2>/dev/null
cpupower frequency-info 2>/dev/null
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null
```

Testprofile nicht mitten zwischen Runs ändern.

### Vor jedem Lauf

- AC-Netzteil und Akku-/Ladezustand festhalten;
- Lüfter-/Kühlprofil festhalten;
- Displayhelligkeit bei Akkutests konstant;
- Updates, Indexer und Backups pausieren;
- Raumtemperatur grob dokumentieren;
- mindestens einen Warm-up-Lauf;
- danach mehrere Messläufe;
- Throttling überwachen;
- Rohdaten speichern.

> [!danger]
> Nicht Sicherheitsdienste, EDR, Mitigations oder Firmware deaktivieren, nur um einen schönen Score zu erhalten, wenn das Produkt später mit diesen Schutzmaßnahmen betrieben wird.

## Linux-Werkzeuge

### `hyperfine`

```bash
hyperfine --warmup 3 --runs 10 \
  'command-a' \
  'command-b'
```

Export:

```bash
hyperfine --warmup 3 --runs 20 \
  --export-json result.json \
  --export-markdown result.md \
  'python3 workload.py'
```

Mit Vorbereitung:

```bash
hyperfine \
  --prepare 'rm -rf build && cmake -S . -B build' \
  --runs 5 \
  'cmake --build build -j1'
```

### `time`

```bash
/usr/bin/time -v ./workload
```

Wichtige Werte:

- elapsed/wall time;
- user/system time;
- maximum resident set size;
- page faults;
- context switches.

### `perf stat`

```bash
perf stat -r 5 -- ./workload
```

Ausgewählte Ereignisse:

```bash
perf stat -r 5 \
  -e cycles,instructions,branches,branch-misses,cache-misses \
  -- ./workload
```

IPC grob:

```text
instructions / cycles
```

Hardwarecounter sind mikroarchitektur- und Berechtigungsabhängig. `perf list` und Kernel-Restriktionen prüfen.

### `sysbench`

```bash
sysbench cpu --threads=1 --time=30 run
sysbench cpu --threads="$(nproc)" --time=30 run
sysbench memory --threads=1 --time=30 run
```

Für Regressionen gut; keine allgemeine CPU-Rangliste.

### `stress-ng`

```bash
stress-ng --cpu 1 --cpu-method matrixprod \
  --timeout 60s --metrics-brief

stress-ng --cpu 0 --timeout 10m --metrics-brief
```

Primär Stresstest/Diagnose. Nicht jede Bogo-Op ist zwischen Versionen/Architekturen vergleichbar.

### Phoronix Test Suite

```bash
phoronix-test-suite system-info
phoronix-test-suite list-recommended-tests
phoronix-test-suite info pts/build-linux-kernel
phoronix-test-suite benchmark pts/build-linux-kernel
```

Nichtinteraktiv:

```bash
phoronix-test-suite batch-setup
phoronix-test-suite batch-benchmark pts/compress-7zip
```

PTS dokumentiert Hardware/Software und aggregiert Wiederholungen, dennoch Testprofilversion und Optionen fixieren.

### CPU-Pinning

```bash
taskset -c 2 ./workload
numactl --cpunodebind=0 --membind=0 ./workload
```

Nur mit dokumentierter Topologie. Pinning kann realistische Schedulerwirkung entfernen.

## Windows-Werkzeuge

### Systeminventar

```powershell
Get-CimInstance Win32_Processor |
  Select-Object Name,Manufacturer,NumberOfCores,
                NumberOfLogicalProcessors,MaxClockSpeed

Get-CimInstance Win32_PhysicalMemory |
  Select-Object Manufacturer,PartNumber,Capacity,Speed,ConfiguredClockSpeed

Get-ComputerInfo | Select-Object OsName,OsVersion,CsSystemType
```

### Powerplan

```powershell
powercfg /getactivescheme
powercfg /list
```

Den produktiven Plan verwenden oder Änderung dokumentieren.

### Laufzeit

```powershell
Measure-Command { .\workload.exe }
```

Mehrere Läufe:

```powershell
1..10 | ForEach-Object {
  [pscustomobject]@{
    Run = $_
    Seconds = (Measure-Command { .\workload.exe }).TotalSeconds
  }
} | Export-Csv .\runs.csv -NoTypeInformation
```

### Windows System Assessment Tool

```powershell
winsat cpuformal
winsat mem
```

Für lokale Diagnose; nicht als moderne universelle Kaufbenchmark behandeln.

### Prozessaffinität

```powershell
$p = Start-Process .\workload.exe -PassThru
$p.ProcessorAffinity = 0x4
$p.WaitForExit()
```

Bitmaske und Prozessorgruppen bei sehr vielen logischen CPUs beachten.

## Energie und Effizienz

### Linux RAPL/Turbostat

```bash
sudo turbostat --Summary --interval 1
sudo turbostat --quiet --show Busy%,Bzy_MHz,PkgWatt,CorWatt,RAMWatt \
  -- ./workload
```

RAPL-Pfade:

```bash
find /sys/class/powercap -maxdepth 3 -type f -name energy_uj -print
```

Unterstützung variiert je Plattform. RAPL ist modellbasierte/integrierte Messung und kein Ersatz für eine kalibrierte Steckdosen-/DC-Messung.

### IPMI/BMC

```bash
ipmitool sensor | grep -i -E 'power|watt'
ipmitool dcmi power reading
```

BMC-Samplingrate und Netzteilverluste beachten.

### Externes Messgerät

Für Gesamtsystem:

```text
Leerlaufleistung
Durchschnitt während Benchmark
Spitzenleistung
Energie Wh pro vollständiger Aufgabe
```

Effizienz:

```text
Joule pro Build/Render/Query
oder
Aufgaben pro kWh
```

### Notebook

Nicht nur CPU-Watt:

- Display;
- RAM;
- SSD;
- Funk;
- Lüfter;
- Netzteilverluste;
- Akkualterung.

Akkuentladung über einen definierten Ablauf ist oft praxisnäher.

## Statistik und Wiederholungen

### Minimum

```text
1 Warm-up + 5 Messläufe
```

Besser bei variablen Workloads:

```text
3 Warm-ups + 10–30 Messläufe
```

Ausgeben:

- Anzahl `n`;
- Median;
- arithmetisches Mittel;
- Standardabweichung;
- Minimum/Maximum;
- p95 bei Latenzen;
- Rohwerte.

### Warum Median?

Der Median ist robuster gegen einzelne Ausreißer durch Scheduler, Updateprozess oder Cacheeffekt. Mittelwert nicht verwerfen, sondern zusammen mit Streuung zeigen.

### Python-Auswertung

```python
from statistics import mean, median, stdev

values = [12.4, 12.1, 12.3, 14.8, 12.2]
print({
    "n": len(values),
    "mean": mean(values),
    "median": median(values),
    "stdev": stdev(values),
    "min": min(values),
    "max": max(values),
})
```

### Signifikanz ist nicht Relevanz

Ein statistisch messbarer Unterschied von 1 % kann praktisch irrelevant sein, während 5 % bei einem 24/7-Rechenzentrum erhebliche Kosten sparen kann. Vorab eine relevante Schwelle definieren.

## Benchmark-Snapshot 2026

Die folgenden Werte sind **gerundete öffentliche PassMark-Momentaufnahmen vom 17. Juli 2026**, keine neutrale oder dauerhafte Rangliste. Stichprobe, Firmware und Datenbankstand ändern sich.

| CPU | Klasse | Kerne/Threads | CPU Mark ca. | Single Thread ca. |
|---|---|---:|---:|---:|
| AMD Ryzen 9 9950X3D | Desktop | 16/32 | 70.100 | 4.740 |
| Intel Core Ultra 9 285K | Desktop | 24 Hybridkerne | 67.300 | 5.090 |
| Intel Core i9-14900K | Desktop | 24 Hybridkerne | 58.300 | 4.690 |
| Apple M5 Max 18-Core | Notebook-SoC | 18 CPU-Kerne | 57.700 | 5.940 |
| Apple M5 10-Core | Notebook-SoC | 10 CPU-Kerne | 26.800 | 5.760 |
| AMD EPYC 9654 | Server | 96/192 | 119.300 | 2.900 |
| Ampere 192-Core | Server/Arm | 192/192 | 57.400 | 1.230 |

> [!warning]
> Server- und Notebookwerte in derselben Datenbank bedeuten nicht dieselbe Leistungs-, Energie- oder Preisdimension. Der EPYC-Score misst massiv parallele Ressourcen; Apple-SoCs arbeiten in einem anderen System- und Powerrahmen.

### Historische Größenordnung derselben Datenbankfamilie

| CPU | Jahr grob | CPU Mark ca. | Single ca. |
|---|---:|---:|---:|
| Pentium 4 3,4 GHz | 2004 | 300 | 650 |
| Core 2 Duo E6600 | 2006 | 1.535 | 923 |
| Core i7-2600K | 2011 | 5.479 | 1.740 |
| Ryzen 5 3600 | 2019 | 17.661 | 2.558 |
| Apple M1 | 2020 | 14.125 | 3.674 |
| Ryzen 7 7800X3D | 2023 | 34.277 | 3.760 |

Die Tabelle illustriert Größenordnungen. Benchmarkdatenbanken können historische Werte neu normalisieren; für wissenschaftliche Langzeitreihen Rohdaten und Benchmarkversion archivieren.

## Reproduzierbares Testprotokoll

### Metadatenvorlage

```yaml
benchmark:
  name: "build-linux-kernel"
  version: "Profil/Commit exakt"
  date: "2026-07-17"
  metric: "seconds"
  direction: "lower-is-better"
workload:
  source_commit: "..."
  command: "make -j32"
  input_hash: "sha256:..."
system:
  model: "..."
  cpu: "..."
  sockets: 1
  cores: 16
  threads: 32
  ram: "64 GiB DDR5-6000"
  firmware: "..."
  microcode: "..."
  cooling: "..."
software:
  os: "..."
  kernel: "..."
  compiler: "..."
  flags: "..."
controls:
  power_profile: "performance"
  ac_power: true
  room_temp_c: 22
  warmups: 3
  runs: 10
results:
  raw: ["..."]
  median: "..."
  stdev: "..."
  energy_wh: "..."
notes: "..."
```

### Erfassungsskript Linux

```bash
#!/usr/bin/env bash
set -Eeuo pipefail

OUT="benchmark-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$OUT"

uname -a > "$OUT/uname.txt"
lscpu > "$OUT/lscpu.txt"
cat /etc/os-release > "$OUT/os-release.txt"
(gcc --version || true) > "$OUT/compiler.txt"
(sensors || true) > "$OUT/sensors-before.txt"

hyperfine --warmup 3 --runs 10 \
  --export-json "$OUT/result.json" \
  --export-markdown "$OUT/result.md" \
  './workload'

(sensors || true) > "$OUT/sensors-after.txt"
sha256sum "$OUT"/* > "$OUT/SHA256SUMS"
```

### Vergleichstabelle

| Feld | System A | System B |
|---|---|---|
| Medianzeit | | |
| p95/Max | | |
| Energie/Aufgabe | | |
| Spitzenleistung | | |
| RAM | | |
| Powerprofil | | |
| Compiler/Flags | | |
| Temperatur/Throttling | | |
| Kosten | | |

## Fehlinterpretationen

### „Doppelt so viele Kerne = doppelt so schnell“

Nur bei gut parallelisierbarer Arbeit ohne Speicher-/I/O-/Synchronisationslimit. Amdahls Gesetz begrenzt den Speedup.

```text
Speedup <= 1 / (serieller_Anteil + paralleler_Anteil / Kerne)
```

### „Höherer GHz-Wert gewinnt“

Falsch ohne IPC, Power, Cache und Workload.

### „Ein synthetischer Score ist objektiv“

Der Lauf kann reproduzierbar sein, die Auswahl/Gewichtung ist trotzdem eine Modellentscheidung.

### „Hersteller A ist immer effizienter“

Effizienz gilt pro Workload und System. Idle, Teillast und Vollast können andere Sieger haben.

### „NPU-TOPS sind CPU-Leistung“

NPU, GPU und CPU sind getrennte Pfade. TOPS hängt von Datentyp, Sparsity und Software ab.

### „Cloud-vCPU ist ein physischer Kern“

Je Anbieter/Instanz kann eine vCPU ein Hardwarethread, ein Anteil oder ein dedizierter Kern sein. Hostgeneration und Noisy Neighbors beachten.

### „Best Score ist repräsentativ“

Bestwert ist oft Ausreißer. Median und Streuung berichten.

## Schnellreferenz

```text
1. Frage definieren: Latenz, Durchsatz, Energie oder Kosten?
2. realen Workload vor synthetischem Score priorisieren
3. Version, Daten, Qualität, Threads und Compiler fixieren
4. BIOS/Microcode/RAM/Power/Kühlung dokumentieren
5. Warm-up + mehrere Läufe
6. Median + Streuung + Rohdaten
7. native ISA gegen native ISA
8. Energie und Preis pro erledigter Arbeit
9. keine Scores zwischen Benchmarkgenerationen mischen
10. Ergebnis mit Entscheidungsschwelle verbinden
```

## Quellen

- [SPEC CPU 2026](https://www.spec.org/cpu2026/)
- [SPEC CPU 2026 Overview](https://www.spec.org/cpu2026/docs/overview.html)
- [SPEC CPU 2026 Result Fields](https://www.spec.org/cpu2026/Docs/result-fields.html)
- [SPEC CPU 2026 Run Rules](https://www.spec.org/cpu2026/docs/runrules.html)
- [SPEC CPU 2017 and retirement plan](https://www.spec.org/cpu2017/)
- [Geekbench 6 internals](https://www.geekbench.com/doc/geekbench6-benchmark-internals.pdf)
- [Phoronix Test Suite](https://www.phoronix-test-suite.com/)
- [Phoronix Test Suite documentation](https://github.com/phoronix-test-suite/phoronix-test-suite/blob/master/documentation/phoronix-test-suite.md)
- [hyperfine](https://github.com/sharkdp/hyperfine)
- [Linux perf](https://perf.wiki.kernel.org/)

## Verwandte Notizen

- [[Prozessorhistorie-Intel-AMD-Arm-Cheatsheet]]
- [[Intel-Prozessorhistorie-Cheatsheet]]
- [[AMD-Prozessorhistorie-Cheatsheet]]
- [[Arm-Prozessorhistorie-Cheatsheet]]
- [[ls-Familie-und-Hardwareinventar-Cheatsheet]]
- [[dmesg-Cheatsheet]]
- [[Make-und-Source-Builds-Cheatsheet]]
