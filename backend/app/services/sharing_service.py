import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.resource import Resource, ResourceAccess
from app.models.user import User
from app.schemas.sharing import ShareGrantRead

logger = logging.getLogger("amu_sharing")


class SharingService:
    """Service governing resource sharing grants, peer access, and authorization resolution."""

    @classmethod
    async def can_access_resource(
        cls,
        session: AsyncSession,
        user: User,
        resource: Resource,
        required_permission: str = "VIEW",
    ) -> bool:
        """
        Evaluate access permission in constant time:
        1. Owner has full access
        2. Administrator has full oversight
        3. Approved departmental or public resources
        4. Explicit ResourceAccess grant
        """
        # 1. Owner always has full access
        if resource.owner_id == user.user_id:
            return True

        # 2. Administrator has full access
        if user.role and user.role.name == "Administrator":
            return True

        # 3. Approved institutional resource (for VIEW permission)
        if resource.status == "APPROVED" and required_permission == "VIEW":
            if resource.visibility == "PUBLIC":
                return True
            if (
                resource.visibility == "DEPARTMENT"
                and resource.owner
                and resource.owner.department_id == user.department_id
            ):
                return True

        # 4. Explicit ResourceAccess grant
        stmt = select(ResourceAccess).where(
            ResourceAccess.resource_id == resource.resource_id,
            ResourceAccess.user_id == user.user_id,
        )
        grant = await session.scalar(stmt)
        if grant:
            if required_permission == "VIEW":
                return True
            if required_permission == "EDIT" and grant.permission == "EDIT":
                return True

        return False

    @classmethod
    async def grant_access(
        cls,
        session: AsyncSession,
        actor: User,
        resource_id: uuid.UUID,
        grantee_email: str,
        permission: str = "VIEW",
    ) -> ResourceAccess:
        """
        Grants VIEW or EDIT access to a user identified by email.
        Enforces EC-07.1 (owner/admin only) and EC-07.2 (cannot self-share).
        """
        clean_permission = permission.upper().strip()
        if clean_permission not in ("VIEW", "EDIT"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid permission. Must be 'VIEW' or 'EDIT'.",
            )

        resource = await session.get(Resource, resource_id)
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found.",
            )

        # EC-07.1: Only owner or admin can share
        if resource.owner_id != actor.user_id and actor.role.name != "Administrator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the resource owner or an administrator can grant access.",
            )

        # EC-07.4: Find grantee user
        grantee = await session.scalar(
            select(User).where(func.lower(User.email) == grantee_email.strip().lower())
        )
        if not grantee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target user with email '{grantee_email}' was not found.",
            )

        # EC-07.2: Self-sharing check
        if grantee.user_id == actor.user_id or grantee.user_id == resource.owner_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot share a resource with yourself.",
            )

        # Check existing grant (upsert behavior)
        stmt_existing = select(ResourceAccess).where(
            ResourceAccess.resource_id == resource_id,
            ResourceAccess.user_id == grantee.user_id,
        )
        existing_grant = await session.scalar(stmt_existing)
        if existing_grant:
            existing_grant.permission = clean_permission
            await session.commit()
            target_id = existing_grant.access_id
        else:
            grant = ResourceAccess(
                resource_id=resource_id,
                user_id=grantee.user_id,
                permission=clean_permission,
                granted_by=actor.user_id,
            )
            session.add(grant)
            await session.commit()
            target_id = grant.access_id

        loaded_stmt = (
            select(ResourceAccess)
            .options(selectinload(ResourceAccess.user))
            .where(ResourceAccess.access_id == target_id)
        )
        access_grant = await session.scalar(loaded_stmt)
        if not access_grant:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load created resource access grant.",
            )
        return access_grant

    @classmethod
    async def revoke_access(
        cls,
        session: AsyncSession,
        actor: User,
        resource_id: uuid.UUID,
        access_id: uuid.UUID,
    ) -> None:
        """Revoke a previously granted access permission (EC-07.3)."""
        resource = await session.get(Resource, resource_id)
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found.",
            )

        if resource.owner_id != actor.user_id and actor.role.name != "Administrator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the resource owner or an administrator can revoke access.",
            )

        grant = await session.get(ResourceAccess, access_id)
        if not grant or grant.resource_id != resource_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Share grant not found for this resource.",
            )

        await session.delete(grant)
        await session.commit()

    @classmethod
    async def list_grants(
        cls,
        session: AsyncSession,
        actor: User,
        resource_id: uuid.UUID,
    ) -> list[ShareGrantRead]:
        """List all active share grants on a resource (Owner/Admin only)."""
        resource = await session.get(Resource, resource_id)
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found.",
            )

        if resource.owner_id != actor.user_id and actor.role.name != "Administrator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the resource owner or an administrator can view share grants.",
            )

        stmt = (
            select(ResourceAccess)
            .options(selectinload(ResourceAccess.user))
            .where(ResourceAccess.resource_id == resource_id)
            .order_by(ResourceAccess.created_at.desc())
        )
        grants = (await session.scalars(stmt)).all()
        return [
            ShareGrantRead(
                access_id=g.access_id,
                resource_id=g.resource_id,
                user_id=g.user_id,
                grantee_email=g.user.email if g.user else "",
                grantee_name=g.user.full_name if g.user else "",
                permission=g.permission,
                granted_by=g.granted_by,
                created_at=g.created_at,
            )
            for g in grants
        ]

    @classmethod
    async def list_shared_with_me(
        cls,
        session: AsyncSession,
        user: User,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Resource]:
        """List resources that have been explicitly shared with the current user."""
        stmt = (
            select(Resource)
            .join(ResourceAccess, ResourceAccess.resource_id == Resource.resource_id)
            .options(
                selectinload(Resource.versions),
                selectinload(Resource.owner),
            )
            .where(ResourceAccess.user_id == user.user_id)
            .order_by(ResourceAccess.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        resources = (await session.scalars(stmt)).all()
        return list(resources)
