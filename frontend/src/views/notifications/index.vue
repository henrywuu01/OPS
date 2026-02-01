<template>
  <div class="page-container">
    <a-card title="通知中心" :bordered="false">
      <template #extra>
        <a-space>
          <a-button @click="markAllRead" :disabled="unreadCount === 0">
            全部已读
          </a-button>
          <a-badge :count="unreadCount" :offset="[-5, 5]">
            <a-button type="primary" @click="fetchNotifications">
              <reload-outlined /> 刷新
            </a-button>
          </a-badge>
        </a-space>
      </template>

      <!-- 筛选 -->
      <a-row :gutter="16" style="margin-bottom: 16px;">
        <a-col :span="6">
          <a-select v-model:value="filterType" style="width: 100%" placeholder="通知类型" allowClear @change="fetchNotifications">
            <a-select-option value="">全部类型</a-select-option>
            <a-select-option value="system">系统通知</a-select-option>
            <a-select-option value="approval">审批通知</a-select-option>
            <a-select-option value="task">任务通知</a-select-option>
            <a-select-option value="alert">告警通知</a-select-option>
          </a-select>
        </a-col>
        <a-col :span="6">
          <a-select v-model:value="filterRead" style="width: 100%" placeholder="阅读状态" allowClear @change="fetchNotifications">
            <a-select-option value="">全部状态</a-select-option>
            <a-select-option value="unread">未读</a-select-option>
            <a-select-option value="read">已读</a-select-option>
          </a-select>
        </a-col>
      </a-row>

      <!-- 通知列表 -->
      <a-list
        :data-source="notifications"
        :loading="loading"
        item-layout="horizontal"
      >
        <template #renderItem="{ item }">
          <a-list-item :class="{ 'unread-item': !item.is_read }">
            <a-list-item-meta>
              <template #avatar>
                <a-avatar :style="{ backgroundColor: getTypeColor(item.type) }">
                  <template #icon>
                    <bell-outlined v-if="item.type === 'system'" />
                    <audit-outlined v-else-if="item.type === 'approval'" />
                    <schedule-outlined v-else-if="item.type === 'task'" />
                    <alert-outlined v-else-if="item.type === 'alert'" />
                    <message-outlined v-else />
                  </template>
                </a-avatar>
              </template>
              <template #title>
                <a-space>
                  <span :class="{ 'unread-title': !item.is_read }">{{ item.title }}</span>
                  <a-tag :color="getLevelColor(item.level)" size="small">
                    {{ getLevelText(item.level) }}
                  </a-tag>
                </a-space>
              </template>
              <template #description>
                <div class="notification-content">{{ item.content }}</div>
                <div class="notification-time">{{ formatTime(item.created_at) }}</div>
              </template>
            </a-list-item-meta>
            <template #actions>
              <a-button
                v-if="!item.is_read"
                type="link"
                size="small"
                @click="markAsRead(item)"
              >
                标为已读
              </a-button>
              <a-button
                v-if="item.link_url"
                type="link"
                size="small"
                @click="goToLink(item)"
              >
                查看详情
              </a-button>
              <a-popconfirm title="确定删除此通知？" @confirm="deleteNotification(item)">
                <a-button type="link" size="small" danger>删除</a-button>
              </a-popconfirm>
            </template>
          </a-list-item>
        </template>

        <template #loadMore>
          <div v-if="hasMore" style="text-align: center; margin-top: 12px;">
            <a-button @click="loadMore" :loading="loadingMore">加载更多</a-button>
          </div>
        </template>
      </a-list>

      <a-empty v-if="!loading && notifications.length === 0" description="暂无通知" />
    </a-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import {
  ReloadOutlined,
  BellOutlined,
  AuditOutlined,
  ScheduleOutlined,
  AlertOutlined,
  MessageOutlined
} from '@ant-design/icons-vue'
import request from '@/api/request'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const router = useRouter()

const notifications = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const unreadCount = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const hasMore = ref(false)

const filterType = ref('')
const filterRead = ref('')

const fetchNotifications = async (reset = true) => {
  if (reset) {
    currentPage.value = 1
    notifications.value = []
  }
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (filterType.value) params.type = filterType.value
    if (filterRead.value === 'read') params.is_read = true
    if (filterRead.value === 'unread') params.is_read = false

    const res = await request.get('/notifications/', { params })
    if (reset) {
      notifications.value = res.results || []
    } else {
      notifications.value = [...notifications.value, ...(res.results || [])]
    }
    total.value = res.total || 0
    hasMore.value = notifications.value.length < total.value
  } catch (error) {
    console.error('加载通知失败:', error)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const loadMore = async () => {
  currentPage.value++
  loadingMore.value = true
  await fetchNotifications(false)
}

const fetchUnreadCount = async () => {
  try {
    const res = await request.get('/notifications/unread-count/')
    unreadCount.value = res.unread_count || 0
  } catch (error) {
    console.error('获取未读数失败:', error)
  }
}

const markAsRead = async (item) => {
  try {
    await request.post(`/notifications/${item.id}/read/`)
    item.is_read = true
    unreadCount.value = Math.max(0, unreadCount.value - 1)
    message.success('已标为已读')
  } catch (error) {
    message.error('操作失败')
  }
}

const markAllRead = async () => {
  try {
    await request.post('/notifications/read-all/')
    notifications.value.forEach(n => n.is_read = true)
    unreadCount.value = 0
    message.success('全部已读')
  } catch (error) {
    message.error('操作失败')
  }
}

const deleteNotification = async (item) => {
  try {
    await request.delete(`/notifications/${item.id}/`)
    notifications.value = notifications.value.filter(n => n.id !== item.id)
    if (!item.is_read) {
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    }
    message.success('删除成功')
  } catch (error) {
    message.error('删除失败')
  }
}

const goToLink = (item) => {
  if (item.link_url) {
    if (item.link_url.startsWith('http')) {
      window.open(item.link_url, '_blank')
    } else {
      router.push(item.link_url)
    }
    if (!item.is_read) {
      markAsRead(item)
    }
  }
}

const getTypeColor = (type) => {
  const colors = {
    system: '#1890ff',
    approval: '#722ed1',
    task: '#13c2c2',
    alert: '#f5222d',
    personal: '#52c41a'
  }
  return colors[type] || '#1890ff'
}

const getLevelColor = (level) => {
  const colors = {
    info: 'blue',
    warning: 'orange',
    error: 'red',
    success: 'green'
  }
  return colors[level] || 'default'
}

const getLevelText = (level) => {
  const texts = {
    info: '信息',
    warning: '警告',
    error: '错误',
    success: '成功'
  }
  return texts[level] || level
}

const formatTime = (time) => {
  return dayjs(time).fromNow()
}

onMounted(() => {
  fetchNotifications()
  fetchUnreadCount()
})
</script>

<style scoped>
.page-container {
  padding: 16px;
}

.unread-item {
  background-color: #f0f7ff;
}

.unread-title {
  font-weight: 600;
}

.notification-content {
  color: rgba(0, 0, 0, 0.65);
  margin-bottom: 4px;
}

.notification-time {
  color: rgba(0, 0, 0, 0.45);
  font-size: 12px;
}
</style>
