from typing import Annotated

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

PageQuery = Annotated[int, Query(ge=1)]
SizeQuery = Annotated[int, Query(ge=1, le=100)]


class Page[T](BaseModel):
    """Shared paginated response; page is 1-based."""

    items: list[T]
    total: int
    page: int
    size: int


async def paginate(db: AsyncSession, stmt: Select, page: int, size: int) -> tuple[list, int]:
    """Return (rows for the page, total row count) for an ordered ORM select."""
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = (await db.execute(count_stmt)).scalar_one()
    rows = (await db.scalars(stmt.limit(size).offset((page - 1) * size))).all()
    return list(rows), total
