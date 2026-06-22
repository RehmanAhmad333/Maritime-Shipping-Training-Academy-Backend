from pydantic import BaseModel

class PlatformStatsResponse(BaseModel):
    projects_delivered: int
    happy_clients: int
    social_base: int
    years_experience: int
    total_users: int
    total_courses: int
    total_trips: int
    total_bookings: int
    total_enrollments: int

    class Config:
        from_attributes = True