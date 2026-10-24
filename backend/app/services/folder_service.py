import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.folder import Folder
from app.models.resource import Resource
from app.models.user import User
from app.repositories.folder_repository import folder_repository
from app.schemas.folder import (
    BreadcrumbItem,
    FolderContentsResponse,
    FolderRead,
    FolderResourceItem,
)


class FolderService:
    @staticmethod
    async def get_breadcrumbs(session: AsyncSession, folder_id: uuid.UUID) -> list[BreadcrumbItem]:
        """Recursive CTE to construct the path breadcrumbs from root to current folder."""
        rows = await folder_repository.get_breadcrumbs_raw(session, folder_id)
        return [BreadcrumbItem(folder_id=r[0], name=r[1]) for r in rows]

    @staticmethod
    async def is_descendant(
        session: AsyncSession, target_parent_id: uuid.UUID, folder_id: uuid.UUID
    ) -> bool:
        """Checks if target_parent_id is folder_id itself or any of its descendants (preventing DAG cycles)."""
        return await folder_repository.is_descendant(session, target_parent_id, folder_id)

    @classmethod
    async def create_folder(
        cls,
        session: AsyncSession,
        user: User,
        name: str,
        parent_folder_id: uuid.UUID | None = None,
    ) -> Folder:
        if parent_folder_id:
            parent = await folder_repository.get_by_id(session, parent_folder_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent folder not found",
                )
            if parent.owner_id != user.user_id and user.role.name != "Administrator":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot create subfolder in another user's folder",
                )

        folder = Folder(
            name=name.strip(),
            parent_folder_id=parent_folder_id,
            owner_id=user.user_id,
        )
        await folder_repository.create(session, folder)
        await session.commit()
        await session.refresh(folder)
        return folder

    @classmethod
    async def list_folders(
        cls,
        session: AsyncSession,
        user: User,
        parent_id: uuid.UUID | None = None,
    ) -> list[Folder]:
        folders = await folder_repository.list_by_owner_and_parent(
            session=session,
            owner_id=user.user_id,
            parent_id=parent_id,
            is_admin=(user.role.name == "Administrator"),
        )
        return list(folders)

    @classmethod
    async def get_folder(cls, session: AsyncSession, user: User, folder_id: uuid.UUID) -> Folder:
        folder = await folder_repository.get_by_id(session, folder_id)
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found",
            )
        if folder.owner_id != user.user_id and user.role.name != "Administrator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this folder",
            )
        return folder

    @classmethod
    async def get_folder_contents(
        cls, session: AsyncSession, user: User, folder_id: uuid.UUID
    ) -> FolderContentsResponse:
        folder = await cls.get_folder(session, user, folder_id)

        breadcrumbs = await cls.get_breadcrumbs(session, folder_id)

        # Child subfolders
        subfolders_stmt = (
            select(Folder).where(Folder.parent_folder_id == folder_id).order_by(Folder.name.asc())
        )
        subfolders = (await session.scalars(subfolders_stmt)).all()

        # Child resources
        resources_stmt = (
            select(Resource)
            .where(Resource.folder_id == folder_id)
            .order_by(Resource.created_at.desc())
        )
        resources = (await session.scalars(resources_stmt)).all()

        return FolderContentsResponse(
            folder=FolderRead.model_validate(folder),
            breadcrumbs=breadcrumbs,
            subfolders=[FolderRead.model_validate(f) for f in subfolders],
            resources=[FolderResourceItem.model_validate(r) for r in resources],
        )

    @classmethod
    async def move_or_rename_folder(
        cls,
        session: AsyncSession,
        user: User,
        folder_id: uuid.UUID,
        new_name: str | None = None,
        new_parent_id: uuid.UUID | None = None,
    ) -> Folder:
        folder = await folder_repository.get_by_id(session, folder_id)
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found",
            )
        if folder.owner_id != user.user_id and user.role.name != "Administrator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied to modify this folder",
            )

        # Handle moving
        if new_parent_id is not None and new_parent_id != folder.parent_folder_id:
            # Prevent DAG cycles
            if await cls.is_descendant(session, new_parent_id, folder_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot move folder into itself or one of its descendants (circular hierarchy).",
                )
            parent = await folder_repository.get_by_id(session, new_parent_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target parent folder not found",
                )
            if parent.owner_id != user.user_id and user.role.name != "Administrator":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Target parent folder is owned by another user",
                )
            folder.parent_folder_id = new_parent_id

        # Handle renaming
        if new_name is not None and new_name.strip():
            folder.name = new_name.strip()

        await session.commit()
        await session.refresh(folder)
        return folder

    @classmethod
    async def delete_folder(cls, session: AsyncSession, user: User, folder_id: uuid.UUID):
        folder = await folder_repository.get_by_id(session, folder_id)
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found",
            )
        if folder.owner_id != user.user_id and user.role.name != "Administrator":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied to delete this folder",
            )

        # SD-09: Verify folder is empty before deleting
        child_folders, child_resources = await folder_repository.count_children_and_resources(
            session, folder_id
        )

        if child_folders > 0 or child_resources > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Folder is not empty. Remove all subfolders and resources before deleting.",
            )

        await session.delete(folder)
        await session.commit()
