import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BreadcrumbItem(BaseModel):
    folder_id: uuid.UUID
    name: str


class FolderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    parent_folder_id: uuid.UUID | None = None


class FolderUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    parent_folder_id: uuid.UUID | None = None


class FolderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    folder_id: uuid.UUID
    owner_id: uuid.UUID
    parent_folder_id: uuid.UUID | None
    name: str
    created_at: datetime
    updated_at: datetime


class FolderResourceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    resource_id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    description: str | None
    visibility: str
    status: str
    created_at: datetime


class FolderContentsResponse(BaseModel):
    folder: FolderRead
    breadcrumbs: list[BreadcrumbItem]
    subfolders: list[FolderRead]
    resources: list[FolderResourceItem]
