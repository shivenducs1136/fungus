"""Demo booking API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.models.request_models import DemoBookingRequest
from app.models.response_models import DemoBookingResponse
from app.services.demo_booking_service import DemoBookingService

log = get_logger("fungus.knowledge_server.api.demo_booking")

router = APIRouter(
    prefix="/api/v1/demo-bookings",
    tags=["Demo Booking"],
    responses={500: {"description": "Storage error"}},
)


@router.post("/", status_code=201, response_model=DemoBookingResponse)
def create_demo_booking(request: DemoBookingRequest, db: Session = Depends(get_db)):
    """Create a demo booking and automatically send confirmation email."""
    log.info("POST /demo-bookings - email=%s", request.work_email)
    return DemoBookingService.create(
        db=db,
        name=request.name,
        work_email=request.work_email,
        preferred_time=request.time,
        contact_number=request.contact_number,
        short_note=request.short_note,
        scheduled_datetime=request.scheduled_datetime,
    )
