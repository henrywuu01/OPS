<template>
  <div class="page-container">
    <!-- Toolbar -->
    <a-card class="toolbar-card">
      <a-row justify="space-between" align="middle">
        <a-col>
          <a-space>
            <a-input-search
              v-model:value="searchText"
              placeholder="搜索角色名称/编码"
              style="width: 250px"
              allow-clear
              @search="handleSearch"
            />
          </a-space>
        </a-col>
        <a-col>
          <a-button type="primary" @click="handleAdd">
            <template #icon><PlusOutlined /></template>
            新增角色
          </a-button>
        </a-col>
      </a-row>
    </a-card>

    <!-- Data Table -->
    <a-card class="table-card">
      <a-table
        :columns="columns"
        :data-source="filteredRoles"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'is_active'">
            <a-tag :color="record.is_active ? 'success' : 'error'">
              {{ record.is_active ? '启用' : '禁用' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'permissions'">
            <a-tag v-if="record.permissions?.length">{{ record.permissions.length }} 个权限</a-tag>
            <span v-else>-</span>
          </template>
          <template v-else-if="column.key === 'created_at'">
            {{ formatDate(record.created_at) }}
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="handleEdit(record)">编辑</a-button>
              <a-button type="link" size="small" @click="handlePermissions(record)">权限配置</a-button>
              <a-popconfirm
                title="确定要删除该角色吗？"
                @confirm="handleDelete(record)"
              >
                <a-button type="link" size="small" danger>删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- Role Form Modal -->
    <a-modal
      v-model:open="formVisible"
      :title="isEdit ? '编辑角色' : '新增角色'"
      :confirm-loading="submitLoading"
      width="500px"
      @ok="handleSubmit"
      @cancel="formVisible = false"
    >
      <a-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        :label-col="{ span: 6 }"
        :wrapper-col="{ span: 16 }"
      >
        <a-form-item label="角色名称" name="name">
          <a-input v-model:value="formData.name" placeholder="请输入角色名称" />
        </a-form-item>
        <a-form-item label="角色编码" name="code">
          <a-input v-model:value="formData.code" placeholder="请输入角色编码" :disabled="isEdit" />
        </a-form-item>
        <a-form-item label="描述" name="description">
          <a-textarea v-model:value="formData.description" placeholder="请输入描述" :rows="3" />
        </a-form-item>
        <a-form-item label="上级角色" name="parent">
          <a-select v-model:value="formData.parent" placeholder="选择上级角色" allow-clear>
            <a-select-option v-for="role in roleList" :key="role.id" :value="role.id" :disabled="role.id === formData.id">
              {{ role.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="排序" name="sort_order">
          <a-input-number v-model:value="formData.sort_order" :min="0" style="width: 100%" />
        </a-form-item>
        <a-form-item label="状态" name="is_active">
          <a-switch v-model:checked="formData.is_active" checked-children="启用" un-checked-children="禁用" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Permission Modal -->
    <a-modal
      v-model:open="permissionVisible"
      title="权限配置"
      :confirm-loading="submitLoading"
      width="600px"
      @ok="handlePermissionSubmit"
      @cancel="permissionVisible = false"
    >
      <div class="permission-header">
        <span>角色: {{ currentRole?.name }}</span>
        <a-space>
          <a-button size="small" @click="handleExpandAll">展开全部</a-button>
          <a-button size="small" @click="handleCollapseAll">收起全部</a-button>
        </a-space>
      </div>
      <a-tree
        v-if="permissionTree.length"
        ref="treeRef"
        v-model:checked-keys="checkedPermissions"
        v-model:expanded-keys="expandedKeys"
        :tree-data="permissionTree"
        checkable
        :field-names="{ title: 'name', key: 'id', children: 'children' }"
        :height="400"
      />
      <a-empty v-else description="暂无权限数据" />
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import {
  getRoles,
  createRole,
  updateRole,
  deleteRole,
  getRolePermissions,
  setRolePermissions,
  getPermissionTree,
} from '@/api/users'

// Search
const searchText = ref('')

// Table data
const loading = ref(false)
const roleList = ref([])
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total) => `共 ${total} 条`,
})

// Filtered roles
const filteredRoles = computed(() => {
  if (!searchText.value) {
    return roleList.value
  }
  const text = searchText.value.toLowerCase()
  return roleList.value.filter(role =>
    role.name.toLowerCase().includes(text) ||
    role.code.toLowerCase().includes(text)
  )
})

// Table columns
const columns = [
  { title: '角色名称', dataIndex: 'name', key: 'name' },
  { title: '角色编码', dataIndex: 'code', key: 'code' },
  { title: '描述', dataIndex: 'description', key: 'description', ellipsis: true },
  { title: '上级角色', dataIndex: 'parent_name', key: 'parent_name' },
  { title: '权限', key: 'permissions', width: 100 },
  { title: '排序', dataIndex: 'sort_order', key: 'sort_order', width: 80 },
  { title: '状态', key: 'is_active', width: 80 },
  { title: '创建时间', key: 'created_at', width: 180 },
  { title: '操作', key: 'action', width: 180, fixed: 'right' },
]

// Form modal
const formVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const submitLoading = ref(false)
const formData = reactive({
  id: null,
  name: '',
  code: '',
  description: '',
  parent: null,
  sort_order: 0,
  is_active: true,
})

const formRules = {
  name: [
    { required: true, message: '请输入角色名称' },
    { max: 50, message: '角色名称不能超过50个字符' },
  ],
  code: [
    { required: true, message: '请输入角色编码' },
    { pattern: /^[a-zA-Z_][a-zA-Z0-9_]*$/, message: '编码只能包含字母、数字和下划线，且以字母或下划线开头' },
  ],
}

// Permission modal
const permissionVisible = ref(false)
const currentRole = ref(null)
const permissionTree = ref([])
const checkedPermissions = ref([])
const expandedKeys = ref([])
const treeRef = ref(null)

// Fetch role list
const fetchRoles = async () => {
  loading.value = true
  try {
    const res = await getRoles()
    roleList.value = res || []
    pagination.total = roleList.value.length
  } catch (error) {
    console.error('Failed to fetch roles:', error)
  } finally {
    loading.value = false
  }
}

// Fetch permission tree
const fetchPermissionTree = async () => {
  try {
    const res = await getPermissionTree()
    permissionTree.value = res || []
    // Get all keys for expand
    const getAllKeys = (nodes) => {
      let keys = []
      nodes.forEach(node => {
        keys.push(node.id)
        if (node.children?.length) {
          keys = keys.concat(getAllKeys(node.children))
        }
      })
      return keys
    }
    expandedKeys.value = getAllKeys(permissionTree.value)
  } catch (error) {
    console.error('Failed to fetch permission tree:', error)
  }
}

// Format date
const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN')
}

