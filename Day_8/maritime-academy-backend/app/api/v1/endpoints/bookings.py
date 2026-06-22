# app/api/v1/endpoints/bookings.py

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.booking import Booking
from app.schemas.booking_schema import BookingResponse
from typing import List

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/bookings", tags=["Bookings"])


# ==================== Admin Endpoints ====================

@router.get(
    "/",
    response_model=List[BookingResponse],
    summary="Get all bookings (Admin only)",
    description="Returns all bookings in the system. Only accessible by admin."
)
def get_all_bookings(
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    try:
        bookings = db.query(Booking).order_by(Booking.created_at.desc()).all()
        return bookings
    except SQLAlchemyError as e:
        logger.error(f"Error fetching all bookings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bookings."
        )


# ==================== User Booking Endpoints ====================

@router.get(
    "/my",
    response_model=List[BookingResponse],
    summary="Get my bookings",
    description="Returns all bookings for the authenticated user."
)
def get_my_bookings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        bookings = db.query(Booking).filter(
            Booking.user_id == current_user.id
        ).order_by(Booking.created_at.desc()).all()
        return bookings
    except SQLAlchemyError as e:
        logger.error(f"Error fetching bookings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bookings."
        )


@router.get(
    "/{booking_id}",
    response_model=BookingResponse,
    summary="Get booking details",
    description="Returns details of a specific booking."
)
def get_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        booking = db.query(Booking).filter(
            Booking.id == booking_id,
            Booking.user_id == current_user.id
        ).first()
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found."
            )
        return booking
    except SQLAlchemyError as e:
        logger.error(f"Error fetching booking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve booking."
        )


@router.put(
    "/{booking_id}/status",
    summary="Update booking status",
    description="Update booking status (confirmed, cancelled). Admin only."
)
def update_booking_status(
    booking_id: int,
    status: str,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found."
            )
        booking.status = status
        db.commit()
        return {"message": f"Booking {status} successfully."}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error updating booking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update booking."
        )


@router.delete(
    "/{booking_id}/cancel",
    summary="Cancel booking",
    description="Cancel a booking. Only the booking owner can cancel."
)
def cancel_booking(
    booking_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        booking = db.query(Booking).filter(
            Booking.id == booking_id,
            Booking.user_id == current_user.id
        ).first()
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found."
            )
        
        booking.status = "cancelled"
        db.commit()
        return {"message": "Booking cancelled successfully."}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error cancelling booking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel booking."
        )