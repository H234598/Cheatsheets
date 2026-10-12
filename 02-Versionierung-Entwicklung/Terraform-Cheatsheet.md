---
title: "Terraform – Cheatsheet"
aliases:
  - "Terraform"
  - "HashiCorp Terraform"
  - "Terraform CLI"
tags:
  - terraform
  - hashicorp
  - infrastructure-as-code
  - entwicklung
  - automatisierung
  - hcl
  - state
  - devops
type: reference
status: fertig
date: '2026-10-12'
created: '2026-10-12'
modified: '2026-10-12'
updates:
  - date: '2026-10-12'
    change: "Eigenständige Terraform-Referenz mit lokalem Übungsprojekt, CLI-Abläufen, HCL, Versionierung, State und offiziellen Quellen erstellt."
source: "https://developer.hashicorp.com/terraform"
---

# Terraform – Cheatsheet

> [!abstract] Zweck
> HashiCorp Terraform praktisch einsetzen: Konfiguration schreiben, Änderungen verstehen, einen geprüften Plan anwenden und den zugehörigen State zuverlässig verwalten. Der vollständige Einstieg verwendet ausschließlich eine lokale `terraform_data`-Ressource und benötigt kein Cloudkonto.

> [!info] Stand und Geltungsbereich
> Geprüfter Dokumentationsstand: **12. Oktober 2026**. Aktuelle stabile Ausgabe: **Terraform 1.16.5**. Die bereits angebotene **1.17.0-rc1** ist eine Vorabversion. Die Beispiele beziehen sich auf Terraform 1.16.x; ältere Mindestversionen werden bei besonderen Funktionen ausdrücklich genannt. Provider haben eigene Versionen und Kompatibilitätsgrenzen. [Offizielle Installation](https://developer.hashicorp.com/terraform/install), [Releaseverzeichnis](https://releases.hashicorp.com/terraform/), [Release 1.16.5](https://github.com/hashicorp/terraform/releases/tag/v1.16.5).

Terraform beschreibt einen gewünschten Zustand. Provider verbinden diese Beschreibung mit den APIs der Zielsysteme; der State ordnet Terraform-Adressen den verwalteten Objekten zu. Beim Planen vergleicht Terraform Konfiguration, gespeicherte Zuordnungen und aktuelle Informationen der Provider. Die Reihenfolge von Änderungen ergibt sich aus Abhängigkeiten. **HCP Terraform** ergänzt unter anderem entfernte Ausführung und Zusammenarbeit; für die lokale CLI-Übung ist dieser Dienst nicht erforderlich. [Terraform-Überblick](https://developer.hashicorp.com/terraform/intro), [CLI-Arbeitsablauf](https://developer.hashicorp.com/terraform/cli/run).

## Inhaltsverzeichnis

- [[#Schnellreferenz]]
- [[#Lokaler Einstieg ohne Cloudkonto]]
- [[#Pläne prüfen und Exitcodes auswerten]]
- [[#Installation und Versionsprüfung]]
- [[#Dateien, HCL und Werte]]
- [[#Ausdrücke, Funktionen und mehrere Instanzen]]
- [[#CLI, Provider und Module versionieren]]
- [[#State lesen und Backends verstehen]]
- [[#Workspaces und Umgebungsgrenzen]]
- [[#Bestehende Ressourcen importieren]]
- [[#Ressourcen umbenennen oder aus der Verwaltung entlassen]]
- [[#Drift erkennen und State gezielt abgleichen]]
- [[#Lifecycle und verbindliche Bedingungen]]
- [[#Geheimnisse und kurzlebige Werte]]
- [[#Git-Dateien und CI-Ablauf]]
- [[#Native Tests für das lokale Grundbeispiel]]
- [[#Fehlerbilder gezielt eingrenzen]]
- [[#Offizielle Referenzen zum Weiterarbeiten]]
- [[#Verwandte Cheatsheets]]

## Schnellreferenz

Die Befehle wirken im aktuellen Root-Modul. Ein anderes Verzeichnis wird mit der **globalen Option vor dem Unterbefehl** gewählt, beispielsweise `terraform -chdir=environments/dev plan`.

| Befehl | Zweck und Wirkung |
|---|---|
| `terraform version` | Tatsächliche CLI-Version anzeigen |
| `terraform init` | Backend initialisieren sowie benötigte Module und Provider installieren |
| `terraform fmt -recursive` | Konfigurationsdateien einschließlich Unterverzeichnissen formatieren; verändert Dateien |
| `terraform fmt -check -diff -recursive` | Formatierung ohne Schreiben prüfen und Abweichungen anzeigen |
| `terraform validate` | Syntax und interne Konsistenz der initialisierten Konfiguration prüfen |
| `terraform plan` | Vorgesehene Änderungen anzeigen; noch keine geplanten Ressourcenänderungen anwenden |
| `terraform plan -out=review.tfplan` | Einen später ausführbaren Plan speichern |
| `terraform show review.tfplan` | Gespeicherten Plan lesbar anzeigen |
| `terraform apply review.tfplan` | Genau den gespeicherten Plan ausführen; **ohne erneute Bestätigungsfrage** |
| `terraform output` | Outputs des Root-Moduls aus dem State lesen |
| `terraform state list` | Im aktuellen State geführte Ressourcenadressen anzeigen |
| `terraform workspace show` | Aktuellen CLI-Workspace anzeigen |
| `terraform providers` | Providerabhängigkeiten der Konfiguration anzeigen |
| `terraform console` | Ausdrücke und Funktionen interaktiv untersuchen |
| `terraform test` | Testdateien ausführen; je nach Testdefinition sind echte Apply-Operationen möglich |
| `terraform plan -destroy` | Vollständige Zerstörung der verwalteten Objekte planen |
| `terraform destroy` | Zerstörungsplan erzeugen und nach Bestätigung ausführen |

`validate` ersetzt keinen Plan mit den tatsächlich verwendeten Variablen und Zugangsdaten. `plan` kann Provider, Datenquellen und das Backend kontaktieren. Auch erfolgreiches Planen garantiert nicht, dass ein späteres Apply gegen unveränderte externe Bedingungen läuft. [CLI-Befehle und `-chdir`](https://developer.hashicorp.com/terraform/cli/commands), [Validierung](https://developer.hashicorp.com/terraform/cli/commands/validate), [Plan](https://developer.hashicorp.com/terraform/cli/commands/plan).

## Lokaler Einstieg ohne Cloudkonto

### Vollständige main.tf

Ein **neues, leeres Verzeichnis** namens `terraform-lab` anlegen, hineinwechseln und dort den folgenden Inhalt als `main.tf` speichern. Das Beispiel enthält keine Provisioner und keine externen Provider. Es verwaltet ausschließlich Übungswerte im lokalen Terraform-State. `terraform_data` ist seit Terraform 1.4 eingebaut; die Versionsgrenze hier hält die Übung bewusst auf dem dokumentierten 1.16-Zweig. [Eingebaute Ressource](https://developer.hashicorp.com/terraform/language/resources/terraform-data).

```hcl
terraform {
  required_version = "~> 1.16.0"
}

variable "project" {
  description = "Projektname für die lokale Terraform-Übung."
  type        = string
  default     = "cheatsheets"
  nullable    = false

  validation {
    condition     = length(trimspace(var.project)) > 0
    error_message = "project darf nicht leer sein."
  }
}

variable "environment" {
  description = "Übungsumgebung: lab oder test."
  type        = string
  default     = "lab"
  nullable    = false

  validation {
    condition     = contains(["lab", "test"], var.environment)
    error_message = "environment muss lab oder test sein."
  }
}

locals {
  name = "${var.project}-${var.environment}"
}

resource "terraform_data" "demo" {
  input = {
    name        = local.name
    environment = var.environment
  }
}

output "name" {
  description = "Name des im Terraform-State gespeicherten Übungsobjekts."
  value       = terraform_data.demo.output.name
}
```

Die Adresse `terraform_data.demo` setzt sich aus Ressourcentyp und lokalem Namen zusammen. `input` wird im State gespeichert, `output` stellt den übernommenen Wert bereit. Das Root-Output `name` ist eine eigene Schnittstelle für Benutzer und nachgelagerte Werkzeuge; sein erwarteter Wert ist `cheatsheets-lab`.

### Initialisieren, prüfen und planen

Im Verzeichnis mit dieser `main.tf`:

```bash
terraform version
terraform init -input=false
terraform fmt -check -diff
terraform validate
terraform plan -out=lab.tfplan
terraform show lab.tfplan
```

Die erste Planung soll genau eine neue `terraform_data.demo` zeigen. `terraform init` verwendet dafür den eingebauten Provider `terraform.io/builtin/terraform`; ein externes Providerpaket ist nicht erforderlich. Bei dieser Konfiguration gibt es deshalb keine externe Provider-Version zu sperren. In Projekten mit externen Providern entsteht dagegen die später erläuterte `.terraform.lock.hcl`. [Provideranforderungen und eingebauter Provider](https://developer.hashicorp.com/terraform/language/providers/requirements).

### Geprüften Plan anwenden und Ergebnis kontrollieren

> [!warning] Die Plandatei ist die Freigabe
> `terraform apply lab.tfplan` fragt **nicht noch einmal nach `yes`**. Erst den gespeicherten Plan lesen, dann diesen Befehl ausführen. Dieselbe Regel gilt für gespeicherte Löschpläne. Ohne Plandatei erzeugt `terraform apply` einen neuen Plan und fordert standardmäßig eine Bestätigung an. [Apply-Modi](https://developer.hashicorp.com/terraform/cli/commands/apply).

```bash
terraform apply lab.tfplan
terraform output -raw name
terraform state list
terraform plan -detailed-exitcode
```

Erwartet werden das Output `cheatsheets-lab`, die Adresse `terraform_data.demo` und anschließend ein Plan ohne Änderungen. `terraform output -raw` fügt keinen abschließenden Zeilenumbruch hinzu. Das Beispiel erzeugt lokale Arbeits- und State-Dateien; diese nicht in eine andere Terraform-Konfiguration übernehmen.

**Eine Änderung ausprobieren:** Als `terraform.tfvars` im gleichen Verzeichnis speichern:

```hcl
environment = "test"
```

Danach mit `terraform plan -out=change.tfplan` einen neuen Plan erstellen, mit `terraform show change.tfplan` prüfen und mit `terraform apply change.tfplan` anwenden. Der Name wird `cheatsheets-test`. Die Variablendatei bleibt beim nächsten Plan wirksam. Ein nur einmal mit `-var` übergebener Wert müsste dagegen erneut übergeben werden. `environment = "prod"` wird von der bewusst engen Übungsvalidierung zurückgewiesen.

### Übungszustand aufräumen

```bash
terraform plan -destroy -out=destroy.tfplan
terraform show destroy.tfplan
terraform apply destroy.tfplan
terraform state list
```

Der letzte Befehl soll keine Ressourcenadresse mehr ausgeben. Konfigurationsdateien, Plandateien und gegebenenfalls State-Backups bleiben auf der Festplatte. Die Befehle ausschließlich im Übungsprojekt ausführen: In einem echten Projekt richtet sich der Löschplan gegen die dort verwalteten Objekte. `terraform destroy` ist die Kurzform von `terraform apply -destroy`, akzeptiert jedoch keine gespeicherte Plandatei. [Destroy-Referenz](https://developer.hashicorp.com/terraform/cli/commands/destroy).

## Pläne prüfen und Exitcodes auswerten

Ein Plan ohne `-out` dient der Vorschau. Für einen späteren Apply muss erneut geplant werden. Mit `-out` entsteht eine Binärdatei, die auch Konfiguration, Eingabewerte und weitere Planinformationen enthalten kann. **Gespeicherte Pläne als vertrauliche Artefakte behandeln**, selbst wenn die Terminalausgabe Werte maskiert. `terraform show -json review.tfplan` erzeugt eine maschinenlesbare Darstellung, deren sensible Werte ebenfalls geschützt werden müssen. [Planoptionen](https://developer.hashicorp.com/terraform/cli/commands/plan), [Show und JSON-Ausgabe](https://developer.hashicorp.com/terraform/cli/commands/show).

Beim Review auf **Anlegen, Ändern, Ersetzen und Löschen** achten. Insbesondere ein Austausch kann Datenverlust oder Unterbrechungen verursachen. Nach Änderungen an Konfiguration, gewöhnlichen Eingabewerten oder Arbeitskontext einen neuen Plan erzeugen. Beim gespeicherten Apply dürfen die im Plan festgelegten Infrastrukturentscheidungen nicht durch neue Planungsoptionen oder geänderte gewöhnliche `-var`-Werte ersetzt werden. **Ephemeral-Inputs bilden eine Ausnahme:** Sie werden nicht im Plan gespeichert und müssen für die Apply-Phase erneut bereitgestellt werden; ihr kurzlebiger Laufzeitwert darf sich ändern. Die geplanten Infrastrukturaktionen bleiben festgelegt. [Gespeicherte Pläne anwenden](https://developer.hashicorp.com/terraform/cli/commands/apply), [Ephemeral-Inputs](https://developer.hashicorp.com/terraform/language/block/variable#ephemeral), [versionsgenaue Apply-Implementierung](https://github.com/hashicorp/terraform/blob/v1.16.5/internal/backend/local/backend_apply.go#L291-L394).

### Detaillierte Exitcodes

Nur mit `terraform plan -detailed-exitcode` gilt folgende Zuordnung:

| Exitcode | Bedeutung | Reaktion im Skript |
|---|---|---|
| `0` | Erfolgreich, keine Änderungen | Ohne Apply abschließen |
| `1` | Fehler | Vorgang abbrechen und Diagnose lesen |
| `2` | Erfolgreich, Änderungen vorhanden | Plan dem vorgesehenen Review zuführen |

**Bash**, auch bei aktiviertem `set -e`: Den Plan bewusst innerhalb einer Fehlerbehandlung ausführen, damit ein erwarteter Code `2` das Skript nicht vorzeitig beendet.

```bash
plan_rc=0
terraform plan -input=false -detailed-exitcode -out=review.tfplan \
  || plan_rc=$?

case "$plan_rc" in
  0) printf '%s\n' "Keine Änderungen." ;;
  2) printf '%s\n' "Änderungen vorhanden; review.tfplan prüfen." ;;
  *) exit "$plan_rc" ;;
esac
```

**PowerShell:** Den nativen Exitcode unmittelbar nach Terraform aus `$LASTEXITCODE` übernehmen. `$?` allein unterscheidet einen erwarteten Änderungsplan nicht hinreichend von einem Fehler.

```powershell
terraform plan -input=false -detailed-exitcode -out=review.tfplan
$planExit = $LASTEXITCODE
if ($planExit -notin 0, 2) { throw "Terraform-Plan fehlgeschlagen: $planExit" }
if ($planExit -eq 2) { Write-Output 'Änderungen vorhanden; Plan prüfen.' }
```

Diese Beispiele erteilen keine automatische Apply-Freigabe. Die dokumentierte Unterscheidung `0`/`1`/`2` gehört zum Planbefehl und darf nicht unverändert auf andere Unterbefehle übertragen werden. [Plan-Exitcodes](https://developer.hashicorp.com/terraform/cli/commands/plan#other-options).

## Installation und Versionsprüfung

| System | Offizieller Weg | Praktischer Hinweis |
|---|---|---|
| Windows | ZIP von der HashiCorp-Installationsseite | Passende Architektur wählen, `terraform.exe` entpacken und Verzeichnis in `PATH` aufnehmen |
| macOS | `brew tap hashicorp/tap`, danach `brew install hashicorp/tap/terraform` | Alternativ ein fest versioniertes ZIP verwenden |
| Fedora | HashiCorp-RPM-Repository für **Fedora**, Installation mit DNF | Die zur Distribution passende Repositorydatei verwenden |
| RHEL | HashiCorp-RPM-Repository für **RHEL**, Installation mit DNF/YUM | In verwalteten Umgebungen den freigegebenen Mirror verwenden |
| Debian/Ubuntu | HashiCorp-APT-Repository mit eigenem Schlüsselbund und `signed-by` | Repositoryeintrag passend zu Distribution und Release setzen |
| Isolierte Systeme | Geprüfte Binärdatei oder freigegebenes Paket übertragen | Prüfsummen und Signatur zusammen mit dem Artefakt übertragen |

Die aktuellen Repository- und Installationsbefehle stehen auf der [offiziellen Installationsseite](https://developer.hashicorp.com/terraform/install). Paketmanager können künftig eine neuere Version liefern. Deshalb nach jeder Installation beziehungsweise Aktualisierung `terraform version` ausführen und die freigegebene Version im Team und in CI identisch festlegen.

**Bei mehreren Installationen:** Unter Bash zeigt `type -a terraform` alle auflösbaren Befehle; unter PowerShell hilft `Get-Command terraform -All`. Ein erfolgreich installiertes Paket garantiert noch nicht, dass dessen Binary im Suchpfad Vorrang hat.

### Binärdatei und Signatur prüfen

Für einen ZIP-Download gehören das Archiv, die zugehörige Datei `terraform_1.16.5_SHA256SUMS` und ihre Signatur zusammen. Zuerst den HashiCorp-Schlüssel aus offizieller Quelle beziehen und seinen vollständigen Fingerprint über die aktuelle [HashiCorp-Sicherheitsseite](https://www.hashicorp.com/en/trust/security) prüfen. Dann die Signatur der Prüfsummendatei und anschließend die Prüfsumme des tatsächlich heruntergeladenen Archivs kontrollieren.

Beispiel unter Linux für bereits heruntergeladene Dateien und einen bereits überprüften Schlüssel:

```bash
gpg --verify terraform_1.16.5_SHA256SUMS.sig terraform_1.16.5_SHA256SUMS
sha256sum --check --ignore-missing terraform_1.16.5_SHA256SUMS
```

Beide Befehle müssen erfolgreich sein; die Prüfsummenausgabe muss **genau das verwendete Archiv** mit `OK` nennen. Eine Prüfsumme allein bestätigt noch nicht den Herausgeber. Erst danach entpacken und installieren. Der vollständige Ablauf ist in [HashiCorps Anleitung zur Binärprüfung](https://developer.hashicorp.com/well-architected-framework/verify-hashicorp-binary) beschrieben.

**Bei GPG-Fehlern im Paketmanager:** Paketquelle, aktuelle Repositoryschlüssel und gegebenenfalls den internen Mirror prüfen. Ein alter Schlüssel auf einem Offline-System wird durch einen erfolgreichen Import auf einem anderen Rechner nicht aktualisiert. Die Signaturprüfung bleibt aktiviert; `--nogpgcheck` oder eine vergleichbare Abschaltung behebt die Vertrauenskette nicht.

## Dateien, HCL und Werte

Alle `.tf`- und `.tf.json`-Dateien unmittelbar im gleichen Modulverzeichnis bilden gemeinsam eine Konfiguration. Dateinamen definieren keine Ausführungsreihenfolge. Unterverzeichnisse sind eigenständige Module und werden nur durch ausdrückliche Modulaufrufe einbezogen. UTF-8 verwenden. [Dateien und Konfigurationsstruktur](https://developer.hashicorp.com/terraform/language/files).

| Datei oder Verzeichnis | Übliche Aufgabe |
|---|---|
| `versions.tf` | CLI- und Provideranforderungen |
| `providers.tf` | Providerkonfigurationen und Aliases |
| `main.tf` | Ressourcen, Datenquellen und Modulaufrufe |
| `variables.tf` | Deklaration der Eingabevariablen |
| `outputs.tf` | Veröffentlichte Moduloutputs |
| `locals.tf` | Wiederverwendete lokale Ausdrücke |
| `terraform.tfvars` | Automatisch geladene Werte für das Root-Modul |
| `environments/dev.tfvars` | Nur über `-var-file=environments/dev.tfvars` geladene Werte |
| `.terraform/` | Lokale Initialisierungsdaten, installierte Module und Provider |
| `.terraform.lock.hcl` | Konkrete Auswahl und Checksummen externer Provider |
| `terraform.tfstate` | Standarddatei des lokalen Backends; enthält den Verwaltungszustand |

Die Aufteilung in mehrere `.tf`-Dateien ist eine Konvention. `variables.tf` deklariert beispielsweise `variable "environment"`; die zugehörige `.tfvars`-Datei enthält eine Zuweisung wie `environment = "lab"`, keinen `variable`-Block.

### Bausteine und Typen

| Ausdruck oder Block | Aufgabe |
|---|---|
| `resource "typ" "name"` | Ein durch Terraform verwaltetes Objekt beschreiben |
| `data "typ" "name"` | Informationen über eine Datenquelle des Providers beziehen |
| `variable "name"` und `var.name` | Eingabe deklarieren und referenzieren |
| `locals` und `local.name` | Ausdruck benennen und innerhalb desselben Moduls verwenden |
| `output "name"` | Ergebnis eines Moduls bereitstellen |
| `module "name"` und `module.name.output_name` | Child-Modul aufrufen und dessen Output lesen |
| `string`, `number`, `bool` | Primitive Typen |
| `list(string)`, `set(string)`, `map(number)` | Gleichartig typisierte Sammlungen |
| `object({ name = string, port = number })` | Objekt mit festgelegten Attributtypen |
| `null` | Abwesenheit eines Wertes; bei optionalen Ressourcenargumenten häufig wie Weglassen |

`type = any` ist keine allgemeine Aufforderung zu beliebigen Werten: Terraform muss daraus einen passenden konkreten Typ bestimmen. Klare Typen erleichtern Diagnose und Modulbenutzung. Ein `default` macht einen Input optional; ohne Default muss ein Wert geliefert werden. `nullable = false` verhindert `null` für den gesamten Input, nicht automatisch für jedes verschachtelte Attribut. [Variablendeklaration](https://developer.hashicorp.com/terraform/language/block/variable), [Typen](https://developer.hashicorp.com/terraform/language/expressions/type-constraints), [Datenquellen](https://developer.hashicorp.com/terraform/language/data-sources).

### Priorität von Eingabewerten

Für lokale CLI-Läufe gilt **niedrige → hohe Priorität**. Ein höherer Eintrag in der folgenden Rangnummer überschreibt einen niedrigeren für denselben Namen:

| Rang | Quelle |
|---|---|
| 1 | `default` im `variable`-Block |
| 2 | Umgebungsvariable `TF_VAR_name` |
| 3 | `terraform.tfvars` |
| 4 | `terraform.tfvars.json` |
| 5 | `*.auto.tfvars` und `*.auto.tfvars.json`, lexikografisch; spätere Dateien gewinnen |
| 6 | `-var` und `-var-file` in der übergebenen Reihenfolge; spätere Zuweisungen gewinnen |

Die automatische Suche gilt für das Root-Modul. Child-Module erhalten Werte über ihre Aufrufargumente. HCP Terraform ergänzt eigene Regeln für Workspace-Variablen und Variable Sets. [Wertezuweisung und Priorität](https://developer.hashicorp.com/terraform/language/values/variables).

```bash
terraform plan -var-file=environments/dev.tfvars -out=dev.tfplan
terraform plan -var='environment=test' -out=test.tfplan
```

Komplexe Werte möglichst in `.tfvars` schreiben, damit Bash-, PowerShell- und Windows-Quotierung keine unterschiedlichen Inhalte erzeugen. Geheimnisse nicht als sichtbare Kommandozeilenargumente hinterlegen. `sensitive = true` maskiert gewöhnliche Ausgaben, ersetzt aber keinen Schutz von State und Plandateien.

## Ausdrücke, Funktionen und mehrere Instanzen

Ein Ressourcenattribut wird direkt referenziert, etwa `terraform_data.demo.output.name`. Die Schreibweise `"${...}"` wird nur benötigt, wenn der Wert in einen größeren String eingebettet wird. Referenzen erzeugen zugleich Abhängigkeiten; `depends_on` ist für zusätzliche, nicht aus Referenzen erkennbare Beziehungen vorgesehen. [Ausdrücke](https://developer.hashicorp.com/terraform/language/expressions), [explizite Abhängigkeiten](https://developer.hashicorp.com/terraform/language/meta-arguments/depends_on).

| Ausdruck | Ergebnis oder Einsatz |
|---|---|
| `length(["api", "worker"])` | Anzahl der Elemente: `2` |
| `lower("LAB")` | Zeichenkette `lab` |
| `format("%s-%02d", "node", 3)` | Zeichenkette `node-03` |
| `contains(["lab", "test"], "lab")` | `true` |
| `lookup({ lab = 1 }, "test", 0)` | Default `0`, wenn der Schlüssel fehlt |
| `merge({ tier = "dev" }, { tier = "test" })` | Späterer gleicher Schlüssel gewinnt: `tier = "test"` |
| `toset(["api", "api", "worker"])` | Menge ohne Duplikate; Reihenfolge nicht als Vertrag verwenden |
| `sort(["worker", "api"])` | Sortierte Liste |
| `jsonencode({ enabled = true })` | Korrekt maskierte JSON-Zeichenkette |
| `[for n in ["api", "db"] : upper(n)]` | Liste `["API", "DB"]` |
| `true ? "aktiv" : "inaktiv"` | Bedingter Ausdruck; beide Zweige brauchen kompatible Typen |

Mit `terraform console` lassen sich diese Ausdrücke untersuchen. Für erzeugte JSON-Konfigurationen `jsonencode` verwenden, statt Anführungszeichen von Hand zusammenzusetzen. `try(...)` und `can(...)` helfen bei erwartbaren dynamischen Auswertungsfehlern; sie beseitigen keine strukturell ungültigen Referenzen. [Funktionsreferenz](https://developer.hashicorp.com/terraform/language/functions), [for-Ausdrücke](https://developer.hashicorp.com/terraform/language/expressions/for), [try](https://developer.hashicorp.com/terraform/language/functions/try), [can](https://developer.hashicorp.com/terraform/language/functions/can).

### count oder for_each

| Auswahl | Adressierung | Geeignet für |
|---|---|---|
| `count = 2` | `terraform_data.copy[0]`, `[1]` | Gleichartige Instanzen mit bewusst numerischer Identität |
| `for_each = ...` | `terraform_data.service["api"]` | Benannte Instanzen mit stabilen Schlüsseln |

Eigenständiges Beispiel mit zwei lokalen State-Ressourcen:

```hcl
locals {
  services = {
    api     = 8443
    metrics = 9090
  }
}

resource "terraform_data" "service" {
  for_each = local.services

  input = {
    name = each.key
    port = each.value
  }
}

output "ports" {
  value = { for name, service in terraform_data.service : name => service.output.port }
}
```

Bei `for_each` sind Maps oder Mengen von Strings erlaubt. Die Map-Schlüssel beziehungsweise alle Set-Einträge müssen vor Apply bekannt und nicht sensitiv sein; Map-Werte dürfen dagegen erst später feststehen. Listen werden nicht automatisch zu Sets. Für `count` muss die Anzahl vor Apply feststehen; `count` und `for_each` sind im gleichen Block gegenseitig ausgeschlossen. [for_each](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each), [count](https://developer.hashicorp.com/terraform/language/meta-arguments/count).

**Adressstabilität:** Wird bei einer über `count.index` ausgewerteten Liste ein Eintrag aus der Mitte entfernt, verschieben sich nachfolgende Indizes. Bei fachlich benannten Objekten helfen stabile Map-Schlüssel, solche unbeabsichtigten Neuzuordnungen zu vermeiden. Eine Schlüsselumbenennung ändert trotzdem die Ressourcenadresse und braucht eine bewusste Migration.

## CLI, Provider und Module versionieren

### Drei getrennte Versionsentscheidungen

| Ebene | Konfiguration | Was dadurch festgelegt wird |
|---|---|---|
| Terraform-CLI | `required_version` im `terraform`-Block | Welche bereits installierte CLI die Konfiguration ausführen darf |
| Provider | `required_providers` mit `source` und `version` | Herkunft und zulässige Versionen eines Plugins |
| Registry-Modul | `source` und `version` im `module`-Block | Quelle und zulässige Modulversionen |

`required_version` installiert keine CLI. Alle Anforderungen aus Root- und Child-Modulen müssen zusammen erfüllbar sein. Für CI zusätzlich die verwendete Binärversion festlegen. [Terraform-Block](https://developer.hashicorp.com/terraform/language/block/terraform).

| Bedingung | Erlaubter Bereich |
|---|---|
| `"= 1.16.5"` | Nur 1.16.5 |
| `"~> 1.16.0"` | Ab 1.16.0, unter 1.17.0 |
| `"~> 1.16"` | Ab 1.16.0, unter 2.0.0 |
| `">= 1.16.0, < 2.0.0"` | Explizite Unter- und Obergrenze |

`~> 1.16` hält also nicht auf dem 1.16-Zweig. Vorabversionen benötigen eine exakte Auswahl; normale Vergleichsbereiche schließen sie nicht ein. [Versionsbedingungen](https://developer.hashicorp.com/terraform/language/expressions/version-constraints).

### Provider konfigurieren und Aliases verwenden

Konfigurationsbeispiel für AWS 6.x mit Standardregion und zweiter Region; Zugangsdaten werden über das für die Umgebung vorgesehene Authentifizierungsverfahren bereitgestellt. Der Ausschnitt deklariert keine AWS-Ressourcen:

```hcl
terraform {
  required_version = "~> 1.16.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = "eu-central-1"
}

provider "aws" {
  alias  = "secondary"
  region = "eu-west-1"
}
```

Eine Ressource wählt die zweite Konfiguration mit `provider = aws.secondary`. Ein Child-Modul kann sie über `providers = { aws = aws.secondary }` als seine Standardkonfiguration erhalten. Aliases sind unterschiedliche **Konfigurationen derselben Provider-Version**. Die Providerkonfiguration gehört ins Root-Modul; Anforderungen an Quelle und Version deklariert jedes verwendende Modul selbst. Der alte `version`-Eintrag direkt im `provider`-Block ist veraltet. [Providerkonfiguration](https://developer.hashicorp.com/terraform/language/block/provider), [AWS-Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs).

### Provider-Lockdatei pflegen

**`.terraform.lock.hcl` einchecken; `.terraform/` nicht einchecken.** Die Lockdatei hält ausgewählte Provider-Versionen und Paketprüfsummen fest. Sie sperrt weder die Terraform-CLI noch Remote-Module und ersetzt keinen State-Lock. Normales `init` verwendet die bestehende Providerauswahl erneut; ein bewusstes `init -upgrade` kann sie innerhalb der Versionsbedingungen aktualisieren. [Dependency Lock File](https://developer.hashicorp.com/terraform/language/files/dependency-lock).

```bash
terraform init -lockfile=readonly
terraform providers lock -platform=linux_amd64 -platform=windows_amd64 -platform=darwin_arm64
```

`-lockfile=readonly` verhindert Lockdateiänderungen und prüft vorhandene Checksummen; nicht mit `-upgrade` kombinieren. `providers lock` ergänzt Prüfsummen für die angegebenen Plattformen, sofern die Provider sie anbieten. Änderungen an Auswahl und Prüfsummen im Review lesen, statt eine widersprüchliche Lockdatei reflexartig zu löschen. [Initialisierung](https://developer.hashicorp.com/terraform/cli/commands/init), [Plattformchecksummen](https://developer.hashicorp.com/terraform/cli/commands/providers/lock).

### Module aufrufen und festlegen

Ein Child-Modul bildet eine wiederverwendbare Konfiguration mit eigenen Inputs und Outputs. Ein lokaler Aufruf innerhalb der obigen Übung kann so aussehen, sobald das passende Unterverzeichnis vorhanden ist:

```hcl
module "label" {
  source  = "./modules/label"
  project = var.project
}

output "module_label" {
  value = module.label.value
}
```

Vollständiger Inhalt von `modules/label/main.tf`:

```hcl
variable "project" {
  type     = string
  nullable = false
}

output "value" {
  value = upper(var.project)
}
```

Nach einem neuen Modulaufruf oder geänderter Quelle erneut `terraform init` ausführen. Bei Registry-Modulen eine geprüfte exakte `version` verwenden. Git-Quellen werden beispielsweise mit `git::https://example.com/team/module.git?ref=<vollstaendiger-commit-sha>` festgelegt; dabei den Platzhalter ersetzen. `version` ist nur für Registry-Quellen vorgesehen. Ein zusätzlicher Git-Parameter `depth` lässt sich nicht mit einem rohen Commit-SHA als `ref` kombinieren. [Modulquellen und Versionen](https://developer.hashicorp.com/terraform/language/block/module).

**Seit Terraform 1.15:** `source` und `version` dürfen konstante Locals und Eingabevariablen mit `const = true` referenzieren. Gewöhnliche erst beim Planen bekannte Inputs oder Ressourcenwerte bleiben dafür ungeeignet. Ein Literal ist weiterhin eine gut überprüfbare Standardwahl. Der `terraform`-Block selbst unterliegt eigenen Einschränkungen und darf nicht mit dieser Modulfunktion gleichgesetzt werden. [Konstante Eingabevariablen](https://developer.hashicorp.com/terraform/language/block/variable#const), [Einführung in Terraform 1.15](https://www.hashicorp.com/en/blog/new-in-terraform-115-dynamic-sources-variable-deprecation-and-more).

## State lesen und Backends verstehen

Der **State** verbindet Terraform-Adressen mit den verwalteten Objekten. Wer ihn verliert oder dieselbe Infrastruktur aus mehreren unabhängigen States verwaltet, verliert diese eindeutige Zuordnung. State-Dateien können außerdem Passwörter, Schlüssel und andere vertrauliche Attribute enthalten; auch Sicherungskopien entsprechend behandeln.

| Aufgabe | Kommando | Bedeutung |
|---|---|---|
| Verwaltete Adressen auflisten | `terraform state list` | Zeigt die Adressen im aktiven State. |
| Eine Ressource ansehen | `terraform state show 'terraform_data.demo'` | Zeigt gespeicherte Attribute; Ausgabe kann vertraulich sein. |
| State vollständig ausgeben | `terraform state pull` | Diagnose/gesicherte Sicherung; nicht in öffentliche Logs kopieren. |
| Backend nach Änderung neu initialisieren | `terraform init -reconfigure` | Neue Backend-Einstellungen übernehmen, ohne bisherigen State zu migrieren. |
| State in ein anderes Backend übernehmen | `terraform init -migrate-state` | Vorhandenen State in das neue Backend kopieren; Rückfragen und Ziel prüfen. |

Eine Backend-Umstellung braucht eine gesicherte Ausgangsversion, eindeutige Zuständigkeit und einen anschließend geprüften Plan. `-reconfigure` und `-migrate-state` sind keine austauschbaren Reparaturversuche. Direkte Änderungen mit `terraform state mv`, `state rm` oder `state push` wirken auf State; deklarative Migrationen sind im Review meist leichter nachvollziehbar.

Ein Root-Modul hat höchstens einen `backend`-Block. `cloud` und `backend` dürfen nicht gemeinsam konfiguriert werden. Backend-Einstellungen können nicht auf gewöhnliche Variablen, Locals oder Data Sources zugreifen. Zugangsdaten für das Backend und für den Infrastruktur-Provider sind getrennt zu betrachten: Ein `provider "aws"`-Block konfiguriert nicht automatisch die Authentifizierung des S3-Backends.

Quellen: [Backend-Konfiguration](https://developer.hashicorp.com/terraform/language/backend), [terraform init](https://developer.hashicorp.com/terraform/cli/commands/init), [State-Befehle](https://developer.hashicorp.com/terraform/cli/commands/state).

### Eigenständiges Beispiel: S3 als Team-Backend

Das folgende Beispiel gehört zu einem **separaten AWS-Projekt**, nicht zur lokalen `terraform_data`-Übung. Der angepasste Bucket muss bereits existieren. Authentifizierung, Bucket-Versionierung, Verschlüsselung und Zugriffsregeln vorher einrichten; dieses Fragment erstellt sie nicht.

```hcl
terraform {
  required_version = "~> 1.16.0"

  backend "s3" {
    bucket       = "ERSETZEN-EIGENER-STATE-BUCKET"
    key          = "projekt/prod/terraform.tfstate"
    region       = "eu-central-1"
    encrypt      = true
    use_lockfile = true
  }
}
```

S3-State-Locking ist standardmäßig **ausgeschaltet**. `use_lockfile = true` aktiviert es. Die Funktion ist seit Terraform 1.10 verfügbar und seit 1.11 allgemein verfügbar; die DynamoDB-Locking-Argumente sind seit 1.11 veraltet. Für die Umstellung älterer Clients können beide Mechanismen vorübergehend gemeinsam konfiguriert werden. DynamoDB erst entfernen, wenn alle beteiligten Clients den neuen Mechanismus verwenden.

Für die `.tflock`-Datei werden `s3:GetObject`, `s3:PutObject` und `s3:DeleteObject` benötigt. Die State-Datei des Default-Workspace braucht Lesen und Schreiben, aber keine Löschberechtigung. Weitere Workspaces benötigen zusätzliche passende Pfadberechtigungen. Bucket-Versionierung erleichtert die Wiederherstellung; ein Lock ersetzt keine Sicherung.

Keine Schlüssel oder Token direkt in den Backend-Block oder in geheime `-backend-config`-Argumente schreiben: Terraform kann sie in `.terraform` und Plan-Dateien speichern. Unterstützte Umgebungsvariablen, Profile oder kurzlebige Web-Identity-Zugangsdaten verwenden.

Quellen: [S3-Backend und IAM-Anforderungen](https://developer.hashicorp.com/terraform/language/backend/s3), [Terraform 1.10](https://github.com/hashicorp/terraform/blob/v1.10/CHANGELOG.md), [Terraform 1.11](https://github.com/hashicorp/terraform/blob/v1.11/CHANGELOG.md).

### Wenn ein State-Lock belegt ist

```bash
terraform plan -lock-timeout=5m
```

Zuerst den laufenden Prozess oder CI-Job prüfen. `-lock=false` unterdrückt den Schutz vor gleichzeitigen Schreibern und gehört nicht in den normalen Arbeitsablauf. `terraform force-unlock LOCK_ID` kommt ausschließlich für den eigenen verwaisten Lock infrage, wenn der verursachende Lauf sicher beendet und automatisches Entsperren fehlgeschlagen ist. Nicht blind eine fremde Lock-ID übernehmen.

**Zwei verschiedene Lock-Arten:** `.terraform.lock.hcl` fixiert Provider-Auswahlen und Checksums; der Backend-Lock koordiniert konkurrierende State-Zugriffe. Ein Problem der einen Art wird nicht durch Löschen der anderen gelöst. [Quelle: State Locking](https://developer.hashicorp.com/terraform/language/state/locking).

## Workspaces und Umgebungsgrenzen

CLI-Workspaces verwalten mehrere States für dieselbe Konfiguration im selben Backend. Sie eignen sich etwa für vorübergehende parallele Instanzen. Sie schaffen allein keine getrennten Accounts, Zugangsdaten oder Berechtigungsgrenzen.

```bash
terraform workspace list
terraform workspace show
terraform workspace select test
```

`select` wechselt zu einem bestehenden Workspace; `terraform workspace new test` legt einen neuen an. Vor jedem produktiven Plan/Apply Arbeitsverzeichnis, Workspace, Backend und Cloud-Identität prüfen. `TF_WORKSPACE` kann die lokale Workspace-Auswahl überschreiben; eine vergessene Shell-Variable kann deshalb das falsche Ziel auswählen.

Für Produktion und Test mit getrennten Zugriffsrechten getrennte Root-Konfigurationen, passende Backends und Identitäten verwenden. **HCP-Terraform-Workspaces** sind ein anderes Organisationsmodell: Sie umfassen unter anderem Konfiguration, Variablen, State und Run-Einstellungen; nicht mit dem CLI-Workspace-Umschalter gleichsetzen.

Auch `terraform_remote_state` bildet keine Berechtigungsgrenze um einzelne Outputs: Der Leser benötigt Zugriff auf den gesamten State-Snapshot. In HCP Terraform kann `tfe_outputs` Outputs ohne vollen State-Zugriff lesen. Gemeinsame Daten gegebenenfalls gezielt in einem dafür vorgesehenen Dienst veröffentlichen.

Quellen: [CLI-Workspaces](https://developer.hashicorp.com/terraform/cli/workspaces), [State und Workspaces](https://developer.hashicorp.com/terraform/language/state/workspaces), [Remote-State-Daten](https://developer.hashicorp.com/terraform/language/state/remote-state-data).

## Bestehende Ressourcen importieren

Ein Import ordnet ein existierendes Objekt einer Terraform-Adresse zu. Er erzeugt keine Kopie. Dasselbe Objekt nicht unabhängig in mehrere States importieren. Ressourcentyp, Objekt-ID beziehungsweise unterstützte `identity`, Account und Provider-Konfiguration müssen zusammenpassen.

**Beispiel für ein bestehendes AWS-Projekt:** Der passende `aws_s3_bucket.logs`-Ressourcenblock und der AWS-Provider gehören zur Zielkonfiguration; folgende Ergänzung allein ist keine vollständige AWS-Konfiguration.

```hcl
import {
  to = aws_s3_bucket.logs
  id = "ERSETZEN-BESTEHENDER-BUCKET-NAME"
}
```

```bash
terraform plan -out=import.tfplan
terraform show import.tfplan
```

Den gesamten Plan prüfen: Neben dem Import können Änderungen oder Ersatzoperationen enthalten sein, wenn Konfiguration und Bestand voneinander abweichen. Erst nach bewusster Freigabe mit `terraform apply import.tfplan` übernehmen. Das Anwenden eines gespeicherten Plans fragt nicht erneut interaktiv nach Zustimmung.

Ohne vorhandenen Ziel-Ressourcenblock kann `terraform plan -generate-config-out=generated.tf` passende Konfiguration erzeugen. Die Zieldatei darf noch nicht existieren; die aktuelle CLI-Referenz kennzeichnet diese Generierung als experimentell. Ergebnis prüfen, vereinfachen und erst danach regulär verwalten. Generierter Code ist kein automatisch freigegebener Sollzustand.

Der klassische Befehl `terraform import 'aws_s3_bucket.logs' 'OBJEKT-ID'` verlangt einen vorbereiteten Ressourcenblock und verändert State direkt. Deklarative `import`-Blöcke gibt es seit 1.5, `for_each` darin seit 1.7. Import-IDs und gegebenenfalls `identity`-Felder sind providerspezifisch; `id` und `identity` schließen sich gegenseitig aus.

Quellen: [Import-Block](https://developer.hashicorp.com/terraform/language/block/import), [Konfiguration generieren](https://developer.hashicorp.com/terraform/language/import/generating-configuration), [CLI-Import](https://developer.hashicorp.com/terraform/cli/commands/import).

## Ressourcen umbenennen oder aus der Verwaltung entlassen

### Adresse ändern mit moved

**Eigenständiges Migrationsbeispiel:** Wenn `terraform_data.demo` bereits im State existiert, seinen Ressourcenblock in `terraform_data.application` umbenennen und die Verweise ebenfalls anpassen. Dazu gehört:

```hcl
moved {
  from = terraform_data.demo
  to   = terraform_data.application
}
```

Ein anschließender Plan soll die Adressänderung zeigen. Ohne Migrationsinformation kann Terraform aus einer Umbenennung eine Löschung plus Neuerstellung ableiten. `moved` verschiebt keine echte Ressource in eine andere Region oder einen anderen Account. Andere gleichzeitig geänderte Argumente können weiterhin Infrastrukturänderungen verursachen.

`moved` ist seit 1.1 verfügbar. In wiederverwendbaren Modulen Migrationsketten nicht voreilig entfernen: Anwender können Versionen überspringen und die alten Übergänge noch benötigen. [Quelle: Refactoring von Modulen und Ressourcen](https://developer.hashicorp.com/terraform/language/modules/develop/refactoring).

### Verwaltung beenden mit removed

**Alternative zur Umbenennung:** Den bisherigen Ressourcenblock entfernen, abhängige Verweise anpassen und das Objekt ausdrücklich ohne Zerstörung aus State entlassen:

```hcl
removed {
  from = terraform_data.demo

  lifecycle {
    destroy = false
  }
}
```

Bei einer echten Infrastrukturressource bleibt das Objekt damit bestehen und wird nach Apply nicht mehr von diesem State verwaltet. Der `terraform_data`-Demonstrationswert hat dagegen kein entsprechendes externes Cloud-Objekt. `removed` ist seit 1.7 verfügbar; **ohne `destroy = false` ist das Standardverhalten zerstörend**.

`terraform state rm ADDRESS` ist die direkte CLI-Variante zum Vergessen einer Bindung. Bleibt die Ressource anschließend in der Konfiguration, kann der nächste Plan eine Neuerstellung verlangen. Das Entfernen aus State beendet auch keine laufenden Kosten des realen Objekts. [Quelle: removed-Block](https://developer.hashicorp.com/terraform/language/block/removed).

## Drift erkennen und State gezielt abgleichen

**Drift** bezeichnet Abweichungen zwischen dem beobachteten Infrastrukturzustand und den bisherigen Aufzeichnungen beziehungsweise dem konfigurierten Soll. Ein normaler Plan liest bestehende Objekte standardmäßig erneut und berechnet die nötigen Änderungen in Richtung Konfiguration.

| Ziel | Vorgehen |
|---|---|
| Externe Änderung wieder zurücknehmen | Normalen `terraform plan` prüfen; freigegebenen Plan anwenden. |
| Externe Änderung dauerhaft übernehmen | Konfiguration passend ändern; vollständigen Plan prüfen. |
| Nur State/Root-Outputs an beobachteten Zustand angleichen | Überprüfbaren Refresh-only-Plan verwenden. |

```bash
terraform plan -refresh-only -out=refresh.tfplan
terraform show refresh.tfplan
```

Erst nach Prüfung `terraform apply refresh.tfplan` ausführen. **Refresh-only schreibt keine `.tf`-Dateien um.** Ohne passende Konfigurationsänderung kann ein späterer normaler Plan die manuelle Änderung wieder rückgängig machen wollen.

`terraform refresh` ist veraltet und bestätigt State-Änderungen implizit automatisch. `-refresh=false` überspringt den Abgleich und kann veraltete Annahmen verbergen. `-target=ADDRESS` ist für Ausnahme- und Wiederherstellungsfälle gedacht; danach wieder einen vollständigen Plan erstellen. Für bewusst notwendigen Ersatz ist `terraform plan -replace='ADRESSE'` der prüfbare Ansatz; der tatsächliche Ersatz erfolgt erst beim Apply.

Quellen: [Plan-Modi und Optionen](https://developer.hashicorp.com/terraform/cli/commands/plan), [Refresh-only-Tutorial](https://developer.hashicorp.com/terraform/tutorials/state/refresh), [Veralteter refresh-Befehl](https://developer.hashicorp.com/terraform/cli/commands/refresh).

## Lifecycle und verbindliche Bedingungen

| Regel | Wirkung und Grenze |
|---|---|
| `create_before_destroy = true` | Erst Ersatz erstellen, dann altes Objekt löschen; freie Kapazität und kollisionsfreie Namen müssen möglich sein. Kein allgemeines Versprechen für unterbrechungsfreien Betrieb. |
| `prevent_destroy = true` | Verhindert einen zerstörenden Plan, solange die Regel vorhanden ist. Das Löschen des gesamten Ressourcenblocks entfernt auch diesen Schutz. |
| `ignore_changes = [tags["extern"]]` | Benanntes Attribut bei Updates ignorieren; bei der Erstellung gilt der konfigurierte Wert weiterhin. |
| `ignore_changes = all` | Keine Attributupdates planen; Erstellen und Löschen bleiben möglich. Nur mit klarer anderer Zuständigkeit verwenden. |
| `replace_triggered_by = [andere_resource.example.id]` | Ersatz durch Änderungen an referenzierten verwalteten Ressourcen/Attributen auslösen. Gewöhnliche Variablen sind keine Ressourcenadressen. |

`create_before_destroy` kann auf Abhängigkeiten propagieren. Bei der betroffenen Ressource verhindert es außerdem Destroy-Provisioner. `ignore_changes` verdeckt keine fehlenden Berechtigungen und ist keine allgemeine Reparatur gegen unerwartete Pläne. [Quelle: lifecycle-Referenz](https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle).

| Prüfmechanismus | Geeigneter Zweck | Bei verletzter Bedingung |
|---|---|---|
| Input-`validation` | Erlaubte Werte, Formate und Bereiche | Fehler; Vorgang wird gestoppt. |
| `precondition` | Voraussetzung an Ressource, Data Source oder Output | Betroffene Operation wird blockiert. |
| `postcondition` | Zusicherung über ermittelten/erzeugten Zustand | Weitere abhängige Aktionen werden blockiert; bereits ausgeführte Änderungen werden nicht zurückgerollt. |
| `check` | Übergreifende Beobachtung, z. B. Erreichbarkeit | Im normalen Plan/Apply eine Warnung; Ausführung läuft weiter. |

Terraform prüft Bedingungen, sobald die benötigten Werte bekannt sind; manche Prüfungen verschieben sich dadurch vom Plan zum Apply. Ein `check` ist kein hartes Deployment-Gate. In `terraform test` führen unerwartet fehlschlagende Checks dagegen zu einem fehlgeschlagenen Test. Preconditions/Postconditions gibt es seit 1.2, `check` seit 1.5.

Quellen: [Validierungen und Bedingungen](https://developer.hashicorp.com/terraform/language/validate), [Checks im Testframework](https://developer.hashicorp.com/terraform/language/tests).

## Geheimnisse und kurzlebige Werte

| Möglichkeit | Was sie schützt | Was sie nicht automatisch erledigt |
|---|---|---|
| `sensitive = true` | Normale CLI-/UI-Anzeige wird verschleiert. | Werte werden weiterhin in State und Plan gespeichert. |
| `ephemeral = true` | Wert wird nicht in State oder Plan persistiert. | Keine allgemeine Verschlüsselung und kein Ersatz für eingeschränkte Zugriffe. |
| Write-only-Argument | Dieses Ressourcenargument wird nicht in State oder Plan gespeichert. | Andere Kopien desselben Geheimnisses können weiterhin persistiert werden. |

`ephemeral` ist seit 1.10 verfügbar, Write-only-Ressourcenargumente seit 1.11. Anbieter müssen passende Ressourcen beziehungsweise Argumente implementieren. Namen wie `password_wo` und `password_wo_version` sind typische providerdefinierte Schnittstellen, keine universellen Meta-Argumente.

**Zusätzliche Variable für eine passende Provider-Konfiguration, nicht für den normalen `input` der Grundübung:**

```hcl
variable "api_token" {
  description = "Kurzlebiges Token für die Provider-Authentifizierung."
  type        = string
  sensitive   = true
  ephemeral   = true
}
```

Ephemeral-Werte sind nur in erlaubten Kontexten nutzbar, etwa Provider-Konfigurationen, anderen ephemeral-Werten oder Write-only-Argumenten. Child-Module dürfen ephemeral-Outputs deklarieren; Root-Outputs nicht. Eine normale persistierte Ressourceneigenschaft kann nicht beliebig einen ephemeral-Wert aufnehmen.

Benötigte Ephemeral-Inputs für **Plan und Apply jeweils bereitstellen**, auch beim Anwenden einer gespeicherten Plandatei. Beispielsweise kann die Apply-Phase ein erneuertes kurzlebiges Token verwenden. Geeignete geschützte Umgebungsvariablen oder die unterstützten Zugangsdatenmechanismen der Ausführungsumgebung verwenden; echte Geheimnisse nicht in Shell-Historie oder Prozessargumente schreiben. Diese erneute Laufzeiteingabe plant die gespeicherten Infrastrukturaktionen nicht neu.

Weil Terraform einen Write-only-Wert nicht behält, kann es dessen Änderung nicht direkt vergleichen. Provider verwenden häufig ein zusätzliches Versionsargument zur gezielten Aktualisierung. Dessen Wert landet regulär im State. Die konkrete Semantik in der jeweiligen Provider-Referenz prüfen. Ephemer erzeugte Geheimnisse bei Bedarf über einen geeigneten Geheimnisspeicher erhalten; sonst sind sie nach dem Lauf nicht wiederherstellbar.

`terraform output -raw NAME`, `terraform output -json` und maschinenlesbare Plan-/State-Ausgaben können sensible Werte offenlegen. Solche Ausgaben weder in PR-Kommentare noch in öffentliche Artefakte übernehmen. Auch eine verschlüsselte Backend-Ablage macht ein exportiertes JSON nicht automatisch verschlüsselt.

Quellen: [Sensitive und ephemeral](https://developer.hashicorp.com/terraform/language/manage-sensitive-data), [Write-only-Werte und Versionsargumente](https://developer.hashicorp.com/terraform/language/manage-sensitive-data/write-only).

## Git-Dateien und CI-Ablauf

Ein konservativer Ausgangspunkt für die `.gitignore` eines Terraform-Projekts:

```gitignore
.terraform/
*.tfstate
*.tfstate.*
tfplan
*.tfplan
plan.json
*.tfplan.json
crash.log
crash.*.log
*.tfvars
*.tfvars.json
credentials.tfrc.json
```

**`.terraform.lock.hcl` einchecken.** Fachlich notwendige `.tf`-Dateien, Tests und Modulquellen ebenfalls versionieren. Die pauschalen `.tfvars`-Regeln sind eine konservative Projektentscheidung: Nachweislich geheimnisfreie Werte können kontrolliert versioniert werden. Eine `terraform.tfvars.example` mit Beispieldaten dokumentiert Inputs, ohne automatisch geladen zu werden. Bereits eingecheckte Geheimnisse verschwinden durch `.gitignore` nicht aus der Historie; veröffentlichte Zugangsdaten zusätzlich widerrufen/rotieren.

Für CI Provider-Lockdatei vorbereiten und prüfen, Terraform-Version fixieren und Registry-Module passend versionieren. Dann beispielsweise:

```bash
export TF_IN_AUTOMATION=1
terraform fmt -check -recursive
terraform init -input=false -lockfile=readonly
terraform validate -no-color
```

Bei realen Provider-Abhängigkeiten muss eine passende Lockdatei bereits committed sein. `-lockfile=readonly` prüft die gespeicherten Checksums und verhindert Änderungen daran. `terraform init -upgrade` gehört in einen ausdrücklich geprüften Abhängigkeits-Update, nicht in jeden Deployment-Lauf. Das providerfreie Grundbeispiel benötigt keinen externen Provider-Eintrag.

Ein belastbarer weiterer Ablauf ist: **geprüfter Commit → Plan erzeugen → genau diesen Plan prüfen/freigeben → denselben Plan anwenden**. Einen nicht mehr zum aktuellen State passenden Plan neu erzeugen. Apply-Schritte pro State koordinieren; ein CI-Concurrency-Schlüssel ergänzt das Backend-Locking. Temporäre Plan-Artefakte geschützt ablegen und zeitnah entfernen.

Bei getrennten Runnern Terraform-/Provider-Version, Betriebssystem, Architektur und erforderliche Arbeitsdateien konsistent halten. Absolute Pfade können im Plan enthalten sein. `terraform apply tfplan` enthält keine erneute Bestätigungsfrage; die Genehmigung muss daher vor diesem Schritt zuverlässig erfolgen. Nicht nach der Freigabe stillschweigend einen anderen Plan berechnen.

Quellen: [Terraform-Stil und Versionskontrolle](https://developer.hashicorp.com/terraform/language/style), [Lockdatei](https://developer.hashicorp.com/terraform/language/files/dependency-lock), [Automatisierung](https://developer.hashicorp.com/terraform/tutorials/automation/automate-terraform).

### Kurzlebige Cloud-Identität statt dauerhafter Schlüssel

Wo unterstützt, OIDC/Workload Identity für zeitlich begrenzte Zugangsdaten einsetzen. HCP Terraform kann Provider-Zugangsdaten für Plan und Apply dynamisch anfordern; bei AWS sind getrennte Rollen über `TFC_AWS_PLAN_ROLE_ARN` und `TFC_AWS_APPLY_ROLE_ARN` möglich. Die Vertrauensbeziehung auf passende Audience und Organisations-/Projekt-/Workspace-/Phasen-Claims begrenzen. Für externe CI gelten die Claim-Formate des jeweiligen Identitätsanbieters.

Backend- und Locking-Zugriffe mit berücksichtigen: Eine Plan-Identität benötigt nicht ausschließlich Lesezugriff auf jede beteiligte Schnittstelle. Sie muss den zugehörigen State-Lock verwenden können. Provider- und Backend-Identität dürfen verschieden sein, müssen aber zum beabsichtigten Ziel passen.

Unvertrauenswürdige PR-Konfiguration nicht mit Produktionszugangsdaten planen. Terraform lädt Provider-Code und wertet auch Data Sources aus; ein Plan ist keine Sandbox für fremden Code. OIDC beseitigt das Problem nicht, wenn unvertrauenswürdiger Code eine privilegierte kurzlebige Identität bekommen kann.

Quellen: [Dynamische Provider-Zugangsdaten](https://developer.hashicorp.com/terraform/cloud-docs/dynamic-provider-credentials), [AWS-Vertrauensbeziehung und Rollen](https://developer.hashicorp.com/terraform/cloud-docs/dynamic-provider-credentials/aws-configuration), [PR-Pläne und Secrets](https://developer.hashicorp.com/terraform/tutorials/automation/automate-terraform).

## Native Tests für das lokale Grundbeispiel

Das aktuelle native Testframework gibt es seit 1.6, Provider-Mocks seit 1.7. **Ohne Angabe führt ein `run` standardmäßig `apply` aus.** Diese vollständige Datei `tests/demo.tftest.hcl` testet ausschließlich die providerfreie Grundübung und verwendet deshalb ausdrücklich Planläufe:

```hcl
variables {
  project     = "cheatsheets"
  environment = "test"
}

run "name_und_umgebung" {
  command = plan

  assert {
    condition     = terraform_data.demo.input.name == "cheatsheets-test"
    error_message = "Der Name muss Projekt und Testumgebung verbinden."
  }

  assert {
    condition     = terraform_data.demo.input.environment == "test"
    error_message = "Die Umgebung muss test sein."
  }
}

run "produktion_ist_im_labor_unzulaessig" {
  command = plan

  variables {
    environment = "prod"
  }

  expect_failures = [var.environment]
}
```

```bash
terraform init -input=false
terraform test -filter=tests/demo.tftest.hcl
```

Erwartet werden zwei erfolgreiche Tests. Der zweite besteht gerade dann, wenn die Input-Validierung `prod` ablehnt. Geprüft wird `input.name`, weil dieser Ausdruck im Plan bekannt ist; `terraform_data.demo.output.name` kann erst nach Apply bekannt sein. `expect_failures` prüft benannte eigene Bedingungen und unterdrückt nicht beliebige Syntax-, Typ- oder Providerfehler.

Bei **anderen** Konfigurationen kann `terraform test` reale, kostenpflichtige Infrastruktur erzeugen. Das Testframework verwendet separaten State im Speicher und versucht anschließend aufzuräumen; fehlgeschlagene Bereinigung muss kontrolliert nachgeholt werden. Ein Plan-Test kann weiterhin Provider-Abfragen ausführen. Für echte Cloud-Tests eigene Testkonten und eindeutige Namen verwenden oder geeignete Provider/Ressourcen vollständig mocken. Die lokale Übung enthält solche Cloud-Abhängigkeiten nicht.

Quellen: [Tests, Assertions und erwartete Fehler](https://developer.hashicorp.com/terraform/language/tests), [Test-CLI und Bereinigung](https://developer.hashicorp.com/terraform/cli/commands/test), [Provider-Mocking](https://developer.hashicorp.com/terraform/language/tests/mocking).

## Fehlerbilder gezielt eingrenzen

| Symptom | Zuerst prüfen | Passender nächster Schritt |
|---|---|---|
| `Backend initialization required` | Backend geändert? Richtiger Projektordner? | `terraform init`; bei echter Umstellung Migration bewusst entscheiden. |
| `Error acquiring the state lock` | Läuft noch ein anderer Job? Stimmt die Identität? | Besitzer/Prozess prüfen, gegebenenfalls mit `-lock-timeout` warten. |
| `Inconsistent dependency lock file` | Stimmen Provider-Anforderungen und Lockdatei zusammen? | Kontrolliert initialisieren/aktualisieren, Diff prüfen und committen. |
| Provider-Checksum passt nicht | Lockdatei, Plattform, Mirror und Herkunft vergleichen. | Quelle klären; Checksum-Prüfung nicht abschalten. |
| Unerwartetes Destroy/Create | Adresse, `count`-Indizes, `for_each`-Schlüssel, unveränderliche Attribute prüfen. | Gegebenenfalls `moved` ergänzen; gesamten Plan erneut prüfen. |
| `Invalid for_each argument` | Sind Instanzschlüssel bekannt und nicht sensibel? | Stabile Konfigurationsschlüssel verwenden. |
| `known after apply` | Benötigt der Wert ein tatsächlich erzeugtes Objekt? | Abhängigkeit korrekt modellieren; im Plan nicht als bekannten Wert behandeln. |
| `403` / `AccessDenied` | Backend und Provider getrennt; Account, Rolle, Token-Laufzeit, Lockdatei-Pfad. | Fehlende konkrete Berechtigung/Zielidentität korrigieren. |
| Plan ist veraltet | Hat ein anderer Lauf State verändert? | Einen neuen vollständigen Plan erzeugen und erneut prüfen. |
| Test schlägt im erwarteten Fehlerfall fehl | Scheitert die benannte eigene Validation oder etwas anderes? | Bei Planvalidierung `command = plan`; `expect_failures` exakt zuordnen. |

Für die erste Diagnose reichen meist `terraform version`, `terraform providers`, `terraform workspace show`, `terraform validate` und ein vollständiger Plan. `TF_LOG`/`TF_LOG_PATH` nur gezielt aktivieren: ausführliche Logs können Geheimnisse enthalten. Nach der Diagnose Logging wieder deaktivieren und Diagnoseartefakte geschützt behandeln.

Quellen: [CLI-Umgebungsvariablen](https://developer.hashicorp.com/terraform/cli/config/environment-variables), [Provider-Auswahl und Prüfsummen](https://developer.hashicorp.com/terraform/language/files/dependency-lock), [Plan-Referenz](https://developer.hashicorp.com/terraform/cli/commands/plan).

## Offizielle Referenzen zum Weiterarbeiten

| Einstieg | Referenz |
|---|---|
| Aktuelle Installation und Versionen | [Terraform installieren](https://developer.hashicorp.com/terraform/install) · [Offizielle Releases](https://releases.hashicorp.com/terraform/) |
| Sprache und CLI | [Konfigurationssprache](https://developer.hashicorp.com/terraform/language) · [CLI-Kommandos](https://developer.hashicorp.com/terraform/cli/commands) |
| Provider und Ressourcen | [Terraform Registry](https://registry.terraform.io/) · [Provider-Anforderungen](https://developer.hashicorp.com/terraform/language/providers/requirements) |
| Gezielte Upgrades | [Terraform-Upgradehinweise](https://developer.hashicorp.com/terraform/language/upgrade-guides) · [Offizielles Quellrepository](https://github.com/hashicorp/terraform) |

Die thematischen Quellen stehen zusätzlich direkt am jeweiligen Abschnitt. Bei providerspezifischen Beispielen immer die Dokumentation **der tatsächlich eingesetzten Provider-Version** lesen: Ein Argument aus der Terraform-CLI-Version lässt sich nicht automatisch auf jeden Provider übertragen.

## Verwandte Cheatsheets

- [[02-Versionierung-Entwicklung/Git-Cheatsheet|Git]] – Änderungen, Branches und Reviews.
- [[02-Versionierung-Entwicklung/GitHub-Cheatsheet|GitHub]] – Pull Requests und Automatisierung.
- [[10-Sicherheit-PKI/HashiCorp-Vault-Cheatsheet|HashiCorp Vault]] – dynamische Zugangsdaten und Geheimnisverwaltung.
- [[10-Sicherheit-PKI/OpenBao-Cheatsheet|OpenBao]] – ergänzende Geheimnisverwaltung.
- [[03-Linux-Administration/SSH-Cheatsheet|SSH]] – Authentifizierung und Verbindungen.
- [[03-Linux-Administration/Paketmanager-Cheatsheet|Paketmanager]] und [[03-Linux-Administration/Fedora-RHEL-Cheatsheet|Fedora/RHEL]] – Installation und Systemumgebung.
- [[02-Versionierung-Entwicklung/Vim-Cheatsheet|Vim]] und [[02-Versionierung-Entwicklung/Vimrc-Konfiguration-Cheatsheet|.vimrc]] – Konfigurationsdateien bearbeiten und den Editor einrichten.
- [[02-Versionierung-Entwicklung/INDEX|Versionierung und Entwicklung]] · [[/INDEX|Gesamtübersicht]].
