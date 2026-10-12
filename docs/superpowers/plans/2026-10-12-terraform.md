---
title: "Terraform – Umsetzungsplan und Veröffentlichungsnachweis"
aliases:
  - "Terraform Veröffentlichungsplan 2026-10-12"
  - "HashiCorp Terraform Cheatsheet Umsetzungsnachweis"
tags:
  - projekt/cheatsheets
  - plan/umsetzung
  - terraform
  - hashicorp
  - infrastructure-as-code
  - github-pages
type: plan
status: fertig
date: '2026-10-12'
created: '2026-10-12'
modified: '2026-10-12'
updates:
  - date: '2026-10-12'
    change: "Aktuellen main geprüft und detaillierten Plan vor der Inhaltsimplementierung angelegt."
  - date: '2026-10-12'
    change: "Terraform-Seite vollständig erstellt, geprüft und mit PR #26 veröffentlicht; erfolgreiche Validate- und Pages-Läufe samt vollständigem Prüfnachweis ergänzt."
repository: "H234598/Cheatsheets"
base_commit: "0d9539153ab52f62a42afeb41cdd607007c10bb7"
---

# Terraform – Umsetzungsplan und Veröffentlichungsnachweis

## Auftrag und Ziel

Eine zusätzliche, eigenständige deutschsprachige Fachseite **Terraform** für **HashiCorp Terraform** erstellen, in die bestehende Cheatsheet-Sammlung integrieren und über den vorhandenen GitHub-Pages-Prozess veröffentlichen. Die vollständige Markdown-Quelle und dieser fortgeschriebene Nachweis werden zur Übergabe bereitgestellt.

Die neue Seite soll sowohl als schneller Befehlszettel als auch als nachvollziehbarer Einstieg dienen. Ein vollständiges lokales Beispiel wird mit der echten Terraform-CLI geprüft. Fortgeschrittene Themen erhalten konkrete Voraussetzungen und Wirkungsgrenzen. Reale Cloud-Infrastruktur ist für die Erstellung und Prüfung der Dokumentation nicht erforderlich.

## Geprüfter Ausgangspunkt

