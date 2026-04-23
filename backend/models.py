from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db import Base


# --- ORM ---

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    company: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    emails: Mapped[list["EmailHistory"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class EmailHistory(Base):
    __tablename__ = "email_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("email_history.id", ondelete="SET NULL"), nullable=True, index=True
    )
    product: Mapped[str] = mapped_column(String(200))
    audience: Mapped[str] = mapped_column(String(200))
    tone: Mapped[str] = mapped_column(String(30))
    length: Mapped[str] = mapped_column(String(30))
    result: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    user: Mapped[User] = relationship(back_populates="emails")


# --- Pydantic request/response schemas ---

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    company: Optional[str] = Field(default=None, max_length=150)
    role: Optional[str] = Field(default=None, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: EmailStr


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: EmailStr
    first_name: str
    last_name: str
    company: Optional[str] = None
    role: Optional[str] = None


class EmailRequest(BaseModel):
    product: str = Field(min_length=1, max_length=200)
    audience: str = Field(min_length=1, max_length=200)
    tone: Literal["professional", "friendly", "persuasive"]
    length: Literal["short", "medium", "long"]


class FollowUpRequest(BaseModel):
    history_id: int
    days_since_sent: int = Field(ge=0, le=365)
    note: Optional[str] = Field(default=None, max_length=500)


class SubjectLinesRequest(BaseModel):
    product: str = Field(min_length=1, max_length=200)
    audience: str = Field(min_length=1, max_length=200)
    tone: Literal["professional", "friendly", "persuasive"]


class SubjectLinesResponse(BaseModel):
    subjects: list[str]


class ProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    company: Optional[str] = Field(default=None, max_length=150)
    role: Optional[str] = Field(default=None, max_length=100)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


class ImproveEmailRequest(BaseModel):
    draft: str = Field(min_length=10, max_length=5000)
    tone: Optional[Literal["professional", "friendly", "persuasive"]] = None


class HistoryUpdate(BaseModel):
    result: str = Field(min_length=1, max_length=20000)


class EmailHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    parent_id: Optional[int] = None
    product: str
    audience: str
    tone: str
    length: str
    result: str
    created_at: datetime
