from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user
from app.models.user import User
from app.repositories.user_repository import user_repository
from app.schemas.user import UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Retrieve current user account details",
)
async def get_current_user_profile(
    current_user: Annotated[User, Depends(get_current_user)],
) -> UserRead:
    return UserRead(
        user_id=current_user.user_id,
        email=current_user.email,
        full_name=current_user.full_name,
        role_id=current_user.role_id,
        role_name=current_user.role.name,
        department_id=current_user.department_id,
        department_name=current_user.department.name if current_user.department else None,
        status=current_user.status,
        created_at=current_user.created_at,
    )


@router.patch(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Update current user account details",
)
async def update_current_user_profile(
    payload: UserUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserRead:
    if payload.full_name is not None and payload.full_name.strip():
        await user_repository.update(
            session, current_user, {"full_name": payload.full_name.strip()}
        )
        await session.commit()
        await session.refresh(current_user)

    return UserRead(
        user_id=current_user.user_id,
        email=current_user.email,
        full_name=current_user.full_name,
        role_id=current_user.role_id,
        role_name=current_user.role.name,
        department_id=current_user.department_id,
        department_name=current_user.department.name if current_user.department else None,
        status=current_user.status,
        created_at=current_user.created_at,
    )
