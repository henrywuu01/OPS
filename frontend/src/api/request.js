import axios from 'axios'
import { message } from 'ant-design-vue'
import router from '@/router'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
request.interceptors.response.use(
  (response) => {
    const res = response.data
    // Standard response format: { code, message, data }
    if (res.code === 0) {
      return res.data
    }
    // Error response
    message.error(res.message || '请求失败')
    return Promise.reject(new Error(res.message || '请求失败'))
  },
  (error) => {
    const { response } = error
    if (response) {
      const { status, data } = response
      switch (status) {
        case 401:
          message.error('登录已过期，请重新登录')
          localStorage.removeItem('token')
          localStorage.removeItem('refreshToken')
          router.push('/login')
          break
        case 403:
          message.error(data?.message || '没有权限访问')
          break
        case 404:
          message.error(data?.message || '资源不存在')
          break
        case 500:
          message.error(data?.message || '服务器错误')
          break
        default:
          message.error(data?.message || '请求失败')
      }
    } else {
      message.error('网络错误，请检查网络连接')
    }
    return Promise.reject(error)
  }
)

export default request
