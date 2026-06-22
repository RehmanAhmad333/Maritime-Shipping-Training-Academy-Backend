import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from app.models import *
from app.core.database import Base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set in .env")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# ---------- SIMPLE PASSWORD HASH (NO bcrypt) ----------
# For development seeding only! Production uses bcrypt in security.py
def simple_hash(password: str) -> str:
    """Simple hash for seeding test accounts only."""
    return f"test_hash_{password}"  # Just a placeholder

# ------------------------------------------------------

# 1. Users
users_data = [
    {"email": "admin@maritime.com", "full_name": "Admin User", "role": "admin"},
    {"email": "student@maritime.com", "full_name": "Student User", "role": "student"},
    {"email": "trainer@maritime.com", "full_name": "Trainer User", "role": "trainer"},
]

for u_data in users_data:
    existing = db.query(User).filter(User.email == u_data["email"]).first()
    if not existing:
        user = User(
            email=u_data["email"],
            password_hash=simple_hash("Test123"),  # All test passwords = "Test123"
            full_name=u_data["full_name"],
            role=u_data["role"],
            is_active=True
        )
        db.add(user)

db.commit()

# 2. Platform Stats
stats = [
    PlatformStat(stat_key="projects_delivered", stat_value=150),
    PlatformStat(stat_key="happy_clients", stat_value=50),
    PlatformStat(stat_key="social_base", stat_value=1000000000),
    PlatformStat(stat_key="years_experience", stat_value=25),
]
for stat in stats:
    if not db.query(PlatformStat).filter(PlatformStat.stat_key == stat.stat_key).first():
        db.add(stat)
db.commit()

# 3. Sample Course
admin_user = db.query(User).filter(User.email == "admin@maritime.com").first()
course = Course(
    title="Yacht Captain Certification",
    description="Complete training program for yacht captains",
    category="Maritime",
    price=2500.00,
    duration_days=30,
    instructor_id=admin_user.id if admin_user else None,
    max_students=20,
    status="active"
)
if not db.query(Course).filter(Course.title == course.title).first():
    db.add(course)
db.commit()

# 4. Course Curriculum
course_obj = db.query(Course).filter(Course.title == "Yacht Captain Certification").first()
if course_obj:
    curriculum = [
        CourseCurriculum(course_id=course_obj.id, day_number=1, title="Maritime & Training", 
                         point_1="Introduction to maritime laws", point_2="Basic navigation skills"),
        CourseCurriculum(course_id=course_obj.id, day_number=2, title="Ship Handling", 
                         point_1="Maneuvering techniques", point_2="Docking procedures"),
        CourseCurriculum(course_id=course_obj.id, day_number=3, title="Drying & Milling", 
                         point_1="Cargo drying techniques", point_2="Milling operations"),
        CourseCurriculum(course_id=course_obj.id, day_number=4, title="Sailor Training", 
                         point_1="Sail handling", point_2="Knot tying"),
        CourseCurriculum(course_id=course_obj.id, day_number=5, title="Safety", 
                         point_1="Emergency procedures", point_2="Life raft drills"),
    ]
    for item in curriculum:
        if not db.query(CourseCurriculum).filter(
            CourseCurriculum.course_id == item.course_id,
            CourseCurriculum.day_number == item.day_number
        ).first():
            db.add(item)
    db.commit()

# 5. Course Schedules
if course_obj:
    schedules = [
        CourseSchedule(course_id=course_obj.id, start_date="2026-07-01", end_date="2026-07-30",
                       time_slot="9:00 AM - 5:00 PM", capacity=20, booked=0, status="available"),
        CourseSchedule(course_id=course_obj.id, start_date="2026-08-15", end_date="2026-09-13",
                       time_slot="10:00 AM - 6:00 PM", capacity=15, booked=0, status="available"),
    ]
    for s in schedules:
        if not db.query(CourseSchedule).filter(
            CourseSchedule.course_id == s.course_id,
            CourseSchedule.start_date == s.start_date
        ).first():
            db.add(s)
    db.commit()

# 6. Trips
trips_data = [
    {"location_name": "Val Di Versa", "country": "Italy", "start_date": "2026-04-06", "duration_days": 14,
     "max_slots": 10, "price": 5000.00, "is_featured": True, "rating": 5.0, "description": "Luxury yacht tour in Italy"},
    {"location_name": "Istanbul", "country": "Turkey", "start_date": "2026-05-15", "duration_days": 12,
     "max_slots": 8, "price": 4000.00, "is_featured": False, "rating": 4.5, "description": "Bosphorus sailing experience"},
    {"location_name": "London", "country": "UK", "start_date": "2026-06-10", "duration_days": 10,
     "max_slots": 12, "price": 4500.00, "is_featured": False, "rating": 4.8, "description": "Thames river cruise"},
]
for trip_data in trips_data:
    if not db.query(Trip).filter(Trip.location_name == trip_data["location_name"]).first():
        db.add(Trip(**trip_data))
db.commit()

print("All seed data inserted successfully!")
db.close()