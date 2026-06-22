import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.course import Course
from app.models.course_curriculum import CourseCurriculum
from app.models.course_schedule import CourseSchedule
from app.schemas.course_schema import (
    CourseCreate, CourseUpdate, CourseResponse, 
    CourseCurriculumCreate, CourseCurriculumResponse,
    CourseScheduleCreate, CourseScheduleResponse,
    CourseListResponse
)

from app.tasks.email_tasks import send_matching_alerts

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/courses", tags=["Courses"])


# ==================== Course CRUD ====================

@router.get(
    "/",
    response_model=CourseListResponse,
    summary="List all courses",
    description="Returns paginated list of active courses. Supports filtering by category and location."
)
def list_courses(
    category: Optional[str] = Query(None, description="Filter by category (Maritime, Ship Handling, Safety, Sailor, Drying)"),
    location: Optional[str] = Query(None, description="Filter by location (Italy, Turkey, London)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(12, ge=1, le=100, description="Number of records to return"),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Course).filter(Course.status == "active")
        
        if category:
            query = query.filter(Course.category == category)
        if location:
            query = query.filter(Course.location == location)
        
        total = query.count()
        courses = query.order_by(Course.created_at.desc()).offset(skip).limit(limit).all()
        
        # Convert to response schema with curriculum and schedules
        course_responses = []
        for course in courses:
            curriculum = db.query(CourseCurriculum).filter(CourseCurriculum.course_id == course.id).order_by(CourseCurriculum.day_number).all()
            schedules = db.query(CourseSchedule).filter(CourseSchedule.course_id == course.id).all()
            
            course_responses.append(
                CourseResponse(
                    **course.__dict__,
                    curriculum=[CourseCurriculumResponse.model_validate(c) for c in curriculum],
                    schedules=[CourseScheduleResponse.model_validate(s) for s in schedules]
                )
            )
        
        return CourseListResponse(
            total=total,
            page=skip // limit + 1 if limit > 0 else 1,
            pages=(total + limit - 1) // limit if limit > 0 else 0,
            courses=course_responses
        )
    
    except SQLAlchemyError as e:
        logger.error(f"Database error in list_courses: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve courses."
        )


@router.get(
    "/{course_id}",
    response_model=CourseResponse,
    summary="Get course details",
    description="Returns full course details including curriculum and schedules."
)
def get_course(
    course_id: int = Path(..., gt=0, description="Course ID must be greater than 0"),
    db: Session = Depends(get_db)
):
    try:
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found."
            )
        
        curriculum = db.query(CourseCurriculum).filter(CourseCurriculum.course_id == course.id).order_by(CourseCurriculum.day_number).all()
        schedules = db.query(CourseSchedule).filter(CourseSchedule.course_id == course.id).all()
        
        return CourseResponse(
            **course.__dict__,
            curriculum=[CourseCurriculumResponse.model_validate(c) for c in curriculum],
            schedules=[CourseScheduleResponse.model_validate(s) for s in schedules]
        )
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_course: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve course details."
        )


@router.post(
    "/",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new course",
    description="Create a new course. Requires admin or trainer role. Triggers email alerts to users with matching preferences."
)
def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(require_role("trainer")),
    db: Session = Depends(get_db)
):
    try:
        # Check if course with same title exists
        existing = db.query(Course).filter(Course.title == course_data.title).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A course with this title already exists."
            )
        
        # Set instructor_id if not provided
        if not course_data.instructor_id:
            course_data.instructor_id = current_user.id
        
        new_course = Course(**course_data.dict())
        db.add(new_course)
        db.commit()
        db.refresh(new_course)
        
        # Trigger matching alerts via Celery (only if course is active)
        if new_course.status == "active":
            try:
                send_matching_alerts.delay(new_course.id)
                logger.info(f"Matching alerts queued for course {new_course.id}")
            except Exception as e:
                # Log but don't fail the course creation if Celery is down
                logger.error(f"Failed to queue matching alerts: {str(e)}")
        
        return CourseResponse(
            **new_course.__dict__,
            curriculum=[],
            schedules=[]
        )
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error in create_course: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create course."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in create_course: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred."
        )



@router.put(
    "/{course_id}",
    response_model=CourseResponse,
    summary="Update a course",
    description="Update an existing course. Requires admin or trainer role."
)
def update_course(
    course_id: int = Path(..., gt=0),
    course_data: CourseUpdate = None,
    current_user: User = Depends(require_role("trainer")),
    db: Session = Depends(get_db)
):
    try:
        if course_data is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Request body is required."
            )
        
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found."
            )
        
        # Check title uniqueness if being updated
        if course_data.title and course_data.title != course.title:
            existing = db.query(Course).filter(Course.title == course_data.title).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A course with this title already exists."
                )
        
        # Update fields
        for key, value in course_data.dict(exclude_unset=True).items():
            setattr(course, key, value)
        
        db.commit()
        db.refresh(course)
        
        curriculum = db.query(CourseCurriculum).filter(CourseCurriculum.course_id == course.id).order_by(CourseCurriculum.day_number).all()
        schedules = db.query(CourseSchedule).filter(CourseSchedule.course_id == course.id).all()
        
        return CourseResponse(
            **course.__dict__,
            curriculum=[CourseCurriculumResponse.model_validate(c) for c in curriculum],
            schedules=[CourseScheduleResponse.model_validate(s) for s in schedules]
        )
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error in update_course: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update course."
        )


