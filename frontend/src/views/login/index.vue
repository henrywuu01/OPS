<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1>IOPS 智能运营系统</h1>
        <p>Intelligent Operations System</p>
      </div>
      <a-form
        :model="formState"
        :rules="rules"
        @finish="handleLogin"
        layout="vertical"
      >
        <a-form-item name="username">
          <a-input
            v-model:value="formState.username"
            placeholder="用户名"
            size="large"
          >
            <template #prefix>
              <UserOutlined />
            </template>
          </a-input>
        </a-form-item>
        <a-form-item name="password">
          <a-input-password
            v-model:value="formState.password"
            placeholder="密码"
            size="large"
          >
            <template #prefix>
              <LockOutlined />
            </template>
          </a-input-password>
        </a-form-item>
        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            size="large"
            block
            :loading="loading"
          >
            登录
          </a-button>
        </a-form-item>
        <div class="register-link">
          还没有账号？<router-link to="/register">立即注册</router-link>
        </div>
      </a-form>

      <!-- SSO Login Section -->
      <div v-if="ssoConfig.sso_enabled" class="sso-section">
        <a-divider>其他登录方式</a-divider>
        <div class="sso-buttons">
          <a-tooltip
            v-for="provider in ssoConfig.providers"
            :key="provider.name"
            :title="provider.label"
          >
            <a-button
              class="sso-btn"
              :class="`sso-btn-${provider.name}`"
              @click="handleSSOLogin(provider.name)"
              :loading="ssoLoading === provider.name"
            >
              <template #icon>
                <WechatOutlined v-if="provider.icon === 'wechat'" />
                <DingdingOutlined v-else-if="provider.icon === 'dingtalk'" />
                <span v-else-if="provider.icon === 'feishu'" class="feishu-icon">飞</span>
              </template>
            </a-button>
          </a-tooltip>
        </div>
      </div>
    </div>

    <!-- SSO QR Code Modal -->
    <a-modal
      v-model:open="ssoModalVisible"
      :title="`${currentSSOProvider?.label || 'SSO'} 扫码登录`"
      :footer="null"
      :width="400"
      centered
      @cancel="handleSSOModalClose"
    >
      <div class="sso-qrcode-container">
        <div v-if="ssoQRLoading" class="qrcode-loading">
          <a-spin size="large" />
          <p>正在加载二维码...</p>
        </div>
        <div v-else-if="ssoQRUrl" class="qrcode-content">
          <p class="qrcode-tip">请使用{{ currentSSOProvider?.label }}扫描二维码登录</p>
          <div class="qrcode-frame">
            <iframe :src="ssoQRUrl" frameborder="0" scrolling="no"></iframe>
          </div>
          <p class="qrcode-hint">扫码后请在手机上确认登录</p>
        </div>
        <div v-else class="qrcode-error">
          <a-result status="error" title="加载失败">
            <template #extra>
              <a-button type="primary" @click="refreshSSOQRCode">重新加载</a-button>
            </template>
          </a-result>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { UserOutlined, LockOutlined, WechatOutlined, DingdingOutlined } from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import { getSSOConfig, getSSOLoginUrl } from '@/api/auth'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const loading = ref(false)
const formState = reactive({
  username: '',
  password: '',
})

const rules = {
  username: [{ required: true, message: '请输入用户名' }],
  password: [{ required: true, message: '请输入密码' }],
}

// SSO state
const ssoConfig = ref({ sso_enabled: false, providers: [] })
const ssoLoading = ref(null)
const ssoModalVisible = ref(false)
const ssoQRLoading = ref(false)
const ssoQRUrl = ref('')
const currentSSOProvider = ref(null)
const ssoState = ref('')

// Load SSO config on mount
onMounted(async () => {
  try {
    const res = await getSSOConfig()
    ssoConfig.value = res
  } catch (err) {
    // SSO not configured, ignore
  }

  // Listen for SSO callback message
  window.addEventListener('message', handleSSOMessage)
})

onUnmounted(() => {
  window.removeEventListener('message', handleSSOMessage)
})

