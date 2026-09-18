from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, ConfigDict

from app.models.user import RoleEnum


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    speaker_code: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    person_id:str
    full_name: str
    email: EmailStr
    role: RoleEnum
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ParticipantProfileUpdate(BaseModel):
    phone_number: Optional[str] = None
    organization: Optional[str] = None
    bio: Optional[str] = None
    photo_url: Optional[str] = None


class ParticipantProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    phone_number: Optional[str] = None
    organization: Optional[str] = None
    bio: Optional[str] = None
    photo_url: Optional[str] = None


class SpeakerProfileUpdate(BaseModel):
    title: Optional[str] = None
    organization: Optional[str] = None
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    expertise: Optional[str] = None


class SpeakerProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    speaker_code: str
    title: Optional[str] = None
    organization: Optional[str] = None
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    expertise: Optional[str] = None

class SpeakerProfileCreate(BaseModel):
    title: Optional[str] = None
    organization: Optional[str] = None
    bio: Optional[str] = None
    expertise: Optional[str] = None


class SpeakerLink(BaseModel):
    speaker_code: str