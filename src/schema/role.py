from pydantic import BaseModel, EmailStr, ConfigDict


class RoleRead(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)
