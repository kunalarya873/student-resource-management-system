import uuid
from datetime import datetime

from pydantic import EmailStr, Field

from app.schemas.common import CoreSchema


class ShareGrantCreate(CoreSchema):
    """Payload to grant a user access to a resource."""

    grantee_email: EmailStr = Field(..., description="Target user's university email address")
    permission: str = Field(default="VIEW", description="Access permission: VIEW or EDIT")


class ShareGrantUpdate(CoreSchema):
    """Payload to update the permission level of an existing share grant."""

    permission: str = Field(..., description="Access permission: VIEW or EDIT")


class ShareGrantRead(CoreSchema):
    """Read schema representing an active resource sharing grant."""

    access_id: uuid.UUID
    resource_id: uuid.UUID
    user_id: uuid.UUID
    grantee_email: str
    grantee_name: str
    permission: str
    granted_by: uuid.UUID
    created_at: datetime
