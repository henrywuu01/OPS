<template>
  <div class="page-container">
    <!-- Header -->
    <a-card :bordered="false">
      <a-row :gutter="16" align="middle">
        <a-col :span="16">
          <a-space>
            <a-input-search
              v-model:value="searchText"
              placeholder="搜索数据源名称"
              style="width: 200px"
              @search="handleSearch"
            />
            <a-select
              v-model:value="filterType"
              placeholder="类型"
              style="width: 120px"
              allowClear
              @change="handleSearch"
            >
              <a-select-option value="mysql">MySQL</a-select-option>
              <a-select-option value="postgresql">PostgreSQL</a-select-option>
              <a-select-option value="clickhouse">ClickHouse</a-select-option>
              <a-select-option value="elasticsearch">Elasticsearch</a-select-option>
              <a-select-option value="mongodb">MongoDB</a-select-option>
            </a-select>
            <a-select
              v-model:value="filterStatus"
              placeholder="状态"
              style="width: 100px"
              allowClear
              @change="handleSearch"
            >
              <a-select-option value="active">正常</a-select-option>
              <a-select-option value="inactive">停用</a-select-option>
              <a-select-option value="error">异常</a-select-option>
            </a-select>
          </a-space>
        </a-col>
        <a-col :span="8" style="text-align: right">
          <a-button type="primary" @click="handleCreate">
            <template #icon><PlusOutlined /></template>
            新建数据源
          </a-button>
        </a-col>
      </a-row>
    </a-card>

    <!-- Data List -->
    <a-card :bordered="false" style="margin-top: 16px">
      <a-table
        :columns="columns"
        :data-source="datasources"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'type'">
            <a-tag :color="typeColors[record.type]">{{ typeLabels[record.type] }}</a-tag>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-badge :status="statusBadge[record.status]" :text="statusLabels[record.status]" />
          </template>
          <template v-else-if="column.key === 'connection'">
            <span>{{ record.host }}:{{ record.port }}</span>
            <span v-if="record.database_name" class="text-gray"> / {{ record.database_name }}</span>
          </template>
          <template v-else-if="column.key === 'last_check_time'">
            {{ record.last_check_time ? formatDate(record.last_check_time) : '-' }}
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-tooltip title="测试连接">
                <a-button
                  type="link"
                  size="small"
                  :loading="testingId === record.id"
                  @click="handleTest(record)"
                >
                  <ApiOutlined />
                </a-button>
              </a-tooltip>
              <a-tooltip title="编辑">
                <a-button type="link" size="small" @click="handleEdit(record)">
                  <EditOutlined />
                </a-button>
              </a-tooltip>
              <a-popconfirm title="确定删除该数据源？" @confirm="handleDelete(record)">
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
      :title="editingRecord ? '编辑数据源' : '新建数据源'"
      width="600px"
      @ok="handleSubmit"
      :confirmLoading="submitting"
    >
      <a-form ref="formRef" :model="formState" :rules="formRules" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-item label="数据源名称" name="name">
          <a-input v-model:value="formState.name" placeholder="请输入数据源名称" />
        </a-form-item>
        <a-form-item label="类型" name="type">
          <a-select v-model:value="formState.type" placeholder="选择数据源类型">
            <a-select-option value="mysql">MySQL</a-select-option>
            <a-select-option value="postgresql">PostgreSQL</a-select-option>
            <a-select-option value="clickhouse">ClickHouse</a-select-option>
            <a-select-option value="elasticsearch">Elasticsearch</a-select-option>
            <a-select-option value="mongodb">MongoDB</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="主机地址" name="host">
          <a-input v-model:value="formState.host" placeholder="如: localhost 或 192.168.1.100" />
        </a-form-item>
        <a-form-item label="端口" name="port">
          <a-input-number v-model:value="formState.port" :min="1" :max="65535" style="width: 100%" />
        </a-form-item>
        <a-form-item label="数据库名" name="database_name">
          <a-input v-model:value="formState.database_name" placeholder="请输入数据库名" />
        </a-form-item>
        <a-form-item label="用户名" name="username">
          <a-input v-model:value="formState.username" placeholder="请输入用户名" />
        </a-form-item>
        <a-form-item label="密码" name="password">
          <a-input-password v-model:value="formState.password" :placeholder="editingRecord ? '留空则不修改' : '请输入密码'" />
        </a-form-item>
        <a-form-item label="状态" name="status">
          <a-select v-model:value="formState.status">
            <a-select-option value="active">正常</a-select-option>
            <a-select-option value="inactive">停用</a-select-option>
          </a-select>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined, EditOutlined, DeleteOutlined, ApiOutlined } from '@ant-design/icons-vue'
