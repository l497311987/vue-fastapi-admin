import { request } from '@/utils'


export default {
  get_index_info: (params = {}) => request.get('/research/index/hk', { params }),
}