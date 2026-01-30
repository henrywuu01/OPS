<template>
  <div class="page-container">
    <!-- Search Bar -->
    <a-card class="search-card">
      <a-form layout="inline" :model="searchForm">
        <a-form-item label="关键词">
          <a-input v-model:value="searchForm.search" placeholder="用户名/姓名/邮箱/手机" allow-clear style="width: 200px" />
        </a-form-item>
        <a-form-item label="部门">
          <a-tree-select
            v-model:value="searchForm.department"
            :tree-data="departmentTree"
            placeholder="选择部门"
            allow-clear
            style="width: 180px"
            :field-names="{ label: 'name', value: 'id', children: 'children' }"
          />
        </a-form-item>
        <a-form-item label="状态">
          <a-select v-model:value="searchForm.is_active" placeholder="全部" allow-clear style="width: 100px">
            <a-select-option :value="true">启用</a-select-option>
            <a-select-option :value="false">禁用</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item>
          <a-space>
            <a-button type="primary" @click="handleSearch">
              <template #icon><SearchOutlined /></template>
              搜索
            </a-button>
            <a-button @click="handleReset">
              <template #icon><ReloadOutlined /></template>
              重置
            </a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>

    <!-- Data Table -->
    <a-card class="table-card">
      <template #title>
        <span>用户列表</span>
      </template>
      <template #extra>
        <a-button type="primary" @click="handleAdd">
          <template #icon><PlusOutlined /></template>
          新增用户
        </a-button>
      </template>

      <a-table
        :columns="columns"
        :data-source="userList"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'avatar'">
            <a-avatar :src="record.avatar" :size="36">
              <template #icon><UserOutlined /></template>
            </a-avatar>
          </template>
          <template v-else-if="column.key === 'is_active'">
            <a-tag :color="record.is_active ? 'success' : 'error'">
              {{ record.is_active ? '启用' : '禁用' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'roles'">
            <a-tag v-for="role in record.roles" :key="role" color="blue">{{ role }}</a-tag>
            <span v-if="!record.roles?.length">-</span>
          </template>
          <template v-else-if="column.key === 'mfa_enabled'">
            <a-tag :color="record.mfa_enabled ? 'success' : 'default'">
              {{ record.mfa_enabled ? '已开启' : '未开启' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="handleEdit(record)">编辑</a-button>
              <a-button type="link" size="small" @click="handleResetPassword(record)">重置密码</a-button>
              <a-button
                type="link"
                size="small"
                :danger="record.is_active"
                @click="handleToggleStatus(record)"
              >
                {{ record.is_active ? '禁用' : '启用' }}
              </a-button>
              <a-popconfirm
                title="确定要删除该用户吗？"
                @confirm="handleDelete(record)"
              >
                <a-button type="link" size="small" danger>删除</a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- User Form Modal -->
    <a-modal
      v-model:open="formVisible"
      :title="isEdit ? '编辑用户' : '新增用户'"
      :confirm-loading="submitLoading"
      width="600px"
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
        <a-form-item label="用户名" name="username">
          <a-input v-model:value="formData.username" placeholder="请输入用户名" :disabled="isEdit" />
        </a-form-item>
        <a-form-item v-if="!isEdit" label="密码" name="password">
          <a-input-password v-model:value="formData.password" placeholder="请输入密码" />
        </a-form-item>
        <a-form-item label="真实姓名" name="real_name">
          <a-input v-model:value="formData.real_name" placeholder="请输入真实姓名" />
        </a-form-item>
        <a-form-item label="邮箱" name="email">
          <a-input v-model:value="formData.email" placeholder="请输入邮箱" />
        </a-form-item>
        <a-form-item label="手机号" name="phone">
          <a-input v-model:value="formData.phone" placeholder="请输入手机号" />
        </a-form-item>
        <a-form-item label="部门" name="department">
          <a-tree-select
            v-model:value="formData.department"
            :tree-data="departmentTree"
            placeholder="选择部门"
            allow-clear
            style="width: 100%"
            :field-names="{ label: 'name', value: 'id', children: 'children' }"
          />
        </a-form-item>
        <a-form-item label="角色" name="role_ids">
          <a-select
            v-model:value="formData.role_ids"
            mode="multiple"
            placeholder="选择角色"
            style="width: 100%"
          >
            <a-select-option v-for="role in roleList" :key="role.id" :value="role.id">
              {{ role.name }}
            </a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="数据权限" name="data_scope">
          <a-select v-model:value="formData.data_scope" placeholder="选择数据权限">
            <a-select-option value="ALL">全部数据</a-select-option>
            <a-select-option value="DEPT">本部门数据</a-select-option>
            <a-select-option value="DEPT_CHILD">本部门及子部门</a-select-option>
            <a-select-option value="SELF">仅本人数据</a-select-option>
          </a-select>
        </a-form-item>
        <a-form-item label="状态" name="is_active">
          <a-switch v-model:checked="formData.is_active" checked-children="启用" un-checked-children="禁用" />
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- Reset Password Modal -->
    <a-modal
      v-model:open="resetPwdVisible"
      title="重置密码"
      :confirm-loading="submitLoading"
      @ok="handleResetPwdSubmit"
      @cancel="resetPwdVisible = false"
    >
      <a-form :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-item label="用户">
          <span>{{ currentUser?.username }}</span>
        </a-form-item>
        <a-form-item label="新密码">
          <a-input-password v-model:value="newPassword" placeholder="请输入新密码，留空则使用默认密码" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import {
  SearchOutlined,
  ReloadOutlined,
  PlusOutlined,
  UserOutlined,
} from '@ant-design/icons-vue'
import {
  getUsers,
  createUser,
  updateUser,
  deleteUser,
  toggleUserStatus,
  resetUserPassword,
  getDepartmentTree,
  getRoles,
} from '@/api/users'

// Search form
const searchForm = reactive({
  search: '',
  department: null,
  is_active: null,
})

// Table data
const loading = ref(false)
const userList = ref([])
const departmentTree = ref([])
const roleList = ref([])
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total) => `共 ${total} 条`,
})

// Table columns
const columns = [
  { title: '头像', key: 'avatar', width: 60 },
  { title: '用户名', dataIndex: 'username', key: 'username' },
  { title: '真实姓名', dataIndex: 'real_name', key: 'real_name' },
  { title: '邮箱', dataIndex: 'email', key: 'email' },
  { title: '手机号', dataIndex: 'phone', key: 'phone' },
  { title: '部门', dataIndex: 'department_name', key: 'department_name' },
  { title: '角色', key: 'roles' },
  { title: 'MFA', key: 'mfa_enabled', width: 80 },
  { title: '状态', key: 'is_active', width: 80 },
  { title: '操作', key: 'action', width: 220, fixed: 'right' },
]

// Form modal
const formVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const submitLoading = ref(false)
const formData = reactive({
  id: null,
  username: '',
  password: '',
  real_name: '',
  email: '',
  phone: '',
  department: null,
  role_ids: [],
  data_scope: 'SELF',
  is_active: true,
})

const formRules = {
  username: [
    { required: true, message: '请输入用户名' },
    { min: 3, max: 50, message: '用户名长度为3-50个字符' },
  ],
  password: [
    { required: true, message: '请输入密码' },
    { min: 8, message: '密码长度不能少于8个字符' },
  ],
  email: [
    { type: 'email', message: '请输入正确的邮箱格式' },
  ],
}

// Reset password modal
const resetPwdVisible = ref(false)
const currentUser = ref(null)
const newPassword = ref('')

// Fetch user list
const fetchUsers = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      ...searchForm,
    }
    // Clean undefined params
    Object.keys(params).forEach(key => {
      if (params[key] === null || params[key] === undefined || params[key] === '') {
        delete params[key]
      }
    })
    const res = await getUsers(params)
    userList.value = res.results || res
    pagination.total = res.total || res.length
  } catch (error) {
    console.error('Failed to fetch users:', error)
  } finally {
    loading.value = false
  }
}

