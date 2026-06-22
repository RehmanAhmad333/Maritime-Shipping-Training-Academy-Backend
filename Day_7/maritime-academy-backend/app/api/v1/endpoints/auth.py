import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.models.user import User
from app.schemas.user_schema import UserCreate, UserLogin, Token, RefreshTokenRequest
from app.core.config import settings
from jose import JWTError, jwt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="""
    Create a new user account.
    - **email**: Must be unique and valid email format
    - **password**: Minimum 6 characters
    - **role**: Optional, defaults to 'student'. Can be 'student' or 'trainer' (admin only via seed)
    - Returns access_token and refresh_token
    """
)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Only allow student and trainer roles via registration (admin via seed only)
        if user_data.role not in ["student", "trainer"]:
            user_data.role = "student"  # Default to student
        
        # Create new user
        new_user = User(
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            full_name=user_data.full_name,
            phone=user_data.phone,
            role=user_data.role,
            is_active=True
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Generate tokens
        access_token = create_access_token(data={"sub": new_user.email, "role": new_user.role})
        refresh_token = create_refresh_token(data={"sub": new_user.email})
        
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    
    except HTTPException:
        raise
    except SQLAlchemyError as db_err:
        db.rollback()
        logger.error(f"Database error during registration for email {user_data.email}: {str(db_err)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while creating user account."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate user and get tokens",
    description="""
    Login with email and password.
    - Returns access_token (expires in 30 minutes) and refresh_token (expires in 7 days)
    - Use the access_token in Authorization header as 'Bearer <token>' for protected endpoints
    """
)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    try:
        # Find user
        user = db.query(User).filter(User.email == user_data.email).first()
        if not user or not verify_password(user_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account disabled. Please contact support."
            )
        
        # Generate tokens
        access_token = create_access_token(data={"sub": user.email, "role": user.role})
        refresh_token = create_refresh_token(data={"sub": user.email})
        
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    
    except HTTPException:
        raise
    except SQLAlchemyError as db_err:
        logger.error(f"Database error during login for email {user_data.email}: {str(db_err)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred. Please try again later."
        )
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
    description="Get a new access token using a valid refresh token."
)
def refresh_token(token_data: RefreshTokenRequest, db: Session = Depends(get_db)):
    try:
        # Decode using refresh secret directly
        payload = jwt.decode(
            token_data.refresh_token,
            settings.JWT_REFRESH_SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        new_access = create_access_token(data={"sub": user.email, "role": user.role})
        new_refresh = create_refresh_token(data={"sub": user.email})
        return {"access_token": new_access, "refresh_token": new_refresh, "token_type": "bearer"}
    
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")