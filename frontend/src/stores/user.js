import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login, logout, getProfile } from '@/api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(null)
  const permissions = ref([])

  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => userInfo.value?.username || '')

  async function loginAction(credentials) {
    const res = await login(credentials)
    token.value = res.access
    localStorage.setItem('token', res.access)
    localStorage.setItem('refreshToken', res.refresh)
    await fetchProfile()
    return res
  }

  async function logoutAction() {
    try {
      await logout()
    } finally {
      token.value = ''
      userInfo.value = null
      permissions.value = []
      localStorage.removeItem('token')
      localStorage.removeItem('refreshToken')
    }
  }

  async function fetchProfile() {
    const res = await getProfile()
    userInfo.value = res
    permissions.value = res.permissions || []
  }

  function hasPermission(code) {
    if (!code) return true
    return permissions.value.includes(code) || permissions.value.includes('*')
  }

  return {
    token,
    userInfo,
    permissions,
    isLoggedIn,
    username,
    loginAction,
    logoutAction,
    fetchProfile,
    hasPermission,
  }
})
