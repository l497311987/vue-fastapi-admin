import asyncio
import logging
from cachetools import TTLCache
from fastapi import APIRouter, Body, Query
from app.controllers.index import hk_index_controller
from app.core.research.market.market_analyzer import MarketAnalyzer
from app.schemas.base import Fail, Success, SuccessExtra

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/index")

# 创建5分钟过期的缓存
market_cache = TTLCache(maxsize=1, ttl=300)

@router.get("/hk/his", summary="香港指数历史数据")
async def get_index_hk_his(
        index_id: str = Query(..., description="指数ID")
):
    index_info, stats_df = await hk_index_controller.get_index_his_data(index_id=index_id)
    return Success(data=index_info.json())


@router.get("/hk/realtime", summary="实时指数分析数据")
async def get_index_hk_realtime():
    df = await hk_index_controller.get_index_realtime_data()
    return Success(data=df)


@router.get("/market/overview", summary="市场整体情况")
async def get_market_overview():
    cache_key = "market_overview"

    if cache_key in market_cache:
        return Success(data=market_cache[cache_key])

    analyzer = MarketAnalyzer()
    overview = await asyncio.to_thread(
        lambda: analyzer.get_market_overview()
    )

    result_data = overview.model_dump()
    market_cache[cache_key] = result_data

    return Success(data=result_data)
