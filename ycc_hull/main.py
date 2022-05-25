import json
from typing import List, Any

import sqlalchemy
import uvicorn
from fastapi import FastAPI
from sqlalchemy import delete
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from ycc_hull.config import DB_URL, UVICORN_PORT, UVICORN_RELOAD
from ycc_hull.db.models import Member, MembershipType, ModelBase

engine: sqlalchemy.future.engine.Engine = sqlalchemy.create_engine(
    DB_URL, echo=True, future=True)

app = FastAPI()


# TODO test data should be disabled on production

@app.post("/api/v0/test-data/generate")
async def test_data_generate():
    log: List[str] = []

    with Session(engine) as session:
        session: Session

        if await membership_types_get():
            log.append("Skipping membership types")
        else:
            with open('test-data/MembershipTypes.json', 'r') as f:
                for entry in json.load(f):
                    log.append(f"Add membership type {entry['mb_name']}")
                    session.add(MembershipType(**entry))

        if await members_get():
            log.append("Skipping members types")
        else:
            with open('test-data/Members.json', 'r') as f:
                members = json.load(f)
                for entry in members:
                    session.add(Member(**entry))

                log.append(f"Add {len(members)} members")

        session.commit()

        log.append("Commit")

    return log


@app.post("/api/v0/test-data/clear")
async def test_data_clear():
    log: List[str] = []

    with Session(engine) as session:
        log.append("Deleting membership types")
        session.execute(delete(MembershipType))

        log.append("Deleting members")
        session.execute(delete(Member))

        session.commit()

        log.append("Commit")

    return log


@app.post("/api/v0/test-data/regenerate")
async def test_data_regenerate():
    log: List[str] = []

    log.extend(await test_data_clear())
    log.extend(await test_data_generate())

    return log


@app.get("/api/v0/members")
async def members_get():
    return query_all(Member)


@app.get("/api/v0/membership-types")
async def membership_types_get():
    return query_all(MembershipType)


def query_all(cls) -> List[Any]:
    if not cls or not issubclass(cls, ModelBase):
        raise ValueError(f"Invalid class: {cls}")

    stmt = select(cls)
    with Session(engine, future=True) as session:
        return [row.json_dict() for row in session.scalars(stmt)]


def start():
    uvicorn.run("ycc_hull.main:app", host="0.0.0.0", port=UVICORN_PORT, reload=UVICORN_RELOAD)
