<template>
  <div class="page-container">
    <!-- Header -->
    <a-card :bordered="false">
      <a-row :gutter="16" align="middle">
        <a-col :span="12">
          <a-space>
            <a-input-search
              v-model:value="searchText"
              placeholder="搜索任务名称"
              style="width: 250px"
              @search="handleSearch"
            />
            <a-select
              v-model:value="filterType"
              placeholder="任务类型"
              style="width: 120px"
              allowClear
              @change="handleSearch"
            >
              <a-select-option value="http">HTTP请求</a-select-option>
              <a-select-option value="shell">Shell脚本</a-select-option>
              <a-select-option value="sql">SQL脚本</a-select-option>
              <a-select-option value="python">Python脚本</a-select-option>
            </a-select>
            <a-select
              v-model:value="filterStatus"
              placeholder="状态"
              style="width: 100px"
              allowClear
              @change="handleSearch"
            >
              <a-select-option value="enabled">启用</a-select-option>
              <a-select-option value="disabled">禁用</a-select-option>
            </a-select>
          </a-space>
        </a-col>
        <a-col :span="12" style="text-align: right">
          <a-space>
            <a-button @click="handleSyncSchedules">
              <template #icon><SyncOutlined /></template>
              同步调度
            </a-button>
            <a-button type="primary" @click="handleCreate">
              <template #icon><PlusOutlined /></template>
              新建任务
            </a-button>
          </a-space>
        </a-col>
      </a-row>
    </a-card>

    <!-- Statistics -->
    <a-row :gutter="16" style="margin-top: 16px">
      <a-col :span="6">
        <a-card :bordered="false">
          <a-statistic title="任务总数" :value="stats.total_jobs" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :bordered="false">
          <a-statistic title="启用任务" :value="stats.enabled_jobs" :value-style="{ color: '#52c41a' }" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :bordered="false">
          <a-statistic title="今日执行" :value="stats.total_executions" />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card :bordered="false">
          <a-statistic
            title="成功率"
            :value="stats.success_rate"
            suffix="%"
            :value-style="{ color: stats.success_rate >= 90 ? '#52c41a' : '#faad14' }"
          />
        </a-card>
      </a-col>
    </a-row>

    <!-- Job List -->
    <a-card :bordered="false" style="margin-top: 16px">
      <a-table
        :columns="columns"
        :data-source="jobs"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <a @click="handleViewDetail(record)">{{ record.name }}</a>
          </template>
          <template v-else-if="column.key === 'job_type'">
            <a-tag :color="typeColors[record.job_type]">{{ typeLabels[record.job_type] }}</a-tag>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-badge :status="record.status === 'enabled' ? 'success' : 'default'" :text="record.status === 'enabled' ? '启用' : '禁用'" />
          </template>
          <template v-else-if="column.key === 'cron_expr'">
            <span v-if="record.cron_expr">{{ record.cron_expr }}</span>
            <span v-else class="text-gray">-</span>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-tooltip title="立即执行">
                <a-button type="link" size="small" @click="handleTrigger(record)">
                  <PlayCircleOutlined />
                </a-button>
              </a-tooltip>
              <a-tooltip :title="record.status === 'enabled' ? '暂停' : '恢复'">
                <a-button type="link" size="small" @click="handleToggleStatus(record)">
                  <PauseCircleOutlined v-if="record.status === 'enabled'" />
                  <PlayCircleOutlined v-else />
                </a-button>
              </a-tooltip>
              <a-tooltip title="查看日志">
                <a-button type="link" size="small" @click="handleViewLogs(record)">
                  <FileTextOutlined />
                </a-button>
              </a-tooltip>
              <a-tooltip title="编辑">
                <a-button type="link" size="small" @click="handleEdit(record)">
                  <EditOutlined />
                </a-button>
              </a-tooltip>
              <a-popconfirm title="确定删除此任务？" @confirm="handleDelete(record)">
                <a-tooltip title="删除">
                  <a-button type="link" size="small" danger>
                    <DeleteOutlined />
                  </a-button>
                </a-tooltip>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- Create/Edit Modal -->
    <a-modal
      v-model:open="modalVisible"
      :title="editingJob ? '编辑任务' : '新建任务'"
      width="700px"
      @ok="handleSubmit"
      :confirmLoading="submitting"
    >
      <a-form ref="formRef" :model="formState" :rules="formRules" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="任务名称" name="name">
              <a-input v-model:value="formState.name" placeholder="请输入任务名称" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="任务类型" name="job_type">
              <a-select v-model:value="formState.job_type" placeholder="请选择任务类型">
                <a-select-option value="http">HTTP请求</a-select-option>
                <a-select-option value="shell">Shell脚本</a-select-option>
                <a-select-option value="sql">SQL脚本</a-select-option>
                <a-select-option value="python">Python脚本</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="任务描述" name="description">
          <a-textarea v-model:value="formState.description" placeholder="请输入任务描述" :rows="2" />
        </a-form-item>
        <a-form-item label="Cron表达式" name="cron_expr">
          <a-input v-model:value="formState.cron_expr" placeholder="如: 0 0 * * * (每天0点执行)" />
          <template #extra>
            <span class="text-gray">格式: 分 时 日 月 周 (留空则不定时执行)</span>
          </template>
        </a-form-item>

        <!-- HTTP Config -->
        <template v-if="formState.job_type === 'http'">
          <a-divider>HTTP配置</a-divider>
          <a-row :gutter="16">
            <a-col :span="16">
              <a-form-item label="请求URL" name="config.url">
                <a-input v-model:value="formState.config.url" placeholder="https://api.example.com/path" />
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item label="请求方法">
                <a-select v-model:value="formState.config.method">
                  <a-select-option value="GET">GET</a-select-option>
                  <a-select-option value="POST">POST</a-select-option>
                  <a-select-option value="PUT">PUT</a-select-option>
                  <a-select-option value="DELETE">DELETE</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>
        </template>

        <!-- Shell Config -->
        <template v-if="formState.job_type === 'shell'">
          <a-divider>Shell配置</a-divider>
          <a-form-item label="脚本内容" name="config.script">
            <a-textarea v-model:value="formState.config.script" placeholder="#!/bin/bash&#10;echo 'Hello World'" :rows="6" />
          </a-form-item>
          <a-form-item label="工作目录">
            <a-input v-model:value="formState.config.working_dir" placeholder="/tmp" />
          </a-form-item>
        </template>

        <!-- SQL Config -->
        <template v-if="formState.job_type === 'sql'">
          <a-divider>SQL配置</a-divider>
          <a-form-item label="SQL语句" name="config.sql">
            <a-textarea v-model:value="formState.config.sql" placeholder="SELECT * FROM users WHERE id = :id" :rows="6" />
          </a-form-item>
        </template>

        <!-- Python Config -->
        <template v-if="formState.job_type === 'python'">
          <a-divider>Python配置</a-divider>
          <a-form-item label="Python脚本" name="config.script">
            <a-textarea v-model:value="formState.config.script" placeholder="# 使用 params 获取输入参数&#10;# 使用 result 设置返回值&#10;result = params.get('value', 0) * 2" :rows="6" />
          </a-form-item>
        </template>

        <a-divider>执行配置</a-divider>
        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="超时时间(秒)">
              <a-input-number v-model:value="formState.timeout" :min="1" :max="3600" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="重试次数">
              <a-input-number v-model:value="formState.retry_count" :min="0" :max="10" style="width: 100%" />
            </a-form-item>
          </a-col>
          <a-col :span="8">
            <a-form-item label="重试间隔(秒)">
              <a-input-number v-model:value="formState.retry_interval" :min="1" :max="600" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>

        <a-divider>告警配置</a-divider>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item>
              <a-checkbox v-model:checked="formState.alert_on_failure">失败时告警</a-checkbox>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item>
              <a-checkbox v-model:checked="formState.alert_on_timeout">超时时告警</a-checkbox>
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>

    <!-- Logs Modal -->
    <a-modal
      v-model:open="logsModalVisible"
      :title="`执行日志 - ${currentJob?.name || ''}`"
      width="900px"
      :footer="null"
    >
      <a-table
        :columns="logColumns"
        :data-source="logs"
        :loading="logsLoading"
        :pagination="logsPagination"
        row-key="id"
        size="small"
        @change="handleLogsTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="statusColors[record.status]">{{ statusLabels[record.status] }}</a-tag>
          </template>
          <template v-else-if="column.key === 'duration'">
            {{ record.duration ? `${record.duration}ms` : '-' }}
          </template>
          <template v-else-if="column.key === 'action'">
            <a-button type="link" size="small" @click="handleViewLogDetail(record)">详情</a-button>
          </template>
        </template>
      </a-table>
    </a-modal>

    <!-- Log Detail Modal -->
    <a-modal
      v-model:open="logDetailVisible"
      title="执行详情"
      width="700px"
      :footer="null"
    >
      <a-descriptions :column="2" bordered size="small" v-if="currentLog">
        <a-descriptions-item label="追踪ID" :span="2">{{ currentLog.trace_id }}</a-descriptions-item>
        <a-descriptions-item label="状态">
          <a-tag :color="statusColors[currentLog.status]">{{ statusLabels[currentLog.status] }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="触发类型">{{ currentLog.trigger_type }}</a-descriptions-item>
        <a-descriptions-item label="开始时间">{{ currentLog.start_time }}</a-descriptions-item>
        <a-descriptions-item label="结束时间">{{ currentLog.end_time || '-' }}</a-descriptions-item>
        <a-descriptions-item label="执行耗时">{{ currentLog.duration ? `${currentLog.duration}ms` : '-' }}</a-descriptions-item>
        <a-descriptions-item label="触发人">{{ currentLog.trigger_user_name || '-' }}</a-descriptions-item>
        <a-descriptions-item label="执行结果" :span="2">
          <pre class="log-content">{{ currentLog.result || '-' }}</pre>
        </a-descriptions-item>
        <a-descriptions-item label="错误信息" :span="2" v-if="currentLog.error_msg">
          <pre class="log-content error">{{ currentLog.error_msg }}</pre>
        </a-descriptions-item>
      </a-descriptions>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  PlusOutlined, SyncOutlined, EditOutlined, DeleteOutlined,
  PlayCircleOutlined, PauseCircleOutlined, FileTextOutlined
} from '@ant-design/icons-vue'
import request from '@/api/request'

