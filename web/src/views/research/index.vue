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
              例如：上证指数 (000001)、深证成指 (399001)
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
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { 
  NInput, 
  NButton, 
  NIcon, 
  NSpin, 
  NEmpty, 
  NH3,
  NText,
  NSpace
} from 'naive-ui'
import * as echarts from 'echarts'
import { 
  Search as SearchIcon,
  TrendingUp as TrendingUpIcon,
  BarChart as BarChartIcon,
  Download as DownloadIcon
} from '@vicons/ionicons5'

// 指数ID
const indexId = ref('000001')
const indexName = ref('上证指数')
const loading = ref(false)

// 图表数据
const chartData = ref([])
const chartRef = ref(null)
let chartInstance = null

// 计算当前价格和涨跌幅
const currentPrice = ref(0)
const currentChange = ref(0)
const currentChangePercent = ref(0)

// 热门指数映射
const indexMap = {
  '000001': '上证指数',
  '399001': '深证成指',
  '399006': '创业板指',
  '000300': '沪深300',
  '000905': '中证500',
  'HSI': '恒生指数',
  'SPX': '标普500',
  'IXIC': '纳斯达克',
  'DJI': '道琼斯',
  'N225': '日经225'
}

// 获取数据
const fetchData = async () => {
  if (!indexId.value) return
  
  loading.value = true
  
  // 设置指数名称
  indexName.value = indexMap[indexId.value] || `指数 ${indexId.value}`
  
  // 模拟API调用延迟
  await new Promise(resolve => setTimeout(resolve, 800))
  
  // 生成模拟数据
  generateMockData()
  
  loading.value = false
  
  // 渲染图表
  nextTick(() => {
    renderChart()
  })
}

// 生成模拟数据
const generateMockData = () => {
  const data = []
  const basePrice = 3000 + Math.random() * 2000
  let currentPrice = basePrice
  
  // 生成最近30天的数据
  for (let i = 30; i >= 0; i--) {
    const date = new Date()
    date.setDate(date.getDate() - i)
    
    // 生成随机价格变化
    const change = (Math.random() - 0.5) * 80
    currentPrice += change
    
    // 防止价格偏离太远
    if (currentPrice < basePrice * 0.7) currentPrice = basePrice * 0.7
    if (currentPrice > basePrice * 1.3) currentPrice = basePrice * 1.3
    
    data.push({
      date: date.toLocaleDateString(),
      price: currentPrice,
      change: change,
      changePercent: (change / (currentPrice - change) * 100)
    })
  }
  
  chartData.value = data
  
  // 计算当前价格和涨跌幅
  if (data.length >= 2) {
    currentPrice.value = data[data.length - 1].price
    currentChange.value = data[data.length - 1].price - data[data.length - 2].price
    currentChangePercent.value = (currentChange.value / data[data.length - 2].price) * 100
  }
}

// 渲染图表
const renderChart = () => {
  if (!chartRef.value || chartData.value.length === 0) return
  
  // 销毁之前的图表实例
  if (chartInstance) {
    chartInstance.dispose()
  }
  
  // 初始化图表
  chartInstance = echarts.init(chartRef.value)
  
  const dates = chartData.value.map(item => item.date)
  const prices = chartData.value.map(item => item.price)
  
  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const data = params[0]
        const index = data.dataIndex
        const item = chartData.value[index]
        
        return `
          <div style="font-weight: bold; margin-bottom: 5px">${item.date}</div>
          <div>
            收盘: <span style="font-weight:bold">${item.price.toFixed(2)}</span>
          </div>
          <div>
            涨跌: <span style="color:${item.change >= 0 ? '#18a058' : '#d03050'};font-weight:bold">
              ${item.change >= 0 ? '+' : ''}${item.change.toFixed(2)} (${item.changePercent.toFixed(2)}%)
            </span>
          </div>
        `
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '10%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        color: '#666'
      },
      axisLine: {
        lineStyle: {
          color: '#ddd'
        }
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}',
        color: '#666'
      },
      axisLine: {
        lineStyle: {
          color: '#ddd'
        }
      },
      splitLine: {
        lineStyle: {
          type: 'dashed',
          color: '#e8e8e8'
        }
      }
    },
    series: [
      {
        name: '指数点位',
        type: 'line',
        data: prices,
        smooth: true,
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

// 生命周期
onMounted(() => {
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