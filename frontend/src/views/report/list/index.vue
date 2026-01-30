<template>
  <div class="page-container">
    <!-- Header -->
    <a-card :bordered="false">
      <a-row :gutter="16" align="middle">
        <a-col :span="16">
          <a-space>
            <a-input-search
              v-model:value="searchText"
              placeholder="搜索报表名称"
              style="width: 200px"
              @search="handleSearch"
            />
            <a-select
              v-model:value="filterDisplayType"
              placeholder="图表类型"
              style="width: 120px"
              allowClear
              @change="handleSearch"
            >
              <a-select-option value="table">表格</a-select-option>
              <a-select-option value="line">折线图</a-select-option>
              <a-select-option value="bar">柱状图</a-select-option>
              <a-select-option value="pie">饼图</a-select-option>
              <a-select-option value="card">卡片指标</a-select-option>
            </a-select>
            <a-select
              v-model:value="filterStatus"
              placeholder="状态"
              style="width: 100px"
              allowClear
              @change="handleSearch"
            >
              <a-select-option value="draft">草稿</a-select-option>
              <a-select-option value="published">已发布</a-select-option>
              <a-select-option value="archived">已归档</a-select-option>
            </a-select>
          </a-space>
        </a-col>
        <a-col :span="8" style="text-align: right">
          <a-button type="primary" @click="handleCreate">
            <template #icon><PlusOutlined /></template>
            新建报表
          </a-button>
        </a-col>
      </a-row>
    </a-card>

    <!-- Report List -->
    <a-card :bordered="false" style="margin-top: 16px">
      <a-table
        :columns="columns"
        :data-source="reports"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <a @click="handleView(record)">{{ record.name }}</a>
          </template>
          <template v-else-if="column.key === 'display_type'">
            <a-tag :color="displayTypeColors[record.display_type]">
              {{ displayTypeLabels[record.display_type] }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-badge :status="statusBadge[record.status]" :text="statusLabels[record.status]" />
          </template>
          <template v-else-if="column.key === 'is_favorited'">
            <a-button
              type="text"
              size="small"
              :style="{ color: record.is_favorited ? '#faad14' : '#999' }"
              @click="handleToggleFavorite(record)"
            >
              <StarFilled v-if="record.is_favorited" />
              <StarOutlined v-else />
            </a-button>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-tooltip title="查看">
                <a-button type="link" size="small" @click="handleView(record)">
                  <EyeOutlined />
                </a-button>
              </a-tooltip>
              <a-tooltip title="编辑">
                <a-button type="link" size="small" @click="handleEdit(record)">
                  <EditOutlined />
                </a-button>
              </a-tooltip>
              <a-dropdown>
                <a-button type="link" size="small">
                  <MoreOutlined />
                </a-button>
                <template #overlay>
                  <a-menu>
                    <a-menu-item v-if="record.status === 'draft'" @click="handlePublish(record, 'publish')">
                      <CheckCircleOutlined /> 发布
                    </a-menu-item>
                    <a-menu-item v-if="record.status === 'published'" @click="handlePublish(record, 'unpublish')">
                      <CloseCircleOutlined /> 取消发布
                    </a-menu-item>
                    <a-menu-item v-if="record.status !== 'archived'" @click="handlePublish(record, 'archive')">
                      <FolderOutlined /> 归档
                    </a-menu-item>
                    <a-menu-divider />
                    <a-menu-item danger @click="handleDelete(record)">
                      <DeleteOutlined /> 删除
                    </a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- Create/Edit Modal -->
    <a-modal
      v-model:open="modalVisible"
      :title="editingRecord ? '编辑报表' : '新建报表'"
      width="800px"
      @ok="handleSubmit"
      :confirmLoading="submitting"
    >
      <a-form ref="formRef" :model="formState" :rules="formRules" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="报表名称" name="name">
              <a-input v-model:value="formState.name" placeholder="请输入报表名称" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="数据源" name="datasource">
              <a-select v-model:value="formState.datasource" placeholder="选择数据源">
                <a-select-option v-for="ds in datasources" :key="ds.id" :value="ds.id">
                  {{ ds.name }} ({{ ds.type }})
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="描述" name="description">
          <a-textarea v-model:value="formState.description" placeholder="请输入描述" :rows="2" />
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="展示类型" name="display_type">
              <a-select v-model:value="formState.display_type">
                <a-select-option value="table">表格</a-select-option>
                <a-select-option value="line">折线图</a-select-option>
                <a-select-option value="bar">柱状图</a-select-option>
                <a-select-option value="pie">饼图</a-select-option>
                <a-select-option value="card">卡片指标</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="是否公开">
              <a-switch v-model:checked="formState.is_public" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="SQL查询" name="query_sql">
          <a-textarea
            v-model:value="formState.query_sql"
            placeholder="SELECT * FROM table_name WHERE ..."
            :rows="5"
            style="font-family: monospace"
          />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- View Report Modal -->
    <a-modal
      v-model:open="viewModalVisible"
      :title="currentReport?.name || '报表详情'"
      width="1000px"
      :footer="null"
    >
      <div v-if="queryLoading" style="text-align: center; padding: 50px">
        <a-spin size="large" />
        <p style="margin-top: 16px; color: #999">正在加载数据...</p>
      </div>
      <div v-else-if="queryError" style="text-align: center; padding: 50px">
        <a-result status="error" :title="queryError" />
      </div>
      <div v-else>
        <!-- Table display -->
        <div v-if="currentReport?.display_type === 'table'">
          <a-table
            :columns="reportColumns"
            :data-source="reportData"
            :pagination="{ pageSize: 10 }"
            size="small"
            :scroll="{ x: 'max-content' }"
          />
        </div>

        <!-- Chart display -->
        <div v-else-if="['line', 'bar', 'pie'].includes(currentReport?.display_type)" class="chart-container">
          <div ref="chartRef" style="width: 100%; height: 400px"></div>
        </div>

        <!-- Card display -->
        <div v-else-if="currentReport?.display_type === 'card'" class="card-container">
          <a-row :gutter="16">
            <a-col v-for="(item, index) in cardData" :key="index" :span="6">
              <a-card>
                <a-statistic :title="item.label" :value="item.value" :precision="item.precision || 0" />
              </a-card>
            </a-col>
          </a-row>
        </div>

        <!-- Export buttons -->
        <div style="margin-top: 16px; text-align: right">
          <a-space>
            <a-button @click="handleExport('excel')">
              <FileExcelOutlined /> 导出Excel
            </a-button>
            <a-button @click="handleExport('csv')">
              <FileTextOutlined /> 导出CSV
            </a-button>
          </a-space>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, watch } from 'vue'
