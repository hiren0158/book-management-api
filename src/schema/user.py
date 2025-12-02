from datetime import datetime
from typing import Optional
import re
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from .role import RoleRead


class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, description="Name is required and cannot be empty")
    password: str = Field(..., min_length=8, max_length=72)
    role_id: int = Field(..., gt=0, description="Role ID must be a valid role (1=Member, 2=Admin, 3=Librarian)")

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: str) -> str:
        """Validate name is not empty or whitespace only."""
        value = value.strip()
        if not value:
            raise ValueError('Name cannot be empty or whitespace only')
        return value

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        """Validate password contains at least 1 uppercase, 1 lowercase, 1 digit, and 1 special character."""
        if not re.search(r'[A-Z]', value):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', value):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', value):
            raise ValueError('Password must contain at least one digit (0-9)')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-=+\[\]\\\/;\'`~]', value):
            raise ValueError('Password must contain at least one special character (!@#$%^&*(),.?":{}|<>_-=+[]\\/;\'`~)')
        return value


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, min_length=1, description="Name cannot be empty if provided")
    password: Optional[str] = Field(None, min_length=8, max_length=72)
    role_id: Optional[int] = None
    is_active: Optional[bool] = None

    @field_validator('name')
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        """Validate name is not empty or whitespace only."""
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError('Name cannot be empty or whitespace only')
        return value

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, value: Optional[str]) -> Optional[str]:
        """Validate password contains at least 1 uppercase, 1 lowercase, 1 digit, and 1 special character."""
        if value is None:
            return value
        
        if not re.search(r'[A-Z]', value):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', value):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', value):
            raise ValueError('Password must contain at least one digit (0-9)')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-=+\[\]\\\/;\'`~]', value):
            raise ValueError('Password must contain at least one special character (!@#$%^&*(),.?":{}|<>_-=+[]\\/;\'`~)')
        return value


class UserRead(BaseModel):
    id: int
    email: str
    name: str
    role_id: int
    is_active: bool
    created_at: datetime
    role: Optional[RoleRead] = None

    model_config = ConfigDict(from_attributes=True)
