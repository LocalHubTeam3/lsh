import { request, toQuery } from './client'

export const getCourses = (params = {}) => request(`/api/courses?${toQuery(params)}`)
export const getCourse = (id) => request(`/api/courses/${id}`)

export const createCourse = (payload) => request('/api/courses', {
  method: 'POST',
  body: JSON.stringify(payload),
})
export const updateCourse = (id, payload) => request(`/api/courses/${id}`, { method: 'PUT', body: JSON.stringify(payload) })
export const deleteCourse = (id, password) => request(`/api/courses/${id}`, { method: 'DELETE', body: JSON.stringify({ password }) })