// Search
const handleSearch = () => {
  pagination.current = 1
}

// Table change
const handleTableChange = (pag) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
}

// Add role
const handleAdd = () => {
  isEdit.value = false
  Object.assign(formData, {
    id: null,
    name: '',
    code: '',
    description: '',
    parent: null,
    sort_order: 0,
    is_active: true,
  })
  formVisible.value = true
}

// Edit role
const handleEdit = (record) => {
  isEdit.value = true
  Object.assign(formData, {
    id: record.id,
    name: record.name,
    code: record.code,
    description: record.description,
    parent: record.parent,
    sort_order: record.sort_order,
    is_active: record.is_active,
  })
  formVisible.value = true
}

// Submit form
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitLoading.value = true

    const data = { ...formData }
    delete data.id

    if (isEdit.value) {
      delete data.code
      await updateRole(formData.id, data)
      message.success('更新成功')
    } else {
      await createRole(data)
      message.success('创建成功')
    }
    formVisible.value = false
    fetchRoles()
  } catch (error) {
    if (error.errorFields) {
      return
    }
    console.error('Failed to save role:', error)
  } finally {
    submitLoading.value = false
  }
}

// Delete role
const handleDelete = async (record) => {
  try {
    await deleteRole(record.id)
    message.success('删除成功')
    fetchRoles()
  } catch (error) {
    console.error('Failed to delete role:', error)
  }
}

// Permission management
const handlePermissions = async (record) => {
  currentRole.value = record
  try {
    const res = await getRolePermissions(record.id)
    checkedPermissions.value = res.permissions || []
  } catch (error) {
    console.error('Failed to fetch role permissions:', error)
    checkedPermissions.value = []
  }
  permissionVisible.value = true
}

const handlePermissionSubmit = async () => {
  try {
    submitLoading.value = true
    await setRolePermissions(currentRole.value.id, {
      permissions: checkedPermissions.value,
    })
    message.success('权限配置成功')
    permissionVisible.value = false
    fetchRoles()
  } catch (error) {
    console.error('Failed to set permissions:', error)
  } finally {
    submitLoading.value = false
  }
}

const handleExpandAll = () => {
  const getAllKeys = (nodes) => {
    let keys = []
    nodes.forEach(node => {
      keys.push(node.id)
      if (node.children?.length) {
        keys = keys.concat(getAllKeys(node.children))
      }
    })
    return keys
  }
  expandedKeys.value = getAllKeys(permissionTree.value)
}

const handleCollapseAll = () => {
  expandedKeys.value = []
}

// Init
onMounted(() => {
  fetchRoles()
  fetchPermissionTree()
})
</script>

<style scoped>
.page-container {
  padding: 16px;
}

.toolbar-card {
  margin-bottom: 16px;
}

.table-card :deep(.ant-card-body) {
  padding: 16px;
}

.permission-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}
</style>
