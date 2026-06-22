import logging
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text


from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.trip import Trip
from app.models.booking import Booking
from app.schemas.trip_schema import (
    TripCreate, TripUpdate, TripResponse, 
    TripBookingRequest, TripBookingResponse,
    TripListResponse
)
from app.schemas.booking_schema import MyBookingResponse
from typing import List

from app.tasks.email_tasks import send_booking_confirmation

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trips", tags=["Trips"])


# ==================== Trip CRUD ====================

@router.get(
    "/",
    response_model=TripListResponse,
    summary="List all trips",
    description="Returns paginated list of active trips. Supports filtering by location and featured status."
)
def list_trips(
    location: Optional[str] = Query(None, description="Filter by location (Italy, Turkey, London)"),
    featured_only: Optional[bool] = Query(False, description="Get only featured trips"),
    available_only: Optional[bool] = Query(False, description="Get only trips with available slots"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(12, ge=1, le=100, description="Number of records to return"),
    db: Session = Depends(get_db)
):
    try:
        query = db.query(Trip).filter(Trip.status == "active")
        
        if location:
            query = query.filter(Trip.location_name == location)
        
        if featured_only:
            query = query.filter(Trip.is_featured == True)
        
        if available_only:
            query = query.filter(Trip.booked_slots < Trip.max_slots)
        
        total = query.count()
        trips = query.order_by(Trip.is_featured.desc(), Trip.rating.desc()).offset(skip).limit(limit).all()
        
        # Convert to response with available_slots
        trip_responses = []
        for trip in trips:
            trip_dict = {
                **trip.__dict__,
                "available_slots": trip.max_slots - trip.booked_slots
            }
            trip_responses.append(TripResponse(**trip_dict))
        
        return TripListResponse(
            total=total,
            page=skip // limit + 1 if limit > 0 else 1,
            pages=(total + limit - 1) // limit if limit > 0 else 0,
            trips=trip_responses
        )
    
    except SQLAlchemyError as e:
        logger.error(f"Database error in list_trips: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trips."
        )


@router.get(
    "/featured",
    response_model=list[TripResponse],
    summary="Get featured trips",
    description="Returns all trips marked as featured (Italy style with TOP RATING)."
)
def get_featured_trips(
    db: Session = Depends(get_db)
):
    try:
        featured_trips = db.query(Trip).filter(
            Trip.is_featured == True,
            Trip.status == "active"
        ).order_by(Trip.rating.desc()).all()
        
        trip_responses = []
        for trip in featured_trips:
            trip_dict = {
                **trip.__dict__,
                "available_slots": trip.max_slots - trip.booked_slots
            }
            trip_responses.append(TripResponse(**trip_dict))
        
        return trip_responses
    
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_featured_trips: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve featured trips."
        )

# trip location filter endpoint
@router.get(
    "/locations",
    response_model=list[str],
    summary="Get unique trip locations",
    description="Returns a list of unique trip locations for filtering purposes."
)
def get_trip_locations(
    db: Session = Depends(get_db)
):
    try:
        locations = db.query(Trip.country).filter(Trip.status == "active").distinct().all()
        return [loc[0] for loc in locations]
    
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_trip_locations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trip locations."
        )

@router.get(
    "/{trip_id}",
    response_model=TripResponse,
    summary="Get trip details",
    description="Returns full details of a specific trip."
)
def get_trip(
    trip_id: int = Path(..., gt=0, description="Trip ID must be greater than 0"),
    db: Session = Depends(get_db)
):
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trip with ID {trip_id} not found."
            )
        
        trip_dict = {
            **trip.__dict__,
            "available_slots": trip.max_slots - trip.booked_slots
        }
        return TripResponse(**trip_dict)
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_trip: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve trip details."
        )


@router.post(
    "/",
    response_model=TripResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new trip",
    description="Create a new trip. Requires admin role."
)
def create_trip(
    trip_data: TripCreate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    try:
        # Check if trip with same location and date exists
        existing = db.query(Trip).filter(
            Trip.location_name == trip_data.location_name,
            Trip.start_date == trip_data.start_date
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A trip to this location on this date already exists."
            )
        
        new_trip = Trip(**trip_data.dict())
        db.add(new_trip)
        db.commit()
        db.refresh(new_trip)
        
        trip_dict = {
            **new_trip.__dict__,
            "available_slots": new_trip.max_slots - new_trip.booked_slots
        }
        return TripResponse(**trip_dict)
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error in create_trip: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create trip."
        )

