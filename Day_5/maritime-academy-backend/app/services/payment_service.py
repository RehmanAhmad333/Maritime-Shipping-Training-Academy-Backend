import stripe
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentService:
    @staticmethod
    def create_payment_intent(amount: float, currency: str = "usd", metadata: dict = None):
        """
        Create a Stripe Payment Intent for course or trip booking.
        """
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency,
                metadata=metadata or {},
                automatic_payment_methods={"enabled": True}
            )
            return {
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id,
                "amount": amount,
                "currency": currency,
                "status": intent.status
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            raise Exception(f"Payment creation failed: {str(e)}")

    @staticmethod
    def confirm_payment(payment_intent_id: str):
        """
        Confirm a payment intent.
        """
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            if intent.status == "succeeded":
                return {"status": "succeeded", "payment_intent_id": payment_intent_id}
            else:
                return {"status": intent.status, "payment_intent_id": payment_intent_id}
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            raise Exception(f"Payment confirmation failed: {str(e)}")

    @staticmethod
    def refund_payment(payment_intent_id: str, amount: float = None):
        """
        Refund a payment.
        """
        try:
            refund_params = {"payment_intent": payment_intent_id}
            if amount:
                refund_params["amount"] = int(amount * 100)
            refund = stripe.Refund.create(**refund_params)
            return {"refund_id": refund.id, "status": refund.status}
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            raise Exception(f"Refund failed: {str(e)}")