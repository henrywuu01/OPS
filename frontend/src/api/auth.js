import request from './request'

// Basic Authentication
export function login(data) {
  return request.post('/auth/login/', data)
}

export function register(data) {
  return request.post('/auth/register/', data)
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

// MFA
export function bindMFA(data) {
  return request.post('/auth/mfa/bind/', data)
}

export function verifyMFA(data) {
  return request.post('/auth/mfa/verify/', data)
}

// SSO
export function getSSOConfig() {
  return request.get('/auth/sso/config/')
}

export function getSSOLoginUrl(provider) {
  return request.get(`/auth/sso/${provider}/login/`)
}

export function ssoCallback(provider, data) {
  return request.post(`/auth/sso/${provider}/callback/`, data)
}

export function bindSSO(provider, data) {
  return request.post(`/auth/sso/${provider}/bind/`, data)
}

export function unbindSSO(provider) {
  return request.post(`/auth/sso/${provider}/unbind/`)
}
