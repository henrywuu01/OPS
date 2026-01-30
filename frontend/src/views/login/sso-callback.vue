<template>
  <div class="sso-callback-container">
    <div class="callback-box">
      <a-spin v-if="loading" size="large" />
      <div v-if="loading" class="loading-text">
        <p>正在处理{{ providerLabel }}登录...</p>
      </div>
      <a-result
        v-else-if="error"
        status="error"
        :title="error"
      >
        <template #extra>
          <a-button type="primary" @click="goToLogin">返回登录</a-button>
        </template>
      </a-result>
      <a-result
        v-else-if="success"
        status="success"
        title="登录成功"
        sub-title="正在跳转..."
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { useUserStore } from '@/stores/user'
import { ssoCallback } from '@/api/auth'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const loading = ref(true)
const error = ref('')
const success = ref(false)

const provider = computed(() => route.params.provider)

const providerLabels = {
  wechat_work: '企业微信',
  dingtalk: '钉钉',
  feishu: '飞书',
}

const providerLabel = computed(() => providerLabels[provider.value] || 'SSO')

onMounted(async () => {
  const code = route.query.code
  const state = route.query.state

  if (!code) {
    error.value = '授权失败，缺少授权码'
    loading.value = false
    return
  }

  try {
    const res = await ssoCallback(provider.value, { code, state })

    userStore.setToken(res.access)
    userStore.setRefreshToken(res.refresh)
    userStore.setUserInfo(res.user)

    success.value = true
    loading.value = false

    message.success(res.is_new_user ? '注册成功，欢迎使用' : '登录成功')

    // Try to notify parent window (if opened in popup/iframe)
    if (window.opener) {
      window.opener.postMessage({
        type: 'sso_callback',
        provider: provider.value,
        code,
        state,
        success: true,
      }, '*')
      window.close()
    } else {
      // Redirect to dashboard
      setTimeout(() => {
        const redirect = route.query.redirect || '/'
        router.push(redirect)
      }, 1000)
    }
  } catch (err) {
    error.value = err.response?.data?.error || 'SSO登录失败'
    loading.value = false

    // Notify parent window of error
    if (window.opener) {
      window.opener.postMessage({
        type: 'sso_callback',
        provider: provider.value,
        success: false,
        error: error.value,
      }, '*')
    }
  }
})

function goToLogin() {
  router.push('/login')
}
</script>

<style scoped lang="less">
.sso-callback-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.callback-box {
  width: 400px;
  padding: 60px 40px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  text-align: center;
}

.loading-text {
  margin-top: 24px;

  p {
    color: #666;
    font-size: 16px;
  }
}
</style>
