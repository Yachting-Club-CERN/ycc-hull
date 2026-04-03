import pytest
import pytest_asyncio
from sqlalchemy import select

from tests.main_test import init_test_database
from ycc_hull.db.context import DatabaseContextHolder
from ycc_hull.db.entities import AuditLogEntryEntity


@pytest_asyncio.fixture(scope="module", autouse=True)
async def init_database() -> None:
    await init_test_database(__name__)


# ==============================================================================
# query_all
# ==============================================================================


@pytest.mark.asyncio
async def test_query_all_no_transformer() -> None:
    ctx = DatabaseContextHolder.context

    with ctx.session() as session:
        session.add(
            AuditLogEntryEntity(
                application="test",
                principal="user",
                description="no transformer test",
            )
        )
        session.commit()

    result = await ctx.query_all(
        select(AuditLogEntryEntity).where(
            AuditLogEntryEntity.description == "no transformer test"
        )
    )
    assert len(result) == 1
    assert isinstance(result[0], AuditLogEntryEntity)
    assert result[0].description == "no transformer test"
    assert result[0].application == "test"


@pytest.mark.asyncio
async def test_query_all_with_transformer() -> None:
    ctx = DatabaseContextHolder.context

    with ctx.session() as session:
        session.add(
            AuditLogEntryEntity(
                application="test",
                principal="user",
                description="transformer test",
            )
        )
        session.commit()

    result = await ctx.query_all(
        select(AuditLogEntryEntity).where(
            AuditLogEntryEntity.description == "transformer test"
        ),
        transformer=lambda row: row.description,
    )
    assert result == ["transformer test"]


@pytest.mark.asyncio
async def test_query_all_with_async_transformer() -> None:
    ctx = DatabaseContextHolder.context

    async def async_tx(row: AuditLogEntryEntity) -> str:
        return row.description

    result = await ctx.query_all(
        select(AuditLogEntryEntity).where(
            AuditLogEntryEntity.description == "transformer test"
        ),
        async_transformer=async_tx,
    )
    assert result == ["transformer test"]


@pytest.mark.asyncio
async def test_query_all_both_transformers_raise() -> None:
    ctx = DatabaseContextHolder.context

    with pytest.raises(
        AssertionError,
        match=r"^Only one of transformer and async_transformer can be specified$",
    ):
        await ctx.query_all(
            select(AuditLogEntryEntity),
            transformer=lambda r: r,
            async_transformer=lambda r: r,
        )


@pytest.mark.asyncio
async def test_query_all_with_session() -> None:
    ctx = DatabaseContextHolder.context
    with ctx.session() as session:
        result = await ctx.query_all(
            select(AuditLogEntryEntity).where(
                AuditLogEntryEntity.description == "transformer test"
            ),
            session=session,
        )
        assert len(result) == 1
        assert result[0].description == "transformer test"


# ==============================================================================
# query_count
# ==============================================================================


@pytest.mark.asyncio
async def test_query_count() -> None:
    ctx = DatabaseContextHolder.context
    count_before = await ctx.query_count(AuditLogEntryEntity)

    with ctx.session() as session:
        session.add(
            AuditLogEntryEntity(
                application="test",
                principal="user",
                description="count test",
            )
        )
        session.commit()

    count_after = await ctx.query_count(AuditLogEntryEntity)
    assert count_after == count_before + 1


@pytest.mark.asyncio
async def test_query_count_with_session() -> None:
    ctx = DatabaseContextHolder.context
    with ctx.session() as session:
        count = await ctx.query_count(AuditLogEntryEntity, session=session)
        all_rows = await ctx.query_all(select(AuditLogEntryEntity), session=session)
        assert count == len(all_rows)
