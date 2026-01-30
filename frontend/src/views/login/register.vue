<template>
  <div class="login-container">
    <div class="login-box">
      <div class="login-header">
        <h1>OPS 智能运营系统</h1>
        <p>用户注册</p>
      </div>
      <a-form
        :model="formState"
        :rules="rules"
        @finish="handleRegister"
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
        <a-form-item name="real_name">
          <a-input
            v-model:value="formState.real_name"
            placeholder="真实姓名（可选）"
            size="large"
          >
            <template #prefix>
              <IdcardOutlined />
            </template>
          </a-input>
        </a-form-item>
        <a-form-item name="email">
          <a-input
            v-model:value="formState.email"
            placeholder="邮箱（可选）"
            size="large"
          >
            <template #prefix>
              <MailOutlined />
            </template>
          </a-input>
        </a-form-item>
        <a-form-item name="phone">
          <a-input
            v-model:value="formState.phone"
            placeholder="手机号（可选）"
            size="large"
          >
            <template #prefix>
              <PhoneOutlined />
            </template>
          </a-input>
        </a-form-item>
        <a-form-item name="password">
          <a-input-password
            v-model:value="formState.password"
            placeholder="密码（至少8位）"
            size="large"
          >
            <template #prefix>
              <LockOutlined />
            </template>
          </a-input-password>
        </a-form-item>
        <a-form-item name="confirm_password">
          <a-input-password
            v-model:value="formState.confirm_password"
            placeholder="确认密码"
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
            注册
          </a-button>
        </a-form-item>
        <div class="login-link">
          已有账号？<router-link to="/login">立即登录</router-link>
        </div>
      </a-form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { UserOutlined, LockOutlined, MailOutlined, PhoneOutlined, IdcardOutlined } from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'
import { register } from '@/api/auth'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const formState = reactive({
  username: '',
  real_name: '',
  email: '',
  phone: '',
  password: '',
  confirm_password: '',
})

const rules = {
  username: [
    { required: true, message: '请输入用户名' },
    { min: 3, max: 20, message: '用户名长度为3-20个字符' },
  ],
  password: [
    { required: true, message: '请输入密码' },
    { min: 8, message: '密码至少8位' },
  ],
  confirm_password: [
    { required: true, message: '请确认密码' },
    {
      validator: (_, value) => {
        if (value && value !== formState.password) {
          return Promise.reject('两次输入的密码不一致')
        }
        return Promise.resolve()
      },
    },
  ],
  email: [
    { type: 'email', message: '请输入有效的邮箱地址' },
  ],
}

async function handleRegister() {
  loading.value = true
  try {
    const res = await register(formState)
    // Save tokens and user info
    userStore.setToken(res.access)
    userStore.setRefreshToken(res.refresh)
    userStore.setUserInfo(res.user)
    message.success('注册成功')
    router.push('/')
  } catch (err) {
    // Error handled by request interceptor
  } finally {
    loading.value = false
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

.login-link {
  text-align: center;
  color: #666;

  a {
    color: #1890ff;
  }
}
</style>