@router.post("/{trip_id}/book", response_model=TripBookingResponse, status_code=201)
def book_trip(
    trip_id: int = Path(..., gt=0),
    booking_data: TripBookingRequest = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if booking_data is None:
            booking_data = TripBookingRequest()
        
        # Validate number of people
        if booking_data.number_of_people < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Number of people must be at least 1."
            )
        
        # ATOMIC BOOKING: Update trip slots using atomic SQL
        result = db.execute(
            text("""
                UPDATE trips 
                SET booked_slots = booked_slots + :num_people 
                WHERE id = :trip_id 
                AND status = 'active'
                AND booked_slots + :num_people <= max_slots
                RETURNING id, price, booked_slots, max_slots, location_name, country
            """),
            {
                "trip_id": trip_id,
                "num_people": booking_data.number_of_people
            }
        )
        
        trip = result.first()
        
        if not trip:
            # Check if trip exists at all
            trip_exists = db.query(Trip).filter(Trip.id == trip_id).first()
            if not trip_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Trip with ID {trip_id} not found."
                )
            
            # If exists but no slots available
            if trip_exists.status != "active":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This trip is no longer active."
                )
            
            available = trip_exists.max_slots - trip_exists.booked_slots
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {available} slot(s) available. You requested {booking_data.number_of_people}."
            )
        
        # Create booking record
        total_price = trip.price * booking_data.number_of_people
        booking = Booking(
            user_id=current_user.id,
            trip_id=trip_id,
            number_of_people=booking_data.number_of_people,
            total_price=total_price,
            status="confirmed",
            payment_status="pending"
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)
        
        # Send confirmation email via Celery
        try:
            send_booking_confirmation.delay(
                current_user.email,
                current_user.full_name,
                trip.location_name,
                trip.country,
                booking.id
            )
            logger.info(f"Booking confirmation email queued for {current_user.email}")
        except Exception as e:
            logger.error(f"Failed to queue booking confirmation email: {str(e)}")
        
        return TripBookingResponse(
            message="Trip booked successfully!",
            booking_id=booking.id,
            trip_id=trip_id,
            total_price=total_price,
            number_of_people=booking_data.number_of_people,
            booking_date=booking.created_at
        )
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error in book_trip: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to book trip due to database error."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in book_trip: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while booking."
        )


@router.delete(
    "/{trip_id}",
    response_model=dict,
    summary="Delete a trip",
    description="Soft delete a trip (sets status to 'inactive'). Requires admin role."
)
def delete_trip(
    trip_id: int = Path(..., gt=0),
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    try:
        trip = db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trip with ID {trip_id} not found."
            )
        
        # Soft delete
        trip.status = "inactive"
        db.commit()
        
        return {"message": "Trip deleted successfully."}
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error in delete_trip: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete trip."
        )


# ==================== Atomic Booking ====================

@router.post(
    "/{trip_id}/book",
    response_model=TripBookingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Book a trip",
    description="Atomically books a trip slot. Prevents overbooking even under high concurrency."
)
def book_trip(
    trip_id: int = Path(..., gt=0),
    booking_data: TripBookingRequest = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if booking_data is None:
            booking_data = TripBookingRequest()
        
        # Validate number of people
        if booking_data.number_of_people < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Number of people must be at least 1."
            )
        
        # ATOMIC BOOKING: Update trip slots using atomic SQL
        result = db.execute(
            text("""
                UPDATE trips 
                SET booked_slots = booked_slots + :num_people 
                WHERE id = :trip_id 
                AND status = 'active'
                AND booked_slots + :num_people <= max_slots
                RETURNING id, price, booked_slots, max_slots, location_name
            """),
            {
                "trip_id": trip_id,
                "num_people": booking_data.number_of_people
            }
        )
        
        trip = result.first()
        
        if not trip:
            # Check if trip exists at all
            trip_exists = db.query(Trip).filter(Trip.id == trip_id).first()
            if not trip_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Trip with ID {trip_id} not found."
                )
            
            # If exists but no slots available
            if trip_exists.status != "active":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This trip is no longer active."
                )
            
            available = trip_exists.max_slots - trip_exists.booked_slots
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {available} slot(s) available. You requested {booking_data.number_of_people}."
            )
        
        # Create booking record
        total_price = trip.price * booking_data.number_of_people
        booking = Booking(
            user_id=current_user.id,
            trip_id=trip_id,
            number_of_people=booking_data.number_of_people,
            total_price=total_price,
            status="confirmed",
            payment_status="pending"
        )
        db.add(booking)
        db.commit()
        db.refresh(booking)
        
        return TripBookingResponse(
            message="Trip booked successfully!",
            booking_id=booking.id,
            trip_id=trip_id,
            total_price=total_price,
            number_of_people=booking_data.number_of_people,
            booking_date=booking.created_at
        )
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error in book_trip: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to book trip due to database error."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in book_trip: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while booking."
        )


# ==================== User Bookings ====================

@router.get(
    "/bookings/my",
    response_model=List[MyBookingResponse],  
    summary="Get current user's bookings",
    description="Returns all bookings made by the authenticated user."
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
        logger.error(f"Database error in get_my_bookings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bookings."
        )



@router.delete(
    "/bookings/{booking_id}/cancel",
    response_model=dict,
    summary="Cancel a booking",
    description="Cancel a booking and release the slot back to the trip."
)
def cancel_booking(
    booking_id: int = Path(..., gt=0),
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
        
        # Release the slot back to the trip
        trip = db.query(Trip).filter(Trip.id == booking.trip_id).first()
        if trip:
            trip.booked_slots = trip.booked_slots - booking.number_of_people
            if trip.booked_slots < 0:
                trip.booked_slots = 0
            db.add(trip)
        
        # Cancel booking
        booking.status = "cancelled"
        db.commit()
        
        return {"message": "Booking cancelled successfully."}
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error in cancel_booking: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel booking."
        )