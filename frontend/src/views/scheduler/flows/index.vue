<template>
  <div class="page-container">
    <!-- Header -->
    <a-card :bordered="false">
      <a-row :gutter="16" align="middle">
        <a-col :span="12">
          <a-space>
            <a-input-search
              v-model:value="searchText"
              placeholder="搜索工作流名称"
              style="width: 250px"
              @search="handleSearch"
            />
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
          <a-button type="primary" @click="handleCreate">
            <template #icon><PlusOutlined /></template>
            新建工作流
          </a-button>
        </a-col>
      </a-row>
    </a-card>

    <!-- Flow List -->
    <a-card :bordered="false" style="margin-top: 16px">
      <a-table
        :columns="columns"
        :data-source="flows"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        :expand-column-width="48"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <a @click="handleViewDetail(record)">{{ record.name }}</a>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-badge :status="record.status === 'enabled' ? 'success' : 'default'" :text="record.status === 'enabled' ? '启用' : '禁用'" />
          </template>
          <template v-else-if="column.key === 'cron_expr'">
            <span v-if="record.cron_expr">{{ record.cron_expr }}</span>
            <span v-else class="text-gray">-</span>
          </template>
          <template v-else-if="column.key === 'nodes'">
            {{ record.dag_config?.nodes?.length || 0 }} 个节点
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-tooltip title="立即执行">
                <a-button type="link" size="small" @click="handleTrigger(record)">
                  <PlayCircleOutlined />
                </a-button>
              </a-tooltip>
              <a-tooltip title="执行记录">
                <a-button type="link" size="small" @click="handleViewInstances(record)">
                  <HistoryOutlined />
                </a-button>
              </a-tooltip>
              <a-tooltip title="编辑">
                <a-button type="link" size="small" @click="handleEdit(record)">
                  <EditOutlined />
                </a-button>
              </a-tooltip>
              <a-popconfirm title="确定删除此工作流？" @confirm="handleDelete(record)">
                <a-tooltip title="删除">
                  <a-button type="link" size="small" danger>
                    <DeleteOutlined />
                  </a-button>
                </a-tooltip>
              </a-popconfirm>
            </a-space>
          </template>
        </template>

        <!-- Expandable row to show internal tasks -->
        <template #expandedRowRender="{ record }">
          <div class="expanded-tasks">
            <a-table
              :columns="taskColumns"
              :data-source="getFlowTasks(record)"
              :pagination="false"
              size="small"
              row-key="nodeId"
            >
              <template #bodyCell="{ column, record: task }">
                <template v-if="column.key === 'order'">
                  <a-tag color="blue">{{ task.order }}</a-tag>
                </template>
                <template v-else-if="column.key === 'jobType'">
                  <a-tag :color="jobTypeColors[task.jobType] || 'default'">{{ jobTypeLabels[task.jobType] || task.jobType }}</a-tag>
                </template>
                <template v-else-if="column.key === 'dependencies'">
                  <span v-if="task.dependencies.length">
                    <a-tag v-for="dep in task.dependencies" :key="dep" size="small">{{ dep }}</a-tag>
                  </span>
                  <span v-else class="text-gray">无</span>
                </template>
                <template v-else-if="column.key === 'action'">
                  <a-space>
                    <a-tooltip title="单独执行此任务">
                      <a-button
                        type="primary"
                        size="small"
                        :loading="triggeringJobId === task.jobId"
                        @click="handleTriggerJob(task)"
                      >
                        <template #icon><PlayCircleOutlined /></template>
                        执行
                      </a-button>
                    </a-tooltip>
                    <a-button type="link" size="small" @click="handleViewJobLogs(task)">
                      日志
                    </a-button>
                  </a-space>
                </template>
              </template>
            </a-table>
          </div>
        </template>
      </a-table>
    </a-card>

    <!-- Create/Edit Modal -->
    <a-modal
      v-model:open="modalVisible"
      :title="editingFlow ? '编辑工作流' : '新建工作流'"
      width="800px"
      @ok="handleSubmit"
      :confirmLoading="submitting"
    >
      <a-form ref="formRef" :model="formState" :rules="formRules" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="工作流名称" name="name">
              <a-input v-model:value="formState.name" placeholder="请输入工作流名称" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="Cron表达式" name="cron_expr">
              <a-input v-model:value="formState.cron_expr" placeholder="如: 0 0 * * * (每天0点执行)" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="描述" name="description">
          <a-textarea v-model:value="formState.description" placeholder="请输入工作流描述" :rows="2" />
        </a-form-item>

        <a-divider>DAG配置</a-divider>

        <!-- Nodes -->
        <a-form-item label="任务节点">
          <div v-for="(node, index) in formState.dag_config.nodes" :key="index" class="node-item">
            <a-row :gutter="8" align="middle">
              <a-col :span="8">
                <a-input v-model:value="node.id" placeholder="节点ID" addon-before="ID" />
              </a-col>
              <a-col :span="12">
                <a-select v-model:value="node.job_id" placeholder="选择任务" style="width: 100%">
                  <a-select-option v-for="job in jobList" :key="job.id" :value="job.id">
                    {{ job.name }}
                  </a-select-option>
                </a-select>
              </a-col>
              <a-col :span="4">
                <a-button type="text" danger @click="removeNode(index)">
                  <DeleteOutlined />
                </a-button>
              </a-col>
            </a-row>
          </div>
          <a-button type="dashed" block @click="addNode">
            <PlusOutlined /> 添加节点
          </a-button>
        </a-form-item>

        <!-- Edges -->
        <a-form-item label="依赖关系 (从 -> 到)">
          <div v-for="(edge, index) in formState.dag_config.edges" :key="index" class="edge-item">
            <a-row :gutter="8" align="middle">
              <a-col :span="10">
                <a-select v-model:value="edge.source" placeholder="源节点" style="width: 100%">
                  <a-select-option v-for="node in formState.dag_config.nodes" :key="node.id" :value="node.id">
                    {{ node.id }}
                  </a-select-option>
                </a-select>
              </a-col>
              <a-col :span="2" style="text-align: center">
                <ArrowRightOutlined />
              </a-col>
              <a-col :span="10">
                <a-select v-model:value="edge.target" placeholder="目标节点" style="width: 100%">
                  <a-select-option v-for="node in formState.dag_config.nodes" :key="node.id" :value="node.id">
                    {{ node.id }}
                  </a-select-option>
                </a-select>
              </a-col>
              <a-col :span="2">
                <a-button type="text" danger @click="removeEdge(index)">
                  <DeleteOutlined />
                </a-button>
              </a-col>
            </a-row>
          </div>
          <a-button type="dashed" block @click="addEdge">
            <PlusOutlined /> 添加依赖
          </a-button>
        </a-form-item>

        <a-divider>高级配置</a-divider>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="错误处理策略">
              <a-select v-model:value="formState.dag_config.error_strategy">
                <a-select-option value="fail_fast">立即失败</a-select-option>
                <a-select-option value="continue">继续执行</a-select-option>
                <a-select-option value="skip_downstream">跳过下游</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="最大并行数">
              <a-input-number v-model:value="formState.dag_config.max_parallel" :min="1" :max="10" style="width: 100%" />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
    </a-modal>

    <!-- Instances Modal -->
    <a-modal
      v-model:open="instancesModalVisible"
      :title="`执行记录 - ${currentFlow?.name || ''}`"
      width="900px"
      :footer="null"
    >
      <a-table
        :columns="instanceColumns"
        :data-source="instances"
        :loading="instancesLoading"
        :pagination="instancesPagination"
        row-key="id"
        size="small"
        @change="handleInstancesTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="instanceStatusColors[record.status]">{{ instanceStatusLabels[record.status] }}</a-tag>
          </template>
          <template v-else-if="column.key === 'duration'">
            {{ record.duration ? `${record.duration}ms` : '-' }}
          </template>
          <template v-else-if="column.key === 'action'">
            <a-button type="link" size="small" @click="handleViewInstanceDetail(record)">详情</a-button>
          </template>
        </template>
      </a-table>
    </a-modal>

    <!-- Instance Detail Modal -->
    <a-modal
      v-model:open="instanceDetailVisible"
      title="执行详情"
      width="900px"
      :footer="null"
    >
      <template v-if="currentInstance">
        <a-descriptions :column="2" bordered size="small">
          <a-descriptions-item label="实例ID" :span="2">{{ currentInstance.instance_id }}</a-descriptions-item>
          <a-descriptions-item label="状态">
            <a-tag :color="instanceStatusColors[currentInstance.status]">{{ instanceStatusLabels[currentInstance.status] }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="触发类型">{{ currentInstance.trigger_type }}</a-descriptions-item>
          <a-descriptions-item label="开始时间">{{ currentInstance.start_time }}</a-descriptions-item>
          <a-descriptions-item label="结束时间">{{ currentInstance.end_time || '-' }}</a-descriptions-item>
          <a-descriptions-item label="执行耗时">{{ currentInstance.duration ? `${currentInstance.duration}ms` : '-' }}</a-descriptions-item>
          <a-descriptions-item label="触发人">{{ currentInstance.trigger_user || '-' }}</a-descriptions-item>
        </a-descriptions>

        <a-divider>任务执行日志</a-divider>
        <a-table
          :columns="jobLogColumns"
          :data-source="currentInstance.job_logs || []"
          row-key="trace_id"
          size="small"
          :pagination="false"
        >
          <template #bodyCell="{ column, record }">
            <template v-if="column.key === 'status'">
              <a-tag :color="statusColors[record.status]">{{ statusLabels[record.status] }}</a-tag>
            </template>
            <template v-else-if="column.key === 'duration'">
              {{ record.duration ? `${record.duration}ms` : '-' }}
            </template>
          </template>
        </a-table>
      </template>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  PlusOutlined, EditOutlined, DeleteOutlined, PlayCircleOutlined,
  HistoryOutlined, ArrowRightOutlined, FileTextOutlined
} from '@ant-design/icons-vue'
import request from '@/api/request'

