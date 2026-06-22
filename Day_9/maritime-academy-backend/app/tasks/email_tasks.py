import logging
import json
from datetime import datetime, timedelta
from celery import Task
from sendgrid.helpers.mail import Mail
from app.tasks.celery_app import celery_app
from app.services.email_service import send_email_sync
from app.core.database import SessionLocal
from app.models.user import User
from app.models.email_alert import EmailAlert
from app.models.course import Course
from app.models.trip import Trip

logger = logging.getLogger(__name__)


class BaseTaskWithRetry(Task):
    """Base task with automatic retry on failure."""
    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3, "countdown": 60}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True


# ==================== 1. Send Inquiry Email ====================
@celery_app.task(base=BaseTaskWithRetry, bind=True, name="app.tasks.email_tasks.send_inquiry_email")
def send_inquiry_email(self, seller_email: str, buyer_name: str, property_title: str, message: str):
    """Send inquiry email to seller when buyer asks about a property."""
    try:
        if not seller_email:
            logger.warning("Seller email is missing, cannot send inquiry email.")
            return {"status": "error", "message": "Seller email missing"}

        subject = f"New Inquiry: {property_title}"
        content = f"""
        New inquiry for your property: {property_title}
        
        From: {buyer_name}
        
        Message:
        {message}
        
        Please login to your dashboard to reply.
        """

        result = send_email_sync(seller_email, subject, content.strip())

        if result and result.get("status") == 200:
            logger.info(f"Inquiry email sent to {seller_email}")
            return {"status": "success", "email": seller_email}
        else:
            logger.error(f"Failed to send inquiry email to {seller_email}: {result}")
            raise Exception(f"SendGrid returned: {result}")

    except Exception as e:
        logger.error(f"Error sending inquiry email to {seller_email}: {str(e)}")
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


# ==================== 2. Send Matching Alerts ====================
@celery_app.task(base=BaseTaskWithRetry, bind=True, name="app.tasks.email_tasks.send_matching_alerts")
def send_matching_alerts(self, course_id: int):
    """Send alerts to users when a new course matches their saved criteria."""
    db = SessionLocal()
    try:
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            logger.warning(f"Course {course_id} not found")
            return {"status": "error", "message": "Course not found"}

        if course.status != "active":
            logger.info(f"Course {course_id} is not active, skipping alerts")
            return {"status": "skipped", "reason": "Course not active"}

        # Get all active alerts
        alerts = db.query(EmailAlert).filter(EmailAlert.is_active == True).all()
        sent_count = 0

        for alert in alerts:
            try:
                filters = json.loads(alert.filters_json) if isinstance(alert.filters_json, str) else alert.filters_json
                
                # Check if course matches filters
                matches = True
                if filters.get("category") and filters["category"] != course.category:
                    matches = False
                if filters.get("location") and filters["location"] != course.location:
                    matches = False
                if filters.get("price_max") and course.price > filters["price_max"]:
                    matches = False
                if filters.get("price_min") and course.price < filters["price_min"]:
                    matches = False

                if not matches:
                    continue

                user = db.query(User).filter(User.id == alert.user_id).first()
                if not user or not user.email:
                    continue

                subject = f"New Course: {course.title}"
                content = f"""
                A new course matching your criteria has been added!
                
                Title: {course.title}
                Category: {course.category}
                Price: ${course.price}
                Location: {course.location}
                
                Visit our website to learn more and enroll.
                """

                send_email_sync(user.email, subject, content.strip())
                sent_count += 1
                logger.info(f"Alert sent to {user.email} for course {course_id}")

            except Exception as e:
                logger.error(f"Error processing alert {alert.id}: {str(e)}")
                continue

        db.commit()
        return {"status": "success", "alerts_sent": sent_count}

    except Exception as e:
        logger.error(f"Error in send_matching_alerts: {str(e)}")
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))
    finally:
        db.close()


