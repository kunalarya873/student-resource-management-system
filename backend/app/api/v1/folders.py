import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.common import StandardMessageResponse
from app.schemas.folder import (
    FolderContentsResponse,
    FolderCreate,
    FolderRead,
    FolderUpdate,
)
from app.services.folder_service import FolderService

router = APIRouter(prefix="/folders", tags=["Folders"])


@router.post(
    "",
    response_model=FolderRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new folder or subfolder",
)
async def create_folder(
    payload: FolderCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> FolderRead:
    folder = await FolderService.create_folder(
        session=session,
        user=current_user,
        name=payload.name,
        parent_folder_id=payload.parent_folder_id,
    )
    return FolderRead.model_validate(folder)


@router.get(
    "",
    response_model=list[FolderRead],
    status_code=status.HTTP_200_OK,
    summary="List root folders or subfolders of a given parent",
)
async def list_folders(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    parent_id: Annotated[uuid.UUID | None, Query()] = None,
) -> list[FolderRead]:
    folders = await FolderService.list_folders(
        session=session,
        user=current_user,
        parent_id=parent_id,
    )
    return [FolderRead.model_validate(f) for f in folders]


@router.get(
    "/{folder_id}",
    response_model=FolderRead,
    status_code=status.HTTP_200_OK,
    summary="Get single folder metadata by ID",
)
async def get_folder(
    folder_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> FolderRead:
    folder = await FolderService.get_folder(
        session=session,
        user=current_user,
        folder_id=folder_id,
    )
    return FolderRead.model_validate(folder)


@router.get(
    "/{folder_id}/contents",
    response_model=FolderContentsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get folder contents including breadcrumbs, subfolders, and resources",
)
async def get_folder_contents(
    folder_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> FolderContentsResponse:
    return await FolderService.get_folder_contents(
        session=session,
        user=current_user,
        folder_id=folder_id,
    )


@router.patch(
    "/{folder_id}",
    response_model=FolderRead,
    status_code=status.HTTP_200_OK,
    summary="Rename or move a folder (with DAG cycle prevention)",
)
async def update_folder(
    folder_id: uuid.UUID,
    payload: FolderUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> FolderRead:
    folder = await FolderService.move_or_rename_folder(
        session=session,
        user=current_user,
        folder_id=folder_id,
        new_name=payload.name,
        new_parent_id=payload.parent_folder_id,
    )
    return FolderRead.model_validate(folder)


@router.delete(
    "/{folder_id}",
    response_model=StandardMessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete an empty folder (enforces SD-09 non-empty protection)",
)
async def delete_folder(
    folder_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> StandardMessageResponse:
    await FolderService.delete_folder(
        session=session,
        user=current_user,
        folder_id=folder_id,
    )
    return StandardMessageResponse(message="Folder deleted successfully")