// Data
const jobs = ref([])
const loading = ref(false)
const searchText = ref('')
const filterType = ref(null)
const filterStatus = ref(null)
const pagination = reactive({ current: 1, pageSize: 10, total: 0 })
const stats = ref({ total_jobs: 0, enabled_jobs: 0, total_executions: 0, success_rate: 0 })

// Modal
const modalVisible = ref(false)
const editingJob = ref(null)
const submitting = ref(false)
const formRef = ref(null)
const formState = reactive({
  name: '',
  description: '',
  job_type: 'http',
  cron_expr: '',
  config: { url: '', method: 'GET', script: '', sql: '' },
  timeout: 60,
  retry_count: 3,
  retry_interval: 60,
  alert_on_failure: true,
  alert_on_timeout: true,
  alert_channels: [],
})

const formRules = {
  name: [{ required: true, message: '请输入任务名称' }],
  job_type: [{ required: true, message: '请选择任务类型' }],
}

// Logs Modal
const logsModalVisible = ref(false)
const logs = ref([])
const logsLoading = ref(false)
const logsPagination = reactive({ current: 1, pageSize: 10, total: 0 })
const currentJob = ref(null)
const logDetailVisible = ref(false)
const currentLog = ref(null)

// Constants
const typeLabels = { http: 'HTTP请求', shell: 'Shell脚本', sql: 'SQL脚本', python: 'Python脚本' }
const typeColors = { http: 'blue', shell: 'green', sql: 'orange', python: 'purple' }
const statusLabels = { pending: '等待中', running: '运行中', success: '成功', failed: '失败', timeout: '超时', cancelled: '已取消', skipped: '已跳过' }
const statusColors = { pending: 'default', running: 'processing', success: 'success', failed: 'error', timeout: 'warning', cancelled: 'default', skipped: 'default' }

