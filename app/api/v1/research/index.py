import logging

from fastapi import APIRouter, Body, Query
from app.controllers.index import index_controller
from app.schemas.base import Fail, Success, SuccessExtra

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/index", tags=["index"])


@router.get("/hk", summary="香港指数分析")
async def get_index_hk(
        index_id: str = Query(..., description="指数ID")
):
    index_info, stats_df = await index_controller.get_index_data(index_id=index_id)
    return Success(data=index_info.json())
