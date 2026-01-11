from typing import List
import akshare as ak

from app.core.research.index.HSTECH import VolatilityAnalyzer
from app.schemas.research.index.index import *


class IndexController:
    def __init__(self):
        pass

    async def get_index_data(self, index_id: str, window: int = 20):
        df = ak.stock_hk_index_daily_sina(symbol=index_id)
        # 初始化波动率分析器
        analyzer = VolatilityAnalyzer(df, price_col='close', date_col='date', trading_days=252)
        # columns = ['standard', 'parkinson', 'garman_klass', 'rogers_satchell', 'yang_zhang']
        df_vol_all = analyzer.compare_volatility_methods(window=window)

        index_info = IndexInfo(
            index_id=index_id,
            window=window,
            last_price=df['close'].iloc[-1],
            price_series=df.apply(row_to_price_point, axis=1).tolist(),
            volatility=df_vol_all['standard'].iloc[-1],  # 默认取标准波动率
            volatility_series=df_vol_all.apply(row_to_volatility_point, axis=1).tolist()
        )

        # 获取统计摘要
        stats_df = analyzer.get_volatility_statistics(windows=[20, 60, 120, 250], method='standard')
        print("\n波动率统计摘要:")
        print(stats_df.round(3))
        return index_info, stats_df


def row_to_price_point(row):
    return PricePoint(
        timestamp=row['date'],
        open=row.get('open'),
        high=row.get('high'),
        low=row.get('low'),
        close=row['close'],
        volume=row.get('volume'),
        amount=row.get('amount')
    )


def row_to_volatility_point(row):
    return VolatilityPoint(
        timestamp=row['date'],
        volatility=row.get('standard')
    )


index_controller = IndexController()
