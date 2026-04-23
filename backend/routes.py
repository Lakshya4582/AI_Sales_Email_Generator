from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.limits import limiter

from backend.auth import (
    create_access_token,
    current_user,
    hash_password,
    verify_password,
)
from backend.db import get_db
from backend.models import (
    ChangePasswordRequest,
    EmailHistory,
    EmailHistoryResponse,
    EmailRequest,
    FollowUpRequest,
    HistoryUpdate,
    ImproveEmailRequest,
    LoginRequest,
    ProfileUpdate,
    SignupRequest,
    SubjectLinesRequest,
    SubjectLinesResponse,
    TokenResponse,
    User,
    UserResponse,
)
from backend.services import (
    generate_email_content,
    generate_followup_content,
    generate_subject_lines,
    improve_email_content,
)

router = APIRouter()


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute;30/hour")
def signup(request: Request, data: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        first_name=data.first_name.strip(),
        last_name=data.last_name.strip(),
        company=(data.company or "").strip() or None,
        role=(data.role or "").strip() or None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user.email), email=user.email)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute;100/hour")
def login(request: Request, data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )
    return TokenResponse(access_token=create_access_token(user.email), email=user.email)


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(current_user)):
    return user


@router.patch("/me", response_model=UserResponse)
def update_me(
    data: ProfileUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if data.first_name is not None:
        user.first_name = data.first_name.strip()
    if data.last_name is not None:
        user.last_name = data.last_name.strip()
    if data.company is not None:
        user.company = data.company.strip() or None
    if data.role is not None:
        user.role = data.role.strip() or None
    db.commit()
    db.refresh(user)
    return user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    data: ChangePasswordRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect.",
        )
    user.password_hash = hash_password(data.new_password)
    db.commit()
    return None


@router.post("/improve-email")
@limiter.limit("10/minute;100/hour")
def improve_email(
    request: Request,
    data: ImproveEmailRequest,
    user: User = Depends(current_user),
):
    sender_name = f"{user.first_name} {user.last_name}".strip()
    result = improve_email_content(
        data.draft,
        tone=data.tone,
        sender_name=sender_name,
        company=user.company,
        role=user.role,
    )
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=result["error"])
    return result


@router.post("/generate-email")
@limiter.limit("10/minute;100/hour")
def generate_email(
    request: Request,
    data: EmailRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    sender_name = f"{user.first_name} {user.last_name}".strip()
    result = generate_email_content(
        data,
        sender_name=sender_name,
        company=user.company,
        role=user.role,
    )

    if "result" in result:
        entry = EmailHistory(
            user_id=user.id,
            product=data.product,
            audience=data.audience,
            tone=data.tone,
            length=data.length,
            result=result["result"],
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        result["history_id"] = entry.id

    return result


@router.post("/subject-lines", response_model=SubjectLinesResponse)
@limiter.limit("20/minute;200/hour")
def subject_lines(
    request: Request,
    data: SubjectLinesRequest,
    user: User = Depends(current_user),
):
    sender_name = f"{user.first_name} {user.last_name}".strip()
    result = generate_subject_lines(
        data,
        sender_name=sender_name,
        company=user.company,
        role=user.role,
    )
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=result["error"])
    return SubjectLinesResponse(subjects=result["subjects"])


@router.post("/follow-up")
@limiter.limit("10/minute;100/hour")
def follow_up(
    request: Request,
    data: FollowUpRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    original = (
        db.query(EmailHistory)
        .filter(EmailHistory.id == data.history_id, EmailHistory.user_id == user.id)
        .first()
    )
    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Original email not found.",
        )

    sender_name = f"{user.first_name} {user.last_name}".strip()
    result = generate_followup_content(
        original,
        days_since_sent=data.days_since_sent,
        note=data.note,
        sender_name=sender_name,
        company=user.company,
        role=user.role,
    )

    if "result" in result:
        entry = EmailHistory(
            user_id=user.id,
            parent_id=original.id,
            product=f"Follow-up: {original.product}",
            audience=original.audience,
            tone=original.tone,
            length=original.length,
            result=result["result"],
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        result["history_id"] = entry.id
        result["parent_id"] = original.id

    return result


@router.get("/history", response_model=list[EmailHistoryResponse])
def list_history(
    limit: int = 50,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    limit = max(1, min(limit, 100))
    rows = (
        db.query(EmailHistory)
        .filter(EmailHistory.user_id == user.id)
        .order_by(desc(EmailHistory.created_at))
        .limit(limit)
        .all()
    )
    return rows


@router.patch("/history/{email_id}", response_model=EmailHistoryResponse)
def update_history(
    email_id: int,
    data: HistoryUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    entry = (
        db.query(EmailHistory)
        .filter(EmailHistory.id == email_id, EmailHistory.user_id == user.id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    entry.result = data.result
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/history/{email_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_history(
    email_id: int,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    entry = (
        db.query(EmailHistory)
        .filter(EmailHistory.id == email_id, EmailHistory.user_id == user.id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    db.delete(entry)
    db.commit()
    return None
