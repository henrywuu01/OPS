<template>
  <div class="page-container">
    <!-- 元表列表 -->
    <a-card title="配置表管理" :bordered="false">
      <template #extra>
        <a-button type="primary" @click="showCreateModal">
          <template #icon><plus-outlined /></template>
          新建配置表
        </a-button>
      </template>

      <a-table
        :columns="columns"
        :data-source="tableList"
        :loading="loading"
        :pagination="pagination"
        @change="handleTableChange"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="record.status === 'active' ? 'green' : 'red'">
              {{ record.status === 'active' ? '启用' : '禁用' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'need_audit'">
            <a-tag :color="record.need_audit ? 'blue' : 'default'">
              {{ record.need_audit ? '是' : '否' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'need_history'">
            <a-tag :color="record.need_history ? 'blue' : 'default'">
              {{ record.need_history ? '是' : '否' }}
            </a-tag>
          </template>
          <template v-if="column.key === 'field_count'">
            {{ record.field_config?.length || 0 }}
          </template>
          <template v-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="viewTableData(record)">
                查看数据
              </a-button>
              <a-button type="link" size="small" @click="editTable(record)">
                编辑
              </a-button>
              <a-popconfirm
                title="确定删除此配置表吗？"
                @confirm="deleteTable(record)"
              >
                <a-button type="link" size="small" danger>删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 新建/编辑元表弹窗 -->
    <a-modal
      v-model:open="modalVisible"
      :title="isEdit ? '编辑配置表' : '新建配置表'"
      :width="700"
      @ok="handleSubmit"
      :confirmLoading="submitLoading"
    >
      <a-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        :label-col="{ span: 5 }"
        :wrapper-col="{ span: 18 }"
      >
        <a-form-item label="表名" name="name">
          <a-input v-model:value="formData.name" placeholder="请输入英文表名" :disabled="isEdit" />
        </a-form-item>
        <a-form-item label="显示名称" name="display_name">
          <a-input v-model:value="formData.display_name" placeholder="请输入显示名称" />
        </a-form-item>
        <a-form-item label="描述" name="description">
          <a-textarea v-model:value="formData.description" placeholder="请输入描述" :rows="2" />
        </a-form-item>
        <a-form-item label="需要审批" name="need_audit">
          <a-switch v-model:checked="formData.need_audit" />
        </a-form-item>
        <a-form-item label="记录历史" name="need_history">
          <a-switch v-model:checked="formData.need_history" />
        </a-form-item>
        <a-form-item label="状态" name="status">
          <a-select v-model:value="formData.status">
            <a-select-option value="active">启用</a-select-option>
            <a-select-option value="inactive">禁用</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="字段配置" name="field_config">
          <div class="field-list">
            <div v-for="(field, index) in formData.field_config" :key="index" class="field-item">
              <a-row :gutter="8">
                <a-col :span="6">
                  <a-input v-model:value="field.name" placeholder="字段名" />
                </a-col>
                <a-col :span="6">
                  <a-input v-model:value="field.label" placeholder="显示名" />
                </a-col>
                <a-col :span="6">
                  <a-select v-model:value="field.type" placeholder="类型">
                    <a-select-option value="string">字符串</a-select-option>
                    <a-select-option value="integer">整数</a-select-option>
                    <a-select-option value="number">数字</a-select-option>
                    <a-select-option value="boolean">布尔</a-select-option>
                    <a-select-option value="text">长文本</a-select-option>
                    <a-select-option value="date">日期</a-select-option>
                    <a-select-option value="datetime">日期时间</a-select-option>
                    <a-select-option value="select">下拉选择</a-select-option>
                    <a-select-option value="json">JSON</a-select-option>
                  </a-select>
                </a-col>
                <a-col :span="4">
                  <a-checkbox v-model:checked="field.required">必填</a-checkbox>
                </a-col>
                <a-col :span="2">
                  <a-button type="link" danger @click="removeField(index)">
                    <delete-outlined />
                  </a-button>
                </a-col>
              </a-row>
            </div>
            <a-button type="dashed" block @click="addField">
              <plus-outlined /> 添加字段
            </a-button>
          </div>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 查看配置数据弹窗 -->
    <a-modal
      v-model:open="dataModalVisible"
      :title="`${currentTable?.display_name || '配置'} - 数据列表`"
      :width="900"
      :footer="null"
    >
      <a-table
        :columns="dataColumns"
        :data-source="tableData"
        :loading="dataLoading"
        :pagination="dataPagination"
        @change="handleDataTableChange"
        row-key="id"
        size="small"
      />
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons-vue'
import request from '@/api/request'

// 元表列表
const tableList = ref([])
const loading = ref(false)
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total) => `共 ${total} 条`
})

const columns = [
  { title: '表名', dataIndex: 'name', key: 'name' },
  { title: '显示名称', dataIndex: 'display_name', key: 'display_name' },
  { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
  { title: '字段数', key: 'field_count', width: 80 },
  { title: '需要审批', key: 'need_audit', width: 90 },
  { title: '记录历史', key: 'need_history', width: 90 },
  { title: '状态', key: 'status', width: 80 },
  { title: '操作', key: 'action', width: 200, fixed: 'right' }
]

// 加载元表列表
const fetchTableList = async () => {
  loading.value = true
  try {
    const res = await request.get('/config/tables/', {
      params: {
        page: pagination.current,
        page_size: pagination.pageSize
      }
    })
    tableList.value = res.items || []
    pagination.total = res.total || 0
  } catch (error) {
    console.error('加载失败:', error)
  } finally {
    loading.value = false
  }
}

const handleTableChange = (pag) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchTableList()
}

// 新建/编辑弹窗
const modalVisible = ref(false)
const isEdit = ref(false)
const submitLoading = ref(false)
const formRef = ref(null)
const formData = reactive({
  name: '',
  display_name: '',
  description: '',
  need_audit: false,
  need_history: true,
  status: 'active',
  field_config: []
})

const formRules = {
  name: [{ required: true, message: '请输入表名' }],
  display_name: [{ required: true, message: '请输入显示名称' }]
}

const showCreateModal = () => {
  isEdit.value = false
  Object.assign(formData, {
    name: '',
    display_name: '',
    description: '',
    need_audit: false,
    need_history: true,
    status: 'active',
    field_config: []
  })
  modalVisible.value = true
}

const editTable = (record) => {
  isEdit.value = true
  Object.assign(formData, {
    id: record.id,
    name: record.name,
    display_name: record.display_name,
    description: record.description,
    need_audit: record.need_audit,
    need_history: record.need_history,
    status: record.status,
    field_config: [...(record.field_config || [])]
  })
  modalVisible.value = true
}

const addField = () => {
  formData.field_config.push({
    name: '',
    label: '',
    type: 'string',
    required: false
  })
}

const removeField = (index) => {
  formData.field_config.splice(index, 1)
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitLoading.value = true

    if (isEdit.value) {
      await request.put(`/config/tables/${formData.id}/`, formData)
      message.success('更新成功')
    } else {
      await request.post('/config/tables/', formData)
      message.success('创建成功')
    }

    modalVisible.value = false
    fetchTableList()
  } catch (error) {
    if (error.errorFields) return
    message.error(error.message || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

const deleteTable = async (record) => {
  try {
    await request.delete(`/config/tables/${record.id}/`)
    message.success('删除成功')
    fetchTableList()
  } catch (error) {
    message.error(error.message || '删除失败')
  }
}

// 查看配置数据
const dataModalVisible = ref(false)
const currentTable = ref(null)
const tableData = ref([])
const dataLoading = ref(false)
const dataPagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0
})

const dataColumns = computed(() => {
  if (!currentTable.value?.field_config) return []
  const cols = currentTable.value.field_config.map(f => ({
    title: f.label || f.name,
    dataIndex: f.name,
    key: f.name,
    ellipsis: true
  }))
  cols.unshift({ title: 'ID', dataIndex: 'id', key: 'id', width: 60 })
  return cols
})

const viewTableData = async (record) => {
  currentTable.value = record
  dataModalVisible.value = true
  dataPagination.current = 1
  await fetchTableData()
}

const fetchTableData = async () => {
  if (!currentTable.value) return
  dataLoading.value = true
  try {
    const res = await request.get(`/config/${currentTable.value.name}/`, {
      params: {
        page: dataPagination.current,
        page_size: dataPagination.pageSize
      }
    })
    tableData.value = res.items || res.results || []
    dataPagination.total = res.total || 0
  } catch (error) {
    console.error('加载数据失败:', error)
    tableData.value = []
  } finally {
    dataLoading.value = false
  }
}

const handleDataTableChange = (pag) => {
  dataPagination.current = pag.current
  dataPagination.pageSize = pag.pageSize
  fetchTableData()
}

onMounted(() => {
  fetchTableList()
})
</script>

<style scoped>
.page-container {
  padding: 16px;
}

.field-list {
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  padding: 12px;
  background: #fafafa;
}

.field-item {
  margin-bottom: 8px;
  padding: 8px;
  background: #fff;
  border-radius: 4px;
}

.field-item:last-child {
  margin-bottom: 12px;
}
</style>
