import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # JWT
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_REFRESH_SECRET_KEY = os.getenv("JWT_REFRESH_SECRET_KEY", "your-refresh-secret-key")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
    
    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Email
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    SENDGRID_FROM_EMAIL = os.getenv("SENDGRID_FROM_EMAIL", "noreply@maritimeacademy.com")
    
    # Stripe
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Frontend
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
    CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

settings = Settings()