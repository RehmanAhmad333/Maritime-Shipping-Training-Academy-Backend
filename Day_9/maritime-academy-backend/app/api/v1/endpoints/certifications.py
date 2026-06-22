import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User
from app.models.certification import Certification
from app.schemas.certification_schema import CertificationResponse
from typing import List
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/certifications", tags=["Certifications"])


@router.get("/my", response_model=List[CertificationResponse])
def get_my_certifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        certs = db.query(Certification).filter(
            Certification.user_id == current_user.id
        ).order_by(Certification.issue_date.desc()).all()
        return certs
    except SQLAlchemyError as e:
        logger.error(f"Error fetching certifications: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve certifications."
        )


@router.get("/{cert_id}", response_model=CertificationResponse)
def get_certification(
    cert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        cert = db.query(Certification).filter(
            Certification.id == cert_id,
            Certification.user_id == current_user.id
        ).first()
        if not cert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Certification not found."
            )
        return cert
    except SQLAlchemyError as e:
        logger.error(f"Error fetching certification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve certification."
        )


@router.post("/generate")
def generate_certificate(
    course_id: int,
    user_id: int,
    current_user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    try:
        # Generate certificate number
        cert_number = f"CERT-{course_id}-{user_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        mock_pdf_url = f"https://maritime-academy.com/certificates/{cert_number}.pdf"
        
        new_cert = Certification(
            user_id=user_id,
            course_id=course_id,
            certificate_number=cert_number,
            pdf_url=mock_pdf_url,
            issue_date=datetime.now()
        )
        db.add(new_cert)
        db.commit()
        db.refresh(new_cert)
        return {"message": "Certificate generated", "certificate_id": new_cert.id}
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error generating certificate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate certificate."
        )