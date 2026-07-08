import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import get_db
from typing import Optional
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.user_schema import UserResponse, UserUpdate, RoleUpdate

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





@router.get(
    "",
    summary="Get all users (Admin only)",
    dependencies=[Depends(require_role("admin"))],
)
def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    role: Optional[str] = Query(None, description="Filter by role: student, trainer, admin"),
    db: Session = Depends(get_db),
):
    """
    Returns paginated list of all users.
    Admin only.
    """
    try:
        query = db.query(User)

        # Filter by role if provided
        if role:
            query = query.filter(User.role == role)

        total = query.count()
        users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()

        page = (skip // limit) + 1
        pages = (total + limit - 1) // limit

        return {
            "total": total,
            "page": page,
            "pages": pages,
            "data": [
                {
                    "id":         u.id,
                    "full_name":  u.full_name,
                    "email":      u.email,
                    "role":       u.role,
                    "phone":      u.phone,
                    "is_active":  u.is_active,
                    "created_at": u.created_at,
                }
                for u in users
            ],
        }
    except SQLAlchemyError as e:
        logger.error(f"Get all users error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch users.")


@router.get(
    "/{user_id}",
    summary="Get single user detail (Admin only)",
    dependencies=[Depends(require_role("admin"))],
)
def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Returns full details of a single user.
    Admin only.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return {
        "id":         user.id,
        "full_name":  user.full_name,
        "email":      user.email,
        "role":       user.role,
        "phone":      user.phone,
        "is_active":  user.is_active,
        "created_at": user.created_at,
    }


@router.put(
    "/{user_id}/role",
    summary="Change user role (Admin only)",
    dependencies=[Depends(require_role("admin"))],
)
def update_user_role(
    user_id: int,
    data: RoleUpdate,
    db: Session = Depends(get_db),
):
    """
    Change a user's role.
    Allowed roles: student, trainer, admin
    Admin only.
    """
    allowed_roles = {"student", "trainer", "admin"}
    if data.role not in allowed_roles:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role. Allowed: {', '.join(allowed_roles)}"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    try:
        user.role = data.role
        db.commit()
        db.refresh(user)
        return {
            "message": f"Role updated to '{data.role}' successfully.",
            "user_id": user.id,
            "new_role": user.role,
        }
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Role update error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update role.")


@router.put(
    "/{user_id}/status",
    summary="Activate or deactivate a user (Admin only)",
    dependencies=[Depends(require_role("admin"))],
)
def toggle_user_status(
    user_id: int,
    db: Session = Depends(get_db),
):
    """
    Toggle a user's active status (ban/unban).
    Admin only.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    try:
        user.is_active = not user.is_active
        db.commit()
        db.refresh(user)
        action = "activated" if user.is_active else "deactivated"
        return {
            "message":   f"User {action} successfully.",
            "user_id":   user.id,
            "is_active": user.is_active,
        }
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Toggle status error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user status.")


@router.delete(
    "/{user_id}",
    summary="Delete a user permanently (Admin only)",
    dependencies=[Depends(require_role("admin"))],
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Permanently delete a user and all related data.
    Admin only. Admin cannot delete themselves.
    """
    # Admin cannot delete themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot delete your own account."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    try:
        db.delete(user)
        db.commit()
        return {"message": f"User '{user.full_name}' deleted successfully."}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Delete user error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete user.")