import logging
import stripe
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.payment import Payment
from app.models.booking import Booking
from app.services.payment_service import PaymentService
from app.schemas.payment_schema import PaymentCreate

 
stripe.api_key = settings.STRIPE_SECRET_KEY

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post(
    "/create-intent",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Create Payment Intent",
    description="Creates a Stripe payment intent for a booking."
)
def create_payment_intent(
    payment_data: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Verify booking exists and belongs to user
        booking = db.query(Booking).filter(
            Booking.id == payment_data.booking_id,
            Booking.user_id == current_user.id
        ).first()
        if not booking:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Booking not found or does not belong to user."
            )

        # Create payment intent
        intent = PaymentService.create_payment_intent(
            amount=float(booking.total_price),
            currency="usd",
            metadata={
                "booking_id": str(booking.id),
                "user_id": str(current_user.id),
                "booking_type": "trip"
            }
        )

        # Create payment record
        payment = Payment(
            user_id=current_user.id,
            booking_id=booking.id,
            amount=booking.total_price,
            currency="usd",
            stripe_payment_intent_id=intent["payment_intent_id"],
            status="pending"
        )
        db.add(payment)
        db.commit()

        return {
            "client_secret": intent["client_secret"],
            "payment_intent_id": intent["payment_intent_id"],
            "amount": intent["amount"],
            "currency": intent["currency"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating payment intent: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create payment: {str(e)}"
        )


@router.post(
    "/webhook",
    summary="Stripe Webhook",
    description="Handles Stripe webhook events for payment confirmation."
)
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        # Verify webhook signature (in production)
        # event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)

        # Mock for now - just log the event
        logger.info("Webhook received")
        return {"status": "success"}

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed."
        )


@router.get(
    "/history",
    response_model=list,
    summary="Get Payment History",
    description="Returns payment history for the authenticated user."
)
def get_payment_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        payments = db.query(Payment).filter(
            Payment.user_id == current_user.id
        ).order_by(Payment.created_at.desc()).all()
        return payments

    except SQLAlchemyError as e:
        logger.error(f"Error getting payment history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve payment history."
        )

# ==================== Payment Verification ====================
@router.get(
    "/verify/{payment_intent_id}",
    response_model=dict,
    summary="Verify Payment Status",
    description="Synchronously verify the status of a payment with Stripe."
)
def verify_payment(
    payment_intent_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        payment = db.query(Payment).filter(
            Payment.stripe_payment_intent_id == payment_intent_id,
            Payment.user_id == current_user.id
        ).first()
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        
        if intent.status == "succeeded" and payment.status != "completed":
            payment.status = "completed"
            db.commit()
            booking = db.query(Booking).filter(Booking.id == payment.booking_id).first()
            if booking:
                booking.payment_status = "paid"
                db.commit()
        
        elif intent.status == "canceled" and payment.status != "cancelled":
            payment.status = "cancelled"
            db.commit()
        
        return {
            "payment_id": payment.id,
            "payment_intent_id": payment_intent_id,
            "status": intent.status,
            "amount": intent.amount / 100,
            "currency": intent.currency,
            "booking_id": payment.booking_id,
            "is_completed": intent.status == "succeeded"
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify payment with Stripe"
        )
    except Exception as e:
        logger.error(f"Verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify payment"
        )


@router.get(
    "/{payment_id}/status",
    response_model=dict,
    summary="Get Payment Status",
    description="Get payment status from our database (not Stripe)."
)
def get_payment_status(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        payment = db.query(Payment).filter(
            Payment.id == payment_id,
            Payment.user_id == current_user.id
        ).first()
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        return {
            "payment_id": payment.id,
            "payment_intent_id": payment.stripe_payment_intent_id,
            "status": payment.status,
            "amount": payment.amount,
            "currency": payment.currency,
            "booking_id": payment.booking_id,
            "created_at": payment.created_at,
            "updated_at": payment.updated_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting payment status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get payment status"
        )
