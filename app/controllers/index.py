from typing import List
import akshare as ak

from app.core.research.index.HSTECH import VolatilityAnalyzer
from app.schemas.research.index.index import *


class HKIndexController:
    def __init__(self):
        pass

    async def get_index_his_data(self, index_id: str, window: int = 20):
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
    
    async def get_index_realtime_data(self):
        """
        Docstring for get_index_realtime_data
        """
        # df 列名：Index(['序号', '内部编号', '代码', '名称', '最新价', '涨跌额', '涨跌幅', '今开', '最高', '最低', '昨收',
        #        '成交量', '成交额'],
        df = ak.stock_hk_index_spot_sina()
        column_mapping = {
            '代码': 'symbol',
            '名称': 'name',
            '最新价': 'price',
            '涨跌额': 'change',
            '涨跌幅': 'pct_change',
            '昨收': 'prev_close',
            '今开': 'open',
            '最高': 'high',
            '最低': 'low'
        }
        df = df.rename(columns=column_mapping)
        json_str = df.to_json(orient='records', date_format='iso', force_ascii=False)
        return json_str


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


hk_index_controller = HKIndexController()