// Data
const flows = ref([])
const loading = ref(false)
const searchText = ref('')
const filterStatus = ref(null)
const pagination = reactive({ current: 1, pageSize: 10, total: 0 })
const jobList = ref([])

// Modal
const modalVisible = ref(false)
const editingFlow = ref(null)
const submitting = ref(false)
const formRef = ref(null)
const formState = reactive({
  name: '',
  description: '',
  cron_expr: '',
  dag_config: {
    nodes: [],
    edges: [],
    error_strategy: 'fail_fast',
    max_parallel: 5,
  },
})

const formRules = {
  name: [{ required: true, message: '请输入工作流名称' }],
}

// Instances
const instancesModalVisible = ref(false)
const instances = ref([])
const instancesLoading = ref(false)
const instancesPagination = reactive({ current: 1, pageSize: 10, total: 0 })
const currentFlow = ref(null)
const instanceDetailVisible = ref(false)
const currentInstance = ref(null)

// Constants
const instanceStatusLabels = { pending: '等待中', running: '运行中', success: '成功', failed: '失败', partial: '部分成功', cancelled: '已取消' }
const instanceStatusColors = { pending: 'default', running: 'processing', success: 'success', failed: 'error', partial: 'warning', cancelled: 'default' }
const statusLabels = { pending: '等待中', running: '运行中', success: '成功', failed: '失败', timeout: '超时', cancelled: '已取消', skipped: '已跳过' }
const statusColors = { pending: 'default', running: 'processing', success: 'success', failed: 'error', timeout: 'warning', cancelled: 'default', skipped: 'default' }

