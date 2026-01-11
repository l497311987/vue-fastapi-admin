"""
@File    : HSTECH.py
@Author  : 040484
@Date    : 2026-01-10 13:08
@Desc    : 波动率计算尝试
"""
import akshare as ak

import numpy as np
import pandas as pd
import warnings


warnings.filterwarnings('ignore')


class VolatilityAnalyzer:
    """
    波动率分析器 - 支持多种波动率计算方法和波动率锥分析
    """

    def __init__(self, df, price_col='close', date_col='date', trading_days=252):
        """
        初始化波动率分析器

        参数:
        df: pandas DataFrame, 包含OHLCV数据
        price_col: str, 价格列名 (默认'close')
        date_col: str, 日期列名 (默认'date')
        trading_days: int, 年化交易天数 (默认252)
        """
        self.df = df.copy()
        self.price_col = price_col
        self.date_col = date_col
        self.trading_days = trading_days

        # 确保日期为datetime格式并按日期排序
        if self.date_col in self.df.columns:
            self.df[self.date_col] = pd.to_datetime(self.df[self.date_col])
            self.df = self.df.sort_values(self.date_col).reset_index(drop=True)

        # 确保必要的列存在
        self._validate_columns()

        # 计算对数收益率
        self.df['log_return'] = np.log(self.df[self.price_col] / self.df[self.price_col].shift(1))

    def _validate_columns(self):
        """验证必需的列是否存在"""
        required_cols = [self.price_col, 'open', 'high', 'low', 'close']
        if self.date_col:
            required_cols.append(self.date_col)

        missing_cols = [col for col in required_cols if col not in self.df.columns]
        if missing_cols:
            raise ValueError(f"DataFrame缺少必需的列: {missing_cols}")

    def calculate_volatility(self, method='standard', window=20, min_periods=None):
        """
        计算波动率

        参数:
        method: str, 计算方法，可选:
            - 'standard': 基于收盘价的标准方法
            - 'parkinson': 基于价格范围的Parkinson估计量
            - 'garman_klass': Garman-Klass估计量
            - 'rogers_satchell': Rogers-Satchell估计量（考虑趋势）
            - 'yang_zhang': Yang-Zhang估计量（考虑开盘跳空）
        window: int, 滚动窗口大小
        min_periods: int, 最小观察期数，None则等于window

        返回:
        pandas Series, 波动率序列
        """
        if min_periods is None:
            min_periods = window

        if method == 'standard':
            # 标准方法：基于收盘价的对数收益率标准差
            volatility = self.df['log_return'].rolling(
                window=window, min_periods=min_periods
            ).std() * np.sqrt(self.trading_days)

        elif method == 'parkinson':
            # Parkinson估计量：基于日内价格范围
            self.df['hl_range'] = np.log(self.df['high'] / self.df['low'])
            volatility = (self.df['hl_range'].rolling(
                window=window, min_periods=min_periods
            ).apply(lambda x: np.sqrt((1 / (4 * np.log(2))) * np.mean(x ** 2)))
                          * np.sqrt(self.trading_days))

        elif method == 'garman_klass':
            # Garman-Klass估计量：综合OHLC信息
            self.df['hl_term'] = 0.5 * (np.log(self.df['high'] / self.df['low'])) ** 2
            self.df['co_term'] = (2 * np.log(2) - 1) * (np.log(self.df['close'] / self.df['open'])) ** 2

            volatility = (self.df['hl_term'].rolling(window=window, min_periods=min_periods).mean() -
                          self.df['co_term'].rolling(window=window, min_periods=min_periods).mean()).apply(
                lambda x: np.sqrt(x) if x > 0 else 0
            ) * np.sqrt(self.trading_days)

        elif method == 'rogers_satchell':
            # Rogers-Satchell估计量：考虑趋势的波动率
            self.df['rs_term'] = (np.log(self.df['high'] / self.df['close']) *
                                  np.log(self.df['high'] / self.df['open']) +
                                  np.log(self.df['low'] / self.df['close']) *
                                  np.log(self.df['low'] / self.df['open']))

            volatility = np.sqrt(self.df['rs_term'].rolling(
                window=window, min_periods=min_periods
            ).mean()) * np.sqrt(self.trading_days)

        elif method == 'yang_zhang':
            # Yang-Zhang估计量：考虑开盘跳空
            # 计算隔夜波动率
            self.df['overnight_return'] = np.log(self.df['open'] / self.df['close'].shift(1))
            sigma_overnight = self.df['overnight_return'].rolling(
                window=window, min_periods=min_periods
            ).std(ddof=0) ** 2

            # 计算日内波动率（Rogers-Satchell）
            self.df['rs_term'] = (np.log(self.df['high'] / self.df['close']) *
                                  np.log(self.df['high'] / self.df['open']) +
                                  np.log(self.df['low'] / self.df['close']) *
                                  np.log(self.df['low'] / self.df['open']))
            sigma_rs = self.df['rs_term'].rolling(
                window=window, min_periods=min_periods
            ).mean()

            # Yang-Zhang估计量
            k = 0.34 / (1.34 + (window + 1) / (window - 1))
            volatility = np.sqrt(sigma_overnight + k * sigma_rs) * np.sqrt(self.trading_days)

        else:
            raise ValueError(f"未知的波动率计算方法: {method}")

        return volatility

    def calculate_volatility_cone(self, windows=[20, 60, 120, 250, 500],
                                  method='standard', quantiles=[0.1, 0.25, 0.5, 0.75, 0.9]):
        """
        计算波动率锥

        参数:
        windows: list, 窗口大小列表（交易日）
        method: str, 波动率计算方法
        quantiles: list, 需要计算的分位数

        返回:
        pandas DataFrame, 波动率锥数据
        """
        volatility_cone = pd.DataFrame(index=windows)

        # 计算每个窗口的滚动波动率
        for window in windows:
            vol_series = self.calculate_volatility(method=method, window=window)

            # 计算分位数
            for q in quantiles:
                volatility_cone.loc[window, f'q_{int(q * 100)}'] = vol_series.quantile(q)

            # 计算均值和标准差
            volatility_cone.loc[window, 'mean'] = vol_series.mean()
            volatility_cone.loc[window, 'std'] = vol_series.std()
            volatility_cone.loc[window, 'current'] = vol_series.iloc[-1] if not vol_series.isna().all() else np.nan

        # 添加窗口描述
        volatility_cone['window_desc'] = volatility_cone.index.map(
            lambda x: f'{x}日\n(~{int(x / 21)}个月)' if x < 250 else f'{x}日\n(~{int(x / 252)}年)'
        )

        return volatility_cone

    def compare_volatility_methods(self, window=20):
        """
        比较不同波动率计算方法

        参数:
        window: int, 滚动窗口大小

        返回:
        pandas DataFrame, 包含各种方法的波动率序列
        """
        methods = ['standard', 'parkinson', 'garman_klass', 'rogers_satchell', 'yang_zhang']
        results = pd.DataFrame()

        for method in methods:
            results[method] = self.calculate_volatility(method=method, window=window)

        # 添加日期列
        if self.date_col in self.df.columns:
            results[self.date_col] = self.df[self.date_col]
        results[self.date_col] = pd.to_datetime(results[self.date_col])

        return results

    def get_volatility_statistics(self, windows=[20, 60, 120, 250], method='standard'):
        """
        获取波动率统计摘要

        参数:
        windows: list, 窗口大小列表
        method: str, 波动率计算方法

        返回:
        pandas DataFrame, 统计摘要
        """
        stats_list = []

        for window in windows:
            vol_series = self.calculate_volatility(method=method, window=window)
            vol_clean = vol_series.dropna()

            if len(vol_clean) > 0:
                stats = {
                    '窗口(日)': window,
                    '均值(%)': vol_clean.mean(),
                    '中位数(%)': vol_clean.median(),
                    '标准差(%)': vol_clean.std(),
                    '最小值(%)': vol_clean.min(),
                    '最大值(%)': vol_clean.max(),
                    '偏度': vol_clean.skew(),
                    '峰度': vol_clean.kurtosis(),
                    '当前值(%)': vol_clean.iloc[-1] if len(vol_clean) > 0 else np.nan,
                    '观察数': len(vol_clean)
                }
                stats_list.append(stats)
        return pd.DataFrame(stats_list)

