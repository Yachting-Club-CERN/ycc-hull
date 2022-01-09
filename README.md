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
