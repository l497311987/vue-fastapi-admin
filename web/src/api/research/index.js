import { request } from '@/utils'


export default {
  get_index_his_data: (params = {}) => request.get('/research/index/hk/his', { params }),
  get_index_realtime_data: () => request.get('/research/index/hk/realtime'),
  get_market_overview: () => request.get('/research/index/market/overview'),
}