import { message } from 'ant-design-vue'
import {
  PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined, MoreOutlined,
  StarFilled, StarOutlined, CheckCircleOutlined, CloseCircleOutlined,
  FolderOutlined, FileExcelOutlined, FileTextOutlined
} from '@ant-design/icons-vue'
import * as echarts from 'echarts'
import {
  getReports, getReport, createReport, updateReport, deleteReport,
  queryReport, exportReport, publishReport, toggleFavorite, removeFavorite,
  getDataSources
} from '@/api/report'

// Data
const reports = ref([])
const datasources = ref([])
const loading = ref(false)
const searchText = ref('')
const filterDisplayType = ref(null)
const filterStatus = ref(null)
const pagination = reactive({ current: 1, pageSize: 10, total: 0 })

// Modal
const modalVisible = ref(false)
const editingRecord = ref(null)
const submitting = ref(false)
const formRef = ref(null)
const formState = reactive({
  name: '',
  description: '',
  datasource: null,
  display_type: 'table',
  query_sql: '',
  is_public: false
})

const formRules = {
  name: [{ required: true, message: '请输入报表名称' }],
  datasource: [{ required: true, message: '请选择数据源' }],
  query_sql: [{ required: true, message: '请输入SQL查询' }]
}

// View Modal
const viewModalVisible = ref(false)
const currentReport = ref(null)
const queryLoading = ref(false)
const queryError = ref(null)
const reportData = ref([])
const reportColumns = ref([])
const cardData = ref([])
const chartRef = ref(null)
let chartInstance = null

// Constants
const displayTypeLabels = {
  table: '表格',
  line: '折线图',
  bar: '柱状图',
  pie: '饼图',
  funnel: '漏斗图',
  gauge: '仪表盘',
  card: '卡片指标'
}

const displayTypeColors = {
  table: 'blue',
  line: 'green',
  bar: 'orange',
  pie: 'purple',
  funnel: 'cyan',
  gauge: 'magenta',
  card: 'gold'
}

const statusLabels = {
  draft: '草稿',
  published: '已发布',
  archived: '已归档'
}

const statusBadge = {
  draft: 'default',
  published: 'success',
  archived: 'warning'
}

// Columns
const columns = [
  { title: '报表名称', key: 'name', width: 200 },
  { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
  { title: '数据源', dataIndex: 'datasource_name', key: 'datasource_name', width: 150 },
  { title: '类型', key: 'display_type', width: 100 },
  { title: '状态', key: 'status', width: 90 },
  { title: '浏览量', dataIndex: 'view_count', key: 'view_count', width: 80 },
  { title: '收藏', key: 'is_favorited', width: 60 },
  { title: '操作', key: 'action', width: 120, fixed: 'right' }
]

// Methods
const fetchReports = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      search: searchText.value || undefined,
      display_type: filterDisplayType.value || undefined,
      status: filterStatus.value || undefined
    }
    const res = await getReports(params)
    reports.value = res.results
    pagination.total = res.total
  } finally {
    loading.value = false
  }
}

const fetchDataSources = async () => {
  try {
    const res = await getDataSources({ page_size: 100 })
    datasources.value = res.results || []
  } catch (e) {
    console.error(e)
  }
}

const handleSearch = () => {
  pagination.current = 1
  fetchReports()
}

const handleTableChange = (pag) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchReports()
}

