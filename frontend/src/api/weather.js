import { request, toQuery } from './client'

export const getSeoulWeather = (startDate, endDate) => request(
  `/api/weather/seoul?${toQuery({ start_date: startDate, end_date: endDate })}`,
)
