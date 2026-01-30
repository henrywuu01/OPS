<template>
  <a-layout class="layout">
    <a-layout-sider
      v-model:collapsed="collapsed"
      collapsible
      theme="dark"
      :width="220"
    >
      <div class="logo">
        <span v-if="!collapsed">OPS</span>
        <span v-else>O</span>
      </div>
      <a-menu
        v-model:selectedKeys="selectedKeys"
        v-model:openKeys="openKeys"
        theme="dark"
        mode="inline"
      >
        <a-menu-item key="dashboard" @click="$router.push('/dashboard')">
          <template #icon><DashboardOutlined /></template>
          <span>工作台</span>
        </a-menu-item>

        <a-sub-menu key="system">
          <template #icon><SettingOutlined /></template>
          <template #title>系统管理</template>
          <a-menu-item key="users" @click="$router.push('/system/users')">用户管理</a-menu-item>
          <a-menu-item key="roles" @click="$router.push('/system/roles')">角色管理</a-menu-item>
        </a-sub-menu>

        <a-sub-menu key="scheduler">
          <template #icon><ScheduleOutlined /></template>
          <template #title>任务调度</template>
          <a-menu-item key="jobs" @click="$router.push('/scheduler/jobs')">任务管理</a-menu-item>
          <a-menu-item key="flows" @click="$router.push('/scheduler/flows')">工作流</a-menu-item>
        </a-sub-menu>

        <a-sub-menu key="report">
          <template #icon><BarChartOutlined /></template>
          <template #title>报表中心</template>
          <a-menu-item key="reports" @click="$router.push('/report/list')">报表管理</a-menu-item>
          <a-menu-item key="datasources" @click="$router.push('/report/datasources')">数据源</a-menu-item>
        </a-sub-menu>

        <a-menu-item key="config" @click="$router.push('/config/tables')">
          <template #icon><DatabaseOutlined /></template>
          <span>配置中心</span>
        </a-menu-item>

        <a-sub-menu key="workflow">
          <template #icon><ApartmentOutlined /></template>
          <template #title>审批中心</template>
          <a-menu-item key="definitions" @click="$router.push('/workflow/definitions')">流程管理</a-menu-item>
          <a-menu-item key="todo" @click="$router.push('/workflow/todo')">待办事项</a-menu-item>
        </a-sub-menu>

        <a-menu-item key="audit" @click="$router.push('/audit/logs')">
          <template #icon><FileSearchOutlined /></template>
          <span>审计日志</span>
        </a-menu-item>

        <a-menu-item key="message" @click="$router.push('/message/templates')">
          <template #icon><MessageOutlined /></template>
          <span>消息中心</span>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>

    <a-layout>
      <a-layout-header class="header">
        <div class="header-left">
          <MenuFoldOutlined v-if="!collapsed" @click="collapsed = true" />
          <MenuUnfoldOutlined v-else @click="collapsed = false" />
        </div>
        <div class="header-right">
          <a-badge :count="5" :offset="[10, 0]">
            <BellOutlined class="header-icon" @click="$router.push('/notifications')" />
          </a-badge>
          <a-dropdown>
            <div class="user-info">
              <a-avatar :size="32">{{ userStore.username?.charAt(0)?.toUpperCase() }}</a-avatar>
              <span class="username">{{ userStore.username }}</span>
            </div>
            <template #overlay>
              <a-menu>
                <a-menu-item key="profile">个人中心</a-menu-item>
                <a-menu-divider />
                <a-menu-item key="logout" @click="handleLogout">退出登录</a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </a-layout-header>

      <a-layout-content class="content">
        <router-view />
      </a-layout-content>
    </a-layout>
  </a-layout>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import {
  DashboardOutlined,
  SettingOutlined,
  ScheduleOutlined,
  BarChartOutlined,
  DatabaseOutlined,
  ApartmentOutlined,
  FileSearchOutlined,
  MessageOutlined,
  BellOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const collapsed = ref(false)
const selectedKeys = ref(['dashboard'])
const openKeys = ref([])

watch(
  () => route.path,
  (path) => {
    // Update selected menu based on route
    const pathParts = path.split('/').filter(Boolean)
    if (pathParts.length > 0) {
      selectedKeys.value = [pathParts[pathParts.length - 1]]
      if (pathParts.length > 1) {
        openKeys.value = [pathParts[0]]
      }
    }
  },
  { immediate: true }
)

async function handleLogout() {
  await userStore.logoutAction()
  message.success('已退出登录')
  router.push('/login')
}
</script>

<style scoped lang="less">
.layout {
  min-height: 100vh;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: bold;
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
}

.header {
  background: #fff;
  padding: 0 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.header-left {
  font-size: 18px;
  cursor: pointer;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.header-icon {
  font-size: 18px;
  cursor: pointer;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;

  .username {
    color: #333;
  }
}

.content {
  margin: 24px;
  background: #fff;
  border-radius: 4px;
  min-height: 280px;
}
</style>
