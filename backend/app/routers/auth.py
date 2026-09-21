from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse
)

from app.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register")
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    # Check if email already exists
    existing_user = db.query(User).filter(
        User.email == request.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Create new user
    new_user = User(
        name=request.name,
        email=request.email,
        password_hash=hash_password(request.password),
        role="user"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    from app.services.audit_service import create_audit_log
    create_audit_log(
        db=db,
        user_id=new_user.id,
        project_id=None,
        action="user_registered",
        entity_type="user",
        entity_id=new_user.id,
        description=f"User {new_user.email} registered"
    )

    return {
        "message": "User registered successfully",
        "user_id": new_user.id
    }


@router.post("/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == request.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        request.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role
        }
    )

    from app.services.audit_service import create_audit_log
    create_audit_log(
        db=db,
        user_id=user.id,
        project_id=None,
        action="user_login",
        entity_type="user",
        entity_id=user.id,
        description=f"User {user.email} logged in"
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }