import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.schemas.enrollment_schema import EnrollmentCreate, EnrollmentResponse
from typing import List
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/enrollments", tags=["Enrollments"])


@router.post("/", response_model=EnrollmentResponse, status_code=201)
def enroll_course(
    enrollment_data: EnrollmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        course = db.query(Course).filter(Course.id == enrollment_data.course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Course not found."
            )
        
        existing = db.query(Enrollment).filter(
            Enrollment.user_id == current_user.id,
            Enrollment.course_id == enrollment_data.course_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Already enrolled in this course."
            )
        
        new_enrollment = Enrollment(
            user_id=current_user.id,
            course_id=enrollment_data.course_id,
            status="active",
            progress=0.0
        )
        db.add(new_enrollment)
        db.commit()
        db.refresh(new_enrollment)
        return new_enrollment
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error enrolling course: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enroll in course."
        )


@router.get("/my", response_model=List[EnrollmentResponse])
def get_my_enrollments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        enrollments = db.query(Enrollment).filter(
            Enrollment.user_id == current_user.id
        ).order_by(Enrollment.created_at.desc()).all()
        return enrollments
    except SQLAlchemyError as e:
        logger.error(f"Error fetching enrollments: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve enrollments."
        )


@router.put("/{enrollment_id}/progress")
def update_progress(
    enrollment_id: int,
    progress: float,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        enrollment = db.query(Enrollment).filter(
            Enrollment.id == enrollment_id,
            Enrollment.user_id == current_user.id
        ).first()
        if not enrollment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Enrollment not found."
            )
        enrollment.progress = progress
        if progress >= 100:
            enrollment.status = "completed"
            enrollment.completion_date = datetime.now()
        db.commit()
        return {"message": "Progress updated."}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error updating progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update progress."
        )