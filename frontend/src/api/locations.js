import { request, toQuery } from './client'

export const getLocations = (params = {}) => request(`/api/locations?${toQuery(params)}`)
export const getLocation = (id) => request(`/api/locations/${id}`)
export const getCrowd = (id) => request(`/api/locations/${id}/crowd`)
export const getMapLocations = (contentType) => request(`/api/map/locations?${toQuery({ content_type: contentType })}`)
export const searchMapLocations = (query) => request(`/api/map/search?${toQuery({ query })}`)
