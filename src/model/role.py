from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship


class Role(SQLModel, table=True):
    __tablename__ = "roles"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)

    users: list["User"] = Relationship(back_populates="role")
