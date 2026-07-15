from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.ai_feedback import TravelBasketFeedbackRequest, TravelBasketFeedbackResponse
from app.services import ai_feedback as service


router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/travel-basket-feedback", response_model=TravelBasketFeedbackResponse)
async def travel_basket_feedback(
    data: TravelBasketFeedbackRequest,
    db: Session = Depends(get_db),
) -> TravelBasketFeedbackResponse:
    return await service.create_travel_basket_feedback(db, data)
