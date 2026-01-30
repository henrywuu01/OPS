import request from './request'

export function login(data) {
  return request.post('/auth/login/', data)
}

export function logout() {
  return request.post('/auth/logout/')
}

export function refreshToken(data) {
  return request.post('/auth/refresh/', data)
}

export function changePassword(data) {
  return request.post('/auth/password/change/', data)
}

export function resetPassword(data) {
  return request.post('/auth/password/reset/', data)
}

export function getProfile() {
  return request.get('/auth/profile/')
}

export function updateProfile(data) {
  return request.put('/auth/profile/', data)
}

export function bindMFA(data) {
  return request.post('/auth/mfa/bind/', data)
}

export function verifyMFA(data) {
  return request.post('/auth/mfa/verify/', data)
}
