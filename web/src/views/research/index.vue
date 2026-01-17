<template>
  <div class="simple-index-chart">
    <!-- 输入区域 -->
    <div class="input-section">
      <n-input
        v-model:value="indexId"
        placeholder="输入指数ID，如：HSTECH"
        clearable
        size="large"
        @keyup.enter="fetchData"
        style="width: 300px; margin-right: 16px;"
      >
        <template #prefix>
          <n-icon :component="SearchIcon" />
        </template>
      </n-input>
      
      <n-button 
        type="primary" 
        size="large" 
        @click="fetchData"
        :loading="loading"
      >
        <template #icon>
          <n-icon :component="TrendingUpIcon" />
        </template>
        查询
      </n-button>
    </div>
    
    <!-- 图表区域 -->
    <div class="chart-container">
      <div v-if="loading" class="chart-loading">
        <n-spin size="large">
          <template #description>
            正在加载数据...
          </template>
        </n-spin>
      </div>
      
      <div v-else-if="chartData.length === 0" class="empty-chart">
        <n-empty size="large" description="请输入指数ID并查询">
          <template #icon>
            <n-icon :component="BarChartIcon" size="60" />
          </template>
          <template #extra>
            <n-text depth="3">
              示例：HSTECH (恒生科技指数)
            </n-text>
          </template>
        </n-empty>
      </div>
      
      <div v-else>
        <div class="chart-header">
          <n-space align="center" justify="space-between">
            <div>
              <n-h3 style="margin: 0">
                {{ indexName }} ({{ indexId }})
              </n-h3>
              <n-text depth="3">
                {{ chartData[chartData.length - 1]?.date }} 收盘: 
                <span :style="{ color: currentChange >= 0 ? '#18a058' : '#d03050' }">
                  {{ currentPrice.toFixed(2) }} 
                  {{ currentChange >= 0 ? '↑' : '↓' }} 
                  {{ Math.abs(currentChange).toFixed(2) }} 
                  ({{ currentChangePercent.toFixed(2) }}%)
                </span>
              </n-text>
            </div>
            
            <n-space>
              <n-select
                v-model:value="chartType"
                :options="chartTypeOptions"
                size="small"
                style="width: 120px;"
              />
              <n-select
                v-model:value="volatilityWindow"
                :options="volatilityOptions"
                size="small"
                style="width: 120px;"
              />
              <n-button 
                size="small" 
                @click="downloadChart"
                secondary
              >
                <template #icon>
                  <n-icon :component="DownloadIcon" />
                </template>
                下载
              </n-button>
            </n-space>
          </n-space>
        </div>
        
        <div id="chart" ref="chartRef" style="width: 100%; height: 500px;"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch, computed } from 'vue'
import { useRoute } from 'vue-router'
import { 
  NInput, 
  NButton, 
  NIcon, 
  NSpin, 
  NEmpty, 
  NH3,
  NText,
  NSpace,
  NSelect
} from 'naive-ui'
import * as echarts from 'echarts'
import { 
  Search as SearchIcon,
  TrendingUp as TrendingUpIcon,
  BarChart as BarChartIcon,
  Download as DownloadIcon
} from '@vicons/ionicons5'

import research from '@/api/research'

const route = useRoute()

// 指数ID
const indexId = ref('HSTECH')
const indexName = ref('恒生科技指数')
const loading = ref(false)

// 图表类型和波动率窗口
const chartType = ref('both')
const volatilityWindow = ref(20)
const chartTypeOptions = [
  { label: '价格走势', value: 'price' },
  { label: '价格+波动率', value: 'both' }
]
const volatilityOptions = [
  { label: '20日波动率', value: 20 },
  { label: '30日波动率', value: 30 },
  { label: '60日波动率', value: 60 }
]

// 图表数据
const chartData = ref([])
const rawData = ref([])
const chartRef = ref(null)
let chartInstance = null

// 计算当前价格和涨跌幅
const currentPrice = ref(0)
const currentChange = ref(0)
const currentChangePercent = ref(0)

