# YCC Hull

YCC back-end service.

## Prerequisites

- Install Python 3.10
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
poetry shell
python manage.py runserver
```

Address: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## PoC History

This section records which technologies were dropped during PoC and why.

* Node.js frameworks (notable Sails and TypeORM): poor integration with the existing Oracle Database. YCC Hull will
  provide a back-end service, which can be used from other applications without having to worry about Oracle
  integration.
* Django: Django ORM is inferior to SQLAlchemy, plus, this service only provides an API. Django would have worked, but
  it would have complicated too much.

Note that other services can be in Node.js/Django, since they only communicate with this one over the network.
