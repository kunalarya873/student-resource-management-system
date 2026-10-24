import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.resource import ResourceAccess
from app.repositories.base import BaseRepository


class SharingRepository(BaseRepository[ResourceAccess]):
    """Data access repository for resource sharing and granular access control grants."""

    def __init__(self) -> None:
        super().__init__(ResourceAccess)

    async def get_active_grant(
        self,
        session: AsyncSession,
        resource_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> ResourceAccess | None:
        """Fetch the active access grant for a specific user on a resource."""
        stmt = select(ResourceAccess).where(
            ResourceAccess.resource_id == resource_id,
            ResourceAccess.granted_to_user_id == user_id,
        )
        return await session.scalar(stmt)

    async def list_grants_for_resource(
        self,
        session: AsyncSession,
        resource_id: uuid.UUID,
    ) -> Sequence[ResourceAccess]:
        """List all active access grants for a given resource."""
        stmt = (
            select(ResourceAccess)
            .where(ResourceAccess.resource_id == resource_id)
            .options(selectinload(ResourceAccess.granted_to_user))
            .order_by(ResourceAccess.created_at.desc())
        )
        result = await session.scalars(stmt)
        return result.all()

    async def list_grants_for_user(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[ResourceAccess]:
        """List resources that have been shared with a specific user."""
        stmt = (
            select(ResourceAccess)
            .where(ResourceAccess.granted_to_user_id == user_id)
            .options(selectinload(ResourceAccess.resource))
            .offset(skip)
            .limit(limit)
        )
        result = await session.scalars(stmt)
        return result.all()


sharing_repository = SharingRepository()