// 获取数据
const fetchData = async () => {
  if (!indexId.value) return
  
  loading.value = true
  
  try {
    const params = {
      index_id: indexId.value
    }
    
    const ret = await research.get_index_his_data(params)
    
    if (ret.code === 200) {
      const data = JSON.parse(ret.data)
      indexName.value = indexId.value === 'HSTECH' ? '恒生科技指数' : `指数 ${indexId.value}`
      
      // 处理原始数据
      processRawData(data)
      
      // 生成图表数据
      generateChartData()
    } else {
      console.error('API返回错误:', ret.msg)
      // 使用模拟数据作为后备
      generateMockData()
    }
  } catch (error) {
    console.error('获取数据失败:', error)
    // 使用模拟数据作为后备
    generateMockData()
  } finally {
    loading.value = false
    // 等待 loading 状态变化后 DOM 更新完成，再渲染图表
    nextTick(() => {
      // 使用 setTimeout 确保 DOM 完全渲染
      setTimeout(() => {
        renderChart()
      }, 0)
    })
  }
}

// 处理原始数据
const processRawData = (data) => {
  const priceSeries = data.price_series || []
  
  // 按时间排序
  priceSeries.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
  
  rawData.value = priceSeries.map(item => ({
    date: item.timestamp.split('T')[0],
    timestamp: new Date(item.timestamp),
    open: item.open,
    high: item.high,
    low: item.low,
    close: item.close,
    volume: item.volume,
    return: 0 // 稍后计算
  }))
  
  // 计算日收益率
  for (let i = 1; i < rawData.value.length; i++) {
    const prevClose = rawData.value[i - 1].close
    const currClose = rawData.value[i].close
    rawData.value[i].return = (currClose - prevClose) / prevClose
  }
}

// 生成图表数据
const generateChartData = () => {
  if (rawData.value.length === 0) {
    chartData.value = []
    return
  }
  
  const data = []
  
  // 计算滚动波动率（年化）
  for (let i = volatilityWindow.value - 1; i < rawData.value.length; i++) {
    const item = rawData.value[i]
    const returns = []
    
    // 获取前N日的收益率
    for (let j = i - volatilityWindow.value + 1; j <= i; j++) {
      if (j >= 0 && rawData.value[j].return !== undefined) {
        returns.push(rawData.value[j].return)
      }
    }
    
    // 计算标准差并年化（假设252个交易日）
    let volatility = 0
    if (returns.length > 1) {
      const mean = returns.reduce((sum, r) => sum + r, 0) / returns.length
      const variance = returns.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / returns.length
      const stdDev = Math.sqrt(variance)
      volatility = stdDev * Math.sqrt(252) * 100 // 转换为百分比
    }
    
    data.push({
      date: item.date,
      timestamp: item.timestamp,
      price: item.close,
      change: i > 0 ? item.close - rawData.value[i-1].close : 0,
      changePercent: i > 0 ? ((item.close - rawData.value[i-1].close) / rawData.value[i-1].close * 100) : 0,
      volatility: volatility,
      open: item.open,
      high: item.high,
      low: item.low,
      volume: item.volume
    })
  }
  
  chartData.value = data
  
  // 计算当前价格和涨跌幅
  if (data.length >= 2) {
    currentPrice.value = data[data.length - 1].price
    currentChange.value = data[data.length - 1].change
    currentChangePercent.value = data[data.length - 1].changePercent
  } else if (data.length === 1) {
    currentPrice.value = data[0].price
    currentChange.value = data[0].change
    currentChangePercent.value = data[0].changePercent
  }
}


