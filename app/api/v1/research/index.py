import logging

from fastapi import APIRouter, Body, Query
from app.controllers.index import hk_index_controller
from app.schemas.base import Fail, Success, SuccessExtra

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/index")


@router.get("/hk/his", summary="香港指数历史数据")
async def get_index_hk_his(
        index_id: str = Query(..., description="指数ID")
):
    index_info, stats_df = await hk_index_controller.get_index_his_data(index_id=index_id)
    return Success(data=index_info)


@router.get("/hk/realtime", summary="实时指数分析数据")
async def get_index_hk_realtime():
    df = await hk_index_controller.get_index_realtime_data()
    return Success(data=df)

