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

// Flag to prevent multiple 401 redirects
let isRedirecting = false

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
    // Error response with non-zero code
    const errMsg = typeof res.message === 'string' ? res.message : '请求失败'
    message.error(errMsg)
    return Promise.reject(new Error(errMsg))
  },
  (error) => {
    const { response } = error
    if (response) {
      const { status, data } = response
      // Extract message safely
      let errMsg = '请求失败'
      if (data) {
        if (typeof data.message === 'string') {
          errMsg = data.message
        } else if (typeof data.detail === 'string') {
          errMsg = data.detail
        }
      }

      switch (status) {
        case 401:
          // Prevent multiple redirects
          if (!isRedirecting) {
            isRedirecting = true
            message.error('登录已过期，请重新登录')
            localStorage.removeItem('token')
            localStorage.removeItem('refreshToken')
            router.push('/login').finally(() => {
              // Reset flag after navigation completes
              setTimeout(() => { isRedirecting = false }, 1000)
            })
          }
          break
        case 403:
          message.error(errMsg || '没有权限访问')
          break
        case 404:
          message.error(errMsg || '资源不存在')
          break
        case 500:
          message.error(errMsg || '服务器错误')
          break
        default:
          message.error(errMsg)
      }
    } else {
      message.error('网络错误，请检查网络连接')
    }
    return Promise.reject(error)
  }
)

export default request