const handleCreate = () => {
  editingRecord.value = null
  Object.assign(formState, {
    name: '',
    description: '',
    datasource: null,
    display_type: 'table',
    query_sql: '',
    is_public: false
  })
  modalVisible.value = true
}

const handleEdit = async (record) => {
  editingRecord.value = record
  const detail = await getReport(record.id)
  Object.assign(formState, {
    name: detail.name,
    description: detail.description || '',
    datasource: detail.datasource,
    display_type: detail.display_type,
    query_sql: detail.query_config?.sql || detail.query_config?.query || '',
    is_public: detail.is_public
  })
  modalVisible.value = true
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true

    const data = {
      name: formState.name,
      description: formState.description,
      datasource: formState.datasource,
      display_type: formState.display_type,
      query_config: { sql: formState.query_sql },
      is_public: formState.is_public
    }

    if (editingRecord.value) {
      await updateReport(editingRecord.value.id, data)
      message.success('更新成功')
    } else {
      await createReport(data)
      message.success('创建成功')
    }
    modalVisible.value = false
    fetchReports()
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
    await deleteReport(record.id)
    message.success('删除成功')
    fetchReports()
  } catch (e) {
    console.error(e)
  }
}

const handlePublish = async (record, action) => {
  try {
    await publishReport(record.id, action)
    message.success('操作成功')
    fetchReports()
  } catch (e) {
    console.error(e)
  }
}

const handleToggleFavorite = async (record) => {
  try {
    if (record.is_favorited) {
      await removeFavorite(record.id)
      message.success('取消收藏')
    } else {
      await toggleFavorite(record.id)
      message.success('收藏成功')
    }
    fetchReports()
  } catch (e) {
    console.error(e)
  }
}

const handleView = async (record) => {
  currentReport.value = record
  viewModalVisible.value = true
  queryLoading.value = true
  queryError.value = null
  reportData.value = []
  reportColumns.value = []
  cardData.value = []

  try {
    const res = await queryReport(record.id, {})
    if (res.success) {
      const data = res.data || []
      const cols = res.columns || []

      if (record.display_type === 'table') {
        reportColumns.value = cols.map(col => ({
          title: col,
          dataIndex: col,
          key: col,
          ellipsis: true
        }))
        reportData.value = data.map((row, i) => {
          const obj = { key: i }
          cols.forEach((col, j) => {
            obj[col] = row[j]
          })
          return obj
        })
      } else if (['line', 'bar'].includes(record.display_type)) {
        await nextTick()
        renderLineBarChart(cols, data, record.display_type)
      } else if (record.display_type === 'pie') {
        await nextTick()
        renderPieChart(cols, data)
      } else if (record.display_type === 'card') {
        cardData.value = cols.map((col, i) => ({
          label: col,
          value: data[0]?.[i] || 0
        }))
      }
    } else {
      queryError.value = res.error || '查询失败'
    }
  } catch (e) {
    queryError.value = e.message || '查询失败'
  } finally {
    queryLoading.value = false
  }
}

const renderLineBarChart = (cols, data, type) => {
  if (!chartRef.value) return

  if (chartInstance) {
    chartInstance.dispose()
  }
  chartInstance = echarts.init(chartRef.value)

  // Assume first column is category, rest are series
  const categories = data.map(row => row[0])
  const series = cols.slice(1).map((col, i) => ({
    name: col,
    type: type,
    data: data.map(row => row[i + 1]),
    smooth: type === 'line'
  }))

  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: cols.slice(1),
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: type === 'bar',
      data: categories
    },
    yAxis: {
      type: 'value'
    },
    series
  }

  chartInstance.setOption(option)
}

const renderPieChart = (cols, data) => {
  if (!chartRef.value) return

  if (chartInstance) {
    chartInstance.dispose()
  }
  chartInstance = echarts.init(chartRef.value)

  // Assume first column is name, second is value
  const pieData = data.map(row => ({
    name: row[0],
    value: row[1]
  }))

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: cols[0] || '数据',
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          formatter: '{b}: {d}%'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold'
          }
        },
        data: pieData
      }
    ]
  }

  chartInstance.setOption(option)
}

const handleExport = async (format) => {
  if (!currentReport.value) return

  try {
    const res = await exportReport(currentReport.value.id, { format })
    const blob = new Blob([res], {
      type: format === 'excel'
        ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        : 'text/csv'
    })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${currentReport.value.name}.${format === 'excel' ? 'xlsx' : 'csv'}`
    a.click()
    window.URL.revokeObjectURL(url)
    message.success('导出成功')
  } catch (e) {
    message.error('导出失败')
  }
}

// Cleanup chart on modal close
watch(viewModalVisible, (val) => {
  if (!val && chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})

onMounted(() => {
  fetchReports()
  fetchDataSources()
})
</script>

<style scoped>
.page-container {
  padding: 16px;
}
.chart-container {
  padding: 16px;
  background: #fafafa;
  border-radius: 4px;
}
.card-container {
  padding: 16px;
}
</style>