// 渲染图表
const renderChart = () => {
  if (chartData.value.length === 0) return
  
  // 如果 chartRef 还没准备好，等待后重试
  if (!chartRef.value) {
    setTimeout(() => {
      renderChart()
    }, 50)
    return
  }
  
  // 销毁之前的图表实例
  if (chartInstance) {
    chartInstance.dispose()
  }
  
  // 初始化图表
  chartInstance = echarts.init(chartRef.value)
  
  const dates = chartData.value.map(item => item.date)
  const prices = chartData.value.map(item => item.price)
  const volatilities = chartData.value.map(item => item.volatility)
  
  const series = []
  
  // 价格系列
  series.push({
    name: '指数点位',
    type: 'line',
    data: prices,
    smooth: false,
    yAxisIndex: 0,
    lineStyle: {
      width: 3,
      color: '#1890ff'
    },
    itemStyle: {
      color: '#1890ff'
    },
    areaStyle: {
      color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        {
          offset: 0,
          color: 'rgba(24, 144, 255, 0.5)'
        },
        {
          offset: 1,
          color: 'rgba(24, 144, 255, 0.1)'
        }
      ])
    },
    markPoint: {
      data: [
        { type: 'max', name: '最高' },
        { type: 'min', name: '最低' }
      ]
    }
  })
  
  // 波动率系列（如果选择显示）
  if (chartType.value === 'both') {
    series.push({
      name: '波动率',
      type: 'line',
      data: volatilities,
      yAxisIndex: 1,
      smooth: false,
      lineStyle: {
        width: 2,
        color: '#d46b08'
      },
      itemStyle: {
        color: '#d46b08'
      }
    })
  }
  
  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        let html = `<div style="font-weight: bold; margin-bottom: 5px">${params[0].axisValue}</div>`
        
        params.forEach(param => {
          if (param.seriesName === '指数点位') {
            const index = param.dataIndex
            const item = chartData.value[index]
            html += `
              <div>
                收盘: <span style="font-weight:bold">${item.price.toFixed(2)}</span>
              </div>
              <div>
                涨跌: <span style="color:${item.change >= 0 ? '#18a058' : '#d03050'};font-weight:bold">
                  ${item.change >= 0 ? '+' : ''}${item.change.toFixed(2)} (${item.changePercent.toFixed(2)}%)
                </span>
              </div>
            `
          } else if (param.seriesName === '波动率') {
            html += `
              <div>
                波动率: <span style="color:#d46b08;font-weight:bold">${param.value.toFixed(2)}%</span>
              </div>
            `
          }
        })
        
        return html
      }
    },
    legend: {
      data: chartType.value === 'both' ? ['指数点位', '波动率'] : ['指数点位'],
      top: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        color: '#666',
        rotate: 45
      },
      axisLine: {
        lineStyle: {
          color: '#ddd'
        }
      }
    },
    yAxis: [
      {
        type: 'value',
        name: '指数点位',
        position: 'left',
        axisLabel: {
          formatter: '{value}',
          color: '#1890ff'
        },
        axisLine: {
          lineStyle: {
            color: '#1890ff'
          },
          show: true
        },
        splitLine: {
          lineStyle: {
            type: 'dashed',
            color: '#e8e8e8'
          }
        }
      },
      ...(chartType.value === 'both' ? [{
        type: 'value',
        name: '波动率 (%)',
        position: 'right',
        axisLabel: {
          formatter: '{value}%',
          color: '#d46b08'
        },
        axisLine: {
          lineStyle: {
            color: '#d46b08'
          },
          show: true
        },
        splitLine: {
          show: false
        }
      }] : [])
    ],
    series: series,
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: 0,
        start: 0,
        end: 100
      },
      {
        type: 'slider',
        xAxisIndex: 0,
        start: 0,
        end: 100,
        bottom: 20
      }
    ]
  }
  
  chartInstance.setOption(option)
  
  // 响应窗口大小变化
  window.addEventListener('resize', handleResize)
}

// 处理窗口大小变化
const handleResize = () => {
  if (chartInstance) {
    chartInstance.resize()
  }
}

// 下载图表
const downloadChart = () => {
  if (!chartInstance) return
  
  const chartDataURL = chartInstance.getDataURL({
    type: 'png',
    pixelRatio: 2,
    backgroundColor: '#fff'
  })
  
  const link = document.createElement('a')
  link.href = chartDataURL
  link.download = `${indexName.value}_${indexId.value}_${new Date().toISOString().slice(0, 10)}.png`
  link.click()
}

// 监听图表类型和波动率窗口的变化
watch([chartType, volatilityWindow], () => {
  if (rawData.value.length > 0) {
    generateChartData()
    nextTick(() => {
      renderChart()
    })
  }
})

// 生命周期
onMounted(() => {
  // 检查是否有路由参数
  if (route.query.symbol) {
    indexId.value = route.query.symbol
    if (route.query.name) {
      indexName.value = route.query.name
    }
  }
  // 初始加载数据
  fetchData()
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
  }
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.simple-index-chart {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.input-section {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e8e8e8;
}

.chart-container {
  border-radius: 8px;
  border: 1px solid #e8e8e8;
  padding: 24px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.chart-header {
  margin-bottom: 24px;
}

.chart-loading, .empty-chart {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 500px;
  width: 100%;
}
</style>