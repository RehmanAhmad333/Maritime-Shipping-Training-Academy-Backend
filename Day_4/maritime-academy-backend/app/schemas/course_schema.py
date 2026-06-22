from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

# ---------- Course Curriculum Schemas ----------
class CourseCurriculumBase(BaseModel):
    day_number: int
    title: str
    point_1: Optional[str] = None
    point_2: Optional[str] = None

class CourseCurriculumCreate(CourseCurriculumBase):
    pass

class CourseCurriculumResponse(CourseCurriculumBase):
    id: int
    course_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Course Schedule Schemas ----------
class CourseScheduleBase(BaseModel):
    start_date: date
    end_date: date
    time_slot: Optional[str] = None
    capacity: int
    booked: Optional[int] = 0
    status: Optional[str] = "available"

class CourseScheduleCreate(CourseScheduleBase):
    pass

class CourseScheduleResponse(CourseScheduleBase):
    id: int
    course_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- Course Schemas ----------
class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    duration_days: Optional[int] = None
    instructor_id: Optional[int] = None
    max_students: Optional[int] = None
    location: Optional[str] = None
    image_url: Optional[str] = None
    status: Optional[str] = "active"

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    duration_days: Optional[int] = None
    instructor_id: Optional[int] = None
    max_students: Optional[int] = None
    location: Optional[str] = None
    image_url: Optional[str] = None
    status: Optional[str] = None

class CourseResponse(CourseBase):
    id: int
    instructor_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    curriculum: List[CourseCurriculumResponse] = []
    schedules: List[CourseScheduleResponse] = []

    class Config:
        from_attributes = True


# ---------- Paginated Course Response ----------
class CourseListResponse(BaseModel):
    total: int
    page: int
    pages: int
    courses: List[CourseResponse]