import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.course import Course
from app.models.trip import Trip
from app.models.booking import Booking
from app.models.enrollment import Enrollment
from app.models.payment import Payment
from app.models.certification import Certification

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_role("admin"))]
)


@router.get(
    "/dashboard/stats",
    response_model=dict,
    summary="Get Admin Dashboard Statistics",
    description="Returns aggregated platform statistics for admin dashboard."
)
def admin_stats(db: Session = Depends(get_db)):
    try:
        total_users = db.query(User).count()
        total_courses = db.query(Course).filter(Course.status == "active").count()
        total_trips = db.query(Trip).filter(Trip.status == "active").count()
        total_bookings = db.query(Booking).count()
        total_enrollments = db.query(Enrollment).count()
        total_payments = db.query(Payment).filter(Payment.status == "completed").count()
        total_certifications = db.query(Certification).count()
        
        # Recent activity (last 30 days)
        from datetime import datetime, timedelta
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_users = db.query(User).filter(User.created_at >= thirty_days_ago).count()
        recent_bookings = db.query(Booking).filter(Booking.created_at >= thirty_days_ago).count()
        
        return {
            "total_users": total_users,
            "total_courses": total_courses,
            "total_trips": total_trips,
            "total_bookings": total_bookings,
            "total_enrollments": total_enrollments,
            "total_payments": total_payments,
            "total_certifications": total_certifications,
            "recent_users": recent_users,
            "recent_bookings": recent_bookings
        }
    
    except SQLAlchemyError as e:
        logger.error(f"Database error in admin_stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard statistics."
        )
    except Exception as e:
        logger.error(f"Unexpected error in admin_stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred."
        )