// Columns
const columns = [
  { title: '任务名称', dataIndex: 'name', key: 'name', width: 200, ellipsis: true },
  { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
  { title: '类型', dataIndex: 'job_type', key: 'job_type', width: 100 },
  { title: 'Cron表达式', dataIndex: 'cron_expr', key: 'cron_expr', width: 140 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 80 },
  { title: '更新时间', dataIndex: 'updated_at', key: 'updated_at', width: 170 },
  { title: '操作', key: 'action', width: 180, fixed: 'right' },
]

const logColumns = [
  { title: '追踪ID', dataIndex: 'trace_id', key: 'trace_id', width: 150, ellipsis: true },
  { title: '状态', dataIndex: 'status', key: 'status', width: 80 },
  { title: '触发类型', dataIndex: 'trigger_type', key: 'trigger_type', width: 80 },
  { title: '开始时间', dataIndex: 'start_time', key: 'start_time', width: 180 },
  { title: '耗时', dataIndex: 'duration', key: 'duration', width: 100 },
  { title: '操作', key: 'action', width: 80 },
]

// Methods
const fetchJobs = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      search: searchText.value || undefined,
      job_type: filterType.value || undefined,
      status: filterStatus.value || undefined,
    }
    const res = await request.get('/jobs/', { params })
    jobs.value = res.results
    pagination.total = res.total
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const res = await request.get('/jobs/statistics/')
    stats.value = res
  } catch (e) {}
}

