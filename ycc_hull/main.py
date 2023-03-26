import json
from typing import Any, List

import sqlalchemy
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import delete
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from ycc_hull.config import DB_URL, CORS_ORIGINS, UVICORN_PORT, UVICORN_RELOAD
from ycc_hull.db.models import Holiday, Member, MembershipType, ModelBase, User, Boat

engine: sqlalchemy.future.engine.Engine = sqlalchemy.create_engine(
    DB_URL, echo=True, future=True
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# TODO test data should be disabled on production


@app.post("/api/v0/test-data/populate")
async def test_data_populate():
    log: List[str] = []

    with Session(engine) as session:
        session: Session

        if await holidays_get():
            log.append("Skipping holidays")
        else:
            with open("test-data/Holidays.json", "r") as f:
                entries = json.load(f)
                for entry in entries:
                    session.add(Holiday(**entry))

                log.append(f"Add {len(entries)} holidays")

        if await membership_types_get():
            log.append("Skipping membership types")
        else:
            with open("test-data/MembershipTypes.json", "r") as f:
                for entry in json.load(f):
                    log.append(f"Add membership type {entry['mb_name']}")
                    session.add(MembershipType(**entry))

        if await members_get():
            log.append("Skipping members")
        else:
            with open("test-data/Members.json", "r") as f:
                entries = json.load(f)
                for entry in entries:
                    session.add(Member(**entry))

                log.append(f"Add {len(entries)} members")

        if await users_get():
            log.append("Skipping users")
        else:
            with open("test-data/Users.json", "r") as f:
                entries = json.load(f)
                for entry in entries:
                    session.add(User(**entry))

                log.append(f"Add {len(entries)} users")

        if await boats_get():
            log.append("Skipping boats")
        else:
            with open("test-data/Boats.json", "r") as f:
                entries = json.load(f)
                for entry in entries:
                    session.add(Boat(**entry))

                log.append(f"Add {len(entries)} boats")

        session.commit()
        log.append("Commit")

    return log


@app.post("/api/v0/test-data/clear")
async def test_data_clear():
    log: List[str] = []

    with Session(engine) as session:
        log.append("Deleting boats")
        session.execute(delete(Boat))

        log.append("Deleting membership types")
        session.execute(delete(MembershipType))

        log.append("Deleting users")
        session.execute(delete(User))

        log.append("Deleting members")
        session.execute(delete(Member))

        log.append("Deleting holidays")
        session.execute(delete(Holiday))

        session.commit()
        log.append("Commit")

    return log


@app.post("/api/v0/test-data/repopulate")
async def test_data_repopulate():
    log: List[str] = []

    log.extend(await test_data_clear())
    log.extend(await test_data_populate())

    return log


@app.get("/api/v0/boats")
async def boats_get():
    return query_all(Boat)


@app.get("/api/v0/holidays")
async def holidays_get():
    return query_all(Holiday)


@app.get("/api/v0/members")
async def members_get():
    return query_all(Member)


@app.get("/api/v0/membership-types")
async def membership_types_get():
    return query_all(MembershipType)


@app.get("/api/v0/users")
async def users_get():
    return query_all(User)


def query_all(cls) -> List[Any]:
    if not cls or not issubclass(cls, ModelBase):
        raise ValueError(f"Invalid class: {cls}")

    stmt = select(cls)
    with Session(engine, future=True) as session:
        return [row.json_dict() for row in session.scalars(stmt)]


def start():
    uvicorn.run(
        "ycc_hull.main:app", host="0.0.0.0", port=UVICORN_PORT, reload=UVICORN_RELOAD
    )
