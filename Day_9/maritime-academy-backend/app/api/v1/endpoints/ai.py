import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.middleware.rate_limit import limiter
from app.models.user import User
from app.models.course import Course
from app.models.trip import Trip
from app.models.chat_history import ChatHistory
from app.schemas.ai_schema import (
    ChatRequest, ChatResponse,
    VoiceSearchRequest, VoiceSearchResponse,
    RecommendationResponse,
    ScheduleOptimizerRequest, ScheduleOptimizerResponse,
    PricePredictionRequest, PricePredictionResponse,
    DescriptionRequest, DescriptionResponse,
    CertificateRequest, CertificateResponse,
    ProgressPredictorRequest, ProgressPredictorResponse
)
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Features"])


# ==================== 1. AI Chatbot ====================
@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="AI Chatbot",
    description="Chatbot powered by RAG pipeline. Returns contextual responses about courses, trips, and shipping services."
)
@limiter.limit("50/minute")
def chat(
    request: Request,
    chat_data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Store user message
        chat_entry = ChatHistory(
            user_id=current_user.id,
            message=chat_data.message,
            reply=None,
            context_snapshot=None
        )
        db.add(chat_entry)
        db.commit()
        db.refresh(chat_entry)

        # Mock response (to be replaced with actual RAG pipeline by Ifrah)
        context = []
        if chat_data.course_id:
            course = db.query(Course).filter(Course.id == chat_data.course_id).first()
            if course:
                context.append({
                    "type": "course",
                    "title": course.title,
                    "category": course.category
                })
        
        if chat_data.trip_id:
            trip = db.query(Trip).filter(Trip.id == chat_data.trip_id).first()
            if trip:
                context.append({
                    "type": "trip",
                    "location": trip.location_name,
                    "country": trip.country
                })

        dummy_reply = f"Thank you for your question: '{chat_data.message}'. Our AI assistant is currently in development. Please contact our team for immediate assistance. If you would like to learn more about our courses or trips, please check our website or contact support."

        # Update chat entry with reply
        chat_entry.reply = dummy_reply
        db.commit()

        return ChatResponse(
            reply=dummy_reply,
            context=context,
            conversation_id=chat_entry.id
        )

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error in chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process chat message."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred."
        )


# ==================== 2. Voice Search ====================
@router.post(
    "/voice-search",
    response_model=VoiceSearchResponse,
    summary="Voice Search",
    description="Converts voice-to-text query into structured search filters for courses and trips."
)
@limiter.limit("50/minute")
def voice_search(
    request: Request,
    voice_data: VoiceSearchRequest
):
    try:
        text = voice_data.text.lower()
        filters = {}
        course_categories = ["maritime", "ship handling", "safety", "sailor", "drying"]
        locations = ["italy", "turkey", "london"]
        
        for category in course_categories:
            if category in text:
                filters["course_category"] = category
                break
        
        for location in locations:
            if location in text:
                filters["location"] = location.capitalize()
                break
        
        if "price" in text:
            import re
            price_match = re.search(r'(\d+)\s*(?:k|thousand)?', text)
            if price_match:
                try:
                    price = int(price_match.group(1))
                    filters["price_max"] = price
                except ValueError:
                    pass

        return VoiceSearchResponse(
            filters=filters,
            original_text=voice_data.text
        )

    except Exception as e:
        logger.error(f"Error in voice_search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process voice search."
        )


# ==================== 3. Course Recommendations ====================
@router.get(
    "/recommendations",
    response_model=RecommendationResponse,
    summary="Course Recommendations",
    description="Get personalized course and trip recommendations based on user profile."
)
@limiter.limit("50/minute")
def get_recommendations(
    request: Request,
    user_id: int = None,
    db: Session = Depends(get_db)
):
    try:
        # Mock recommendations (to be replaced by Tazaeen's model)
        recommended_courses = [
            {
                "id": 1,
                "title": "Maritime Training",
                "category": "Maritime",
                "price": 2500.00,
                "match_score": 0.95
            },
            {
                "id": 2,
                "title": "Ship Handling",
                "category": "Ship Handling",
                "price": 3000.00,
                "match_score": 0.88
            },
            {
                "id": 3,
                "title": "Safety Training",
                "category": "Safety",
                "price": 2000.00,
                "match_score": 0.82
            }
        ]

        recommended_trips = [
            {
                "id": 1,
                "location": "Val Di Versa",
                "country": "Italy",
                "price": 5000.00,
                "match_score": 0.90
            },
            {
                "id": 2,
                "location": "Istanbul",
                "country": "Turkey",
                "price": 4000.00,
                "match_score": 0.85
            }
        ]

        return RecommendationResponse(
            recommended_courses=recommended_courses,
            recommended_trips=recommended_trips
        )

    except Exception as e:
        logger.error(f"Error in get_recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get recommendations."
        )


