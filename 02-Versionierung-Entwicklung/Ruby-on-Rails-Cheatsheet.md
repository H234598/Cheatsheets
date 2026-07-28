---
title: "Ruby on Rails – Cheatsheet"
aliases: ["Rails Cheatsheet", "RoR", "Ruby Rails"]
created: 2026-07-17
modified: 2026-07-17
type: reference
status: fertig
tags: [ruby, rails, web-development, mvc, active-record]
source: "https://guides.rubyonrails.org/getting_started.html"
---

# Ruby on Rails – Cheatsheet

> [!abstract] Zweck
> Praxisreferenz für moderne Rails-Anwendungen: Projektstruktur, MVC, Routing, Active Record, Migrationen, Controller/Views, Jobs, Tests, Sicherheit, Performance und Deployment.

> [!note]
> Beispiele orientieren sich an modernem Rails. Generatorausgaben und Defaults ändern sich zwischen Hauptversionen; `bin/rails --help` und die Guides der eingesetzten Version sind maßgeblich.

## Inhalt

- [[#Installation und neues Projekt]]
- [[#Projektstruktur]]
- [[#Request-Lebenszyklus und MVC]]
- [[#Routing]]
- [[#Active Record]]
- [[#Migrationen]]
- [[#Controller und Views]]
- [[#Konfiguration, Credentials und Umgebungen]]
- [[#Jobs, Mail und Storage]]
- [[#Tests und Diagnose]]
- [[#Sicherheit und Performance]]
- [[#Deployment-Checkliste]]

## Installation und neues Projekt

Ruby über Versionsmanager wie `mise`, `asdf` oder `rbenv` verwalten; System-Ruby nicht ungeprüft für Projekte verwenden.

```bash
ruby --version
gem --version
bundle --version
rails --version
```

Rails installieren:

```bash
gem install rails
```

Projekt mit PostgreSQL:

```bash
rails new shop --database=postgresql
cd shop
bin/rails db:create
bin/rails server
```

API-only:

```bash
rails new api --api --database=postgresql
```

Hilfen:

```bash
bin/rails --help
bin/rails generate --help
bin/rails routes --help
```

## Projektstruktur

```text
app/
├── controllers/
├── models/
├── views/
├── jobs/
├── mailers/
├── channels/
├── helpers/
└── assets/javascript...
config/
├── routes.rb
├── database.yml
├── environments/
└── initializers/
db/
├── migrate/
├── schema.rb oder structure.sql
└── seeds.rb
lib/
test/ oder spec/
public/
storage/
```

| Pfad | Zweck |
|---|---|
| `app/` | Anwendungslogik und UI |
| `config/` | Laufzeit-, Routing- und Frameworkkonfiguration |
| `db/migrate` | versionierte Schemaänderungen |
| `bin/` | projektgebundene Executables |
| `Gemfile` | Dependencies |
| `Gemfile.lock` | exakt aufgelöste Dependencyversionen |

## Request-Lebenszyklus und MVC

```text
HTTP Request
  → Router
  → Controller Action
  → Model/Service/Query
  → View/Serializer
  → HTTP Response
```

- **Model:** Domänendaten, Validierungen, Beziehungen, fachnahe Logik.
- **View:** Darstellung, keine komplexe Datenbanklogik.
- **Controller:** Orchestriert Request/Response, sollte schlank bleiben.

Generator:

```bash
bin/rails generate scaffold Product name:string price:decimal active:boolean
bin/rails db:migrate
```

Für Lernzwecke praktisch, produktiv Generatorausgabe prüfen und unnötige Felder/Routes entfernen.

## Routing

`config/routes.rb`:

```ruby
Rails.application.routes.draw do
  root "products#index"
  resources :products

  namespace :admin do
    resources :products
  end

  get "/health", to: "health#show"
end
```

Routen ansehen:

```bash
bin/rails routes
bin/rails routes -g product
bin/rails routes --expanded
```

REST-Konvention:

| Verb | Pfad | Aktion |
|---|---|---|
| GET | `/products` | index |
| GET | `/products/:id` | show |
| GET | `/products/new` | new |
| POST | `/products` | create |
| GET | `/products/:id/edit` | edit |
| PATCH/PUT | `/products/:id` | update |
| DELETE | `/products/:id` | destroy |

Nur benötigte Routen:

```ruby
resources :products, only: %i[index show create]
```

## Active Record

### Beziehungen

```ruby
class Order < ApplicationRecord
  belongs_to :customer
  has_many :line_items, dependent: :destroy
  has_many :products, through: :line_items
end
```

### Validierungen

```ruby
class Product < ApplicationRecord
  validates :name, presence: true, length: { maximum: 200 }
  validates :price, numericality: { greater_than_or_equal_to: 0 }
  validates :sku, uniqueness: { case_sensitive: false }
end
```

> [!important]
> Anwendungsvalidierung ersetzt keine Datenbankconstraints. Kritische Eindeutigkeit, NOT NULL und Fremdschlüssel zusätzlich in der Datenbank absichern.

### Abfragen

```ruby
Product.where(active: true)
       .where("price >= ?", 10)
       .order(:name)
       .limit(50)
```

```ruby
Product.find(params[:id])
Product.find_by(sku: params[:sku])
Product.find_by!(sku: params[:sku])
```

N+1 vermeiden:

```ruby
Order.includes(:customer, :line_items).where(status: "open")
```

Nur benötigte Spalten:

```ruby
Product.where(active: true).pluck(:id, :name)
```

Transaktion:

```ruby
ApplicationRecord.transaction do
  order.update!(status: "paid")
  Payment.create!(order:, amount: order.total)
end
```

Callbacks sparsam; komplexe Prozesslogik besser explizit in Serviceobjekten/Jobs orchestrieren.

## Migrationen

```bash
bin/rails generate migration AddSkuToProducts sku:string
bin/rails db:migrate
bin/rails db:rollback
bin/rails db:migrate:status
```

Beispiel:

```ruby
class AddSkuToProducts < ActiveRecord::Migration[8.1]
  def change
    add_column :products, :sku, :string
    add_index :products, :sku, unique: true
  end
end
```

### Sichere Produktionsmigration

Bei großen Tabellen:

1. nullable/spärliche Spalte hinzufügen
2. Anwendung dual lesen/schreiben lassen
3. Daten in Batches backfillen
4. Constraint validieren
5. NOT NULL/Index kontrolliert setzen
6. alte Spalte/Logik in späterem Release entfernen

> [!danger]
> Umbenennen, Typwechsel, Default mit Tabellenrewrite und Indexbau können sperren. Datenbankversion und Online-DDL-Möglichkeiten prüfen; Migration vor Produktionslauf mit realistischem Datenvolumen testen.

Schemaformat:

- `schema.rb`: portabel, Ruby-Darstellung
- `structure.sql`: vollständiger DB-spezifischer Zustand, nötig bei Views/Extensions/komplexen Features

## Controller und Views

### Controller

```ruby
class ProductsController < ApplicationController
  before_action :set_product, only: %i[show update destroy]

  def index
    @products = Product.where(active: true).order(:name)
  end

  def create
    product = Product.new(product_params)
    if product.save
      redirect_to product, notice: "Produkt angelegt"
    else
      render :new, status: :unprocessable_entity
    end
  end

  private

  def set_product
    @product = Product.find(params[:id])
  end

  def product_params
    params.require(:product).permit(:name, :price, :active)
  end
end
```

Strong Parameters begrenzen Mass Assignment, ersetzen aber keine Autorisierung.

### View

```erb
<%= form_with model: @product do |form| %>
  <%= form.label :name %>
  <%= form.text_field :name %>
  <%= form.submit %>
<% end %>
```

Partials:

```erb
<%= render @products %>
```

### JSON/API

Statuscodes korrekt verwenden:

```ruby
render json: product, status: :created
render json: { error: "ungültig" }, status: :unprocessable_entity
head :no_content
```

## Konfiguration, Credentials und Umgebungen

```bash
bin/rails credentials:edit
bin/rails credentials:show
bin/rails runner 'puts Rails.env'
```

Master Key/Environment Key nie committen. Produktionssecrets vorzugsweise aus Secret Manager/Umgebungsintegration beziehen.

Konfiguration:

```ruby
# config/environments/production.rb
config.force_ssl = true
config.log_level = ENV.fetch("RAILS_LOG_LEVEL", "info")
```

Umgebungsvariablen:

```bash
RAILS_ENV=production bin/rails runner 'puts Product.count'
```

## Jobs, Mail und Storage

### Active Job

```bash
bin/rails generate job RecalculateReport
```

```ruby
class RecalculateReportJob < ApplicationJob
  queue_as :default

  retry_on Net::ReadTimeout, wait: :polynomially_longer, attempts: 5

  def perform(report_id)
    Report.find(report_id).recalculate!
  end
end
```

Jobs müssen idempotent und retry-tauglich sein. Externe Nebenwirkungen mit stabilen Schlüsseln absichern.

Aufruf:

```ruby
RecalculateReportJob.perform_later(report.id)
```

### Active Storage

```bash
bin/rails active_storage:install
bin/rails db:migrate
```

Dateityp, Größe, Malwareprüfung, Zugriffskontrolle und Lifecycle des Object Storage berücksichtigen.

## Tests und Diagnose

### Testbefehle

```bash
bin/rails test
bin/rails test test/models/product_test.rb
bin/rails test test/models/product_test.rb:42
bin/rails test:system
```

RSpec, falls verwendet:

```bash
bundle exec rspec
bundle exec rspec spec/models/product_spec.rb:42
```

### Console und Runner

```bash
bin/rails console
bin/rails console --sandbox
bin/rails runner 'puts Product.count'
```

Sandbox rollt DB-Änderungen beim Verlassen zurück, externe Nebenwirkungen jedoch nicht.

### Logs

```bash
tail -f log/development.log
RAILS_LOG_LEVEL=debug bin/rails server
```

Routes, Zeit und SQL korrelieren. Sensible Parameter filtern:

```ruby
Rails.application.config.filter_parameters += %i[password token secret]
```

## Sicherheit und Performance

### Sicherheit

- Authentisierung und Autorisierung getrennt implementieren.
- CSRF-Schutz nicht unüberlegt deaktivieren.
- SQL mit Bindparametern/Active Record statt Stringinterpolation.
- Ausgabe standardmäßig escapen; `html_safe` nur kontrolliert.
- offene Redirects vermeiden.
- Datei-Uploads validieren und isoliert speichern.
- Host Authorization, TLS, Secure Cookies und Security Headers prüfen.
- Dependencies mit `bundle audit` und Plattformscanner prüfen.
- Rails Security Guide und Releasehinweise verfolgen.

### Performance

- N+1-Abfragen identifizieren.
- passende Datenbankindizes nutzen.
- Pagination statt unbeschränkter Listen.
- Caching mit sauberer Invalidierung.
- schwere Arbeit in Background Jobs.
- Connection Pool an Web-/Job-Concurrency anpassen.
- Memory, GC, DB-Latenz und Queuezeit messen.
- nicht vor Messung optimieren.

Diagnose SQL:

```ruby
Product.where(active: true).explain
```

## Deployment-Checkliste

```text
[ ] Ruby/Rails/Dependencies fixiert
[ ] Assets gebaut
[ ] Datenbankbackup und Migration bewertet
[ ] Secrets/Keys vorhanden
[ ] DB-Pool und Job-Backend dimensioniert
[ ] Health-/Readiness-Endpunkte
[ ] TLS/Proxy-Header korrekt
[ ] Logs/Metriken/Fehlertracking
[ ] Job-Worker und Scheduler
[ ] Rollback für Code und Schema
[ ] Smoke Test nach Deployment
```

Typische Produktionsbefehle:

```bash
RAILS_ENV=production bin/rails db:migrate
RAILS_ENV=production bin/rails assets:precompile
RAILS_ENV=production bin/rails runner 'puts Rails.application.config.eager_load'
```

Deploymentwerkzeug kann Kamal, Containerplattform, systemd/Puma hinter nginx oder ein PaaS sein. Betriebskonzept vor Toolwahl definieren.

## Quellen
- [Rails Guides: Getting Started](https://guides.rubyonrails.org/getting_started.html)
- [Rails Guides Index](https://guides.rubyonrails.org/)
- [Securing Rails Applications](https://guides.rubyonrails.org/security.html)
- [Rails Command Line](https://guides.rubyonrails.org/command_line.html)

## Verwandte Notizen
- [[Python-3-Cheatsheet|Python 3 – Sprachvergleich]]
- [[nginx-Cheatsheet]]
- [[Git-Cheatsheet]]
- [[nginx-Cheatsheet|nginx und Deployment]]
