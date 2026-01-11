from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from enum import Enum


# 时间粒度枚举
class TimeGranularity(str, Enum):
    MINUTE_1 = "1min"
    MINUTE_5 = "5min"
    MINUTE_15 = "15min"
    MINUTE_30 = "30min"
    HOUR_1 = "1hour"
    DAY_1 = "1day"
    WEEK_1 = "1week"
    MONTH_1 = "1month"


# 价格时间点数据
class PricePoint(BaseModel):
    timestamp: datetime
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: float =None
    volume: Optional[float] = None  # 成交量（指数可能没有）
    amount: Optional[float] = None  # 成交额（指数可能没有）

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# 波动率数据点
class VolatilityPoint(BaseModel):
    timestamp: datetime
    volatility: float = None  # 波动率值（通常以年化百分比表示，如0.15表示15%）
    calculation_window: Optional[int] = None  # 计算窗口（如20日）

    class Config:  # 当把 datetime 对象序列化为 JSON 时，使用 ISO 8601 格式（字符串）
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# 指数行情响应模型
class IndexInfo(BaseModel):
    index_id: str  # 例如：HSTECH (恒生科技)
    name: Optional[str] = None  # 可选：名称
    last_price: Optional[float] = None  # 最新价
    price_series: List[PricePoint]  # 价格时间序列
    # granularity: TimeGranularity  # 时间粒度
    volatility_series: List[VolatilityPoint] = None
    volatility: Optional[float] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }