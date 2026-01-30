import request from './request'

// DataSource APIs
export function getDataSources(params) {
  return request.get('/reports/datasources/', { params })
}

export function getDataSource(id) {
  return request.get(`/reports/datasources/${id}/`)
}

export function createDataSource(data) {
  return request.post('/reports/datasources/', data)
}

export function updateDataSource(id, data) {
  return request.put(`/reports/datasources/${id}/`, data)
}

export function deleteDataSource(id) {
  return request.delete(`/reports/datasources/${id}/`)
}

export function testDataSource(id) {
  return request.post(`/reports/datasources/${id}/test/`)
}

// Report APIs
export function getReports(params) {
  return request.get('/reports/reports/', { params })
}

export function getReport(id) {
  return request.get(`/reports/reports/${id}/`)
}

export function createReport(data) {
  return request.post('/reports/reports/', data)
}

export function updateReport(id, data) {
  return request.put(`/reports/reports/${id}/`, data)
}

export function deleteReport(id) {
  return request.delete(`/reports/reports/${id}/`)
}

export function queryReport(id, data) {
  return request.post(`/reports/reports/${id}/query/`, data)
}

export function exportReport(id, data) {
  return request.post(`/reports/reports/${id}/export/`, data, {
    responseType: 'blob'
  })
}

export function publishReport(id, action) {
  return request.post(`/reports/reports/${id}/publish/`, { action })
}

// Favorite APIs
export function toggleFavorite(id) {
  return request.post(`/reports/reports/${id}/favorite/`)
}

export function removeFavorite(id) {
  return request.delete(`/reports/reports/${id}/favorite/`)
}

export function getFavoriteReports(params) {
  return request.get('/reports/favorites/', { params })
}

// Subscription APIs
export function getSubscriptions(reportId) {
  return request.get(`/reports/reports/${reportId}/subscriptions/`)
}

export function createSubscription(reportId, data) {
  return request.post(`/reports/reports/${reportId}/subscriptions/`, data)
}

export function updateSubscription(reportId, subId, data) {
  return request.put(`/reports/reports/${reportId}/subscriptions/${subId}/`, data)
}

export function deleteSubscription(reportId, subId) {
  return request.delete(`/reports/reports/${reportId}/subscriptions/${subId}/`)
}