# ==================== 3. Weekly Digest ====================
@celery_app.task(name="app.tasks.email_tasks.send_weekly_digest")
def send_weekly_digest():
    """Send weekly digest email to all users with weekly alerts."""
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        one_week_ago = datetime.utcnow() - timedelta(days=7)

        for user in users:
            try:
                # Get new courses in last week
                new_courses = db.query(Course).filter(
                    Course.created_at >= one_week_ago,
                    Course.status == "active"
                ).all()

                # Get new trips in last week
                new_trips = db.query(Trip).filter(
                    Trip.created_at >= one_week_ago,
                    Trip.status == "active"
                ).all()

                if not new_courses and not new_trips:
                    continue

                # Build email content
                content = f"Hi {user.full_name},\n\n"
                content += "Here are the new courses and trips from the past week:\n\n"

                if new_courses:
                    content += "📚 **New Courses:**\n"
                    for course in new_courses:
                        content += f"  - {course.title} (${course.price})\n"

                if new_trips:
                    content += "\n✈️ **New Trips:**\n"
                    for trip in new_trips:
                        content += f"  - {trip.location_name}, {trip.country} (${trip.price})\n"

                content += "\nVisit our website to learn more!"

                send_email_sync(user.email, "Weekly Digest - New Courses & Trips", content.strip())
                logger.info(f"Weekly digest sent to {user.email}")

            except Exception as e:
                logger.error(f"Error sending weekly digest to {user.email}: {str(e)}")
                continue

        return {"status": "success", "message": "Weekly digests sent"}

    except Exception as e:
        logger.error(f"Error in send_weekly_digest: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


# ==================== 4. Daily Digest ====================
@celery_app.task(name="app.tasks.email_tasks.send_daily_digest")
def send_daily_digest():
    """Send daily digest email to all users with daily alerts."""
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        one_day_ago = datetime.utcnow() - timedelta(days=1)

        for user in users:
            try:
                # Get new courses in last 24 hours
                new_courses = db.query(Course).filter(
                    Course.created_at >= one_day_ago,
                    Course.status == "active"
                ).all()

                # Get new trips in last 24 hours
                new_trips = db.query(Trip).filter(
                    Trip.created_at >= one_day_ago,
                    Trip.status == "active"
                ).all()

                if not new_courses and not new_trips:
                    continue

                content = f"Hi {user.full_name},\n\n"
                content += "Here are the new courses and trips from the past 24 hours:\n\n"

                if new_courses:
                    content += "📚 **New Courses:**\n"
                    for course in new_courses:
                        content += f"  - {course.title} (${course.price})\n"

                if new_trips:
                    content += "\n✈️ **New Trips:**\n"
                    for trip in new_trips:
                        content += f"  - {trip.location_name}, {trip.country} (${trip.price})\n"

                content += "\nVisit our website to learn more!"

                send_email_sync(user.email, "Daily Digest - New Courses & Trips", content.strip())
                logger.info(f"Daily digest sent to {user.email}")

            except Exception as e:
                logger.error(f"Error sending daily digest to {user.email}: {str(e)}")
                continue

        return {"status": "success", "message": "Daily digests sent"}

    except Exception as e:
        logger.error(f"Error in send_daily_digest: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


# ==================== 5. Retry Failed Emails ====================
@celery_app.task(name="app.tasks.email_tasks.retry_failed_emails")
def retry_failed_emails():
    """Retry failed email sending tasks."""
    logger.info("Checking for failed email tasks to retry...")
    # This is a placeholder - actual implementation would check a database table
    # of failed emails and retry them
    return {"status": "success", "message": "Failed emails check completed"}

# ==================== 6. Booking Confirmation Email ====================
@celery_app.task(base=BaseTaskWithRetry, bind=True, name="app.tasks.email_tasks.send_booking_confirmation")
def send_booking_confirmation(self, user_email: str, user_name: str, location: str, country: str, booking_id: int):
    """Send booking confirmation email to user."""
    try:
        subject = f"Booking Confirmed: {location}, {country}"
        content = f"""
        Hi {user_name},
        
        Your trip to {location}, {country} has been confirmed!
        
        Booking ID: #{booking_id}
        Location: {location}, {country}
        
        We will send you more details about your trip soon.
        
        Thank you for choosing Maritime Academy!
        """
        
        result = send_email_sync(user_email, subject, content.strip())
        if result and result.get("status") == 200:
            logger.info(f"Booking confirmation sent to {user_email}")
            return {"status": "success", "email": user_email}
        else:
            raise Exception(f"SendGrid returned: {result}")
    except Exception as e:
        logger.error(f"Error sending booking confirmation to {user_email}: {str(e)}")
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


# ==================== 7. Booking Cancellation Email ====================
@celery_app.task(base=BaseTaskWithRetry, bind=True, name="app.tasks.email_tasks.send_booking_cancellation")
def send_booking_cancellation(self, user_email: str, user_name: str, booking_id: int):
    """Send booking cancellation email to user."""
    try:
        subject = f"Booking Cancelled: #{booking_id}"
        content = f"""
        Hi {user_name},
        
        Your booking (ID: #{booking_id}) has been successfully cancelled.
        
        If you did not request this cancellation, please contact us immediately.
        
        Thank you for using Maritime Academy!
        """
        
        result = send_email_sync(user_email, subject, content.strip())
        if result and result.get("status") == 200:
            logger.info(f"Booking cancellation sent to {user_email}")
            return {"status": "success", "email": user_email}
        else:
            raise Exception(f"SendGrid returned: {result}")
    except Exception as e:
        logger.error(f"Error sending cancellation to {user_email}: {str(e)}")
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


# ==================== 8. Welcome Email ====================
@celery_app.task(base=BaseTaskWithRetry, bind=True, name="app.tasks.email_tasks.send_welcome_email")
def send_welcome_email(self, user_email: str, user_name: str):
    """Send welcome email to new user."""
    try:
        subject = "Welcome to Maritime Academy!"
        content = f"""
        Hi {user_name},
        
        Welcome to Maritime Academy!
        
        We are excited to have you on board. Here are some things you can do:
        
        1. Browse our courses and trips
        2. Enroll in a course
        3. Book a trip
        4. Explore our shipping services
        
        If you have any questions, feel free to contact us.
        
        Happy learning!
        Maritime Academy Team
        """
        
        result = send_email_sync(user_email, subject, content.strip())
        if result and result.get("status") == 200:
            logger.info(f"Welcome email sent to {user_email}")
            return {"status": "success", "email": user_email}
        else:
            raise Exception(f"SendGrid returned: {result}")
    except Exception as e:
        logger.error(f"Error sending welcome email to {user_email}: {str(e)}")
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))