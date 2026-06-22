import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db
from app.models.platform_stat import PlatformStat
from app.models.user import User
from app.models.course import Course
from app.models.trip import Trip
from app.models.booking import Booking
from app.schemas.platform_schema import PlatformStatsResponse
from app.models.enrollment import Enrollment

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/platform", tags=["Platform"])


@router.get(
    "/stats",
    response_model=PlatformStatsResponse,
    summary="Get Platform Statistics",
    description="Returns platform statistics including static values (150+, 50+, 1000M, 25+) and real-time counts."
)
def get_platform_stats(db: Session = Depends(get_db)):
    try:
        # Get static stats from platform_stats table with fallback defaults
        stats_dict = {
            "projects_delivered": 150,
            "happy_clients": 50,
            "social_base": 1000000000,
            "years_experience": 25
        }
        
        try:
            stats = db.query(PlatformStat).all()
            for stat in stats:
                if stat.stat_key == "projects_delivered":
                    stats_dict["projects_delivered"] = stat.stat_value
                elif stat.stat_key == "happy_clients":
                    stats_dict["happy_clients"] = stat.stat_value
                elif stat.stat_key == "social_base":
                    stats_dict["social_base"] = stat.stat_value
                elif stat.stat_key == "years_experience":
                    stats_dict["years_experience"] = stat.stat_value
        except SQLAlchemyError as e:
            logger.warning(f"Could not fetch platform_stats from database: {str(e)}")
        
        # Get real-time dynamic counts
        total_users = db.query(User).count()
        total_courses = db.query(Course).filter(Course.status == "active").count()
        total_trips = db.query(Trip).filter(Trip.status == "active").count()
        total_bookings = db.query(Booking).count()
        total_enrollments = db.query(Enrollment).count() if 'Enrollment' in locals() else 0
        
        return PlatformStatsResponse(
            projects_delivered=stats_dict["projects_delivered"],
            happy_clients=stats_dict["happy_clients"],
            social_base=stats_dict["social_base"],
            years_experience=stats_dict["years_experience"],
            total_users=total_users,
            total_courses=total_courses,
            total_trips=total_trips,
            total_bookings=total_bookings,
            total_enrollments=total_enrollments
        )
    
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_platform_stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve platform statistics."
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_platform_stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred."
        )