<template>
  <div class="page-container">
    <a-row :gutter="16">
      <a-col :span="6">
        <a-card class="stat-card">
          <div class="stat-value">128</div>
          <div class="stat-label">定时任务</div>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stat-card">
          <div class="stat-value" style="color: #52c41a">95.2%</div>
          <div class="stat-label">任务成功率</div>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stat-card">
          <div class="stat-value" style="color: #faad14">12</div>
          <div class="stat-label">待办审批</div>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card class="stat-card">
          <div class="stat-value" style="color: #722ed1">56</div>
          <div class="stat-label">今日操作</div>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16" class="mt-16">
      <a-col :span="16">
        <a-card title="任务执行趋势">
          <div style="height: 300px; display: flex; align-items: center; justify-content: center; color: #999;">
            图表区域 - M2 实现
          </div>
        </a-card>
      </a-col>
      <a-col :span="8">
        <a-card title="待办事项">
          <a-list :data-source="todoList" size="small">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta :description="item.time">
                  <template #title>{{ item.title }}</template>
                </a-list-item-meta>
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>
    </a-row>

    <a-row :gutter="16" class="mt-16">
      <a-col :span="24">
        <a-card title="最近操作日志">
          <a-table :columns="logColumns" :data-source="[]" size="small">
            <template #emptyText>
              <a-empty description="暂无数据 - M6 实现" />
            </template>
          </a-table>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const todoList = ref([
  { title: '配置变更审批 - 费率调整', time: '10分钟前' },
  { title: '用户权限申请 - 张三', time: '30分钟前' },
  { title: '报表订阅 - 日报推送失败', time: '1小时前' },
])

const logColumns = [
  { title: '操作人', dataIndex: 'user', key: 'user' },
  { title: '操作类型', dataIndex: 'action', key: 'action' },
  { title: '操作内容', dataIndex: 'content', key: 'content' },
  { title: '操作时间', dataIndex: 'time', key: 'time' },
]
</script>