async function handleLogin() {
  loading.value = true
  try {
    await userStore.loginAction(formState)
    message.success('登录成功')
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (err) {
    // Error handled by request interceptor
  } finally {
    loading.value = false
  }
}

async function handleSSOLogin(provider) {
  const providerInfo = ssoConfig.value.providers.find(p => p.name === provider)
  if (!providerInfo) return

  currentSSOProvider.value = providerInfo
  ssoLoading.value = provider

  try {
    const res = await getSSOLoginUrl(provider)
    ssoQRUrl.value = res.qr_url
    ssoState.value = res.state
    ssoModalVisible.value = true
  } catch (err) {
    message.error('获取登录二维码失败')
  } finally {
    ssoLoading.value = null
  }
}

function handleSSOModalClose() {
  ssoModalVisible.value = false
  ssoQRUrl.value = ''
  currentSSOProvider.value = null
}

async function refreshSSOQRCode() {
  if (!currentSSOProvider.value) return

  ssoQRLoading.value = true
  try {
    const res = await getSSOLoginUrl(currentSSOProvider.value.name)
    ssoQRUrl.value = res.qr_url
    ssoState.value = res.state
  } catch (err) {
    message.error('获取登录二维码失败')
  } finally {
    ssoQRLoading.value = false
  }
}

function handleSSOMessage(event) {
  // Handle SSO callback from iframe/popup
  if (event.data && event.data.type === 'sso_callback') {
    const { code, state, provider } = event.data
    handleSSOCallback(provider, code, state)
  }
}

async function handleSSOCallback(provider, code, state) {
  if (!code) return

  try {
    const { ssoCallback } = await import('@/api/auth')
    const res = await ssoCallback(provider, { code, state })

    userStore.setToken(res.access)
    userStore.setRefreshToken(res.refresh)
    userStore.setUserInfo(res.user)

    ssoModalVisible.value = false
    message.success(res.is_new_user ? '注册成功，欢迎使用' : '登录成功')

    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (err) {
    message.error(err.response?.data?.error || 'SSO登录失败')
  }
}
</script>

<style scoped lang="less">
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-box {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;

  h1 {
    font-size: 24px;
    color: #333;
    margin-bottom: 8px;
  }

  p {
    color: #999;
    font-size: 14px;
  }
}

.register-link {
  text-align: center;
  color: #666;

  a {
    color: #1890ff;
  }
}

.sso-section {
  margin-top: 24px;

  :deep(.ant-divider-inner-text) {
    color: #999;
    font-size: 12px;
  }
}

.sso-buttons {
  display: flex;
  justify-content: center;
  gap: 16px;
}

.sso-btn {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  transition: all 0.3s;

  &:hover {
    transform: scale(1.1);
  }

  &.sso-btn-wechat_work {
    background: #07c160;
    border-color: #07c160;
    color: #fff;

    &:hover {
      background: #06ad56;
      border-color: #06ad56;
    }
  }

  &.sso-btn-dingtalk {
    background: #3a8bff;
    border-color: #3a8bff;
    color: #fff;

    &:hover {
      background: #2979ff;
      border-color: #2979ff;
    }
  }

  &.sso-btn-feishu {
    background: #3370ff;
    border-color: #3370ff;
    color: #fff;

    &:hover {
      background: #2563eb;
      border-color: #2563eb;
    }
  }
}

.feishu-icon {
  font-size: 18px;
  font-weight: bold;
}

.sso-qrcode-container {
  text-align: center;
  padding: 20px;
}

.qrcode-loading {
  p {
    margin-top: 16px;
    color: #666;
  }
}

.qrcode-content {
  .qrcode-tip {
    margin-bottom: 16px;
    color: #333;
    font-size: 14px;
  }

  .qrcode-frame {
    width: 300px;
    height: 300px;
    margin: 0 auto;
    border: 1px solid #eee;
    border-radius: 8px;
    overflow: hidden;

    iframe {
      width: 100%;
      height: 100%;
    }
  }

  .qrcode-hint {
    margin-top: 16px;
    color: #999;
    font-size: 12px;
  }
}
</style>
