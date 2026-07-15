import { request, toQuery } from './client'

export const getPosts = (params = {}) => request(`/api/posts?${toQuery(params)}`)
export const getPost = (id) => request(`/api/posts/${id}`)
export const createPost = (payload) => request('/api/posts', { method: 'POST', body: JSON.stringify(payload) })
export const updatePost = (id, payload) => request(`/api/posts/${id}`, { method: 'PUT', body: JSON.stringify(payload) })
export const deletePost = (id, password) => request(`/api/posts/${id}`, { method: 'DELETE', body: JSON.stringify({ password }) })
