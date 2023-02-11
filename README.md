# YCC Hull

YCC back-end service.

## Prerequisites

- Install Python 3.11
- Install Poetry
- Install Docker & Docker Compose

## Run Application Locally

Initialise environment:

```
poetry install
```

Start database:

```
cd db && docker-compose up
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

For sensitive data (names, addresses, bookings, *boat logs*), automatic one-shot generation is preferred with tools like
[Faker](https://faker.readthedocs.io) or [Mockaroo](https://www.mockaroo.com/).

### Database Schema Upgrade

AS the DB changes, you need to update to Docker other non-PRO databases. This is what I found a relatively simple workflow:

1. Export schema:
   1. Open Oracle SQL Developer
   2. Connect to YCC DB (outside of CERN you can tunnel to Oracle with extra port forwarding)
   3. Select `Top Menu -> Tools -> Database Export...`
   4. Export DDL (without data) to a single UTF-8 file (it can take a few minutes)
   5. Save it to the `db/` directory, e.g., `db/schema-export-2023-02.sql`
   6. Double check that it has no sensitive and personal data in it
2. Check what changed (diff against previous version)
3. Port changes to `db/init-local/sql/schema-local.sql.noautorun`
   1. In the Docker DB we do not store table storage constraints and grants
   2. If there are many changes, the best is to diff one or two more times, to eliminate mistakes
4. Test the local schema by deleting and recreating the Docker container
5. Regenerate model from the database (see above)
6. Update models and test data if necessary

## PoC History

This section records which technologies were dropped during PoC and why.

* Node.js frameworks (notable Sails and TypeORM): poor integration with the existing Oracle Database. YCC Hull will
  provide a back-end service, which can be used from other applications without having to worry about Oracle
  integration.
* Django: Django ORM is inferior to SQLAlchemy, plus, this service only provides an API. Django would have worked, but
  it would have complicated too much.

Note that other services can be in Node.js/Django, since they only communicate with this one over the network.