# ==================== 4. Schedule Optimizer ====================
@router.post(
    "/schedule-optimizer",
    response_model=ScheduleOptimizerResponse,
    summary="Schedule Optimizer",
    description="Suggests optimal training schedules based on course availability and user preferences."
)
@limiter.limit("50/minute")
def optimize_schedule(
    request: Request,
    schedule_data: ScheduleOptimizerRequest,
    db: Session = Depends(get_db)
):
    try:
        # Mock optimization (to be replaced by Tazaeen's ML algorithm)
        course = db.query(Course).filter(Course.id == schedule_data.course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {schedule_data.course_id} not found."
            )

        # Generate mock optimized dates
        base_date = datetime.now()
        optimized_dates = [
            (base_date + timedelta(days=7)).strftime("%Y-%m-%d"),
            (base_date + timedelta(days=14)).strftime("%Y-%m-%d"),
            (base_date + timedelta(days=21)).strftime("%Y-%m-%d")
        ]

        return ScheduleOptimizerResponse(
            optimized_dates=optimized_dates,
            confidence=0.85,
            recommended_location=course.location if course.location else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in optimize_schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize schedule."
        )


# ==================== 5. Price Prediction ====================
@router.post(
    "/predict-price",
    response_model=PricePredictionResponse,
    summary="Price Prediction",
    description="Predicts course price based on demand, seasonality, and historical data."
)
@limiter.limit("50/minute")
def predict_price(
    request: Request,
    prediction_data: PricePredictionRequest,
    db: Session = Depends(get_db)
):
    try:
        course = db.query(Course).filter(Course.id == prediction_data.course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {prediction_data.course_id} not found."
            )

        # Mock prediction (to be replaced by Tazaeen's model)
        base_price = float(course.price) if course.price else 2500.00
        predicted_price = base_price * 1.05  # 5% increase based on demand
        
        return PricePredictionResponse(
            course_id=prediction_data.course_id,
            predicted_price=round(predicted_price, 2),
            confidence=0.92,
            estimated_price_range={
                "min": round(predicted_price * 0.9, 2),
                "max": round(predicted_price * 1.1, 2)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in predict_price: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to predict price."
        )


# ==================== 6. Description Generator ====================
@router.post(
    "/generate-description",
    response_model=DescriptionResponse,
    summary="Description Generator",
    description="Generates a professional course description using OpenAI."
)
@limiter.limit("50/minute")
def generate_description(
    request: Request,
    description_data: DescriptionRequest
):
    try:
        # Mock description (to be replaced by Hibba's OpenAI implementation)
        mock_desc = f"""
        Join our comprehensive {description_data.category} training program: {description_data.course_title}.
        
        This {description_data.duration_days}-day intensive course is designed for maritime professionals seeking to enhance their skills and knowledge. With a limited class size of {description_data.max_students} students, participants receive personalized attention from industry experts.
        
        Course highlights include hands-on training, theoretical knowledge, and real-world simulations. Available at our {description_data.location} facility, this program is ideal for both beginners and experienced professionals.
        
        Enroll now to advance your maritime career.
        """

        return DescriptionResponse(description=mock_desc.strip())

    except Exception as e:
        logger.error(f"Error in generate_description: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate description."
        )


# ==================== 7. Certificate Generator ====================
@router.post(
    "/generate-certificate",
    response_model=CertificateResponse,
    summary="Certificate Generator",
    description="Generates a PDF certificate upon course completion."
)
@limiter.limit("50/minute")
def generate_certificate(
    request: Request,
    certificate_data: CertificateRequest,
    db: Session = Depends(get_db)
):
    try:
        course = db.query(Course).filter(Course.id == certificate_data.course_id).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Course with ID {certificate_data.course_id} not found."
            )

        # Mock certificate generation (to be replaced by Hibba's implementation)
        certificate_number = f"CERT-{certificate_data.course_id}-{certificate_data.user_id}-{datetime.now().strftime('%Y%m%d')}"
        mock_pdf_url = f"https://maritime-academy.com/certificates/{certificate_number}.pdf"

        return CertificateResponse(
            certificate_number=certificate_number,
            pdf_url=mock_pdf_url
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_certificate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate certificate."
        )


# ==================== 8. Progress Predictor ====================
@router.post(
    "/progress-predictor",
    response_model=ProgressPredictorResponse,
    summary="Progress Predictor",
    description="Predicts student completion rate based on activity and engagement."
)
@limiter.limit("50/minute")
def predict_progress(
    request: Request,
    progress_data: ProgressPredictorRequest,
    db: Session = Depends(get_db)
):
    try:
        # Mock prediction (to be replaced by Azeem's ML model)
        completion_rate = 0.75  # 75% predicted completion rate
        estimated_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        return ProgressPredictorResponse(
            predicted_completion_rate=completion_rate,
            estimated_completion_date=estimated_date
        )

    except Exception as e:
        logger.error(f"Error in predict_progress: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to predict progress."
        )