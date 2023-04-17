# YCC Hull

YCC backend service.

## Prerequisites

- Install Python 3.9
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

Start Keycloak & configure clients if needed (see below for details):

```sh
cd ../ycc-infra/ycc-keycloak-local
./init.sh
./kc.sh start-dev
```

Start application:

```sh
poetry run start
```

- Address: [http://localhost:8000/](http://localhost:8000/)
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## Keycloak Client Configuration

For a clean config two clients are recommended, one for `ycc-hull` and one for the Swagger UI. The latter is optional.

For `ycc-hull` create a client with:

- Client authentication enabled (authorisation disabled)
- Service accounts roles enabled
- Ensure that the `ycc-client-groups-and-roles` client scope is enabled
- Save the credentials to `config/conf.json`

For the Swagger UI (optional) create a client with:

- Client authentication disabled
- Direct access grants enabled
- Ensure that the `ycc-client-groups-and-roles` client scope is enabled
- URLs `http://localhost:8000` (base, home, admin) and `http://localhost:8000/*` (redirect)
- Web origins `+`
- Optionally you can increase token refresh for example to 1 hour under the advanced settings

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
poetry install
poetry run sqlacodegen oracle+cx_oracle://ycclocal:changeit@127.0.0.1:1521 --outfile entities_generated.py
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
poetry run pytest --cov=ycc_hull --cov-branch --cov-report=html

poetry run black .
poetry run mypy .
poetry run flake8 .
poetry run pylint --jobs 0 legacy_password_hashing test_data tests ycc_hull
```

### Database Schema Upgrade

See the `ycc-infra` repository for updating the Docker image. Then apply the update to `ycc-hull`:

1. Regenerate entities from the database (see above)
2. Update entities and test data if necessary

## Usage

Deployed on CERN OKD.

### Testing Docker Build Locally

You can test the build locally. If you do not want to run the instance, but only inspect the contents, you can set the entry point in your local copy to `/bin/bash` for simplicity.

You can test the build with this command:

```sh
docker build . -t ycc-hull-local-test
```

Then start a new container from the image:

```sh
# You might want to update the config file to work on your computer
CONFIG_JSON=$(cat conf/config.json)
LOGGING_CONF=$(cat conf/logging.conf)
docker run -p 8000:8080  -e CONFIG_JSON="$CONFIG_JSON" -e LOGGING_CONF="$LOGGING_CONF" -it ycc-hull-local-test
```

## PoC History

This section records which technologies were dropped during PoC and why.

- Node.js frameworks (notable Sails and TypeORM): poor integration with the existing Oracle Database. YCC Hull will
  provide a backend service, which can be used from other applications without having to worry about Oracle
  integration.
- Django: Django ORM is inferior to SQLAlchemy, plus, this service only provides an API. Django would have worked, but
  it would have complicated too much.

Note that other services can be in Node.js/Django, since they only communicate with this one over the network.

(On the funny note when `ycc-hull` was already under development, Sequelize (Node/JS) came out with Oracle support...)
