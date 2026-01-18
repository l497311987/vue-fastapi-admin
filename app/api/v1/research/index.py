import logging

from fastapi import APIRouter, Body, Query
from app.controllers.index import hk_index_controller
from app.core.research.market.market_analyzer import MarketAnalyzer
from app.schemas.base import Fail, Success, SuccessExtra

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/index")


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
    analyzer = MarketAnalyzer()
    # 测试获取市场概览
    overview = analyzer.get_market_overview()
    data = {
        "date": str(overview.date),  # 确保日期是可序列化的字符串
        "summary": {
            "index_count": len(overview.indices),
            "up_count": overview.up_count,
            "down_count": overview.down_count,
            "total_amount": float(round(overview.total_amount, 2))
        },
        "indices": [
            {
                "name": idx.name,
                "current": float(round(idx.current, 2)),
                "change": float(round(idx.change_pct, 2)),
                "change_display": f"{idx.change_pct:+.2f}%",
                "direction": "up" if idx.change_pct >= 0 else "down"
            }
            for idx in overview.indices
        ]
    },
    return Success(data=data)
