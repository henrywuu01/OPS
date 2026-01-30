import request from './request'

// User Management
export function getUsers(params) {
  return request.get('/auth/users/', { params })
}

export function getUser(id) {
  return request.get(`/auth/users/${id}/`)
}

export function createUser(data) {
  return request.post('/auth/users/', data)
}

export function updateUser(id, data) {
  return request.put(`/auth/users/${id}/`, data)
}

export function deleteUser(id) {
  return request.delete(`/auth/users/${id}/`)
}

export function toggleUserStatus(id) {
  return request.post(`/auth/users/${id}/status/`)
}

export function resetUserPassword(id, data) {
  return request.post(`/auth/users/${id}/reset-password/`, data)
}

// Department Management
export function getDepartments(params) {
  return request.get('/auth/departments/', { params })
}

export function getDepartmentTree() {
  return request.get('/auth/departments/tree/')
}

export function createDepartment(data) {
  return request.post('/auth/departments/', data)
}

export function updateDepartment(id, data) {
  return request.put(`/auth/departments/${id}/`, data)
}

export function deleteDepartment(id) {
  return request.delete(`/auth/departments/${id}/`)
}

// Role Management
export function getRoles(params) {
  return request.get('/auth/roles/', { params })
}

export function getRole(id) {
  return request.get(`/auth/roles/${id}/`)
}

export function createRole(data) {
  return request.post('/auth/roles/', data)
}

export function updateRole(id, data) {
  return request.put(`/auth/roles/${id}/`, data)
}

export function deleteRole(id) {
  return request.delete(`/auth/roles/${id}/`)
}

export function getRolePermissions(id) {
  return request.get(`/auth/roles/${id}/permissions/`)
}

export function setRolePermissions(id, data) {
  return request.put(`/auth/roles/${id}/permissions/`, data)
}

// Permission Management
export function getPermissions(params) {
  return request.get('/auth/permissions/', { params })
}

export function getPermissionTree() {
  return request.get('/auth/permissions/tree/')
}
