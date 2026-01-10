import logging

from fastapi import APIRouter, Body, Query
from app.controllers.dept import dept_controller
from app.controllers.user import user_controller
from app.schemas.base import Fail, Success, SuccessExtra

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/index/hk", summary="香港指数分析")
async def get_index_hk(
    index_id: int = Query(..., description="指数ID"),
):
    return Success(data=index_id)