// Columns
const columns = [
  { title: '工作流名称', dataIndex: 'name', key: 'name', width: 180, ellipsis: true },
  { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
  { title: 'Cron表达式', dataIndex: 'cron_expr', key: 'cron_expr', width: 140 },
  { title: '节点数', key: 'nodes', width: 80 },
  { title: '状态', dataIndex: 'status', key: 'status', width: 80 },
  { title: '更新时间', dataIndex: 'updated_at', key: 'updated_at', width: 170 },
  { title: '操作', key: 'action', width: 160, fixed: 'right' },
]

const instanceColumns = [
  { title: '实例ID', dataIndex: 'instance_id', key: 'instance_id', width: 150, ellipsis: true },
  { title: '状态', dataIndex: 'status', key: 'status', width: 80 },
  { title: '触发类型', dataIndex: 'trigger_type', key: 'trigger_type', width: 80 },
  { title: '开始时间', dataIndex: 'start_time', key: 'start_time', width: 180 },
  { title: '耗时', dataIndex: 'duration', key: 'duration', width: 100 },
  { title: '操作', key: 'action', width: 80 },
]

const jobLogColumns = [
  { title: '任务名称', dataIndex: 'job_name', key: 'job_name' },
  { title: '状态', dataIndex: 'status', key: 'status', width: 80 },
  { title: '开始时间', dataIndex: 'start_time', key: 'start_time', width: 180 },
  { title: '耗时', dataIndex: 'duration', key: 'duration', width: 100 },
  { title: '错误信息', dataIndex: 'error_msg', key: 'error_msg', ellipsis: true },
]

// Task columns for expanded row
const taskColumns = [
  { title: '执行顺序', key: 'order', width: 80 },
  { title: '节点ID', dataIndex: 'nodeId', key: 'nodeId', width: 100 },
  { title: '任务名称', dataIndex: 'jobName', key: 'jobName', width: 180 },
  { title: '任务类型', key: 'jobType', width: 100 },
  { title: '依赖节点', key: 'dependencies' },
  { title: '操作', key: 'action', width: 150 },
]

// Job type labels and colors
const jobTypeLabels = {
  shell: 'Shell脚本',
  python: 'Python脚本',
  http: 'HTTP请求',
  sql: 'SQL查询',
}
const jobTypeColors = {
  shell: 'orange',
  python: 'green',
  http: 'blue',
  sql: 'purple',
}

// Triggering job state
const triggeringJobId = ref(null)

// Methods
const fetchFlows = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      search: searchText.value || undefined,
      status: filterStatus.value || undefined,
    }
    const res = await request.get('/job-flows/', { params })
    flows.value = res.results
    pagination.total = res.total
  } finally {
    loading.value = false
  }
}

