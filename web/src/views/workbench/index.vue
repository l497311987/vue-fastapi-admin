<template>
  <AppPage :show-footer="false">
    <div flex-1>
      <n-card rounded-10>
        <div flex items-center justify-between>
          <div flex items-center>
            <img rounded-full width="60" :src="userStore.avatar" />
            <div ml-10>
              <p text-20 font-semibold>
                {{ $t('views.workbench.text_hello', { username: userStore.name }) }}
              </p>
              <p mt-5 text-14 op-60>{{ $t('views.workbench.text_welcome') }}</p>
            </div>
          </div>
          <n-space :size="12" :wrap="false">
            <n-statistic v-for="item in statisticData" :key="item.id" v-bind="item"></n-statistic>
          </n-space>
        </div>
      </n-card>

      <!-- 大盘行情概览 -->
      <n-card size="small" :segmented="true" mt-15 rounded-10>
        <template #header>
          <span text-18 font-bold>大盘行情</span>
        </template>
        <template #header-extra>
          <n-space align="center" justify="center">
            <n-tag :bordered="false" type="info">{{ marketData.date }}</n-tag>
            <n-tag :bordered="false" type="default" v-if="marketData.update_time">
              更新于 {{ marketData.update_time }}
            </n-tag>
            <n-button type="primary" size="small" secondary :loading="loading" @click="fetchMarketOverview">
              <template #icon>
                <i i-carbon-refresh />
              </template>
              刷新
            </n-button>
          </n-space>
        </template>
        <n-spin :show="loading">
          <!-- 主要指数 -->
          <div mb-15>
            <p font-bold mb-10 text-16>主要指数</p>
            <div flex flex-wrap gap-10>
              <n-card
                v-for="index in marketData.indices"
                :key="index.code"
                class="w-200"
                size="small"
                :bordered="true"
              >
                <div flex flex-col>
                  <span text-14 font-medium>{{ index.name }}</span>
                  <span text-20 font-bold :style="{ color: getChangeColor(index.change) }">
                    {{ index.current?.toFixed(2) }}
                  </span>
                  <div flex justify-between text-12>
                    <span :style="{ color: getChangeColor(index.change) }">
                      {{ index.change >= 0 ? '+' : '' }}{{ index.change?.toFixed(2) }}
                    </span>
                    <span :style="{ color: getChangeColor(index.change_pct) }">
                      {{ index.change_pct >= 0 ? '+' : '' }}{{ index.change_pct?.toFixed(2) }}%
                    </span>
                  </div>
                  <div flex justify-between text-12 op-60 mt-5>
                    <span>振幅: {{ index.amplitude?.toFixed(2) }}%</span>
                  </div>
                </div>
              </n-card>
            </div>
          </div>

          <!-- 市场概况 -->
          <div flex gap-20 mb-15>
            <n-card class="flex-1" size="small">
              <template #header>
                <span font-bold>市场概况</span>
              </template>
              <div flex justify-around text-center>
                <div>
                  <p text-24 font-bold text-green-500>{{ marketData.up_count }}</p>
                  <p text-12 op-60>上涨</p>
                </div>
                <div>
                  <p text-24 font-bold text-gray-500>{{ marketData.flat_count }}</p>
                  <p text-12 op-60>平盘</p>
                </div>
                <div>
                  <p text-24 font-bold text-red-500>{{ marketData.down_count }}</p>
                  <p text-12 op-60>下跌</p>
                </div>
                <div>
                  <p text-24 font-bold text-red-600>{{ marketData.limit_up_count }}</p>
                  <p text-12 op-60>涨停</p>
                </div>
                <div>
                  <p text-24 font-bold text-green-600>{{ marketData.limit_down_count }}</p>
                  <p text-12 op-60>跌停</p>
                </div>
              </div>
              <n-divider />
              <div flex justify-around text-center>
                <div>
                  <p text-18 font-bold>{{ (marketData.total_amount / 10000).toFixed(2) }}</p>
                  <p text-12 op-60>成交额(万亿)</p>
                </div>
                <div>
                  <p text-18 font-bold :style="{ color: getChangeColor(marketData.north_flow) }">
                    {{ marketData.north_flow >= 0 ? '+' : '' }}{{ marketData.north_flow?.toFixed(2) }}
                  </p>
                  <p text-12 op-60>北向资金(亿)</p>
                </div>
              </div>
            </n-card>
          </div>

          <!-- 板块涨跌 -->
          <div flex gap-20>
            <n-card class="flex-1" size="small">
              <template #header>
                <span font-bold>领涨板块</span>
              </template>
              <div v-for="(sector, idx) in marketData.top_sectors" :key="idx" flex items-center gap-10 py-5>
                <span>{{ sector.name }}</span>
                <n-tag type="error" size="small">+{{ sector.change_pct?.toFixed(2) }}%</n-tag>
              </div>
            </n-card>
            <n-card class="flex-1" size="small">
              <template #header>
                <span font-bold>领跌板块</span>
              </template>
              <div v-for="(sector, idx) in marketData.bottom_sectors" :key="idx" flex items-center gap-10 py-5>
                <span>{{ sector.name }}</span>
                <n-tag type="success" size="small">{{ sector.change_pct?.toFixed(2) }}%</n-tag>
              </div>
            </n-card>
          </div>
        </n-spin>
      </n-card>
    </div>
  </AppPage>
</template>

<script setup>
import { useUserStore } from '@/store'
import { useI18n } from 'vue-i18n'
import research from '@/api/research'

const { t } = useI18n({ useScope: 'global' })

const statisticData = computed(() => [
  {
    id: 0,
    label: t('views.workbench.label_number_of_items'),
    value: '25',
  },
  {
    id: 1,
    label: t('views.workbench.label_upcoming'),
    value: '4/16',
  },
  {
    id: 2,
    label: t('views.workbench.label_information'),
    value: '12',
  },
])

const userStore = useUserStore()

// 大盘行情数据
const loading = ref(false)
const marketData = ref({
  date: '',
  update_time: '',
  indices: [],
  up_count: 0,
  down_count: 0,
  flat_count: 0,
  limit_up_count: 0,
  limit_down_count: 0,
  total_amount: 0,
  north_flow: 0,
  top_sectors: [],
  bottom_sectors: [],
})

// 获取涨跌颜色
const getChangeColor = (value) => {
  if (value > 0) return '#ef4444' // 红色-上涨
  if (value < 0) return '#22c55e' // 绿色-下跌
  return '#6b7280' // 灰色-平盘
}

// 获取大盘行情
const fetchMarketOverview = async () => {
  loading.value = true
  try {
    const res = await research.get_market_overview()
    if (res.code === 200 && res.data) {
      marketData.value = res.data
    }
  } catch (error) {
    console.error('获取大盘行情失败:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchMarketOverview()
})
</script>