| Aspekt | Verbindlicher Stand |
|---|---|
| Repository | [H234598/Cheatsheets](https://github.com/H234598/Cheatsheets) |
| Ausgangscommit | [`0d95391`](https://github.com/H234598/Cheatsheets/commit/0d9539153ab52f62a42afeb41cdd607007c10bb7), aktueller `main` nach der Vim-Veröffentlichung |
| Arbeitskopie | Sauberer lokaler Checkout; Remote-Branch vor der Implementierung erneut abgefragt und gefetcht |
| Bestand | 88 Fachseiten in 12 Kategorien; Zielkategorie umfasst 14 Fachseiten |
| Neue Datei | `02-Versionierung-Entwicklung/Terraform-Cheatsheet.md` |
| Seitentitel | `Terraform – Cheatsheet`, eindeutige Aliases für HashiCorp Terraform |
| Geplanter Branch | `docs/terraform-2026-10-12` |
| Neue Inhaltsversion | 2.3.0; nach Integration 89 Fachseiten und 15 Seiten in Kategorie 02 |
| Veröffentlichung | Vorhandene Validate- und Pages-Workflows; ausschließlich das erzeugte `site/`-Artefakt wird ausgeliefert |
| Produktive Zielroute | `https://cheatsheets.telacore.org/02-Versionierung-Entwicklung/Terraform-Cheatsheet/` |
| Aktuelle fachliche Basis | Terraform 1.16.5 laut offizieller Installationsseite und GitHub-Release; 1.17-Vorabversionen werden nicht als stabile Basis behandelt |

Projektregeln: [Contentmodell](../../WEB-CONTENTMODELL.md), [Webbuild](../../WEB-BUILD.md), [Downloads](../../WEB-DOWNLOADS.md), [Tests](../../WEB-TESTS.md), [Wartung](../../WEB-WARTUNG.md), [GitHub-Automation](../../../.github/README.md). Der [Vim-Veröffentlichungsnachweis](2026-10-12-vim-und-vimrc.md) dokumentiert den unmittelbar vorausgehenden Stand.

## Bekannte Betriebsgrenze

Die unmittelbar vorherige Veröffentlichung war erfolgreich. Bei der abschließenden Browserprüfung blockierte die vorgeschaltete Cloudflare-Verarbeitung die Prüfzugriffe ausdrücklich. Die bekannte Ray-ID ist `a4950c08ab37258c`; andere begrenzte HTTP-Prüfungen trafen auf eine wiederholte relative Weiterleitung zu `awsas.de/403-page.html`.

Diese Einschränkung wird als bestehende Grenze der Liveprüfung berücksichtigt. Sie verhindert nicht die autorisierte Erstellung, fachliche Prüfung, Integration oder Veröffentlichung über GitHub. Cloudflare-Schutzregeln werden für diese Inhaltsaufgabe nicht verändert oder umgangen. Das erfolgreiche Pages-Deployment wird im Abschluss belegt; die Auslieferung bis zum Browser bleibt aus dieser Prüfungsumgebung unbestätigt.

## Inhaltlicher Entwurf

### 1. Einordnung, Versionen und Installation

- Terraform-CLI, Provider, Module, Backend, State und HCP Terraform verständlich auseinanderhalten.
- Offiziell bestätigte stabile Version und Recherchetag angeben; Beispiele mit klarer Versionsanforderung versehen.
- Offizielle Installationswege für Windows, macOS sowie Fedora/RHEL und Debian/Ubuntu verlinken; Versionsprüfung, Prüfsummen und Signaturprüfung erklären, ohne einen ungeprüften Schlüssel-Fingerprint fest einzubauen.
- CLI-Version, Provider-Version und Modul-Version getrennt behandeln. `.terraform.lock.hcl` korrekt als Provider-Lockdatei erklären.

### 2. Schnellreferenz und vollständiger Einstieg

- Befehle für `version`, `init`, `fmt`, `validate`, `plan`, `apply`, `output`, `show`, `state`, `workspace`, `test` und `destroy` mit tatsächlicher Wirkung erläutern.
- Vollständiges `terraform_data`-Beispiel mit Variablen, Typprüfung, Validierung, Locals, Ressource und Output zeigen. Es verwendet den eingebauten Provider und braucht kein Cloud-Konto.
- Den Ablauf Initialisieren → Formatieren → Validieren → gespeicherten Plan lesen → Anwenden → Ergebnis prüfen → erneut planen → lokalen Übungszustand entfernen ausführbar beschreiben.
- Gespeicherte Pläne, die Bedeutung von `-detailed-exitcode`, Arbeitsverzeichnis und Shell-Unterschiede ausdrücklich erklären.

### 3. Sprache, Struktur und Wiederverwendung

- Dateien im Root-Modul, Ressource versus Datenquelle, Typen und Variablenpriorität erklären.
- Häufige Funktionen, Ausdrücke, `for_each`, `count` und stabile Ressourcenadressen zeigen.
- Provider-Konfiguration, Aliases, Abhängigkeiten und Module samt Versionierung behandeln.
- `lifecycle`, Validierungen, Vor-/Nachbedingungen und native Tests mit ihren jeweiligen Grenzen erläutern.
- Neuere Sprachfunktionen wie konstante Modulparameter nur mit aktuellen Quellen und Versionsgrenzen aufnehmen; überholte Einschränkungen nicht fortschreiben.

### 4. State und vorhandene Infrastruktur

- Bindung zwischen Ressourcenadresse und realem Objekt, Backends, Zugriffsschutz, Serialisierung und Locking erklären.
- S3-Beispiel mit explizitem `use_lockfile`; das veraltete DynamoDB-Locking korrekt einordnen.
- CLI-Workspaces von Berechtigungsisolation und HCP-Workspaces unterscheiden.
- `import`, `moved`, `removed`, Drift und `-refresh-only` mit überprüfbaren Beispielen behandeln.
- `state rm`, `state mv`, `force-unlock`, gezielte Ersetzung und Zerstörung mit ihren unmittelbaren Konsequenzen beschreiben.

### 5. Geheimnisse, Teamablauf und Fehlersuche

- `sensitive`, `ephemeral` und Write-only-Argumente unterscheiden; Plan-, State- und JSON-Ausgaben als mögliche Geheimnisträger erläutern.
- Geeignete Git-Dateien und Ausschlüsse zeigen; Lockdatei nicht versehentlich ausschließen.
- CI mit unveränderter Version, reproduzierbaren Providern, geprüftem Plan, beschränkter Artefaktaufbewahrung, geeignetem Authentifizierungsverfahren und serialisiertem Apply erklären.
- Typische Fehler nach Symptom, Ursache und nächstem sicheren Prüfschritt ordnen.
- Interne Verweise auf Git, GitHub, Vault, Betriebssystem-/Paketverwaltung und Vim ergänzen; offizielle Quellen nach Themen verlinken.

## Geplante Dateien und Integrationsentscheidungen

| Datei | Konkrete Änderung |
|---|---|
| `02-Versionierung-Entwicklung/Terraform-Cheatsheet.md` | Vollständiger neuer Fachartikel mit allen Dokumenteneigenschaften |
| `02-Versionierung-Entwicklung/INDEX.md` | Terraform genau einmal aufnehmen; Beschreibung, Seitenzahl und Quellumfang aktualisieren |
| `INDEX.md` | Kategorie- und alphabetischen Eintrag ergänzen; Gesamtzahl und Version aktualisieren |
| `00-START-HIER.md` | Neue Seite auffindbar verlinken; tatsächliche Gesamtzahlen übernehmen |
| `README.md` | Umfang, Stand und Inhaltsversion aktualisieren |
| `CHANGELOG.md` | Neue Inhaltsversion 2.3.0 dokumentieren; bestehende Historie erhalten |
| `Cheatsheet-Gesamtband.md` | Vollständigen Terraform-Artikel zusätzlich anhängen; bisherigen Inhalt vollständig erhalten |
| `scripts/validate_content.py` | Bestehenden Sollwert für Referenzseiten gezielt von 88 auf 89 erhöhen; alle Prüfregeln erhalten |
| `scripts/build_manifest.py` | Fehlende Obsidian-Pflichtfelder im ohnehin neu erzeugten `MANIFEST.md` deterministisch ergänzen; vorhandenes Tabellenformat erhalten |
| `scripts/download_sources.py` | Obsidian-Pflichtfelder des neu erzeugten Markdown-Gesamtbands aus den kanonischen Metadaten übernehmen; Inhaltsumwandlung und Codefence-Schutz erhalten |
| `MANIFEST.csv`, `MANIFEST.md`, `BUILD-REPORT.yaml`, `SHA256SUMS.txt` | Mit dem bestehenden Generator reproduzierbar neu erzeugen |
| Dieser Plan | Fortschritt, fachliche Korrekturen, Tests, PR, Commit und Deployment fortschreiben |

Alle redaktionell bearbeiteten Markdown-Dateien behalten ihre vorhandenen Informationen und erhalten mindestens `tags`, `type`, `status`, `updates`, `date`, `aliases`, `created` und `title`. Bereits vorhandene Änderungsvermerke werden erhalten und um Terraform ergänzt. Keine neue Website-Architektur und keine Abhängigkeitsaktualisierung sind erforderlich.

Vor der Integrationsänderung festgestellt: Der bisherige Manifestgenerator erzeugt nur `title`, `type`, `status` und `pages`. Da `MANIFEST.md` für diese Veröffentlichung ohnehin neu erzeugt wird, wird sein Frontmatter gezielt vervollständigt. `created` verwendet das durch die vollständige GitHub-Historie belegte Erstellungsdatum **2026-07-17**, Commit [`af0fc9057`](https://github.com/H234598/Cheatsheets/commit/af0fc9057f0a2c6d43e9bb3532acb96b1ebb9520); `date`, `modified` und der aktuelle Änderungsvermerk werden aus dem vorhandenen deterministischen Inhaltsdatum abgeleitet. Es wird keine laufzeitabhängige Uhrzeit eingeführt.

Bei der abschließenden Downloadprüfung vor der entsprechenden Codeänderung festgestellt: Der Webbuild erzeugt einen eigenen Gesamtband aus den Fachseiten, geordnet nach Kategorien, und ergänzt stabile Seitenanker. Sein bisheriger Header enthielt noch nicht alle verlangten Obsidian-Eigenschaften. Der Downloadgenerator wird deshalb ebenfalls gezielt angepasst: vorhandene Aliases, Tags, Erstellungsdatum und Änderungsvermerke des kanonischen Gesamtbands übernehmen und deterministisches Inhaltsdatum ergänzen. Die Artikelreihenfolge, Linkumwandlung und Prüfung unveränderter Code-Fences bleiben bestehen.

## Meilensteine

### M1 – Bestandsaufnahme und Plan

- [x] Lokalen Stand prüfen und aktuellen Remote-`main` bestätigen.
- [x] Kategorie und Publikationsmodell bestimmen; vorhandene Terraform-Seite ausschließen.
- [x] Offizielle Versionsquellen öffnen und fachliche Recherche parallel beginnen.
- [x] Inhalt, Dateiumfang und Prüfkriterien vor der Implementierung festhalten.
- [x] Arbeitsbranch aus dem bestätigten Ausgangscommit anlegen.

### M2 – Fachartikel und echte Terraform-Prüfung

- [x] Vollständige Seite einschließlich Querverweisen und Primärquellen schreiben.
- [x] Terraform aus einer offiziellen Quelle als temporäres Prüfwerkzeug bereitstellen und die veröffentlichte SHA256-Prüfsumme vergleichen.
- [x] Exakten Übungs-Codeblock aus dem Artikel extrahieren und mit Terraform 1.16.5 prüfen.
- [x] `init`, `fmt -check`, `validate`, Plan/Apply, gespeicherten Plan, Outputs, zweiten unveränderten Plan und Destroy im isolierten Übungsverzeichnis durchführen.
- [x] Relevante native Plan-Tests und die beschriebenen Exitcodes tatsächlich prüfen.
- [x] Unabhängigen fachlichen Review durchführen und konkrete Funde korrigieren.

### M3 – Integration und Build

- [x] Redaktionsdateien und Gesamtband ergänzen; bestehende Artikel und Metadatenhistorien erhalten.
- [x] Sollzahl im Inhaltsprüfer auf 89 setzen und kanonische Metadaten erzeugen.
- [x] Inhaltsmodell, Links, Sicherheit und Metadatenvergleich ohne blockierenden Befund abschließen.
- [x] Vorhandene vollständige Python-Test-Suite ausführen.
- [x] Strict-Build einschließlich Offlineausgabe und Downloadpaketen ausführen.
- [x] Erzeugten Seitentitel, Route, Querverweise und tatsächliche ZIP-Mitglieder prüfen.
- [x] Diff und Git-Baum vor der Übergabe an GitHub abschließend prüfen.

### M4 – Veröffentlichung

- [x] Geprüften Branch und Commit auf GitHub bereitstellen; Remote-Baum mit lokalem Baum vergleichen.
- [x] Pull Request mit konkretem Zweck, Inhalt und Nachweisen eröffnen.
- [x] CI und eingereichte Reviews prüfen; relevante neue Funde bearbeiten.
- [x] Den geprüften PR im Rahmen des Veröffentlichungsauftrags zusammenführen.
- [x] Validate und Pages auf dem resultierenden `main` bis zum Abschluss verfolgen.
- [x] Veröffentlichte Route und Artefakte nachweisen; bekannte Cloudflare-Grenze bei der Liveprüfung ausdrücklich dokumentieren.
- [x] Vollständigen Abschlussnachweis und Fachartikel zur Download-Übergabe fertigstellen.

## Prüfstrategie und Erfolgskriterien

| Prüffrage | Aussagekräftiger Nachweis |
|---|---|
| Ist die technische Basis aktuell? | Offizielle Installationsseite und stabiles Release stimmen überein; Vorabversionen getrennt |
| Ist das Beispiel kopierbar? | Exakt veröffentlichter HCL-Code wird formatiert, validiert und mit echtem Terraform ausgeführt |
| Ist der Ablauf korrekt? | Plan mit Änderungen, gespeicherter Apply, erwartete Outputs, No-op-Plan und vollständiges lokales Destroy |
| Sind Terraform-Tests richtig beschrieben? | Ausdrückliches `command = plan`; positive und negative Vertragsprüfung, keine Cloudressourcen |
| Sind sensible Wirkungen korrekt eingeordnet? | Unabhängiges Gegenlesen von State, Plan, Locking, Workspaces, Import und Geheimnissen |
| Ist die neue Seite vollständig integriert? | 89 reale Fachseiten, eindeutige Navigation, bytegleiche Metadaten und vollständiger Gesamtband |
| Funktioniert die Website weiter? | Bestehende 132 Python-Tests sowie reguläre Browser-/Mobil-/Accessibility-CI |
| Ist wirklich veröffentlicht? | Zusammengeführter PR, erfolgreicher Pages-Lauf und eindeutiger Quellcommit |
| Was bleibt gegebenenfalls offen? | Live-Auslieferung aus einer von Cloudflare gesperrten Prüfungsumgebung wird nicht als erfolgreich behauptet |

## Fortschritt und Nachweise

Dieser Abschnitt enthält tatsächlich beobachtete Ergebnisse einschließlich der erfolgreichen Veröffentlichung und der nachgelagerten CI auf dem Mergecommit.

### Inhalt und Review

- Die zusätzliche Seite enthält vollständige Obsidian-Eigenschaften, ein verlinktes Inhaltsverzeichnis, nachvollziehbare lokale Beispiele und Primärquellen bei den Fachthemen.
- Alle bisherigen 88 Fachseiten bleiben unverändert; der vollständige neue Artikel wird dem Gesamtband zusätzlich angehängt.
- Der tatsächliche Integrationsvergleich bestätigt die unveränderten Bytes aller 88 bisherigen Fachseiten, des vollständigen bisherigen Gesamtband-Inhalts und der bisherigen Changelog-Historie. Alle bearbeiteten Markdown-Dateien haben die verlangten Pflichtfelder; bestehende `created`-Werte und `updates`-Einträge bleiben erhalten.
- Ein unabhängiger Review erkannte ein falsch abgeleitetes Erstellungsdatum des Manifests: Der lokale Checkout ist shallow und zeigte an seiner Historiengrenze fälschlich eine Erstanlage am 12. August. Die vollständige GitHub-Dateihistorie belegt den **17. Juli 2026**. Generator und Plan wurden entsprechend korrigiert.

- Der fachliche Review erkannte die Ausnahme für Ephemeral-Inputs beim gespeicherten Apply. Die zunächst pauschale Aussage zu nachträglichen Variablen wurde auf gewöhnliche persistierte Inputs begrenzt; erneuerte kurzlebige Laufzeitwerte für Plan und Apply werden nun ausdrücklich beschrieben. Die Korrektur beruht auf der offiziellen Ephemeral-Dokumentation und einer unabhängigen Reproduktion mit Terraform 1.16.5.
- Der erste Build wurde vor der Git-Aufnahme der neuen Quelle regelkonform gestoppt. Nach dem Staging fand der Strict-Offline-Build einen nicht umgeschriebenen relativen Link `../INDEX.md`; der Artikel verwendet jetzt den vorhandenen absoluten Obsidian-Verweis `[[/INDEX|Gesamtübersicht]]`. Die Link- und Inhaltsprüfungen sind nach dieser Korrektur erneut fehler- und warnungsfrei.

### Bereitgestellte Terraform-CLI

- Version: **1.16.5**, Plattform `linux_amd64`; temporär und ohne globale Installation bereitgestellt.
- Offizielles Archiv: [terraform_1.16.5_linux_amd64.zip](https://releases.hashicorp.com/terraform/1.16.5/terraform_1.16.5_linux_amd64.zip), 36.363.219 Bytes.
- Die SHA256-Prüfsumme stimmt mit der [offiziellen Prüfsummendatei](https://releases.hashicorp.com/terraform/1.16.5/terraform_1.16.5_SHA256SUMS) überein: `2bc2fcfff033265c9e02ca0351f01794eb122f62a9b2a49a3294b9e49eaab5e4`. Die Bereitstellung prüfte HTTPS-Herkunft und SHA256; eine zusätzliche GPG-Signaturprüfung wurde dabei nicht ausgeführt.
- Ausführung in getrennten temporären Projektverzeichnissen mit einer eigenen leeren CLI-Konfiguration und `CHECKPOINT_DISABLE=1`. Ausschließlich `terraform.io/builtin/terraform`, kein externer Provider und keine Cloudressource.

### Exakte geprüfte Artikelblöcke

| Datei im Übungsprojekt | Zeilen | Bytes | SHA256 |
|---|---:|---:|---|
| `main.tf` | 43 | 941 | `dfcd95ba087a8fc4a78acc89bd77ea51d80dec9684373467caf3aadc9f5bbf04` |
| `tests/demo.tftest.hcl` | 28 | 556 | `315b6f208fdabd7ba6aef6c40222144ec73b5d55cfd45434eaaf78fcd618c303` |

Die Prüfsummen wurden nach dem Zusammenführen und Verlinken des Artikels nochmals gegen seine tatsächlichen Code-Fences verglichen. Beide Codeblöcke sind unverändert. Insgesamt wurden **25 tatsächliche CLI-Aufrufe** mit **61 erfolgreichen Assertions** und **zwei bestandenen nativen Testläufen** ausgeführt.

### Lokaler Lebenszyklus: vollständiger Befehlsnachweis

Zeitraum (UTC): `2026-10-12T09:38:33.838644+00:00` bis `2026-10-12T09:38:34.932786+00:00`. **19 Aufrufe, 40 Assertions, keine Fehler.**

| Nr. | Tatsächlich ausgeführter Befehl | Erwarteter Exitcode | Gemessener Exitcode |
|---:|---|---:|---:|
| 1 | `terraform version -json` | 0 | 0 |
| 2 | `terraform init -input=false -no-color` | 0 | 0 |
| 3 | `terraform fmt -check -diff -no-color` | 0 | 0 |
| 4 | `terraform validate -json` | 0 | 0 |
| 5 | `terraform plan -input=false -no-color -detailed-exitcode -out=tfplan` | 2 | 2 |
| 6 | `terraform show -json tfplan` | 0 | 0 |
| 7 | `terraform apply -input=false -no-color tfplan` | 0 | 0 |
| 8 | `terraform output -raw name` | 0 | 0 |
| 9 | `terraform state list` | 0 | 0 |
| 10 | `terraform show -json` | 0 | 0 |
| 11 | `terraform plan -input=false -no-color -detailed-exitcode -out=noop.tfplan` | 0 | 0 |
| 12 | `terraform plan -input=false -no-color -detailed-exitcode -var=environment=prod` | 1 | 1 |
| 13 | `terraform plan -input=false -no-color -detailed-exitcode -replace=terraform_data.demo -out=replace.tfplan` | 2 | 2 |
| 14 | `terraform show -json replace.tfplan` | 0 | 0 |
| 15 | `terraform plan -destroy -input=false -no-color -detailed-exitcode -out=destroy.tfplan` | 2 | 2 |
| 16 | `terraform show -json destroy.tfplan` | 0 | 0 |
| 17 | `terraform apply -input=false -no-color destroy.tfplan` | 0 | 0 |
| 18 | `terraform state list` | 0 | 0 |
| 19 | `terraform state pull` | 0 | 0 |

#### Vollständige Assertions

| Nr. | Prüfung | Erwartet | Gemessen | Ergebnis |
|---:|---|---|---|---|
| 1 | version: exit code | `0` | `0` | bestanden |
| 2 | Terraform version | `"1.16.5"` | `"1.16.5"` | bestanden |
| 3 | init: exit code | `0` | `0` | bestanden |
| 4 | fmt-check: exit code | `0` | `0` | bestanden |
| 5 | validate: exit code | `0` | `0` | bestanden |
| 6 | validate valid | `true` | `true` | bestanden |
| 7 | validate errors | `0` | `0` | bestanden |
| 8 | validate warnings | `0` | `0` | bestanden |
| 9 | plan-create: exit code | `2` | `2` | bestanden |
| 10 | show-create-plan: exit code | `0` | `0` | bestanden |
| 11 | create resource addresses | `["terraform_data.demo"]` | `["terraform_data.demo"]` | bestanden |
| 12 | create actions | `["create"]` | `["create"]` | bestanden |
| 13 | built-in provider | `"terraform.io/builtin/terraform"` | `"terraform.io/builtin/terraform"` | bestanden |
| 14 | apply-saved-create-plan: exit code | `0` | `0` | bestanden |
| 15 | output-name: exit code | `0` | `0` | bestanden |
| 16 | output name | `"cheatsheets-lab"` | `"cheatsheets-lab"` | bestanden |
| 17 | state-list-created: exit code | `0` | `0` | bestanden |
| 18 | created state addresses | `["terraform_data.demo"]` | `["terraform_data.demo"]` | bestanden |
| 19 | show-state-created: exit code | `0` | `0` | bestanden |
| 20 | created state resource count | `1` | `1` | bestanden |
| 21 | created state object name | `"cheatsheets-lab"` | `"cheatsheets-lab"` | bestanden |
| 22 | created state object environment | `"lab"` | `"lab"` | bestanden |
| 23 | plan-noop: exit code | `0` | `0` | bestanden |
| 24 | plan-invalid-environment: exit code | `1` | `1` | bestanden |
| 25 | invalid environment explanation | `true` | `true` | bestanden |
| 26 | plan-replace: exit code | `2` | `2` | bestanden |
| 27 | show-replace-plan: exit code | `0` | `0` | bestanden |
| 28 | replace resource addresses | `["terraform_data.demo"]` | `["terraform_data.demo"]` | bestanden |
| 29 | replace actions | `["delete","create"]` | `["delete","create"]` | bestanden |
| 30 | plan-destroy: exit code | `2` | `2` | bestanden |
| 31 | show-destroy-plan: exit code | `0` | `0` | bestanden |
| 32 | destroy resource addresses | `["terraform_data.demo"]` | `["terraform_data.demo"]` | bestanden |
| 33 | destroy actions | `["delete"]` | `["delete"]` | bestanden |
| 34 | apply-saved-destroy-plan: exit code | `0` | `0` | bestanden |
| 35 | state-list-destroyed: exit code | `0` | `0` | bestanden |
| 36 | destroyed state list empty | `""` | `""` | bestanden |
| 37 | state-pull-destroyed: exit code | `0` | `0` | bestanden |
| 38 | destroyed state resources empty | `[]` | `[]` | bestanden |
| 39 | destroyed state outputs empty | `{}` | `{}` | bestanden |
| 40 | original code unchanged | `"dfcd95ba087a8fc4a78acc89bd77ea51d80dec9684373467caf3aadc9f5bbf04"` | `"dfcd95ba087a8fc4a78acc89bd77ea51d80dec9684373467caf3aadc9f5bbf04"` | bestanden |

### Native Terraform-Tests: vollständiger Befehlsnachweis

Zeitraum (UTC): `2026-10-12T09:41:15.888808+00:00` bis `2026-10-12T09:41:16.390408+00:00`. **6 Aufrufe, 21 Assertions, keine Fehler.**

| Nr. | Tatsächlich ausgeführter Befehl | Erwarteter Exitcode | Gemessener Exitcode |
|---:|---|---:|---:|
| 1 | `terraform version -json` | 0 | 0 |
| 2 | `terraform init -input=false -no-color` | 0 | 0 |
| 3 | `terraform fmt -check -diff -recursive -no-color` | 0 | 0 |
| 4 | `terraform validate -json` | 0 | 0 |
| 5 | `terraform test -json -no-color` | 0 | 0 |
| 6 | `terraform show -json` | 0 | 0 |

#### Vollständige Assertions

| Nr. | Prüfung | Erwartet | Gemessen | Ergebnis |
|---:|---|---|---|---|
| 1 | same main.tf as previous smoke test | `"dfcd95ba087a8fc4a78acc89bd77ea51d80dec9684373467caf3aadc9f5bbf04"` | `"dfcd95ba087a8fc4a78acc89bd77ea51d80dec9684373467caf3aadc9f5bbf04"` | bestanden |
| 2 | two test runs | `["name_und_umgebung","produktion_ist_im_labor_unzulaessig"]` | `["name_und_umgebung","produktion_ist_im_labor_unzulaessig"]` | bestanden |
| 3 | only plan test commands | `["plan","plan"]` | `["plan","plan"]` | bestanden |
| 4 | version: exit code | `0` | `0` | bestanden |
| 5 | Terraform version | `"1.16.5"` | `"1.16.5"` | bestanden |
| 6 | init: exit code | `0` | `0` | bestanden |
| 7 | fmt-check: exit code | `0` | `0` | bestanden |
| 8 | validate: exit code | `0` | `0` | bestanden |
| 9 | validate valid | `true` | `true` | bestanden |
| 10 | validate error count | `0` | `0` | bestanden |
| 11 | validate warning count | `0` | `0` | bestanden |
| 12 | native-test: exit code | `0` | `0` | bestanden |
| 13 | two completed test runs | `2` | `2` | bestanden |
| 14 | all completed runs passed | `["pass","pass"]` | `["pass","pass"]` | bestanden |
| 15 | no native test errors | `[]` | `[]` | bestanden |
| 16 | show-state-after-test: exit code | `0` | `0` | bestanden |
| 17 | no resources after tests | `[]` | `[]` | bestanden |
| 18 | no outputs after tests | `{}` | `{}` | bestanden |
| 19 | no state files left by plan-only tests | `[]` | `[]` | bestanden |
| 20 | main.tf unchanged | `"dfcd95ba087a8fc4a78acc89bd77ea51d80dec9684373467caf3aadc9f5bbf04"` | `"dfcd95ba087a8fc4a78acc89bd77ea51d80dec9684373467caf3aadc9f5bbf04"` | bestanden |
| 21 | test file unchanged | `"315b6f208fdabd7ba6aef6c40222144ec73b5d55cfd45434eaaf78fcd618c303"` | `"315b6f208fdabd7ba6aef6c40222144ec73b5d55cfd45434eaaf78fcd618c303"` | bestanden |

Der Lebenszyklustest endete nach dem Destroy mit leerer Ressourcen- und Outputliste. Die beiden nativen Plan-Tests hinterließen weder State-Dateien noch Ressourcen oder Outputs. Der negative Test besteht, weil die benannte Input-Validierung `environment = "prod"` erwartungsgemäß ablehnt.

### Unabhängiger Sonderfalltest: Ephemeral-Input beim gespeicherten Apply

Der unabhängige fachliche Review ist abgeschlossen. Beide konkreten Befunde wurden korrigiert und gegengelesen; im beauftragten Scope bestehen keine weiteren wesentlichen Befunde.

Die allgemeine Apply-Dokumentation beschreibt die Ephemeral-Ausnahme nicht vollständig. Der zusätzlich gelesene [Quellcode von Terraform 1.16.5](https://github.com/hashicorp/terraform/blob/v1.16.5/internal/backend/local/backend_apply.go#L291-L394) belegt sie unmittelbar: erneut übergebene ephemere Werte werden für Apply übernommen; gewöhnliche persistierte Werte werden mit dem gespeicherten Plan verglichen. Beim Planen gesetzte Ephemeral-Inputs müssen auch bei Apply gesetzt sein. Der Artikel verlinkt diesen versionsgenauen Primärbeleg.

Der Review führte **vier zusätzliche CLI-Aufrufe**, jeweils mit Exitcode **0**, unabhängig von den oben dokumentierten 25 Aufrufen aus. Die folgende Aufzeichnung transkribiert die tatsächlich beobachteten Befehle und Ergebnisse; sie wird nicht als ursprüngliches Rohlog ausgegeben. Es wurden ausschließlich synthetische Werte `before` und `after`, lokaler State, der eingebaute Provider und ein `true`-Provisioner verwendet. Keine AWS-, Remote-State- oder echten Zugangsdatenabfragen.

**Exakte Konfiguration des Sonderfalltests:**

```hcl
terraform {
  required_version = "~> 1.16.0"
}
variable "api_token" {
  type = string
  sensitive = true
  ephemeral = true
}
resource "terraform_data" "demo" {
  input = "local-only"
  provisioner "local-exec" {
    command = "true"
    environment = { DEMO_TOKEN = var.api_token }
  }
}
```

SHA256: `3132042ae2b9af85c15a7dab76dffce375bacb6482e1aac37e63fa8643a03be9`. Terraform 1.16.5; eigene leere CLI-Konfiguration, `CHECKPOINT_DISABLE=1` und `TF_IN_AUTOMATION=1`.

| Nr. | Tatsächlich ausgeführter Befehl | Exitcode | Beobachtetes Ergebnis |
|---:|---|---:|---|
| 1 | `terraform version` | 0 | Terraform v1.16.5 on linux_amd64 |
| 2 | `terraform init -input=false -no-color` | 0 | Initialization successful using the built-in terraform provider. |
| 3 | `terraform plan -input=false -no-color -var=api_token=before -out=saved.tfplan` | 0 | Saved plan created for one local terraform_data.demo resource. |
| 4 | `terraform apply -input=false -no-color -var=api_token=after saved.tfplan` | 0 | Saved plan applied without a confirmation prompt; one terraform_data.demo resource created. Provisioner output was suppressed due to sensitive and ephemeral values. |

Der gelesene lokale State enthielt anschließend ausschließlich `terraform_data.demo`. Das bestätigt die Annahme eines geänderten, nicht-nullwertigen Ephemeral-Inputs beim gespeicherten Apply; es ist kein Nachweis für das Verhalten eines realen Cloud-Providers.

### Repository-Validierung

- Kanonische Metadaten reproduzierbar und aktuell.
- Inhaltsinventur: **89 Fachseiten, 12 Kategorien, 0 Fehler, 0 Warnungen**.
- Linkvalidierung: **0 Fehler, 0 Warnungen**.
- Sicherheitsvalidierung: keine blockierenden Befunde.
- Vollständige Python-Test-Suite: **132 bestanden**.
- Die beiden Generatoren ergänzen jetzt die Pflichtfelder auch in `MANIFEST.md` und im automatisch erzeugten Markdown-Gesamtband. Der Gesamtband übernimmt bestehende Obsidian-Eigenschaften des kanonischen Dokuments; der Quellen- und Codefence-Schutz bleibt erhalten.
- Strict-Build und Artefaktprüfung erfolgreich; die Remote-CI ist sowohl auf dem Pull Request als auch auf dem Mergecommit erfolgreich abgeschlossen.


### Abschließender Build und Downloads

- Finaler Strict-Build erfolgreich: **108 HTML-Quellseiten**.
- Gebauter Seitentitel: `Terraform – Cheatsheet - Cheatsheets`.
- Route: `02-Versionierung-Entwicklung/Terraform-Cheatsheet/`.
- Fachartikel: **805 Zeilen**, **58213 Bytes**, SHA256 `1232215ee0a726c9692824a27db5a5fc0b7637fe7d42ecd42ce1e6ef3cfb3372`.
- **27 Codeblöcke** sind in Online-HTML, Offline-HTML und dem neu erzeugten Markdown-Gesamtband inhaltlich unverändert. Der Gesamtband führt außerdem den passenden Quell-SHA-256 des Artikels.
- Das Quellarchiv enthält `02-Versionierung-Entwicklung/Terraform-Cheatsheet.md` bytegleich zur Quelle; das Offlinearchiv enthält `02-Versionierung-Entwicklung/Terraform-Cheatsheet.html`.
- Der Quelllink auf GitHub und die bestehende Downloadzentrale sind verknüpft. Das Quellarchiv und der Gesamtband sind über die Downloadzentrale erreichbar; es wird kein zusätzlicher Einzeldatei-Download auf der Fachseite behauptet.
- Offlinepaket unabhängig geprüft: **187 Dateien**, **38.441 lokale Referenzen**, Baum-SHA-256 `06ce7afb32cd7261d5fae732f0251bea83df8669eaade778266eee583ff20823`.
- Pages-Artefakt: **186 Dateien**, **42.015.540 Bytes**, Baum-SHA-256 `d8de39fb9a8d03498ae0b62171a77afe1b0845f0563df7a7bbd005a3df24a689`.
- Webbudgets eingehalten: **116 HTML-Dateien**, JavaScript **9.067 Gzip-Bytes**, CSS **2.325 Gzip-Bytes**, keine externen Laufzeitassets.
- Zusätzlicher unabhängiger Generatorreview: gesamter Gesamtband-Text nach Frontmatter unverändert; bisherige Kopfzeilen samt Quotierung erhalten; vorhandene Obsidian-Eigenschaften vollständig übernommen; zwei Renderdurchläufe bytegleich.
- Die lokalen Artefakte wurden vor dem Commit erzeugt; ihr Provenienzheader benennt deshalb noch den Ausgangscommit. Die GitHub-CI hat die veröffentlichten Artefakte aus dem tatsächlichen Veröffentlichungscommit neu erzeugt; deren Nachweise stehen im folgenden Abschnitt.
- Die Browser-/Mobil-/Accessibility-Prüfung wurde in der regulären GitHub-CI mit **9 bestandenen Tests** abgeschlossen. Der lokale Chromium-Download war bereits in der vorangegangenen Aufgabe fehlgeschlagen; ein lokaler Browser-Test wird nicht als bestanden ausgegeben.

### Veröffentlichung

- Pull Request: [#26 – HashiCorp Terraform als vollständige Fachseite ergänzen](https://github.com/H234598/Cheatsheets/pull/26).
- Geprüfter PR-Quellcommit: [`fae183f`](https://github.com/H234598/Cheatsheets/commit/fae183f4e85bfdf4a14702a814f328e3b8e04f36).
- Der GitHub-Git-Baum `115188064ae0683f396e33682e2bfb9a7a59760f` stimmt exakt mit dem lokal geprüften Baum überein; der Remote-Branch wurde anschließend gefetcht und ohne Inhaltsdifferenz übernommen.
- PR-Validierung: [Validate 38233305798](https://github.com/H234598/Cheatsheets/actions/runs/38233305798), **abgeschlossen und erfolgreich** auf dem geprüften PR-Quellcommit. **132 Python-Tests und 9 Browser-, Mobil- und Accessibility-Tests bestanden**; alle 26 Jobschritte erfolgreich.
- Die Qlty-Prüfung war vor dem Merge erfolgreich. CodeRabbit stand zu diesem Zeitpunkt noch auf `pending`; es waren keine Reviews oder Review-Threads eingereicht. Für diesen Branch bestand kein verpflichtendes CodeRabbit-Gate. Der oben dokumentierte unabhängige fachliche und technische Review war abgeschlossen, seine beiden Befunde waren korrigiert.
- PR #26 wurde im Rahmen des ausdrücklich erteilten Veröffentlichungsauftrags per Squash zusammengeführt. Mergecommit: [`07402749b31eb93cd53316d43b597de60b4f5e2d`](https://github.com/H234598/Cheatsheets/commit/07402749b31eb93cd53316d43b597de60b4f5e2d).
- Der gefetchte Mergecommit hat denselben Git-Baum `115188064ae0683f396e33682e2bfb9a7a59760f` wie der geprüfte PR-Commit. Die Integration hat den geprüften Inhalt nicht verändert.

| Nachweis auf dem veröffentlichten Mergecommit | Ergebnis |
|---|---|
| [Validate 38233681818](https://github.com/H234598/Cheatsheets/actions/runs/38233681818) | `completed / success`; 132 Python-Tests und 9 Browser-, Mobil- und Accessibility-Tests bestanden |
| Inhalts- und Linkprüfung | 89 Fachseiten in 12 Kategorien, jeweils 0 Fehler und 0 Warnungen |
| Strict-Build | 108 HTML-Quellseiten erfolgreich gebaut |
| [Pages 38233681768](https://github.com/H234598/Cheatsheets/actions/runs/38233681768) | `completed / success`; Build und produktives Deployment erfolgreich |
| Produktives Pages-Artefakt | 186 Dateien, 42.012.899 Bytes, Baum-SHA-256 `31b92a20b8859effd7bbc9f743edf201aa578f5a4b168702a5f237846a6324dc` |
| Artefakt-Upload | [github-pages, ID 11739916119](https://github.com/H234598/Cheatsheets/actions/runs/38233681768/artifacts/11739916119); Upload-SHA256 `9502c622ac58c2beda007ceb4f879a36e644fa642cf5569990c503425ae54ad8` |
| Deployment-Protokoll | `pages_build_version` und Deployment-ID zeigen auf `07402749b31eb93cd53316d43b597de60b4f5e2d`; GitHub meldete `Reported success!` am 12.10.2026 um 10:03:37 UTC |
| Neue Fachseite | [Terraform – Cheatsheet](https://cheatsheets.telacore.org/02-Versionierung-Entwicklung/Terraform-Cheatsheet/) |
| GitHub-Quelle | [Terraform-Cheatsheet.md](https://github.com/H234598/Cheatsheets/blob/main/02-Versionierung-Entwicklung/Terraform-Cheatsheet.md) |

Der Validate-Build mit dem Project-Page-Testpfad und der produktive Pages-Build verwenden unterschiedliche Website-Basis-URLs. Ihre Artefaktgrößen und Baum-Prüfsummen unterscheiden sich dadurch erwartungsgemäß. Das produktiv hochgeladene und erfolgreich ausgerollte Artefakt stammt aus dem oben verlinkten Pages-Lauf.

**Ergebnis:** Terraform ist als 89. Fachseite in Inhaltsversion **2.3.0** integriert und über den vorhandenen Pages-Prozess veröffentlicht. Navigation, Gesamtband, Manifest, Prüfsummen sowie Online-, Offline- und Quell-Downloads enthalten den neuen Artikel. Die vorhandenen 88 Fachseiten und die bisherige Dokumenthistorie wurden erhalten.

**Grenze der Liveprüfung:** Der erfolgreiche GitHub-Pages-Rollout ist belegt. Wegen der bereits ausdrücklich beobachteten Cloudflare-Sperre wurde kein weiterer automatisierter Zugriff auf die neue öffentliche Route versucht. Die Auslieferung der Terraform-Seite bis zum Browser dieser Prüfungsumgebung wird deshalb nicht als geprüft behauptet. Es wurden keine Cloudflare-Regeln verändert und keine Sperren umgangen.

Dieser Abschlussnachweis dokumentiert die ursprüngliche Inhaltsveröffentlichung. Seine anschließende Ablage auf `main` ist eine reine Dokumentationsergänzung; sie verändert den Fachartikel nicht. Die dadurch erneut gestarteten regulären Workflows werden vor der Übergabe ebenfalls bis zum erfolgreichen Abschluss verfolgt.

## Primärquellen für die Umsetzung

- [Offizielle Terraform-Installation](https://developer.hashicorp.com/terraform/install).
- [Terraform v1.16.5](https://github.com/hashicorp/terraform/releases/tag/v1.16.5).
- [Terraform-Konfigurationssprache](https://developer.hashicorp.com/terraform/language).
- [Terraform-CLI](https://developer.hashicorp.com/terraform/cli).
- [State](https://developer.hashicorp.com/terraform/language/state).
- [Umgang mit sensiblen Werten](https://developer.hashicorp.com/terraform/language/manage-sensitive-data).

Recherche- und Umsetzungstag: **12. Oktober 2026**. Der Fachartikel erhält zusätzliche Quellen unmittelbar bei den jeweiligen Themen.
