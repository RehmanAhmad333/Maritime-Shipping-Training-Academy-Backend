from pydantic import BaseModel
from typing import Optional, List, Dict, Any

# ---------- Chatbot Schemas ----------
class ChatRequest(BaseModel):
    message: str
    course_id: Optional[int] = None
    trip_id: Optional[int] = None

class ChatResponse(BaseModel):
    reply: str
    context: Optional[List[Dict[str, Any]]] = None
    conversation_id: Optional[int] = None


# ---------- Voice Search Schemas ----------
class VoiceSearchRequest(BaseModel):
    text: str

class VoiceSearchResponse(BaseModel):
    filters: Dict[str, Any]
    original_text: str


# ---------- Recommendations Schemas ----------
class RecommendationResponse(BaseModel):
    recommended_courses: List[Dict[str, Any]]
    recommended_trips: List[Dict[str, Any]]


# ---------- Schedule Optimizer Schemas ----------
class ScheduleOptimizerRequest(BaseModel):
    course_id: int
    preferred_start_date: Optional[str] = None
    preferred_location: Optional[str] = None

class ScheduleOptimizerResponse(BaseModel):
    optimized_dates: List[str]
    confidence: float
    recommended_location: Optional[str] = None


# ---------- Price Prediction Schemas ----------
class PricePredictionRequest(BaseModel):
    course_id: int

class PricePredictionResponse(BaseModel):
    course_id: int
    predicted_price: float
    confidence: float
    estimated_price_range: Dict[str, float]


# ---------- Description Generator Schemas ----------
class DescriptionRequest(BaseModel):
    course_title: str
    category: str
    duration_days: int
    max_students: int
    location: str

class DescriptionResponse(BaseModel):
    description: str


# ---------- Certificate Generator Schemas ----------
class CertificateRequest(BaseModel):
    course_id: int
    user_id: int

class CertificateResponse(BaseModel):
    certificate_number: str
    pdf_url: str


# ---------- Progress Predictor Schemas ----------
class ProgressPredictorRequest(BaseModel):
    course_id: int
    user_id: int

class ProgressPredictorResponse(BaseModel):
    predicted_completion_rate: float
    estimated_completion_date: Optional[str] = None