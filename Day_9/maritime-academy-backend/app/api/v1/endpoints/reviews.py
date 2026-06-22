import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db
from app.models.review import Review
from app.schemas.review_schema import ReviewResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get(
    "/featured",
    response_model=list[ReviewResponse],
    summary="Get Featured Reviews",
    description="Returns up to 5 featured reviews for the homepage."
)
def get_featured_reviews(db: Session = Depends(get_db)):
    try:
        reviews = db.query(Review).filter(
            Review.is_featured == True
        ).order_by(
            Review.created_at.desc()
        ).limit(5).all()
        
        return reviews
    
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching featured reviews: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve featured reviews."
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching featured reviews: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred."
        )