// Fetch departments and roles
const fetchDepartmentsAndRoles = async () => {
  try {
    const [deptRes, roleRes] = await Promise.all([
      getDepartmentTree(),
      getRoles(),
    ])
    departmentTree.value = deptRes || []
    roleList.value = roleRes || []
  } catch (error) {
    console.error('Failed to fetch departments/roles:', error)
  }
}

// Search
const handleSearch = () => {
  pagination.current = 1
  fetchUsers()
}

// Reset
const handleReset = () => {
  searchForm.search = ''
  searchForm.department = null
  searchForm.is_active = null
  pagination.current = 1
  fetchUsers()
}

// Table change
const handleTableChange = (pag) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchUsers()
}

// Add user
const handleAdd = () => {
  isEdit.value = false
  Object.assign(formData, {
    id: null,
    username: '',
    password: '',
    real_name: '',
    email: '',
    phone: '',
    department: null,
    role_ids: [],
    data_scope: 'SELF',
    is_active: true,
  })
  formVisible.value = true
}

// Edit user
const handleEdit = (record) => {
  isEdit.value = true
  Object.assign(formData, {
    id: record.id,
    username: record.username,
    password: '',
    real_name: record.real_name,
    email: record.email,
    phone: record.phone,
    department: record.department,
    role_ids: [], // Will be loaded from API if needed
    data_scope: record.data_scope,
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
      delete data.password
      delete data.username
      await updateUser(formData.id, data)
      message.success('更新成功')
    } else {
      await createUser(data)
      message.success('创建成功')
    }
    formVisible.value = false
    fetchUsers()
  } catch (error) {
    if (error.errorFields) {
      // Validation error
      return
    }
    console.error('Failed to save user:', error)
  } finally {
    submitLoading.value = false
  }
}

// Toggle status
const handleToggleStatus = async (record) => {
  try {
    await toggleUserStatus(record.id)
    message.success('状态更新成功')
    fetchUsers()
  } catch (error) {
    console.error('Failed to toggle status:', error)
  }
}

// Delete user
const handleDelete = async (record) => {
  try {
    await deleteUser(record.id)
    message.success('删除成功')
    fetchUsers()
  } catch (error) {
    console.error('Failed to delete user:', error)
  }
}

// Reset password
const handleResetPassword = (record) => {
  currentUser.value = record
  newPassword.value = ''
  resetPwdVisible.value = true
}

const handleResetPwdSubmit = async () => {
  try {
    submitLoading.value = true
    await resetUserPassword(currentUser.value.id, { password: newPassword.value || undefined })
    message.success('密码重置成功')
    resetPwdVisible.value = false
  } catch (error) {
    console.error('Failed to reset password:', error)
  } finally {
    submitLoading.value = false
  }
}

// Init
onMounted(() => {
  fetchUsers()
  fetchDepartmentsAndRoles()
})
</script>

<style scoped>
.page-container {
  padding: 16px;
}

.search-card {
  margin-bottom: 16px;
}

.table-card :deep(.ant-card-body) {
  padding: 0;
}

.table-card :deep(.ant-table) {
  padding: 0 16px 16px;
}
</style>
