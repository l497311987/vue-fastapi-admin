<template>
  <div class="realtime-index">
    <!-- 头部 -->
    <div class="header-section">
      <n-space align="center" justify="space-between">
        <n-h2 style="margin: 0">
          <n-icon :component="TrendingUpIcon" style="margin-right: 8px;" />
          指数实时行情
        </n-h2>
        <n-space>
          <n-input
            v-model:value="searchKeyword"
            placeholder="搜索指数名称或代码"
            clearable
            style="width: 200px;"
          >
            <template #prefix>
              <n-icon :component="SearchIcon" />
            </template>
          </n-input>
          <n-button 
            type="primary" 
            @click="fetchData"
            :loading="loading"
          >
            <template #icon>
              <n-icon :component="RefreshIcon" />
            </template>
            刷新
          </n-button>
        </n-space>
      </n-space>
      <n-text depth="3" v-if="lastUpdateTime">
        最后更新: {{ lastUpdateTime }}
      </n-text>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading && indexList.length === 0" class="loading-container">
      <n-spin size="large">
        <template #description>
          正在加载行情数据...
        </template>
      </n-spin>
    </div>

    <!-- 空状态 -->
    <div v-else-if="filteredList.length === 0 && !loading" class="empty-container">
      <n-empty size="large" :description="searchKeyword ? '未找到匹配的指数' : '暂无数据'">
        <template #icon>
          <n-icon :component="BarChartIcon" size="60" />
        </template>
      </n-empty>
    </div>

    <!-- 卡片列表 -->
    <div v-else class="card-grid">
      <div 
        v-for="item in filteredList" 
        :key="item.symbol" 
        class="index-card"
        :class="{ 'card-up': item.change > 0, 'card-down': item.change < 0 }"
        @click="goToDetail(item)"
      >
        <div class="card-header">
          <span class="symbol">{{ item.symbol }}</span>
          <n-tag 
            :type="item.change > 0 ? 'success' : item.change < 0 ? 'error' : 'default'" 
            size="small"
            round
          >
            {{ item.change > 0 ? '↑' : item.change < 0 ? '↓' : '-' }}
            {{ Math.abs(item.pct_change).toFixed(2) }}%
          </n-tag>
        </div>
        
        <div class="card-name">{{ item.name }}</div>
        
        <div class="card-price" :class="{ 'price-up': item.change > 0, 'price-down': item.change < 0 }">
          {{ item.price.toFixed(2) }}
        </div>
        
        <div class="card-change" :class="{ 'change-up': item.change > 0, 'change-down': item.change < 0 }">
          {{ item.change > 0 ? '+' : '' }}{{ item.change.toFixed(2) }}
        </div>
        
        <n-divider style="margin: 12px 0;" />
        
        <div class="card-details">
          <div class="detail-row">
            <span class="label">昨收</span>
            <span class="value">{{ item.prev_close.toFixed(2) }}</span>
          </div>
          <div class="detail-row">
            <span class="label">今开</span>
            <span class="value">{{ item.open.toFixed(2) }}</span>
          </div>
          <div class="detail-row">
            <span class="label">最高</span>
            <span class="value high">{{ item.high.toFixed(2) }}</span>
          </div>
          <div class="detail-row">
            <span class="label">最低</span>
            <span class="value low">{{ item.low.toFixed(2) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  NButton, 
  NIcon, 
  NSpin, 
  NEmpty, 
  NH2,
  NText,
  NSpace,
  NInput,
  NTag,
  NDivider
} from 'naive-ui'
import { 
  Search as SearchIcon,
  TrendingUp as TrendingUpIcon,
  BarChart as BarChartIcon,
  Refresh as RefreshIcon
} from '@vicons/ionicons5'

import research from '@/api/research'

const router = useRouter()

// 数据
const indexList = ref([])
const loading = ref(false)
const lastUpdateTime = ref('')
const searchKeyword = ref('')

// 自动刷新定时器
let refreshTimer = null

// 过滤后的列表
const filteredList = computed(() => {
  if (!searchKeyword.value) {
    return indexList.value
  }
  const keyword = searchKeyword.value.toLowerCase()
  return indexList.value.filter(item => 
    item.symbol.toLowerCase().includes(keyword) || 
    item.name.toLowerCase().includes(keyword)
  )
})

// 获取数据
const fetchData = async () => {
  loading.value = true
  
  try {
    const ret = await research.get_index_realtime_data()
    
    if (ret.code === 200) {
      const data = JSON.parse(ret.data)
      indexList.value = data
      lastUpdateTime.value = new Date().toLocaleString('zh-CN')
    } else {
      console.error('API返回错误:', ret.msg)
    }
  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 跳转到指数详情页
const goToDetail = (item) => {
  router.push({
    path: '/research/analyse',
    query: {
      symbol: item.symbol,
      name: item.name
    }
  })
}

// 生命周期
onMounted(() => {
  fetchData()
  // 每60秒自动刷新
  refreshTimer = setInterval(fetchData, 60000)
})

onUnmounted(() => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
  }
})
</script>

<style scoped>
.realtime-index {
  padding: 24px;
  max-width: 1600px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.header-section {
  flex-shrink: 0;
  margin-bottom: 24px;
  padding: 20px 24px;
  border-bottom: none;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.loading-container,
.empty-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
  padding-bottom: 24px;
  overflow-y: auto;
  flex: 1;
}

.index-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #f0f0f0;
  transition: all 0.3s ease;
}

.index-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  cursor: pointer;
}

.card-up {
  border-left: 4px solid #18a058;
}

.card-down {
  border-left: 4px solid #d03050;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.symbol {
  font-size: 14px;
  font-weight: 600;
  color: #666;
}

.card-name {
  font-size: 13px;
  color: #999;
  margin-bottom: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-price {
  font-size: 28px;
  font-weight: 700;
  color: #333;
  line-height: 1.2;
}

.price-up {
  color: #18a058;
}

.price-down {
  color: #d03050;
}

.card-change {
  font-size: 16px;
  font-weight: 500;
  margin-top: 4px;
}

.change-up {
  color: #18a058;
}

.change-down {
  color: #d03050;
}

.card-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.detail-row .label {
  color: #999;
}

.detail-row .value {
  color: #333;
  font-weight: 500;
}

.detail-row .value.high {
  color: #18a058;
}

.detail-row .value.low {
  color: #d03050;
}
</style>