@router.delete(
    "/{course_id}",
    response_model=dict,
    summary="Delete a course",
    description="Soft delete a course (sets status to 'inactive'). Requires admin role."
)
def delete_course(
    course_id: int = Path(..., gt=0),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    try:
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found."
            )
        
        # Soft delete: set status to inactive
        course.status = "inactive"
        db.commit()
        
        return {"message": "Course deleted successfully."}
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error in delete_course: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete course."
        )


# ==================== Course Curriculum ====================

@router.get(
    "/{course_id}/curriculum",
    response_model=list[CourseCurriculumResponse],
    summary="Get course curriculum",
    description="Returns Day 1-5 curriculum modules for a course."
)
def get_curriculum(
    course_id: int = Path(..., gt=0),
    db: Session = Depends(get_db)
):
    try:
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found."
            )
        
        curriculum = db.query(CourseCurriculum).filter(
            CourseCurriculum.course_id == course_id
        ).order_by(
            CourseCurriculum.day_number
        ).all()
        
        return curriculum
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_curriculum: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve curriculum."
        )


@router.post(
    "/{course_id}/curriculum",
    response_model=CourseCurriculumResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add curriculum day to course",
    description="Add a Day 1-5 module to a course. Requires admin or trainer role."
)
def add_curriculum_day(
    course_id: int = Path(..., gt=0),
    curriculum_data: CourseCurriculumCreate = None,
    current_user: User = Depends(require_role("trainer")),
    db: Session = Depends(get_db)
):
    try:
        if curriculum_data is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Request body is required."
            )
        
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {course_id} not found."
            )
        
        # Check if day already exists
        existing = db.query(CourseCurriculum).filter(
            CourseCurriculum.course_id == course_id,
            CourseCurriculum.day_number == curriculum_data.day_number
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Day {curriculum_data.day_number} already exists for this course."
            )
        
        new_curriculum = CourseCurriculum(
            course_id=course_id,
            **curriculum_data.dict()
        )
        db.add(new_curriculum)
        db.commit()
        db.refresh(new_curriculum)
        
        return new_curriculum
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error in add_curriculum_day: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add curriculum day."
        )


@router.put(
    "/{course_id}/curriculum/{day_number}",
    response_model=CourseCurriculumResponse,
    summary="Update curriculum day",
    description="Update a specific day's curriculum. Requires admin or trainer role."
)
def update_curriculum_day(
    course_id: int = Path(..., gt=0),
    day_number: int = Path(..., ge=1, le=5),
    curriculum_data: CourseCurriculumCreate = None,
    current_user: User = Depends(require_role("trainer")),
    db: Session = Depends(get_db)
):
    try:
        if curriculum_data is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Request body is required."
            )
        
        curriculum = db.query(CourseCurriculum).filter(
            CourseCurriculum.course_id == course_id,
            CourseCurriculum.day_number == day_number
        ).first()
        
        if not curriculum:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Day {day_number} not found for this course."
            )
        
        # Update fields
        for key, value in curriculum_data.dict(exclude_unset=True).items():
            setattr(curriculum, key, value)
        
        db.commit()
        db.refresh(curriculum)
        
        return curriculum
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error in update_curriculum_day: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update curriculum day."
        )


@router.delete(
    "/{course_id}/curriculum/{day_number}",
    response_model=dict,
    summary="Delete curriculum day",
    description="Delete a specific day's curriculum. Requires admin role."
)
def delete_curriculum_day(
    course_id: int = Path(..., gt=0),
    day_number: int = Path(..., ge=1, le=5),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    try:
        curriculum = db.query(CourseCurriculum).filter(
            CourseCurriculum.course_id == course_id,
            CourseCurriculum.day_number == day_number
        ).first()
        
        if not curriculum:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Day {day_number} not found for this course."
            )
        
        db.delete(curriculum)
        db.commit()
        
        return {"message": f"Day {day_number} deleted successfully."}
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error in delete_curriculum_day: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete curriculum day."
        )


# ==================== Course Categories ====================

@router.get(
    "/categories",
    response_model=list,
    summary="Get all course categories",
    description="Returns a list of all available course categories."
)
def get_categories(db: Session = Depends(get_db)):
    categories = ["Maritime", "Ship Handling", "Safety", "Sailor", "Drying"]
    return [{"name": cat, "label": cat} for cat in categories]


# ==================== Course Locations ====================
# set of valid locations is defined in the Course model and can be extended as needed
@router.get(
    "/locations",
    response_model=list,
    summary="Get all course locations",
    description="Returns a list of all available course locations."
)   
def get_locations(db: Session = Depends(get_db)):
    locations = ["Italy", "Turkey", "London"]
    return [{"name": loc, "label": loc} for loc in locations]
