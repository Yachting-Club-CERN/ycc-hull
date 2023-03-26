# YCC Hull

YCC backend service.

## Prerequisites

- Install Python 3.11
- Install Poetry & [poetry-plugin-up](https://github.com/MousaZeidBaker/poetry-plugin-up)
  - `pipx install poetry && pipx inject poetry poetry-plugin-up`
- Install Docker & Docker Compose

## Run Application Locally

Initialise environment:

```
poetry install
```

Start database:

```
cd ../ycc-infra/ycc-db-local && docker-compose up
```

Start application:

```
poetry run start
```

Address: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## Development Guide

### Regenerating Python Model from Database

You can regenerate models using the following commands:

```
poetry run sqlacodegen oracle+cx_oracle://ycclocal:changeit@127.0.0.1:1521 --outfile ycc_hull/db/models_generated.py
```

Generated models does not work as good as handwritten ones. Please use the generated models as a reference for updating
handwritten models in `models.py`.

### Test Data

For non-sensitive data such as membership types or boats, we can use directly the real YCC data.

For sensitive data (names, addresses, bookings, _boat logs_), automatic one-shot generation is preferred with tools like
[Faker](https://faker.readthedocs.io) or [Mockaroo](https://www.mockaroo.com/).

### Dependency Upgrade

Upgrade to latest compatible versions:

`poetry up`

Upgrade to latest versions:

`poetry up --latest`

### Database Schema Upgrade

See the `ycc-infra` repository for updating the Docker image. Then apply the update to `ycc-hull`:

1. Regenerate model from the database (see above)
2. Update models and test data if necessary

## PoC History

This section records which technologies were dropped during PoC and why.

- Node.js frameworks (notable Sails and TypeORM): poor integration with the existing Oracle Database. YCC Hull will
  provide a backend service, which can be used from other applications without having to worry about Oracle
  integration.
- Django: Django ORM is inferior to SQLAlchemy, plus, this service only provides an API. Django would have worked, but
  it would have complicated too much.

Note that other services can be in Node.js/Django, since they only communicate with this one over the network.
