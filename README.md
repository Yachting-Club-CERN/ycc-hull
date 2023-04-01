# YCC Hull

YCC backend service.

## Prerequisites

- Install Python 3.11
- Install Poetry & [poetry-plugin-up](https://github.com/MousaZeidBaker/poetry-plugin-up)
  - `pipx install poetry && pipx inject poetry poetry-plugin-up`
- Install Docker & Docker Compose

## Run Application Locally

Initialise environment:

```sh
poetry install
```

Start database:

```sh
cd ../ycc-infra/ycc-db-local && docker-compose up
```

Start application:

```sh
poetry run start
```

- Address: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Development Guide

### Module Structure

- `generated_entities`: generated entities for reference
- `legacy_password_hashing`: Perl-compatible password hashing
- `test_data`: test data & generator
- `ycc_hull`: published module
  - `api`: API endpoints, which are also responsible for authorisation
  - `controllers`: controllers, responsible for business logic and DB to DTO conversion
  - `db`: DB-related components, entities
  - `models`: models, DTOs

### Regenerating Python Entities from Database

You can regenerate entities using the following commands:

```sh
cd generated_entities
poetry run sqlacodegen oracle+cx_oracle://ycclocal:changeit@127.0.0.1:1521 --outfile ycc_hull/db/entities_generated.py
```

Generated entities does not work as good as handwritten ones. Please use the generated entities as a reference for updating handwritten entities in `entities.py`.

(Also note that as of 2023-03 we use SQLAlchemy 2.x (way faster with Oracle and way more convenient), while latest sqlacodegen only supports SQLAlchemy 1.x.)

### Test Data

For non-sensitive data such as membership types or boats, we can use directly the real YCC data.

For sensitive data (names, addresses, bookings, _boat logs_), automatic one-shot generation is preferred with tools like [Faker](https://faker.readthedocs.io) or [Mockaroo](https://www.mockaroo.com/).

### Dependency Upgrade

Upgrade to latest compatible versions:

`poetry up`

Upgrade to latest versions:

`poetry up --latest`

### Basic QA

```sh
poetry run black .
poetry run mypy .
poetry run flake8 .
poetry run pylint legacy_password_hashing
poetry run pylint test_data
poetry run pylint ycc_hull
```

### Database Schema Upgrade

See the `ycc-infra` repository for updating the Docker image. Then apply the update to `ycc-hull`:

1. Regenerate entities from the database (see above)
2. Update entities and test data if necessary

## PoC History

This section records which technologies were dropped during PoC and why.

- Node.js frameworks (notable Sails and TypeORM): poor integration with the existing Oracle Database. YCC Hull will
  provide a backend service, which can be used from other applications without having to worry about Oracle
  integration.
- Django: Django ORM is inferior to SQLAlchemy, plus, this service only provides an API. Django would have worked, but
  it would have complicated too much.

Note that other services can be in Node.js/Django, since they only communicate with this one over the network.

(On the funny note when `ycc-hull` was already under development, Sequelize (Node/JS) came out with Oracle support...)
