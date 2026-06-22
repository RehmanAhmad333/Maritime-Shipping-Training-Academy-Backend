import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.user_schema import UserResponse, UserUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Returns the profile of the authenticated user."
)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="Update the authenticated user's full name and phone."
)
def update_me(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if user_data.full_name:
            current_user.full_name = user_data.full_name.strip()
        if user_data.phone:
            current_user.phone = user_data.phone.strip()
        
        db.commit()
        db.refresh(current_user)
        return current_user
    
    except SQLAlchemyError as db_err:
        db.rollback()
        logger.error(f"Database error updating user {current_user.id}: {str(db_err)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile due to a database error."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error updating user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating profile."
        )