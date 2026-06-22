import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.shipping_service import ShippingService
from app.schemas.shipping_schema import ShippingCreate, ShippingResponse , ShippingUpdate
from typing import List

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/shipping", tags=["Shipping Services"])


@router.get("/", response_model=List[ShippingResponse])
def list_shipping_services(db: Session = Depends(get_db)):
    try:
        services = db.query(ShippingService).filter(
            ShippingService.status == "active"
        ).all()
        return services
    except SQLAlchemyError as e:
        logger.error(f"Error fetching shipping services: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve shipping services."
        )


@router.get("/{service_id}", response_model=ShippingResponse)
def get_shipping_service(service_id: int, db: Session = Depends(get_db)):
    try:
        service = db.query(ShippingService).filter(ShippingService.id == service_id).first()
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shipping service not found."
            )
        return service
    except SQLAlchemyError as e:
        logger.error(f"Error fetching shipping service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve shipping service."
        )


@router.post("/", response_model=ShippingResponse, status_code=201)
def create_shipping_service(
    service_data: ShippingCreate,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    try:
        new_service = ShippingService(**service_data.dict())
        db.add(new_service)
        db.commit()
        db.refresh(new_service)
        return new_service
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating shipping service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create shipping service."
        )


@router.put("/{service_id}", response_model=ShippingResponse)
def update_shipping_service(
    service_id: int,
    service_data: ShippingUpdate,  
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    try:
        service = db.query(ShippingService).filter(ShippingService.id == service_id).first()
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shipping service not found."
            )
        
        update_data = service_data.dict(exclude_unset=True)
        
        for key, value in update_data.items():
            setattr(service, key, value)
        
        db.commit()
        db.refresh(service)
        return service
        
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error updating shipping service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update shipping service."
        )


@router.delete("/{service_id}")
def delete_shipping_service(
    service_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    try:
        service = db.query(ShippingService).filter(ShippingService.id == service_id).first()
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shipping service not found."
            )
        
        service.status = "inactive"
        db.commit()
        return {"message": "Shipping service deleted successfully."}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error deleting shipping service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete shipping service."
        )

@router.post("/{service_id}/book")
def book_shipping_service(
    service_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        service = db.query(ShippingService).filter(ShippingService.id == service_id).first()
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shipping service not found."
            )
        
        # Create a booking record
        # You'll need a shipping_bookings table or extend the bookings table
        # For now, return a proper response
        return {
            "message": "Shipping service booked successfully.",
            "service_id": service_id,
            "service_title": service.title,
            "user_id": current_user.id,
            "booking_status": "pending",
            "booking_id": None  # Placeholder until table is created
        }
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error booking shipping service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to book shipping service."
        )