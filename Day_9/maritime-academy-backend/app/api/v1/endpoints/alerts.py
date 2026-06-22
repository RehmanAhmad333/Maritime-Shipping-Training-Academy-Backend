import logging
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.email_alert import EmailAlert
from app.schemas.alert_schema import EmailAlertCreate, EmailAlertResponse, AlertResponse, AlertToggleResponse
from app.tasks.email_tasks import send_weekly_digest  # Optional: trigger manually

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["Email Alerts"])


@router.post(
    "/",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Email Alert",
    description="Creates an email alert for the current user with specified filters."
)
def create_alert(
    alert_data: EmailAlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if not alert_data.filters_json:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filters are required."
            )
        
        filters_string = json.dumps(alert_data.filters_json)
        
        new_alert = EmailAlert(
            user_id=current_user.id,
            filters_json=filters_string,
            frequency=alert_data.frequency,
            is_active=True
        )
        db.add(new_alert)
        db.commit()
        db.refresh(new_alert)
        
        # Email notification is now handled by Celery Beat (scheduled tasks)
        # No need to send immediate confirmation email
        
        return AlertResponse(
            message="Email alert created successfully.",
            alert_id=new_alert.id
        )
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating alert: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create email alert."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating alert: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred."
        )


@router.get(
    "/",
    response_model=list[EmailAlertResponse],
    summary="Get User Alerts",
    description="Returns all active alerts for the current user."
)
def get_my_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        alerts = db.query(EmailAlert).filter(
            EmailAlert.user_id == current_user.id,
            EmailAlert.is_active == True
        ).order_by(EmailAlert.created_at.desc()).all()
        
        # Parse filters_json back to dict
        result = []
        for alert in alerts:
            alert_dict = {
                "id": alert.id,
                "user_id": alert.user_id,
                "filters_json": json.loads(alert.filters_json) if alert.filters_json else {},
                "is_active": alert.is_active,
                "frequency": alert.frequency,
                "last_sent_at": alert.last_sent_at,
                "created_at": alert.created_at
            }
            result.append(EmailAlertResponse(**alert_dict))
        
        return result
    
    except SQLAlchemyError as e:
        logger.error(f"Database error fetching alerts for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alerts."
        )
    except Exception as e:
        logger.error(f"Unexpected error fetching alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred."
        )


@router.put(
    "/{alert_id}/toggle",
    response_model=AlertToggleResponse,
    summary="Toggle Alert Status",
    description="Activate or deactivate an existing alert."
)
def toggle_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        alert = db.query(EmailAlert).filter(
            EmailAlert.id == alert_id,
            EmailAlert.user_id == current_user.id
        ).first()
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found."
            )
        
        alert.is_active = not alert.is_active
        db.commit()
        
        return AlertToggleResponse(active=alert.is_active)
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error toggling alert {alert_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to toggle alert."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error toggling alert: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred."
        )


@router.delete(
    "/{alert_id}",
    response_model=dict,
    summary="Delete Alert",
    description="Permanently delete an email alert."
)
def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        alert = db.query(EmailAlert).filter(
            EmailAlert.id == alert_id,
            EmailAlert.user_id == current_user.id
        ).first()
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found."
            )
        
        db.delete(alert)
        db.commit()
        
        return {"message": "Alert deleted successfully."}
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error deleting alert {alert_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete alert."
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error deleting alert: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred."
        )