const handleSearch = () => {
  pagination.current = 1
  fetchJobs()
}

const handleTableChange = (pag) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchJobs()
}

const handleCreate = () => {
  editingJob.value = null
  Object.assign(formState, {
    name: '', description: '', job_type: 'http', cron_expr: '',
    config: { url: '', method: 'GET', script: '', sql: '' },
    timeout: 60, retry_count: 3, retry_interval: 60,
    alert_on_failure: true, alert_on_timeout: true, alert_channels: [],
  })
  modalVisible.value = true
}

const handleEdit = (record) => {
  editingJob.value = record
  Object.assign(formState, {
    name: record.name,
    description: record.description,
    job_type: record.job_type,
    cron_expr: record.cron_expr || '',
    config: record.config || {},
    timeout: record.timeout,
    retry_count: record.retry_count,
    retry_interval: record.retry_interval,
    alert_on_failure: record.alert_on_failure,
    alert_on_timeout: record.alert_on_timeout,
    alert_channels: record.alert_channels || [],
  })
  modalVisible.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true
    const data = { ...formState }
    if (editingJob.value) {
      await request.put(`/jobs/${editingJob.value.id}/`, data)
      message.success('任务更新成功')
    } else {
      await request.post('/jobs/', data)
      message.success('任务创建成功')
    }
    modalVisible.value = false
    fetchJobs()
  } catch (e) {
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (record) => {
  await request.delete(`/jobs/${record.id}/`)
  message.success('任务已删除')
  fetchJobs()
}

const handleTrigger = async (record) => {
  await request.post(`/jobs/${record.id}/trigger/`)
  message.success('任务已触发执行')
}

const handleToggleStatus = async (record) => {
  if (record.status === 'enabled') {
    await request.post(`/jobs/${record.id}/pause/`)
    message.success('任务已暂停')
  } else {
    await request.post(`/jobs/${record.id}/resume/`)
    message.success('任务已恢复')
  }
  fetchJobs()
}

const handleViewDetail = (record) => {
  handleEdit(record)
}

const handleViewLogs = async (record) => {
  currentJob.value = record
  logsModalVisible.value = true
  logsPagination.current = 1
  await fetchLogs(record.id)
}

const fetchLogs = async (jobId) => {
  logsLoading.value = true
  try {
    const res = await request.get(`/jobs/${jobId}/logs/`, {
      params: { page: logsPagination.current, page_size: logsPagination.pageSize }
    })
    logs.value = res.results
    logsPagination.total = res.total
  } finally {
    logsLoading.value = false
  }
}

const handleLogsTableChange = (pag) => {
  logsPagination.current = pag.current
  fetchLogs(currentJob.value.id)
}

const handleViewLogDetail = async (record) => {
  const res = await request.get(`/jobs/${currentJob.value.id}/logs/${record.id}/`)
  currentLog.value = res
  logDetailVisible.value = true
}

const handleSyncSchedules = async () => {
  await request.post('/jobs/sync-schedules/')
  message.success('调度任务同步完成')
}

onMounted(() => {
  fetchJobs()
  fetchStats()
})
</script>

<style scoped>
.page-container {
  padding: 16px;
}
.text-gray {
  color: #999;
}
.log-content {
  background: #f5f5f5;
  padding: 8px;
  border-radius: 4px;
  max-height: 200px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
}
.log-content.error {
  background: #fff2f0;
  color: #ff4d4f;
}
</style>
