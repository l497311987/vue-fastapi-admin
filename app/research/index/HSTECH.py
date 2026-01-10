"""
@File    : HSTECH.py
@Author  : 040484
@Date    : 2026-01-10 13:08
@Desc    : 波动率计算尝试
"""
import akshare as ak

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
from matplotlib import font_manager


warnings.filterwarnings('ignore')

# 设置中文字体和样式
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.style.use('seaborn-v0_8-darkgrid')


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

    def plot_volatility_cone(self, volatility_cone, figsize=(12, 8)):
        """
        绘制波动率锥

        参数:
        volatility_cone: pandas DataFrame, 波动率锥数据
        figsize: tuple, 图形大小
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize,
                                       gridspec_kw={'height_ratios': [2, 1]})

        # 准备数据
        windows = volatility_cone.index.tolist()
        window_labels = volatility_cone['window_desc'].tolist()

        # 主要波动率锥图
        colors = plt.cm.viridis(np.linspace(0.3, 0.9, 5))

        # 绘制分位数区域
        ax1.fill_between(windows,
                         volatility_cone['q_10'],
                         volatility_cone['q_90'],
                         alpha=0.1, color='blue', label='10%-90% 区间')

        ax1.fill_between(windows,
                         volatility_cone['q_25'],
                         volatility_cone['q_75'],
                         alpha=0.2, color='green', label='25%-75% 区间')

        # 绘制分位数线
        quantile_lines = ['q_10', 'q_25', 'q_50', 'q_75', 'q_90']
        quantile_labels = ['10%分位', '25%分位', '中位数(50%)', '75%分位', '90%分位']

        for q_line, q_label, color in zip(quantile_lines, quantile_labels, colors):
            ax1.plot(windows, volatility_cone[q_line],
                     marker='o', color=color, linewidth=2, label=q_label)

        # 绘制当前波动率线
        if 'current' in volatility_cone.columns:
            ax1.plot(windows, volatility_cone['current'],
                     marker='s', color='red', linewidth=3,
                     linestyle='--', label='当前波动率')

            # 标记当前波动率位置
            for i, (window, current) in enumerate(zip(windows, volatility_cone['current'])):
                # 判断当前值在哪个分位数区间
                if pd.isna(current):
                    continue

                if current <= volatility_cone.loc[window, 'q_10']:
                    position = "极低 (<10%)"
                    color = 'darkgreen'
                elif current <= volatility_cone.loc[window, 'q_25']:
                    position = "较低 (10-25%)"
                    color = 'green'
                elif current <= volatility_cone.loc[window, 'q_75']:
                    position = "正常 (25-75%)"
                    color = 'orange'
                elif current <= volatility_cone.loc[window, 'q_90']:
                    position = "较高 (75-90%)"
                    color = 'darkorange'
                else:
                    position = "极高 (>90%)"
                    color = 'red'

                ax1.annotate(position,
                             xy=(window, current),
                             xytext=(0, 10 if i % 2 == 0 else -25),
                             textcoords='offset points',
                             ha='center',
                             fontsize=8,
                             color=color,
                             bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

        # 设置主图属性
        ax1.set_title('波动率锥分析 (Volatility Cone)', fontsize=16, fontweight='bold', pad=20)
        ax1.set_xlabel('时间窗口 (交易日)', fontsize=12)
        ax1.set_ylabel('年化波动率 (%)', fontsize=12)
        ax1.set_xticks(windows)
        ax1.set_xticklabels(window_labels, rotation=0)
        ax1.legend(loc='upper right', fontsize=10)
        ax1.grid(True, alpha=0.3)

        # 添加统计表格（子图2）
        if 'current' in volatility_cone.columns:
            # 准备表格数据
            table_data = []
            for window in windows:
                current = volatility_cone.loc[window, 'current']
                if pd.isna(current):
                    continue

                # 计算百分位排名
                all_values = self.calculate_volatility(window=window).dropna()
                if len(all_values) > 0:
                    percentile = (all_values < current).sum() / len(all_values) * 100
                else:
                    percentile = np.nan

                table_data.append([
                    window_labels[windows.index(window)],
                    f'{current:.2f}%',
                    f'{volatility_cone.loc[window, "q_50"]:.2f}%',
                    f'{percentile:.1f}%'
                ])

            # 创建表格
            if table_data:
                table = ax2.table(cellText=table_data,
                                  colLabels=['窗口', '当前值', '历史中位数', '历史百分位'],
                                  loc='center',
                                  cellLoc='center')
                table.auto_set_font_size(False)
                table.set_fontsize(10)
                table.scale(1, 2)

                # 设置表格样式
                for i in range(len(table_data) + 1):
                    for j in range(4):
                        cell = table[(i, j)]
                        cell.set_edgecolor('lightgray')
                        if i == 0:  # 标题行
                            cell.set_facecolor('#2E86AB')
                            cell.set_text_props(weight='bold', color='white')
                        elif i > 0 and j == 3:  # 百分位列
                            percentile_val = float(table_data[i - 1][3].replace('%', ''))
                            if percentile_val > 75:
                                cell.set_facecolor('#FF6B6B')  # 红色 - 极高
                            elif percentile_val > 60:
                                cell.set_facecolor('#FFD166')  # 橙色 - 较高
                            elif percentile_val > 40:
                                cell.set_facecolor('#06D6A0')  # 绿色 - 正常
                            elif percentile_val > 25:
                                cell.set_facecolor('#118AB2')  # 蓝色 - 较低
                            else:
                                cell.set_facecolor('#073B4C')  # 深蓝 - 极低
                                cell.set_text_props(color='white')

        ax2.axis('off')
        ax2.set_title('当前波动率统计', fontsize=12, fontweight='bold', pad=10)

        plt.tight_layout()
        return fig, (ax1, ax2)

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

        return results

    def plot_volatility_comparison(self, window=20, figsize=(14, 10)):
        """
        绘制不同波动率计算方法的比较图

        参数:
        window: int, 滚动窗口大小
        figsize: tuple, 图形大小
        """
        vol_comparison = self.compare_volatility_methods(window=window)

        fig, axes = plt.subplots(2, 1, figsize=figsize, height_ratios=[3, 1])

        # 主图：波动率序列比较
        methods = ['standard', 'parkinson', 'garman_klass', 'rogers_satchell', 'yang_zhang']
        method_labels = ['标准方法', 'Parkinson', 'Garman-Klass', 'Rogers-Satchell', 'Yang-Zhang']
        colors = plt.cm.Set2(np.linspace(0, 1, len(methods)))

        for method, label, color in zip(methods, method_labels, colors):
            axes[0].plot(self.df[self.date_col], vol_comparison[method],
                         label=label, color=color, linewidth=2, alpha=0.8)

        axes[0].set_title(f'不同波动率计算方法比较 ({window}日窗口)',
                          fontsize=14, fontweight='bold')
        axes[0].set_ylabel('年化波动率 (%)', fontsize=12)
        axes[0].legend(loc='best')
        axes[0].grid(True, alpha=0.3)

        # 子图：最近一段时间的详细比较
        recent_data = vol_comparison.tail(min(120, len(vol_comparison)))

        # 箱型图比较
        vol_data = [recent_data[method].dropna() for method in methods]
        box = axes[1].boxplot(vol_data, patch_artist=True,
                              labels=method_labels, showfliers=False)

        # 设置箱型图颜色
        for patch, color in zip(box['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)

        axes[1].set_title(f'最近{len(recent_data)}个交易日波动率分布比较',
                          fontsize=12, fontweight='bold')
        axes[1].set_ylabel('年化波动率 (%)', fontsize=10)
        axes[1].grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        return fig, axes

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


# 扩展类，添加热力图功能
class VolatilityAnalyzerExtended(VolatilityAnalyzer):
    """扩展的波动率分析器"""

    def create_volatility_heatmap(self, window_range=(5, 250, 5), method='standard'):
        """
        创建波动率热力图，展示不同窗口下的波动率变化

        参数:
        window_range: tuple, (最小窗口, 最大窗口, 步长)
        method: str, 波动率计算方法

        返回:
        matplotlib Figure对象
        """
        min_window, max_window, step = window_range
        windows = list(range(min_window, max_window + 1, step))

        # 创建热力图数据矩阵
        heatmap_data = []
        dates_for_plot = []

        # 为每个窗口计算波动率并获取最近N个值
        for window in windows:
            vol_series = self.calculate_volatility(method=method, window=window)
            # 获取最近500个值或全部
            recent_values = vol_series.dropna().iloc[-500:] if len(vol_series.dropna()) > 500 else vol_series.dropna()
            heatmap_data.append(recent_values.values)
            if not dates_for_plot:
                dates_for_plot = self.df[self.date_col].iloc[-len(recent_values):].values

        # 转换为矩阵
        heatmap_matrix = np.array(heatmap_data)

        # 创建热力图
        fig, axes = plt.subplots(2, 1, figsize=(16, 12),
                                 gridspec_kw={'height_ratios': [3, 1]})

        # 热力图
        im = axes[0].imshow(heatmap_matrix, aspect='auto',
                            cmap='RdYlGn_r',
                            extent=[0, len(dates_for_plot), min_window, max_window])

        axes[0].set_title('波动率热力图 (窗口 vs 时间)', fontsize=16, fontweight='bold')
        axes[0].set_xlabel('时间 (从早到晚)', fontsize=12)
        axes[0].set_ylabel('窗口大小 (交易日)', fontsize=12)

        # 添加颜色条
        plt.colorbar(im, ax=axes[0], label='年化波动率 (%)')

        # 添加重要窗口的标注
        important_windows = [20, 60, 120, 250]
        for win in important_windows:
            if min_window <= win <= max_window:
                axes[0].axhline(y=win, color='white', linestyle='--', alpha=0.5, linewidth=1)
                axes[0].text(len(dates_for_plot) * 0.98, win, f'{win}日',
                             color='white', fontsize=10, ha='right', va='center',
                             bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.5))

        # 添加当前波动率线（右侧Y轴）
        ax2 = axes[0].twinx()
        current_vols = [heatmap_matrix[i, -1] for i in range(len(windows))]
        ax2.plot(current_vols, windows, color='blue', linewidth=2, linestyle='-', marker='o', markersize=3)
        ax2.set_ylabel('当前波动率 (%)', fontsize=12, color='blue')
        ax2.tick_params(axis='y', labelcolor='blue')

        # 底部：关键窗口波动率时间序列
        colors = plt.cm.tab10(np.linspace(0, 1, len(important_windows)))

        for i, window in enumerate(important_windows):
            if window in windows:
                idx = windows.index(window)
                vol_series = heatmap_matrix[idx, :]
                axes[1].plot(range(len(vol_series)), vol_series,
                             label=f'{window}日窗口', color=colors[i], linewidth=2)

        axes[1].set_title('关键窗口波动率时间序列', fontsize=12, fontweight='bold')
        axes[1].set_xlabel('相对时间 (最近N个交易日)', fontsize=10)
        axes[1].set_ylabel('波动率 (%)', fontsize=10)
        axes[1].legend(loc='best')
        axes[1].grid(True, alpha=0.3)

        plt.tight_layout()
        return fig, axes

    # 使用示例
    # extended_analyzer = VolatilityAnalyzerExtended(df)
    #     # fig_heatmap, axes_heatmap = extended_analyzer.create_volatility_heatmap(
    #     #     window_range=(10, 200, 5),
    #     #     method='garman_klass'
    #     # )
    #     # plt.show()


def setup_chinese_font():
    """
    设置matplotlib中文字体
    """
    try:
        # 方法1: 使用系统自带的中文字体
        # Windows系统常见中文字体
        windows_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'KaiTi', 'FangSong']

        # Mac系统常见中文字体
        mac_fonts = ['PingFang SC', 'Hiragino Sans GB', 'STHeiti', 'Apple LiGothic']

        # Linux系统常见中文字体
        linux_fonts = ['WenQuanYi Zen Hei', 'WenQuanYi Micro Hei', 'DejaVu Sans']

        # 尝试添加所有可能的字体
        all_fonts = windows_fonts + mac_fonts + linux_fonts

        # 检查系统中已有的字体
        system_fonts = [f.name for f in font_manager.fontManager.ttflist]

        # 查找可用的中文字体
        available_fonts = []
        for font in all_fonts:
            if font in system_fonts:
                available_fonts.append(font)
                print(f"找到系统字体: {font}")

        if available_fonts:
            # 使用第一个可用的中文字体
            plt.rcParams['font.sans-serif'] = available_fonts
            plt.rcParams['axes.unicode_minus'] = False
            print(f"已设置中文字体为: {available_fonts[0]}")
            return True
        else:
            print("警告: 未找到系统中文字体，将尝试下载字体文件...")
            return False

    except Exception as e:
        print(f"设置字体时出错: {e}")
        return False



if __name__ == '__main__':
    # 尝试设置中文字体
    setup_chinese_font()

    df = ak.stock_hk_index_daily_sina(symbol="HSTECH")
    print(f"数据形状: {df.shape}")
    print(df.head())

    # 3. 初始化波动率分析器
    analyzer = VolatilityAnalyzer(df, price_col='close', date_col='date', trading_days=252)

    # 4. 计算不同方法的波动率
    window = 20
    standard_vol = analyzer.calculate_volatility(method='standard', window=window)
    parkinson_vol = analyzer.calculate_volatility(method='parkinson', window=window)
    garman_klass_vol = analyzer.calculate_volatility(method='garman_klass', window=window)

    print(f"\n当前{window}日波动率:")
    print(f"标准方法: {standard_vol.iloc[-1]:.2f}%")
    print(f"Parkinson: {parkinson_vol.iloc[-1]:.2f}%")
    print(f"Garman-Klass: {garman_klass_vol.iloc[-1]:.2f}%")

    # 5. 计算并绘制波动率锥
    windows = [20, 60, 120, 250, 500]
    volatility_cone = analyzer.calculate_volatility_cone(
        windows=windows,
        method='garman_klass',  # 使用最精确的方法
        quantiles=[0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95]
    )

    print("\n波动率锥数据:")
    print(volatility_cone[['mean', 'q_50', 'current', 'window_desc']])

    # 6. 绘制波动率锥
    fig, axes = analyzer.plot_volatility_cone(volatility_cone, figsize=(14, 10))
    plt.show()

    # 7. 比较不同计算方法
    fig2, axes2 = analyzer.plot_volatility_comparison(window=20, figsize=(14, 10))
    plt.show()

    # 8. 获取统计摘要
    stats_df = analyzer.get_volatility_statistics(windows=[20, 60, 120, 250], method='garman_klass')
    print("\n波动率统计摘要:")
    print(stats_df.round(3))

    # 9. 可视化不同窗口的波动率
    fig3, ax3 = plt.subplots(figsize=(14, 6))
    windows_plot = [20, 60, 120]
    colors = ['blue', 'green', 'red']

    for window, color in zip(windows_plot, colors):
        vol_series = analyzer.calculate_volatility(method='garman_klass', window=window)
        ax3.plot(df['date'], vol_series, label=f'{window}日波动率', color=color, alpha=0.8)

    ax3.set_title('不同时间窗口的波动率序列', fontsize=14, fontweight='bold')
    ax3.set_xlabel('日期', fontsize=12)
    ax3.set_ylabel('年化波动率 (%)', fontsize=12)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
