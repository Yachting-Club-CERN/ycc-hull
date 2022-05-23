import sqlalchemy
import uvicorn
from fastapi import FastAPI
from sqlalchemy.engine import ScalarResult
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from ycc_hull.db.models import Members

engine: sqlalchemy.future.engine.Engine = sqlalchemy.create_engine(
    "oracle+cx_oracle://ycclocal:changeit@127.0.0.1:1521", echo=True, future=True)

conn: str = "oracle+cx_oracle://ycclocal:changeit@127.0.0.1:1521"

# with Session(engine) as session:
#     session: Session
#
#     mem = Member(id=1000, name="Yager", firstname="Alice", membership="XY", home_addr="No addr", member_entrance="2021")
#
#     session.add(mem)
#     session.commit()

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World" + str(type(engine))}


@app.get("/v0/members")
async def members_get():
    stmt = select(Members)
    with Session(engine, future=True) as session:
        session: Session
        res: ScalarResult = session.scalars(stmt)

        m = []
        for member in res:
            member: Members
            m.append(to_dict(member))

        return m


def to_dict(member: Members):
    if not member:
        raise ValueError("Invalid argument: " + member)

    return {
        'id': int(member.id),
        'first_name': member.firstname,
        'last_name': member.name,
        'membership_type': member.membership
    }


def start_dev():
    uvicorn.run("ycc_hull.main:app", host="0.0.0.0", port=8000, reload=True)