import {
  getDataSources,
  createDataSource,
  updateDataSource,
  deleteDataSource,
  testDataSource
} from '@/api/report'

// Data
const datasources = ref([])
const loading = ref(false)
const searchText = ref('')
const filterType = ref(null)
const filterStatus = ref(null)
const pagination = reactive({ current: 1, pageSize: 10, total: 0 })
const testingId = ref(null)

// Modal
const modalVisible = ref(false)
const editingRecord = ref(null)
const submitting = ref(false)
const formRef = ref(null)
const formState = reactive({
  name: '',
  type: 'mysql',
  host: '',
  port: 3306,
  database_name: '',
  username: '',
  password: '',
  status: 'active'
})

const formRules = {
  name: [{ required: true, message: '请输入数据源名称' }],
  type: [{ required: true, message: '请选择类型' }],
  host: [{ required: true, message: '请输入主机地址' }],
  port: [{ required: true, message: '请输入端口' }]
}

// Constants
const typeLabels = {
  mysql: 'MySQL',
  postgresql: 'PostgreSQL',
  clickhouse: 'ClickHouse',
  elasticsearch: 'Elasticsearch',
  mongodb: 'MongoDB'
}

const typeColors = {
  mysql: 'blue',
  postgresql: 'cyan',
  clickhouse: 'orange',
  elasticsearch: 'green',
  mongodb: 'purple'
}

const statusLabels = {
  active: '正常',
  inactive: '停用',
  error: '异常'
}

const statusBadge = {
  active: 'success',
  inactive: 'default',
  error: 'error'
}

// Columns
const columns = [
  { title: '名称', dataIndex: 'name', key: 'name', width: 180 },
  { title: '类型', key: 'type', width: 120 },
  { title: '连接信息', key: 'connection' },
  { title: '状态', key: 'status', width: 100 },
  { title: '最后检查', key: 'last_check_time', width: 170 },
  { title: '操作', key: 'action', width: 120, fixed: 'right' }
]

// Methods
const fetchDataSources = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      search: searchText.value || undefined,
      type: filterType.value || undefined,
      status: filterStatus.value || undefined
    }
    const res = await getDataSources(params)
    datasources.value = res.results
    pagination.total = res.total
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.current = 1
  fetchDataSources()
}

const handleTableChange = (pag) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchDataSources()
}

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

const handleCreate = () => {
  editingRecord.value = null
  Object.assign(formState, {
    name: '',
    type: 'mysql',
    host: '',
    port: 3306,
    database_name: '',
    username: '',
    password: '',
    status: 'active'
  })
  modalVisible.value = true
}

const handleEdit = (record) => {
  editingRecord.value = record
  Object.assign(formState, {
    name: record.name,
    type: record.type,
    host: record.host,
    port: record.port,
    database_name: record.database_name || '',
    username: record.username || '',
    password: '',
    status: record.status
  })
  modalVisible.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true

    const data = { ...formState }
    if (editingRecord.value && !data.password) {
      delete data.password
    }

    if (editingRecord.value) {
      await updateDataSource(editingRecord.value.id, data)
      message.success('更新成功')
    } else {
      await createDataSource(data)
      message.success('创建成功')
    }
    modalVisible.value = false
    fetchDataSources()
  } catch (e) {
    if (!e.errorFields) {
      console.error(e)
    }
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (record) => {
  try {
    await deleteDataSource(record.id)
    message.success('删除成功')
    fetchDataSources()
  } catch (e) {
    console.error(e)
  }
}

const handleTest = async (record) => {
  testingId.value = record.id
  try {
    const res = await testDataSource(record.id)
    if (res.success) {
      message.success('连接成功')
    } else {
      message.error(res.message || '连接失败')
    }
    fetchDataSources()
  } catch (e) {
    message.error('测试失败')
  } finally {
    testingId.value = null
  }
}

onMounted(() => {
  fetchDataSources()
})
</script>

<style scoped>
.page-container {
  padding: 16px;
}
.text-gray {
  color: #999;
}
</style>