const fetchJobs = async () => {
  try {
    const res = await request.get('/jobs/', { params: { page_size: 100 } })
    jobList.value = res.results
  } catch (e) {}
}

const handleSearch = () => {
  pagination.current = 1
  fetchFlows()
}

const handleTableChange = (pag) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchFlows()
}

const handleCreate = () => {
  editingFlow.value = null
  Object.assign(formState, {
    name: '', description: '', cron_expr: '',
    dag_config: { nodes: [], edges: [], error_strategy: 'fail_fast', max_parallel: 5 },
  })
  modalVisible.value = true
}

const handleEdit = (record) => {
  editingFlow.value = record
  Object.assign(formState, {
    name: record.name,
    description: record.description,
    cron_expr: record.cron_expr || '',
    dag_config: record.dag_config || { nodes: [], edges: [], error_strategy: 'fail_fast', max_parallel: 5 },
  })
  modalVisible.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true
    const data = { ...formState }
    if (editingFlow.value) {
      await request.put(`/job-flows/${editingFlow.value.id}/`, data)
      message.success('工作流更新成功')
    } else {
      await request.post('/job-flows/', data)
      message.success('工作流创建成功')
    }
    modalVisible.value = false
    fetchFlows()
  } catch (e) {
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (record) => {
  await request.delete(`/job-flows/${record.id}/`)
  message.success('工作流已删除')
  fetchFlows()
}

const handleTrigger = async (record) => {
  await request.post(`/job-flows/${record.id}/trigger/`)
  message.success('工作流已触发执行')
}

const handleViewDetail = (record) => {
  handleEdit(record)
}

const addNode = () => {
  const id = `node_${formState.dag_config.nodes.length + 1}`
  formState.dag_config.nodes.push({ id, job_id: null })
}

const removeNode = (index) => {
  formState.dag_config.nodes.splice(index, 1)
}

const addEdge = () => {
  formState.dag_config.edges.push({ source: '', target: '' })
}

const removeEdge = (index) => {
  formState.dag_config.edges.splice(index, 1)
}

const handleViewInstances = async (record) => {
  currentFlow.value = record
  instancesModalVisible.value = true
  instancesPagination.current = 1
  await fetchInstances(record.id)
}

const fetchInstances = async (flowId) => {
  instancesLoading.value = true
  try {
    const res = await request.get(`/job-flows/${flowId}/instances/`, {
      params: { page: instancesPagination.current, page_size: instancesPagination.pageSize }
    })
    instances.value = res.results
    instancesPagination.total = res.total
  } finally {
    instancesLoading.value = false
  }
}

const handleInstancesTableChange = (pag) => {
  instancesPagination.current = pag.current
  fetchInstances(currentFlow.value.id)
}

const handleViewInstanceDetail = async (record) => {
  const res = await request.get(`/job-flows/${currentFlow.value.id}/instances/${record.instance_id}/`)
  currentInstance.value = res
  instanceDetailVisible.value = true
}

// Get flow tasks from dag_config with job details
const getFlowTasks = (flow) => {
  const nodes = flow.dag_config?.nodes || []
  const edges = flow.dag_config?.edges || []

  // Build job map for quick lookup
  const jobMap = {}
  jobList.value.forEach(job => {
    jobMap[job.id] = job
  })

  // Calculate execution order using topological sort
  const inDegree = {}
  const adjList = {}
  nodes.forEach(node => {
    inDegree[node.id] = 0
    adjList[node.id] = []
  })
  edges.forEach(edge => {
    if (inDegree[edge.target] !== undefined) {
      inDegree[edge.target]++
    }
    if (adjList[edge.source]) {
      adjList[edge.source].push(edge.target)
    }
  })

  // Topological sort to get execution order
  const order = {}
  const queue = []
  let orderNum = 1
  Object.keys(inDegree).forEach(nodeId => {
    if (inDegree[nodeId] === 0) {
      queue.push(nodeId)
    }
  })
  while (queue.length > 0) {
    const nodeId = queue.shift()
    order[nodeId] = orderNum++
    (adjList[nodeId] || []).forEach(target => {
      inDegree[target]--
      if (inDegree[target] === 0) {
        queue.push(target)
      }
    })
  }

  // Get dependencies for each node
  const getDependencies = (nodeId) => {
    return edges.filter(e => e.target === nodeId).map(e => e.source)
  }

  return nodes.map(node => {
    const job = jobMap[node.job_id] || {}
    return {
      nodeId: node.id,
      jobId: node.job_id,
      jobName: job.name || `未知任务 (${node.job_id})`,
      jobType: job.job_type || 'unknown',
      order: order[node.id] || '-',
      dependencies: getDependencies(node.id),
    }
  }).sort((a, b) => (a.order || 999) - (b.order || 999))
}

// Trigger individual job
const handleTriggerJob = async (task) => {
  if (!task.jobId) {
    message.error('任务ID不存在')
    return
  }
  try {
    triggeringJobId.value = task.jobId
    await request.post(`/jobs/${task.jobId}/trigger/`)
    message.success(`任务 "${task.jobName}" 已触发执行`)
  } catch (e) {
    message.error('触发任务失败')
  } finally {
    triggeringJobId.value = null
  }
}

// View job execution logs
const handleViewJobLogs = async (task) => {
  // Navigate to jobs page with filter or open log modal
  message.info(`查看任务 "${task.jobName}" 的执行日志`)
  // TODO: Can implement a job log modal or navigate to job detail page
}

onMounted(() => {
  fetchFlows()
  fetchJobs()
})
</script>

<style scoped>
.page-container {
  padding: 16px;
}
.text-gray {
  color: #999;
}
.node-item, .edge-item {
  margin-bottom: 8px;
}
.expanded-tasks {
  padding: 8px 16px;
  background: #fafafa;
  border-radius: 4px;
}
.expanded-tasks :deep(.ant-table) {
  background: transparent;
}
.expanded-tasks :deep(.ant-table-thead > tr > th) {
  background: #f0f0f0;
}
</style>
